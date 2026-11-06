import os
import threading
from typing import Callable, Optional
from PIL import Image, ImageDraw
import pystray
from core.config import Config

class SystemTrayManager:
    """
    Manajer System Tray Windows (pystray).
    Memungkinkan aplikasi berjalan di latar belakang (minimize to tray),
    menampilkan menu konteks klik kanan, dan mengirim notifikasi desktop sistem.
    """
    def __init__(
        self,
        on_show: Optional[Callable[[], None]] = None,
        on_open_folder: Optional[Callable[[], None]] = None,
        on_quit: Optional[Callable[[], None]] = None,
    ):
        self.on_show = on_show
        self.on_open_folder = on_open_folder
        self.on_quit = on_quit
        
        self.icon: Optional[pystray.Icon] = None
        self._thread: Optional[threading.Thread] = None
        self._running = False

    def _create_icon_image(self) -> Image.Image:
        """Memuat icon resmi dari assets jika tersedia, atau membuat fallback grafis modern."""
        icon_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "assets", "icon.png"))
        if os.path.exists(icon_path):
            try:
                img = Image.open(icon_path).convert("RGBA")
                return img.resize((64, 64), Image.Resampling.LANCZOS)
            except Exception:
                pass

        size = 64
        image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        
        # Gambar lingkaran dasar biru safir modern
        draw.ellipse([4, 4, size - 4, size - 4], fill="#2563eb", outline="#3b82f6", width=2)
        
        # Gambar simbol panah unduh putih di tengah
        # Batang panah vertikal
        draw.rectangle([28, 16, 36, 36], fill="#ffffff")
        # Segitiga mata panah
        draw.polygon([(20, 36), (44, 36), (32, 48)], fill="#ffffff")
        # Garis landasan bawah
        draw.rectangle([20, 50, 44, 53], fill="#ffffff")
        
        return image

    def start(self):
        """Menjalankan tray icon di background thread."""
        if self._running:
            return

        image = self._create_icon_image()
        menu = pystray.Menu(
            pystray.MenuItem("Buka MediaDownloader", self._action_show, default=True),
            pystray.MenuItem("Buka Folder Unduhan", self._action_open_folder),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Keluar Aplikasi", self._action_quit)
        )

        self.icon = pystray.Icon("MediaDownloader", image, f"{Config.APP_TITLE} {Config.VERSION}", menu)
        self._running = True

        def _run_tray():
            try:
                self.icon.run()
            except Exception as e:
                print(f"[Tray] Error: {e}")
            finally:
                self._running = False

        self._thread = threading.Thread(target=_run_tray, daemon=True)
        self._thread.start()

    def stop(self):
        """Menghentikan tray icon."""
        if self.icon and self._running:
            self._running = False
            try:
                self.icon.stop()
            except Exception:
                pass

    def notify(self, title: str, message: str):
        """Mengirimkan notifikasi sistem tray Windows."""
        if self.icon and self._running:
            try:
                self.icon.notify(message, title)
            except Exception as e:
                print(f"[Tray Notify Error] {e}")

    def _action_show(self, icon=None, item=None):
        if self.on_show:
            self.on_show()

    def _action_open_folder(self, icon=None, item=None):
        if self.on_open_folder:
            self.on_open_folder()

    def _action_quit(self, icon=None, item=None):
        self.stop()
        if self.on_quit:
            self.on_quit()

