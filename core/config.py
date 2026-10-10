import os
from pathlib import Path

class Config:
    # Mengambil path folder 'Downloads' default dari sistem operasi user
    DEFAULT_DOWNLOAD_DIR = str(Path.home() / "Downloads")
    
    # Path untuk menyimpan file list lagu yang sudah di-download (archive)
    ARCHIVE_FILE = str(Path(__file__).parent.parent / "download_archive.txt")
    
    # Pengaturan UI
    THEME = "dark"
    COLOR_THEME = "dark-blue"
    APP_TITLE = "Personal Music Downloader"
    VERSION = "v1.1.1"
    WINDOW_SIZE = "980x760"
    
    # Palet Warna Modern Obsidian & Indigo
    BG_COLOR = "#0e1117"
    CARD_BG = "#161b26"
    CARD_HOVER = "#1c2230"
    CARD_BORDER = "#232938"
    ACCENT_COLOR = "#6366f1"
    ACCENT_HOVER = "#4f46e5"
    SUCCESS_COLOR = "#10b981"
    DANGER_COLOR = "#ef4444"
    DANGER_HOVER = "#dc2626"
    SECONDARY_BTN = "#232a3b"
    SECONDARY_HOVER = "#2e374d"
    TEXT_MAIN = "#f8fafc"
    TEXT_MUTED = "#94a3b8"
    TEXT_DIM = "#64748b"