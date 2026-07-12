import os
import requests
from io import BytesIO
from PIL import Image
from yt_dlp import YoutubeDL
from core.config import Config

# Menggunakan eyeD3 untuk kompatibilitas Windows penuh
import eyed3
from eyed3.id3.frames import ImageFrame

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
        ydl_opts = {
            'extract_flat': 'in_playlist',
            'skip_download': True,
            'ffmpeg_location': os.getcwd(),
        }
        try:
            with YoutubeDL(ydl_opts) as ydl:
                return ydl.extract_info(url, download=False)
        except Exception as e:
            self._ui_log(f"[Error Info] Gagal mengambil preview: {str(e)}")
            return None

    def _inject_eye3_metadata(self, file_path: str, title: str, artist: str, thumb_url: str, embed_meta: bool, embed_thumb: bool, album: str = None):
        """
        Fungsi penyuntik metadata menggunakan EyeD3 dengan Fallback Nama Album Dinamis.
        """
        try:
            if not os.path.exists(file_path):
                self._ui_log(f"[eyeD3 Error] File tidak ditemukan di: {file_path}")
                return

            audiofile = eyed3.load(file_path)
            if audiofile.tag is None:
                audiofile.initTag()

            # 1. Suntik Teks Metadata (Judul, Artis, Album)
            if embed_meta:
                self._ui_log("[eyeD3] Menyuntik data judul, uploader, dan album...")
                clean_title = title if title else os.path.splitext(os.path.basename(file_path))[0]
                
                # Cek jika album bawaan youtube ada/tidak kosong, jika kosong pakai judul lagu
                clean_album = album if (album and str(album).strip()) else clean_title

                audiofile.tag.title = clean_title
                audiofile.tag.artist = artist
                audiofile.tag.album = clean_album

            # 2. Suntik Cover Art Menggunakan Konversi JPEG murni
            if embed_thumb and thumb_url:
                self._ui_log("[eyeD3] Mendownload dan memproses Cover Art...")
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

                    audiofile.tag.images.set(
                        ImageFrame.FRONT_COVER, 
                        jpeg_bin_data, 
                        "image/jpeg", 
                        u"Front Cover"
                    )
                    self._ui_log("[eyeD3] Cover Art berhasil ditempel!")

            # Simpan perubahan (ID3v2.3 sangat disukai Windows Explorer)
            audiofile.tag.save(version=eyed3.id3.ID3_V2_3)
            self._ui_log("[eyeD3 Sukses] ID3 v2.3 Tags berhasil diamankan!")
        except Exception as e:
            self._ui_log(f"[eyeD3 Error] Gagal menulis metadata: {str(e)}")

    def download(self, url: str, output_dir: str, format_type: str, quality_setting: str, embed_meta: bool, embed_thumb: bool):
        """
        Proses download murni yt-dlp, diakhiri intervensi pasca-proses menggunakan EyeD3.
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

        ydl_opts = {
            'outtmpl': out_template,
            'logger': MyYtdlpLogger(self.log_callback),
            'ffmpeg_location': os.getcwd(), 
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
        else:
            ydl_opts.update({
                'format': 'bestvideo+bestaudio/best',
                'merge_output_format': 'mp4',
            })

        try:
            with YoutubeDL(ydl_opts) as ydl:
                info_dict = ydl.extract_info(url, download=True)
                
                # Eksekusi EyeD3 (Hanya untuk format MP3)
                if format_type == "MP3" and info_dict:
                    final_filename = ydl.prepare_filename(info_dict)
                    final_mp3_path = os.path.splitext(final_filename)[0] + ".mp3"
                    
                    # Ekstraksi informasi dari dictionary yt-dlp
                    title = info_dict.get('title', 'Unknown Title')
                    artist = info_dict.get('uploader', 'Unknown Artist')
                    thumb_url = info_dict.get('thumbnail', None)
                    album_name = info_dict.get('album', None) # Data album asli YT
                    
                    # Panggil fungsi penyuntik dengan parameter lengkap
                    self._inject_eye3_metadata(
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