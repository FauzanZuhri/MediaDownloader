import os
import requests
from io import BytesIO
from PIL import Image
from yt_dlp import YoutubeDL
from core.config import Config

class YtdlpManager:
    def __init__(self, log_callback=None, progress_callback=None):
        """
        :param log_callback: Callback untuk menulis text log ke UI.
        :param progress_callback: Callback untuk mengirim data progress (dict) ke UI.
        """
        self.log_callback = log_callback
        self.progress_callback = progress_callback

    def _ui_log(self, message: str):
        if self.log_callback:
            self.log_callback(message)

    def _my_progress_hook(self, d):
        """Fungsi internal untuk menangkap statistik download dari yt-dlp."""
        if d['status'] == 'downloading':
            # Ambil data mentah dari dict internal yt-dlp
            total_bytes = d.get('total_bytes') or d.get('total_bytes_estimate') or 0
            downloaded_bytes = d.get('downloaded_bytes', 0)
            
            # Hitung persentase (0.0 sampai 1.0 untuk CTkProgressBar)
            percentage = downloaded_bytes / total_bytes if total_bytes > 0 else 0.0
            
            # Ambil data teks kecepatan dan ETA yang sudah diformat oleh yt-dlp
            speed = d.get('_speed_str', '0 KB/s')
            eta = d.get('_eta_str', '00:00')
            filename = os.path.basename(d.get('filename', 'Lagu'))
            
            # Kirim paket data ini ke UI lewat callback jika tersedia
            if self.progress_callback:
                self.progress_callback({
                    'percentage': percentage,
                    'speed': speed,
                    'eta': eta,
                    'status': f"Downloading: {filename[:40]}..."
                })
                
        elif d['status'] == 'finished':
            if self.progress_callback:
                self.progress_callback({
                    'percentage': 1.0,
                    'speed': '0 KB/s',
                    'eta': '00:00',
                    'status': "Mengekstrak & mengonversi audio ke MP3..."
                })

    def fetch_metadata(self, url: str) -> dict:
        if not url.strip(): return None
        ydl_opts = {
            'extract_flat': 'in_playlist',
            'skip_download': True,
            'ffmpeg_location': '.',
        }
        try:
            with YoutubeDL(ydl_opts) as ydl:
                return ydl.extract_info(url, download=False)
        except Exception as e:
            self._ui_log(f"[Error Info] Gagal mengambil preview: {str(e)}")
            return None

    def download(self, url: str, output_dir: str, format_type: str):
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
            'ffmpeg_location': '.', 
            'progress_hooks': [self._my_progress_hook],
            'noplaylist': not is_playlist,
            
            # TAHAP 8: Mengaktifkan rekam jejak unduhan (Archive Mode)
            # File 'download_archive.txt' akan otomatis dibuat di folder utama proyek
            'download_archive': Config.ARCHIVE_FILE,
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
                ydl.download([url])
            self._ui_log("[Sukses] Semua unduhan selesai!")
            if self.progress_callback:
                self.progress_callback({
                    'percentage': 1.0, 'speed': '0 KB/s', 'eta': '00:00', 'status': "Status: Selesai!"
                })
        except Exception as e:
            self._ui_log(f"[Error] Terjadi kesalahan: {str(e)}")

class MyYtdlpLogger:
    def __init__(self, log_callback):
        self.log_callback = log_callback
    def debug(self, msg):
        if "[download]" not in msg: self.log_callback(f"[yt-dlp] {msg}")
    def info(self, msg): self.log_color_callback(f"[yt-dlp] {msg}") if hasattr(self, 'log_color_callback') else self.log_callback(f"[yt-dlp] {msg}")
    def warning(self, msg): self.log_callback(f"[Warning] {msg}")
    def error(self, msg): self.log_callback(f"[Error] {msg}")