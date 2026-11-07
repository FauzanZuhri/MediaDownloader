import threading
from ui.main_window import MainWindow
from core.downloader import get_ydl_class

def main():
    # Inisialisasi dan jalankan window utama aplikasi
    app = MainWindow()
    
    # Warmup yt-dlp di background setelah window tampil (instant startup <250ms)
    app.after(300, lambda: threading.Thread(target=get_ydl_class, daemon=True).start())
    
    app.mainloop()

if __name__ == "__main__":
    main()
