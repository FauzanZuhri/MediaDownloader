import os
import sys
import time
import ctypes
import threading
from typing import Optional, Callable

class AudioPlayer:
    """
    Pemutar Audio Ringan Bawaan Sistem Windows (MCI - Media Control Interface).
    Mendukung pemutaran file MP3, WAV, M4A, dan audio lainnya secara native
    tanpa membutuhkan library C eksternal atau dependensi berat.
    """
    _ALIAS = "MediaDownloaderAudio"

    def __init__(
        self,
        on_position_change: Optional[Callable[[int, int], None]] = None,
        on_finished: Optional[Callable[[], None]] = None,
    ):
        self.on_position_change = on_position_change
        self.on_finished = on_finished

        self.current_file: Optional[str] = None
        self.duration_ms: int = 0
        self._is_playing: bool = False
        self._is_paused: bool = False
        self._volume: int = 80  # 0 to 100

        self._lock = threading.Lock()
        self._monitor_thread: Optional[threading.Thread] = None
        self._stop_monitor = threading.Event()

        # Inisialisasi API Windows kernel32 & winmm
        self._winmm = ctypes.windll.winmm if sys.platform == "win32" else None
        self._kernel32 = ctypes.windll.kernel32 if sys.platform == "win32" else None

    def _get_short_path(self, path: str) -> str:
        """Mengonversi path panjang/spasi ke format short path Windows 8.3 untuk keandalan MCI."""
        if not self._kernel32 or not os.path.exists(path):
            return path
        buf = ctypes.create_unicode_buffer(500)
        res = self._kernel32.GetShortPathNameW(path, buf, 500)
        return buf.value if res > 0 else path

    def _send_cmd(self, cmd: str) -> str:
        """Mengirim perintah teks ke MCI Windows."""
        if not self._winmm:
            return ""
        buf = ctypes.create_unicode_buffer(256)
        err = self._winmm.mciSendStringW(cmd, buf, 255, 0)
        return buf.value

    def load(self, file_path: str) -> bool:
        """Memuat file audio ke dalam engine pemutar."""
        if not os.path.exists(file_path):
            return False

        with self._lock:
            self._close_internal()
            short_path = self._get_short_path(os.path.abspath(file_path))

            # Buka media dengan tipe mpegvideo (kompatibel MP3, WAV, M4A)
            res = self._send_cmd(f'open "{short_path}" type mpegvideo alias {self._ALIAS}')
            self._send_cmd(f"set {self._ALIAS} time format milliseconds")

            # Ambil total durasi media dalam milidetik
            len_str = self._send_cmd(f"status {self._ALIAS} length")
            try:
                self.duration_ms = int(len_str) if len_str else 0
            except ValueError:
                self.duration_ms = 0

            self.current_file = file_path
            self._is_playing = False
            self._is_paused = False
            self.set_volume(self._volume)
            return True

    def play(self) -> bool:
        """Memulai pemutaran audio dari awal atau posisi saat ini."""
        with self._lock:
            if not self.current_file:
                return False

            self._send_cmd(f"play {self._ALIAS}")
            self._is_playing = True
            self._is_paused = False

            self._start_monitor_thread()
            return True

    def pause(self) -> bool:
        """Menjeda pemutaran audio sementara."""
        with self._lock:
            if not self._is_playing:
                return False
            self._send_cmd(f"pause {self._ALIAS}")
            self._is_playing = False
            self._is_paused = True
            return True

    def resume(self) -> bool:
        """Melanjutkan pemutaran audio dari kondisi jeda."""
        with self._lock:
            if not self._is_paused:
                return False
            self._send_cmd(f"resume {self._ALIAS}")
            self._is_playing = True
            self._is_paused = False
            self._start_monitor_thread()
            return True

    def stop(self) -> bool:
        """Menghentikan pemutaran audio dan mereset posisi ke awal."""
        with self._lock:
            if not self.current_file:
                return False
            self._send_cmd(f"stop {self._ALIAS}")
            self._send_cmd(f"seek {self._ALIAS} to 0")
            self._is_playing = False
            self._is_paused = False
            self._stop_monitor.set()
            return True

    def seek(self, position_ms: int) -> bool:
        """Melompat ke posisi tertentu (milidetik)."""
        with self._lock:
            if not self.current_file:
                return False
            pos = max(0, min(position_ms, self.duration_ms))
            self._send_cmd(f"seek {self._ALIAS} to {pos}")
            if self._is_playing:
                self._send_cmd(f"play {self._ALIAS}")
            return True

    def set_volume(self, volume: int) -> bool:
        """Mengatur tingkat volume suara (0 s/d 100)."""
        self._volume = max(0, min(100, volume))
        with self._lock:
            if not self.current_file:
                return False
            # MCI volume range: 0 to 1000
            mci_vol = int(self._volume * 10)
            self._send_cmd(f"setaudio {self._ALIAS} volume to {mci_vol}")
            return True

    def get_position(self) -> int:
        """Mengambil posisi pemutaran saat ini (milidetik)."""
        with self._lock:
            if not self.current_file:
                return 0
            pos_str = self._send_cmd(f"status {self._ALIAS} position")
            try:
                return int(pos_str) if pos_str else 0
            except ValueError:
                return 0

    def is_playing(self) -> bool:
        return self._is_playing

    def is_paused(self) -> bool:
        return self._is_paused

    def close(self):
        """Menutup pemutar dan melepaskan resource audio."""
        with self._lock:
            self._close_internal()

    def _close_internal(self):
        self._stop_monitor.set()
        self._send_cmd(f"close {self._ALIAS}")
        self.current_file = None
        self.duration_ms = 0
        self._is_playing = False
        self._is_paused = False

    def _start_monitor_thread(self):
        self._stop_monitor.set()
        time.sleep(0.05)
        self._stop_monitor.clear()

        def _monitor_loop():
            while not self._stop_monitor.is_set():
                if self._is_playing:
                    pos = self.get_position()
                    if self.on_position_change:
                        try:
                            self.on_position_change(pos, self.duration_ms)
                        except Exception:
                            pass

                    # Deteksi selesai putar
                    if self.duration_ms > 0 and pos >= self.duration_ms - 300:
                        self._is_playing = False
                        self._is_paused = False
                        if self.on_finished:
                            try:
                                self.on_finished()
                            except Exception:
                                pass
                        break

                time.sleep(0.25)

        self._monitor_thread = threading.Thread(target=_monitor_loop, daemon=True)
        self._monitor_thread.start()

