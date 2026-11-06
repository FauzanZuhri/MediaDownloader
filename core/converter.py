import os
import re
import sys
import subprocess
import threading
from typing import Optional, Callable

class MediaConverter:
    """
    Engine Konversi Media Offline & Audio Trimmer berbasis FFmpeg Lokal.
    Berjalan 100% offline tanpa membutuhkan koneksi internet.
    """

    FORMAT_PRESETS = {
        "MP3": {
            "ext": ".mp3",
            "lossless": False,
            "presets": {
                "Audiophile (320 kbps)": ["-c:a", "libmp3lame", "-b:a", "320k"],
                "High Quality (256 kbps)": ["-c:a", "libmp3lame", "-b:a", "256k"],
                "Standard (192 kbps)": ["-c:a", "libmp3lame", "-b:a", "192k"],
                "Compact (128 kbps)": ["-c:a", "libmp3lame", "-b:a", "128k"],
            }
        },
        "FLAC": {
            "ext": ".flac",
            "lossless": True,
            "presets": {
                "Lossless Audiophile (Level 5)": ["-c:a", "flac", "-compression_level", "5"],
                "Lossless Maximum (Level 8)": ["-c:a", "flac", "-compression_level", "8"],
            }
        },
        "WAV": {
            "ext": ".wav",
            "lossless": True,
            "presets": {
                "PCM Uncompressed (16-bit)": ["-c:a", "pcm_s16le"],
                "PCM High-Res (24-bit)": ["-c:a", "pcm_s24le"],
            }
        },
        "M4A (AAC)": {
            "ext": ".m4a",
            "lossless": False,
            "presets": {
                "High Quality (256 kbps)": ["-c:a", "aac", "-b:a", "256k"],
                "Standard (192 kbps)": ["-c:a", "aac", "-b:a", "192k"],
                "Voice / Podcast (128 kbps)": ["-c:a", "aac", "-b:a", "128k"],
            }
        },
        "OGG (Opus)": {
            "ext": ".ogg",
            "lossless": False,
            "presets": {
                "High Quality (160 kbps)": ["-c:a", "libopus", "-b:a", "160k"],
                "Voice (96 kbps)": ["-c:a", "libopus", "-b:a", "96k"],
            }
        },
        "MP4 (Universal Video)": {
            "ext": ".mp4",
            "lossless": False,
            "presets": {
                "Fast Remux / Copy (Instant)": ["-c:v", "copy", "-c:a", "copy"],
                "Standard H.264 + AAC": ["-c:v", "libx264", "-preset", "fast", "-crf", "22", "-c:a", "aac", "-b:a", "192k"],
                "High Quality H.264": ["-c:v", "libx264", "-preset", "slow", "-crf", "18", "-c:a", "aac", "-b:a", "256k"],
            }
        }
    }

    def __init__(self, ffmpeg_path: Optional[str] = None):
        if ffmpeg_path and os.path.exists(ffmpeg_path):
            self.ffmpeg_path = ffmpeg_path
        else:
            local_ffmpeg = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "ffmpeg.exe"))
            if os.path.exists(local_ffmpeg):
                self.ffmpeg_path = local_ffmpeg
            else:
                self.ffmpeg_path = "ffmpeg"

    @staticmethod
    def parse_time_str(time_str: str) -> float:
        """Mengonversi format waktu 'MM:SS' atau 'HH:MM:SS' atau angka detik ke float detik."""
        time_str = str(time_str).strip()
        if not time_str:
            return 0.0
        parts = time_str.split(":")
        try:
            if len(parts) == 1:
                return float(parts[0])
            elif len(parts) == 2:
                return int(parts[0]) * 60 + float(parts[1])
            elif len(parts) == 3:
                return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
        except ValueError:
            return 0.0
        return 0.0

    @staticmethod
    def format_seconds(seconds: float) -> str:
        """Mengonversi float detik menjadi string 'MM:SS' atau 'HH:MM:SS'."""
        sec_int = int(max(0, seconds))
        m, s = divmod(sec_int, 60)
        h, m = divmod(m, 60)
        if h > 0:
            return f"{h:02d}:{m:02d}:{s:02d}"
        return f"{m:02d}:{s:02d}"

    def get_media_duration(self, file_path: str) -> float:
        """Mendapatkan total durasi media menggunakan ffmpeg banner stderr."""
        if not os.path.exists(file_path):
            return 0.0
        startupinfo = None
        if sys.platform == "win32":
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

        cmd = [self.ffmpeg_path, "-i", file_path]
        try:
            p = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                startupinfo=startupinfo,
                text=True,
                encoding="utf-8",
                errors="replace"
            )
            _, err = p.communicate()
            match = re.search(r"Duration:\s*(\d+):(\d+):(\d+\.\d+)", err)
            if match:
                h = int(match.group(1))
                m = int(match.group(2))
                s = float(match.group(3))
                return h * 3600 + m * 60 + s
        except Exception:
            return 0.0
        return 0.0

    def convert(
        self,
        input_path: str,
        output_path: str,
        format_name: str,
        preset_name: str,
        progress_callback: Optional[Callable[[float, str], None]] = None,
        log_callback: Optional[Callable[[str], None]] = None,
        cancel_event: Optional[threading.Event] = None
    ) -> bool:
        """
        Menjalankan proses konversi media offline dengan FFmpeg.
        Menghasilkan output audio atau video sesuai format & preset yang dipilih.
        """
        if not os.path.exists(input_path):
            if log_callback:
                log_callback(f"[Converter] File sumber tidak ditemukan: {input_path}")
            return False

        format_info = self.FORMAT_PRESETS.get(format_name)
        if not format_info:
            if log_callback:
                log_callback(f"[Converter] Format '{format_name}' tidak didukung.")
            return False

        preset_args = format_info["presets"].get(preset_name)
        if not preset_args:
            # Gunakan preset pertama sebagai default
            first_key = list(format_info["presets"].keys())[0]
            preset_args = format_info["presets"][first_key]

        total_duration = self.get_media_duration(input_path)
        if log_callback:
            log_callback(f"[Converter] Memulai konversi: {os.path.basename(input_path)} -> {format_name}")
            if total_duration > 0:
                log_callback(f"[Converter] Durasi media sumber: {self.format_seconds(total_duration)}")

        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

        startupinfo = None
        if sys.platform == "win32":
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

        cmd = [self.ffmpeg_path, "-y", "-i", input_path]
        # Jika targetnya audio murni dan sumbernya video, tambahkan -vn agar cepat
        if format_name in ["MP3", "FLAC", "WAV", "M4A (AAC)", "OGG (Opus)"]:
            cmd.append("-vn")
        cmd.extend(preset_args)
        cmd.append(output_path)

        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                startupinfo=startupinfo,
                text=True,
                encoding="utf-8",
                errors="replace"
            )

            # Thread reader stderr untuk membaca progress realtime
            time_pattern = re.compile(r"time=(\d+):(\d+):(\d+\.\d+)")

            for line in process.stderr:
                if cancel_event and cancel_event.is_set():
                    process.kill()
                    if log_callback:
                        log_callback("[Converter] Konversi dibatalkan oleh pengguna.")
                    if os.path.exists(output_path):
                        try:
                            os.remove(output_path)
                        except Exception:
                            pass
                    return False

                match = time_pattern.search(line)
                if match and total_duration > 0:
                    curr_h = int(match.group(1))
                    curr_m = int(match.group(2))
                    curr_s = float(match.group(3))
                    curr_total = curr_h * 3600 + curr_m * 60 + curr_s
                    pct = min(99.0, (curr_total / total_duration) * 100.0)
                    if progress_callback:
                        progress_callback(pct, f"{pct:.1f}% ({self.format_seconds(curr_total)} / {self.format_seconds(total_duration)})")

            process.wait()

            if process.returncode == 0:
                if progress_callback:
                    progress_callback(100.0, "100% Selesai")
                if log_callback:
                    log_callback(f"[Converter] Berhasil! File tersimpan: {output_path}")
                return True
            else:
                if log_callback:
                    log_callback(f"[Converter] Gagal mengonversi file (Kode exit: {process.returncode}).")
                return False

        except Exception as e:
            if log_callback:
                log_callback(f"[Converter] Terjadi error: {e}")
            return False

    def trim(
        self,
        input_path: str,
        output_path: str,
        start_sec: float,
        end_sec: float,
        fade_in_sec: float = 0.0,
        fade_out_sec: float = 0.0,
        log_callback: Optional[Callable[[str], None]] = None,
        cancel_event: Optional[threading.Event] = None
    ) -> bool:
        """
        Memotong klip audio dari start_sec ke end_sec secara instan.
        Mendukung penambahan efek fade-in dan fade-out halus untuk nada dering.
        """
        if not os.path.exists(input_path):
            if log_callback:
                log_callback(f"[Trimmer] File sumber tidak ditemukan: {input_path}")
            return False

        if end_sec <= start_sec:
            if log_callback:
                log_callback("[Trimmer] Waktu selesai harus lebih besar dari waktu mulai!")
            return False

        duration = end_sec - start_sec
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

        startupinfo = None
        if sys.platform == "win32":
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

        cmd = [
            self.ffmpeg_path,
            "-y",
            "-ss", str(start_sec),
            "-i", input_path,
            "-t", str(duration),
            "-vn"
        ]

        # Audio filters untuk fade-in dan fade-out
        filters = []
        if fade_in_sec > 0:
            fade_in_actual = min(fade_in_sec, duration / 2)
            filters.append(f"afade=t=in:ss=0:d={fade_in_actual:.2f}")

        if fade_out_sec > 0:
            fade_out_actual = min(fade_out_sec, duration / 2)
            fade_start = duration - fade_out_actual
            filters.append(f"afade=t=out:st={fade_start:.2f}:d={fade_out_actual:.2f}")

        if filters:
            cmd.extend(["-af", ",".join(filters), "-c:a", "libmp3lame", "-b:a", "320k"])
        else:
            # Jika tanpa filter dan ekstensi sama, gunakan fast copy jika memungkinkan
            if output_path.lower().endswith(".mp3") and input_path.lower().endswith(".mp3"):
                cmd.extend(["-c:a", "copy"])
            else:
                cmd.extend(["-c:a", "libmp3lame", "-b:a", "320k"])

        cmd.append(output_path)

        if log_callback:
            log_callback(f"[Trimmer] Memotong audio: {self.format_seconds(start_sec)} s/d {self.format_seconds(end_sec)} (Durasi: {self.format_seconds(duration)})")

        try:
            p = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                startupinfo=startupinfo,
                text=True,
                encoding="utf-8",
                errors="replace"
            )
            _, err = p.communicate()
            if p.returncode == 0:
                if log_callback:
                    log_callback(f"[Trimmer] Berhasil! Potongan audio tersimpan: {output_path}")
                return True
            else:
                if log_callback:
                    log_callback(f"[Trimmer] Gagal memotong audio: {err[-200:] if err else 'Error'}")
                return False
        except Exception as e:
            if log_callback:
                log_callback(f"[Trimmer] Terjadi error pemotongan: {e}")
            return False

