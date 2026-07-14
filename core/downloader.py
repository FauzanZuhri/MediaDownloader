import os
import requests
import sys
from io import BytesIO
from PIL import Image
from yt_dlp import YoutubeDL
from core.config import Config

# Menggunakan Mutagen untuk kompatibilitas .exe yang sempurna dan bebas error biner
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, TIT2, TPE1, TALB, APIC, ID3NoHeaderError

class YtdlpManager:
    def __init__(self, log_callback=None, progress_callback=None):
        self.log_callback = log_callback
        self.progress_callback = progress_callback

    def _ui_log(self, message: str):
        if self.log_callback:
            self.log_callback(message)

    def _my_progress_hook(self, d):
        if d['status'] == 'downloading':
            total_bytes = d.get('total_bytes') or d.get('total_bytes_estimate') or 0
            downloaded_bytes = d.get('downloaded_bytes', 0)
            percentage = downloaded_bytes / total_bytes if total_bytes > 0 else 0.0
            speed = d.get('_speed_str', '0 KB/s')
            eta = d.get('_eta_str', '00:00')
            filename = os.path.basename(d.get('filename', 'Lagu'))
            
            current_index = d.get('info_dict', {}).get('playlist_index', 1)
            total_entries = d.get('info_dict', {}).get('n_entries', 1)
            status_text = f"[{current_index}/{total_entries}] Downloading: {filename[:30]}..."
            
            if self.progress_callback:
                self.progress_callback({
                    'percentage': percentage, 'speed': speed, 'eta': eta, 'status': status_text
                })
        elif d['status'] == 'finished':
            if self.progress_callback:
                self.progress_callback({
                    'percentage': 1.0, 'speed': '0 KB/s', 'eta': '00:00', 'status': "Menyuntikkan Tag & Cover Art..."
                })

    def fetch_metadata(self, url: str) -> dict:
        if not url.strip(): return None

        if getattr(sys, 'frozen', False):
            ffmpeg_dir = sys._MEIPASS
        else:
            ffmpeg_dir = os.getcwd()

        ydl_opts = {
            'extract_flat': 'in_playlist',
            'skip_download': True,
            'ffmpeg_location': ffmpeg_dir,
        }
        try:
            with YoutubeDL(ydl_opts) as ydl:
                return ydl.extract_info(url, download=False)
        except Exception as e:
            self._ui_log(f"[Error Info] Gagal mengambil preview: {str(e)}")
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

    def download(self, url: str, output_dir: str, format_type: str, quality_setting: str, embed_meta: bool, embed_thumb: bool):
        """
        Proses download yt-dlp menggunakan Postprocessor kustom untuk menyuntik metadata
        secara realtime (berlaku untuk single video maupun playlist).
        """
        if not url.strip():
            self._ui_log("[Error] URL tidak boleh kosong!")
            return

        self._ui_log(f"[System] Memulai proses untuk: {url}")
        
        if 'playlist' in url.lower():
            out_template = os.path.join(output_dir, '%(playlist_title)s', '%(title)s.%(ext)s')
            is_playlist = True
        else:
            out_template = os.path.join(output_dir, '%(title)s.%(ext)s')
            is_playlist = False

        if getattr(sys, 'frozen', False):
            ffmpeg_dir = sys._MEIPASS
        else:
            ffmpeg_dir = os.getcwd()

        ydl_opts = {
            'outtmpl': out_template,
            'logger': MyYtdlpLogger(self.log_callback),
            'ffmpeg_location': ffmpeg_dir, 
            'progress_hooks': [self._my_progress_hook],
            'noplaylist': not is_playlist,
            'download_archive': Config.ARCHIVE_FILE,
            'writethumbnail': False,      
            'embedmetadata': False,        
            'embedthumbnail': False,      

            'extractor_args': {'youtube': {'player_client': ['web', 'default']}},
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            },
        }

        if format_type == "MP3":
            bitrate_map = {"Best Audio": "0", "320kbps": "320", "192kbps": "192", "128kbps": "128"}
            preferred_quality = bitrate_map.get(quality_setting, "0")
            
            ydl_opts.update({
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': preferred_quality,
                }]
            })

        try:
            with YoutubeDL(ydl_opts) as ydl:
                # Ambil metadata info terlebih dahulu
                info_dict = ydl.extract_info(url, download=True)
                
                # Eksekusi Mutagen setelah download selesai
                if format_type == "MP3" and info_dict:
                    self._ui_log("[System] Memproses penyuntikan metadata...")
                    
                    # Cek apakah yang diunduh adalah playlist (memiliki entries)
                    if 'entries' in info_dict:
                        # Jika playlist, kita looping setiap item lagu di dalamnya
                        for entry in info_dict['entries']:
                            if entry:  # Pastikan data entry lagu tidak kosong
                                # Ambil path file MP3 yang seharusnya dibuat untuk entry ini
                                final_filename = ydl.prepare_filename(entry)
                                final_mp3_path = os.path.splitext(final_filename)[0] + ".mp3"
                                
                                # Ambil metadata spesifik lagu ini
                                title = entry.get('title', 'Unknown Title')
                                artist = entry.get('uploader', 'Unknown Artist')
                                thumb_url = entry.get('thumbnail', None)
                                album_name = entry.get('album', None)
                                
                                # Suntik metadata ke file MP3 lagu ini
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
                        # Jika hanya single video (bukan playlist)
                        final_filename = ydl.prepare_filename(info_dict)
                        final_mp3_path = os.path.splitext(final_filename)[0] + ".mp3"
                        
                        title = info_dict.get('title', 'Unknown Title')
                        artist = info_dict.get('uploader', 'Unknown Artist')
                        thumb_url = info_dict.get('thumbnail', None)
                        album_name = info_dict.get('album', None)
                        
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
            self._ui_log(f"[Error] Terjadi kesalahan saat download: {str(e)}")

class MyYtdlpLogger:
    def __init__(self, log_callback):
        self.log_callback = log_callback
    def debug(self, msg):
        if "[download]" not in msg: self.log_callback(f"[yt-dlp] {msg}")
    def info(self, msg): self.log_callback(f"[yt-dlp] {msg}")
    def warning(self, msg): self.log_callback(f"[Warning] {msg}")
    def error(self, msg): self.log_callback(f"[Error] {msg}")