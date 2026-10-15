import sys
import subprocess
import requests
import yt_dlp

class YtdlpUpdater:
    @staticmethod
    def get_current_version() -> str:
        """Mengambil versi yt-dlp yang saat ini terpasang."""
        try:
            return yt_dlp.version.__version__
        except Exception:
            return "Unknown"

    @staticmethod
    def check_latest_version(timeout: int = 5) -> tuple:
        """
        Mengecek versi rilis terbaru yt-dlp dari PyPI.
        Returns: (current_version, latest_version, has_update, error_msg)
        """
        curr = YtdlpUpdater.get_current_version()
        try:
            res = requests.get("https://pypi.org/pypi/yt-dlp/json", timeout=timeout)
            if res.status_code == 200:
                data = res.json()
                latest = data.get("info", {}).get("version", curr)
                has_update = str(curr).strip() != str(latest).strip()
                return (curr, latest, has_update, None)
            else:
                return (curr, curr, False, f"HTTP Error {res.status_code}")
        except Exception as e:
            return (curr, curr, False, str(e))

    @staticmethod
    def run_update(log_callback=None) -> tuple:
        """
        Menjalankan proses pembaruan engine yt-dlp.
        Returns: (success: bool, message: str)
        """
        def log(msg):
            if log_callback:
                log_callback(msg)

        log("[Updater] Memulai proses pembaruan yt-dlp...")
        
        # Skenario 1: Berjalan dalam executable PyInstaller (Frozen)
        if getattr(sys, 'frozen', False):
            try:
                # Coba gunakan modul updater internal yt-dlp jika tersedia
                from yt_dlp.update import run_update
                res = run_update()
                log(f"[Updater] yt-dlp update selesai: {res}")
                return (True, "Engine yt-dlp berhasil diperbarui.")
            except Exception as e:
                log(f"[Updater Error] Gagal update standalone yt-dlp: {e}")
                return (False, f"Gagal memperbarui versi .exe: {e}")

        # Skenario 2: Berjalan dalam environment Python / venv
        cmd = [sys.executable, "-m", "pip", "install", "--upgrade", "yt-dlp"]
        try:
            log(f"[Updater] Menjalankan: {' '.join(cmd)}")
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
            )
            for line in proc.stdout:
                line_str = line.strip()
                if line_str:
                    log(f"[pip] {line_str}")
            proc.wait()
            
            if proc.returncode == 0:
                log("[Updater] ✅ yt-dlp berhasil diperbarui ke versi terbaru!")
                return (True, "yt-dlp berhasil diperbarui ke versi terbaru.")
            else:
                log(f"[Updater] ❌ Update gagal dengan exit code: {proc.returncode}")
                return (False, f"Gagal update (exit code {proc.returncode})")
        except Exception as e:
            log(f"[Updater Error] Terjadi kesalahan: {e}")
            return (False, str(e))
