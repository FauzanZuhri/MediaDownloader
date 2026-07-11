import os
import requests
from io import BytesIO
from PIL import Image
from yt_dlp import YoutubeDL

class YtdlpManager:
    def __init__(self, log_callback=None):
        self.log_callback = log_callback

    def _ui_log(self, message: str):
        if self.log_callback:
            self.log_callback(message)

    def fetch_metadata(self, url: str) -> dict:
        """
        Mengambil metadata video/playlist tanpa mendownload filenya.
        Berfungsi untuk fitur Preview.
        """
        if not url.strip():
            return None

        ydl_opts = {
            'extract_flat': 'in_playlist', # Cepat, tidak memakan waktu lama untuk playlist besar
            'skip_download': True,
            'ffmpeg_location': '.',
        }

        try:
            with YoutubeDL(ydl_opts) as ydl:
                # download=False artinya hanya ambil info saja
                info = ydl.extract_info(url, download=False)
                return info
        except Exception as e:
            self._ui_log(f"[Error Info] Gagal mengambil preview: {str(e)}")
            return None

    def download(self, url: str, output_dir: str, format_type: str):
        # ... (KODE DOWNLOAD DARI TAHAP 4 TETAP SAMA, TIDAK DIUBAH) ...
        if not url.strip():
            self._ui_log("[Error] URL tidak boleh kosong!")
            return

        self._ui_log(f"[System] Memulai proses untuk: {url}")
        
        ydl_opts = {
            'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s'),
            'noplaylist': True,
            'logger': MyYtdlpLogger(self.log_callback),
            'ffmpeg_location': '.', 
        }

        if format_type == "MP3":
            ydl_opts.update({
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '0',
                }],
            })
        else:
            ydl_opts.update({
                'format': 'bestvideo+bestaudio/best',
                'merge_output_format': 'mp4',
            })

        try:
            with YoutubeDL(ydl_opts) as ydl:
                self._ui_log("[System] Mengunduh dan memproses file dengan FFmpeg...")
                ydl.download([url])
            self._ui_log("[Sukses] Download dan konversi selesai murni!")
        except Exception as e:
            self._ui_log(f"[Error] Terjadi kesalahan: {str(e)}")

class MyYtdlpLogger:
    def __init__(self, log_callback):
        self.log_callback = log_callback
    def debug(self, msg):
        if "[download]" not in msg: self.log_callback(f"[yt-dlp] {msg}")
    def info(self, msg): self.log_callback(f"[yt-dlp] {msg}")
    def warning(self, msg): self.log_callback(f"[Warning] {msg}")
    def error(self, msg): self.log_callback(f"[Error] {msg}")