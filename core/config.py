import os
from pathlib import Path

class Config:
    # Mengambil path folder 'Downloads' default dari sistem operasi user
    DEFAULT_DOWNLOAD_DIR = str(Path.home() / "Downloads")
    
    # Path untuk menyimpan file list lagu yang sudah di-download (archive)
    ARCHIVE_FILE = str(Path(__file__).parent.parent / "download_archive.txt")
    
    # Pengaturan UI
    THEME = "dark"          # opsi: "dark", "light", "system"
    COLOR_THEME = "blue"    # opsi: "blue", "green", "dark-blue"
    APP_TITLE = "Personal Music Downloader"
    WINDOW_SIZE = "900x700"