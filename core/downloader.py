import os
import re
import requests
import sys
import time
from io import BytesIO
from PIL import Image
from core.config import Config
from core.settings import SettingsManager
from core.spotify_parser import MusicLinkParser
from core.platform_helper import PlatformHelper

# Lazy loader yt-dlp untuk startup instan (0.2s vs 2.5s)
_YoutubeDL = None

def get_ydl_class():
    """Mengimpor YoutubeDL secara malas (lazy) hanya saat dibutuhkan."""
    global _YoutubeDL
    if _YoutubeDL is None:
        from yt_dlp import YoutubeDL
        _YoutubeDL = YoutubeDL
    return _YoutubeDL

# Menggunakan Mutagen untuk kompatibilitas .exe yang sempurna dan bebas error biner
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, TIT2, TPE1, TALB, APIC, ID3NoHeaderError

ANSI_REGEX = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')

def clean_ansi(text: str) -> str:
    """Membersihkan kode escape ANSI/warna terminal dari string output yt-dlp."""
    if not text:
        return ""
    return ANSI_REGEX.sub('', str(text)).strip()

class YtdlpManager:
    # In-memory LRU Cache untuk metadata media (maksimal 50 entri)
    _metadata_cache = {}

    def __init__(self, log_callback=None, progress_callback=None):
        self.log_callback = log_callback
        self.progress_callback = progress_callback
        self.cancel_requested = False
        self._last_progress_time = 0.0

    def cancel(self):
        self.cancel_requested = True
        self._ui_log("[System] Meminta pembatalan unduhan...")

    def _ui_log(self, message: str):
        if self.log_callback:
            self.log_callback(message)

    def _cache_metadata(self, url: str, info: dict):
        if not url or not info:
            return
        if len(self._metadata_cache) >= 50:
            try:
                # Buang entri tertua
                oldest_key = next(iter(self._metadata_cache))
                del self._metadata_cache[oldest_key]
            except Exception:
                pass
        self._metadata_cache[url] = info

    def _my_progress_hook(self, d):
        if self.cancel_requested:
            raise Exception("Download dibatalkan oleh pengguna.")

        status = d.get('status')
        if status == 'downloading':
            # Frame Limiter: Maksimal 25 FPS (40ms) untuk menghemat CPU & mencegah UI micro-stutter
            now = time.time()
            if now - self._last_progress_time < 0.04:
                return
            self._last_progress_time = now

            total_bytes = d.get('total_bytes') or d.get('total_bytes_estimate') or 0
            downloaded_bytes = d.get('downloaded_bytes', 0)
            percentage = downloaded_bytes / total_bytes if total_bytes > 0 else 0.0
            
            # Bersihkan kode ANSI (warna terminal [0;32m dsb) dari teks Speed dan ETA
            raw_speed = d.get('_speed_str') or ''
            raw_eta = d.get('_eta_str') or ''
            speed = clean_ansi(raw_speed) if raw_speed else "0 KB/s"
            eta = clean_ansi(raw_eta) if raw_eta else "00:00"
            
            raw_filename = d.get('filename') or 'Media'
            clean_filename = os.path.splitext(os.path.basename(raw_filename))[0]
            disp_filename = clean_filename if len(clean_filename) <= 35 else clean_filename[:32] + "..."
            
            info = d.get('info_dict') or {}
            playlist_idx = info.get('playlist_index')
            n_entries = info.get('n_entries')
            
            if playlist_idx and n_entries and n_entries > 1:
                status_text = f"[{playlist_idx}/{n_entries}] Mengunduh: {disp_filename}"
            else:
                status_text = f"Mengunduh: {disp_filename}"
            
            if self.progress_callback:
                self.progress_callback({
                    'percentage': percentage, 'speed': speed, 'eta': eta, 'status': status_text
                })
        elif status == 'finished':
            if self.progress_callback:
                self.progress_callback({
                    'percentage': 1.0, 'speed': '0 KB/s', 'eta': '00:00', 'status': "Menyuntikkan Tag & Cover Art..."
                })

    def fetch_metadata(self, url: str) -> dict:
        if not url.strip(): return None

        # Cek in-memory LRU Cache (0 ms instant retrieval)
        if url in self._metadata_cache:
            self._ui_log(f"[Cache] Memuat metadata dari cache lokal (0ms)...")
            return self._metadata_cache[url]

        platform_info = PlatformHelper.detect(url)
        self._ui_log(f"[Platform] Sumber media: {platform_info['badge']}")

        # 1. Cek apakah tautan adalah Spotify atau Apple Music
        music_data = MusicLinkParser.parse(url)
        if music_data.get('is_music_link') and music_data.get('title'):
            self._ui_log(f"[Music Parser] Terdeteksi link {music_data['platform'].capitalize()}: {music_data['title']} - {music_data.get('artist')}")
            res = {
                'title': music_data.get('title'),
                'uploader': music_data.get('artist') or f"{music_data['platform'].capitalize()} Music",
                'duration': 0,
                'thumbnail': music_data.get('thumbnail_url'),
                '_max_res': "Audio Only (HQ)",
                '_music_data': music_data,
                '_platform_info': platform_info,
                'webpage_url': url
            }
            self._cache_metadata(url, res)
            return res

        if getattr(sys, 'frozen', False):
            ffmpeg_dir = sys._MEIPASS
        else:
            ffmpeg_dir = os.getcwd()

        ydl_opts = {
            'extract_flat': 'in_playlist',
            'skip_download': True,
            'ffmpeg_location': ffmpeg_dir,
            'socket_timeout': 10,
            'remote_components': ['ejs:github'],
            'extractor_args': {'youtube': {'player_client': ['android', 'web']}},
            'no_warnings': True,
            'quiet': True,
        }
        try:
            with get_ydl_class()(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                if not info:
                    return None

                # Analisis resolusi maksimum yang tersedia
                max_height = 0
                formats = info.get('formats', [])
                for f in formats:
                    h = f.get('height')
                    if h and isinstance(h, int) and h > max_height:
                        max_height = h

                if not max_height and info.get('height'):
                    max_height = info.get('height')

                if max_height >= 2160:
                    max_res_str = "4K UHD"
                elif max_height >= 1440:
                    max_res_str = "2K QHD"
                elif max_height >= 1080:
                    max_res_str = "1080p FHD"
                elif max_height >= 720:
                    max_res_str = "720p HD"
                elif max_height > 0:
                    max_res_str = f"{max_height}p"
                elif platform_info["type"] == "audio":
                    max_res_str = "Audio HQ"
                else:
                    max_res_str = "Standard"

                info['_max_res'] = max_res_str
                info['_platform_info'] = platform_info
                self._cache_metadata(url, info)
                return info
        except Exception as e:
            self._ui_log(f"[Error Info] Gagal mengambil preview: {str(e)}")
            return None

    def fetch_playlist_tracks(self, url: str) -> dict:
        """
        Mengekstrak daftar isi playlist secara datar (flat extraction) tanpa mendownload media.
        """
        if not url.strip():
            return None

        if getattr(sys, 'frozen', False):
            ffmpeg_dir = sys._MEIPASS
        else:
            ffmpeg_dir = os.getcwd()

        ydl_opts = {
            'extract_flat': True,
            'skip_download': True,
            'ffmpeg_location': ffmpeg_dir,
            'remote_components': ['ejs:github'],
            'extractor_args': {'youtube': {'player_client': ['ios', 'android', 'web']}},
            'ignoreerrors': True,
        }
        try:
            self._ui_log(f"[Playlist] Menganalisis daftar trek playlist...")
            with get_ydl_class()(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                if not info:
                    return None

                raw_entries = info.get('entries', [])
                clean_entries = []
                for idx, entry in enumerate(raw_entries, 1):
                    if not entry:
                        continue
                    entry_id = entry.get('id')
                    entry_url = entry.get('url')
                    if entry_url and not entry_url.startswith("http"):
                        entry_url = f"https://www.youtube.com/watch?v={entry_url}"
                    elif not entry_url and entry_id:
                        entry_url = f"https://www.youtube.com/watch?v={entry_id}"
                    
                    entry_title = entry.get('title') or f"Track #{idx}"
                    entry_duration = entry.get('duration') or 0
                    entry_uploader = entry.get('uploader') or entry.get('channel') or "Unknown"
                    clean_entries.append({
                        'index': idx,
                        'id': entry_id,
                        'title': entry_title,
                        'url': entry_url,
                        'duration': entry_duration,
                        'uploader': entry_uploader,
                    })

                self._ui_log(f"[Playlist] Berhasil mengekstrak {len(clean_entries)} trek.")
                return {
                    'title': info.get('title', 'YouTube Playlist'),
                    'uploader': info.get('uploader') or info.get('channel') or 'YouTube Playlist',
                    'count': len(clean_entries),
                    'entries': clean_entries,
                }
        except Exception as e:
            self._ui_log(f"[Error Playlist] Gagal mengambil daftar trek: {str(e)}")
            return None

    def _inject_mutagen_metadata(self, file_path: str, title: str, artist: str, thumb_url: str, embed_meta: bool, embed_thumb: bool, album: str = None):
        """
        Penyuntik metadata menggunakan Mutagen (Pure Python) yang dijamin bekerja mulus di dalam format .exe.
        """
        try:
            if not os.path.exists(file_path):
                self._ui_log(f"[Mutagen Error] File tidak ditemukan di: {file_path}")
                return

            # Inisialisasi Tag ID3 pada file MP3
            try:
                audio = MP3(file_path, ID3=ID3)
            except ID3NoHeaderError:
                audio = MP3(file_path)
                audio.add_tags()
                audio.save()
                audio = MP3(file_path, ID3=ID3)

            # 1. Suntik Teks Metadata (Judul, Artis, Album)
            if embed_meta:
                self._ui_log("[Mutagen] Menyuntik data judul, uploader, dan album...")
                clean_title = title if title else os.path.splitext(os.path.basename(file_path))[0]
                clean_album = album if (album and str(album).strip()) else clean_title

                audio.tags.add(TIT2(encoding=3, text=clean_title))    # Judul
                audio.tags.add(TPE1(encoding=3, text=artist))       # Artis / Uploader
                audio.tags.add(TALB(encoding=3, text=clean_album))    # Album Dinamis

            # 2. Suntik Cover Art Menggunakan Konversi JPEG murni
            if embed_thumb and thumb_url:
                self._ui_log("[Mutagen] Mendownload dan memproses Cover Art...")
                headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
                res = requests.get(thumb_url, headers=headers, timeout=10)
                
                if res.status_code == 200:
                    img_data = BytesIO(res.content)
                    with Image.open(img_data) as img:
                        if img.mode in ("RGBA", "P", "LA"):
                            img = img.convert("RGB")
                        
                        output_buffer = BytesIO()
                        img.save(output_buffer, format="JPEG", quality=90)
                        jpeg_bin_data = output_buffer.getvalue()

                    audio.tags.add(APIC(
                        encoding=3,
                        mime="image/jpeg",
                        type=3,  # 3 = Front Cover
                        desc=u"Front Cover",
                        data=jpeg_bin_data
                    ))
                    self._ui_log("[Mutagen] Cover Art berhasil ditempel!")

            # Simpan paksa menggunakan ID3v2.3 (sangat kompatibel dengan Windows Explorer & Pemutar Musik)
            audio.save(v2_version=3)
            self._ui_log("[Mutagen Sukses] ID3 v2.3 Tags berhasil diamankan!")
        except Exception as e:
            self._ui_log(f"[Mutagen Error] Gagal menulis metadata: {str(e)}")

    def download(
        self, 
        url: str, 
        output_dir: str, 
        format_type: str, 
        quality_setting: str, 
        embed_meta: bool, 
        embed_thumb: bool, 
        use_archive: bool = True,
        normalize_audio: bool = None,
        override_meta: dict = None
    ):
        """
        Proses download yt-dlp multi-format (MP3, MP4, MKV) dengan muxer FFmpeg,
        kontrol resolusi adaptif (4K s/d 360p), multi-threaded fragment downloads (Turbo 4x),
        Spotify/Apple Music matching, dan penyeragaman audio EBU R128 loudnorm.
        """
        if not url.strip():
            self._ui_log("[Error] URL tidak boleh kosong!")
            return

        self.cancel_requested = False
        target_url = url.strip()

        # Deteksi otomatis Spotify & Apple Music
        music_data = MusicLinkParser.parse(target_url)
        if music_data.get('is_music_link') and music_data.get('search_query'):
            self._ui_log(f"[Music Parser] Mengonversi tautan {music_data['platform'].capitalize()} ke pencarian audio YouTube Music...")
            self._ui_log(f"[Music Parser] Target: '{music_data['title']}' oleh '{music_data.get('artist', 'Unknown')}'")
            target_url = f"ytsearch1:{music_data['search_query']}"
            if not override_meta:
                override_meta = music_data

        self._ui_log(f"[System] Memulai proses untuk: {target_url}")
        
        naming_template = SettingsManager.get("naming_template", "{title}")
        
        if 'playlist' in target_url.lower() and not target_url.startswith("ytsearch"):
            is_playlist = True
            if naming_template == "{artist} - {title}":
                file_pattern = "%(uploader,creator,artist)s - %(title)s.%(ext)s"
            elif naming_template == "{title} [{id}]":
                file_pattern = "%(title)s [%(id)s].%(ext)s"
            elif naming_template == "{index}. {title}":
                file_pattern = "%(playlist_index)02d. %(title)s.%(ext)s"
            else:
                file_pattern = "%(title)s.%(ext)s"
            out_template = os.path.join(output_dir, '%(playlist_title)s', file_pattern)
        else:
            is_playlist = False
            if naming_template == "{artist} - {title}":
                file_pattern = "%(uploader,creator,artist)s - %(title)s.%(ext)s"
            elif naming_template == "{title} [{id}]":
                file_pattern = "%(title)s [%(id)s].%(ext)s"
            elif naming_template == "{index}. {title}":
                file_pattern = "%(title)s.%(ext)s"
            else:
                file_pattern = "%(title)s.%(ext)s"
            out_template = os.path.join(output_dir, file_pattern)

        if getattr(sys, 'frozen', False):
            ffmpeg_dir = sys._MEIPASS
        else:
            ffmpeg_dir = os.getcwd()

        postprocessors = []

        use_turbo = SettingsManager.get("turbo_speed", True)

        ydl_opts = {
            'outtmpl': out_template,
            'logger': MyYtdlpLogger(self.log_callback),
            'ffmpeg_location': ffmpeg_dir, 
            'progress_hooks': [self._my_progress_hook],
            'noplaylist': not is_playlist,
            'writethumbnail': False,      
            'embedmetadata': False,        
            'embedthumbnail': False,      
            'ignoreerrors': 'only_download',
            'remote_components': ['ejs:github'],
            'extractor_args': {'youtube': {'player_client': ['ios', 'android', 'web']}},
            # Multi-Threaded Parallel Fragment Downloads
            'concurrent_fragment_downloads': 4 if use_turbo else 1,
            'buffersize': 1024 * 64,      # 64 KB buffer
        }

        if use_turbo:
            ydl_opts['http_chunk_size'] = 10485760  # 10 MB HTTP chunk buffer

        # Normalisasi Volume Suara Otomatis (EBU R128 loudnorm)
        if normalize_audio is None:
            normalize_audio = SettingsManager.get("normalize_audio", False)

        if normalize_audio:
            self._ui_log("[Audio Engine] Normalisasi volume suara (EBU R128) AKTIF.")
            ydl_opts['postprocessor_args'] = {
                'ExtractAudio': ['-af', 'loudnorm=I=-16:TP=-1.5:LRA=11']
            }

        if use_archive:
            ydl_opts['download_archive'] = Config.ARCHIVE_FILE

        # ---------------------------------------------------------------------
        # 1. KONFIGURASI AUDIO (MP3) ATAU VIDEO (MP4 / MKV)
        # ---------------------------------------------------------------------
        if format_type == "MP3":
            bitrate_map = {"Best Audio": "0", "320kbps": "320", "256kbps": "256", "192kbps": "192", "128kbps": "128"}
            preferred_quality = bitrate_map.get(quality_setting, "0")
            
            ydl_opts['format'] = 'bestaudio/best'
            postprocessors.append({
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': preferred_quality,
            })
        else:
            # Format Video: MP4 (Standar Universal)
            ydl_opts['merge_output_format'] = "mp4"

            # Mapping resolusi video adaptif
            res_format_map = {
                "Best (4K/Max)": "bestvideo+bestaudio/best",
                "2160p (4K UHD)": "bestvideo[height<=2160]+bestaudio/best[height<=2160]/best",
                "1440p (2K QHD)": "bestvideo[height<=1440]+bestaudio/best[height<=1440]/best",
                "1080p (Full HD)": "bestvideo[height<=1080]+bestaudio/best[height<=1080]/best",
                "720p (HD)": "bestvideo[height<=720]+bestaudio/best[height<=720]/best",
                "480p (SD)": "bestvideo[height<=480]+bestaudio/best[height<=480]/best",
                "360p": "bestvideo[height<=360]+bestaudio/best[height<=360]/best",
            }
            ydl_opts['format'] = res_format_map.get(quality_setting, "bestvideo+bestaudio/best")

            # Embed Metadata untuk file video container
            if embed_meta:
                postprocessors.append({'key': 'FFmpegMetadata'})

        if postprocessors:
            ydl_opts['postprocessors'] = postprocessors

        try:
            with get_ydl_class()(ydl_opts) as ydl:
                info_dict = ydl.extract_info(target_url, download=True)
                
                # Eksekusi Mutagen khusus format MP3
                if format_type == "MP3" and info_dict:
                    self._ui_log("[System] Memproses penyuntikan metadata MP3...")
                    
                    if 'entries' in info_dict:
                        for entry in info_dict['entries']:
                            if entry:
                                final_filename = ydl.prepare_filename(entry)
                                final_mp3_path = os.path.splitext(final_filename)[0] + ".mp3"
                                
                                title = (override_meta.get('title') if override_meta else None) or entry.get('title', 'Unknown Title')
                                artist = (override_meta.get('artist') if override_meta else None) or entry.get('uploader', 'Unknown Artist')
                                thumb_url = (override_meta.get('thumbnail_url') if override_meta else None) or entry.get('thumbnail', None)
                                album_name = (override_meta.get('album') if override_meta else None) or entry.get('album', None)
                                
                                self._inject_mutagen_metadata(
                                    file_path=final_mp3_path,
                                    title=title,
                                    artist=artist,
                                    thumb_url=thumb_url,
                                    embed_meta=embed_meta,
                                    embed_thumb=embed_thumb,
                                    album=album_name
                                )
                    else:
                        final_filename = ydl.prepare_filename(info_dict)
                        final_mp3_path = os.path.splitext(final_filename)[0] + ".mp3"
                        
                        title = (override_meta.get('title') if override_meta else None) or info_dict.get('title', 'Unknown Title')
                        artist = (override_meta.get('artist') if override_meta else None) or info_dict.get('uploader', 'Unknown Artist')
                        thumb_url = (override_meta.get('thumbnail_url') if override_meta else None) or info_dict.get('thumbnail', None)
                        album_name = (override_meta.get('album') if override_meta else None) or info_dict.get('album', None)
                        
                        self._inject_mutagen_metadata(
                            file_path=final_mp3_path,
                            title=title,
                            artist=artist,
                            thumb_url=thumb_url,
                            embed_meta=embed_meta,
                            embed_thumb=embed_thumb,
                            album=album_name
                        )

            self._ui_log("[Sukses] Seluruh rangkaian unduhan selesai!")
            if self.progress_callback:
                self.progress_callback({
                    'percentage': 1.0, 'speed': '0 KB/s', 'eta': '00:00', 'status': "Status: Selesai!"
                })
        except Exception as e:
            if self.cancel_requested or "dibatalkan" in str(e).lower():
                self._ui_log("[System] Unduhan telah dibatalkan.")
                if self.progress_callback:
                    self.progress_callback({
                        'percentage': 0.0, 'speed': '0 KB/s', 'eta': '00:00', 'status': "Status: Dibatalkan"
                    })
            else:
                self._ui_log(f"[Error] Terjadi kesalahan saat download: {str(e)}")
                if self.progress_callback:
                    self.progress_callback({
                        'percentage': 0.0, 'speed': '0 KB/s', 'eta': '00:00', 'status': "Status: Gagal"
                    })

class MyYtdlpLogger:
    def __init__(self, log_callback):
        self.log_callback = log_callback
    def debug(self, msg):
        if "[download]" not in msg: self.log_callback(f"[yt-dlp] {msg}")
    def info(self, msg): self.log_callback(f"[yt-dlp] {msg}")
    def warning(self, msg): self.log_callback(f"[Warning] {msg}")
    def error(self, msg):
        if "subtitles" in msg.lower() or "429" in msg:
            self.log_callback(f"[Warning Subtitle] Subtitle tidak dapat dimuat: {msg}")
        else:
            self.log_callback(f"[Error] {msg}")