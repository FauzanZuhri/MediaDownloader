import os
from pathlib import Path

class Config:
    # Mengambil path folder 'Downloads' default dari sistem operasi user
    DEFAULT_DOWNLOAD_DIR = str(Path.home() / "Downloads")
    
    # Path untuk menyimpan file list lagu yang sudah di-download (archive)
    ARCHIVE_FILE = str(Path(__file__).parent.parent / "download_archive.txt")
    
    # Pengaturan UI & Metadata
    APP_TITLE = "MediaDownloader"
    VERSION = "v2.0.0"
    WINDOW_SIZE = "1020x820"
    
    # Default appearance mode: "dark" atau "light"
    THEME = "dark"
    COLOR_THEME = "blue"
    
    # =========================================================================
    # PALET WARNA MODERN MINIMALIST (ZINC CANVAS + MODERN ACCENTS)
    # Bersih, seimbang, dan elegan (tidak norak tapi memiliki aksen modern)
    # =========================================================================
    # Latar Belakang Jendela Utama (Canvas)
    BG_COLOR = ("#f8fafc", "#09090b")
    
    # Permukaan Kartu & Kontainer Utama
    CARD_BG = ("#ffffff", "#121215")
    CARD_BG_ELEVATED = ("#f1f5f9", "#18181c")
    CARD_HOVER = ("#e2e8f0", "#222228")
    CARD_BORDER = ("#e2e8f0", "#24242a")
    
    # Navbar Capsule Dock Track
    NAV_TRACK_BG = ("#eaeff5", "#131317")
    NAV_TRACK_BORDER = ("#d5dde7", "#222228")
    NAV_TAB_ACTIVE_BG = ("#ffffff", "#22222a")
    NAV_TAB_ACTIVE_BORDER = ("#2563eb", "#3b82f6")  # Aksen halus pada tab aktif
    NAV_TAB_ACTIVE_TEXT = ("#0f172a", "#f8fafc")
    NAV_TAB_INACTIVE_TEXT = ("#64748b", "#8e8e99")
    NAV_TAB_HOVER = ("#dde4ec", "#1b1b22")
    
    # Tombol Aksi Utama (Modern Sapphire Blue: Bersih, Mewah, & Energik)
    BTN_PRIMARY_BG = ("#2563eb", "#3b82f6")
    BTN_PRIMARY_HOVER = ("#1d4ed8", "#2563eb")
    BTN_PRIMARY_TEXT = ("#ffffff", "#ffffff")
    
    # Tombol Sekunder / Netral
    SECONDARY_BTN = ("#f1f5f9", "#1c1c22")
    SECONDARY_HOVER = ("#e2e8f0", "#26262e")
    SECONDARY_TEXT = ("#0f172a", "#f4f4f5")
    
    # Input Background & Border
    INPUT_BG = ("#f8fafc", "#0b0b0e")
    INPUT_BORDER = ("#dbe2ea", "#24242a")
    
    # Status & Utility (Emerald Green & Rose Red)
    SUCCESS_COLOR = ("#059669", "#10b981")
    SUCCESS_BG = ("#ecfdf5", "#0d2818")
    SUCCESS_BORDER = ("#a7f3d0", "#164e2e")
    
    DANGER_COLOR = ("#e11d48", "#f43f5e")
    DANGER_HOVER = ("#be123c", "#e11d48")
    DANGER_BG = ("#fff1f2", "#291317")
    DANGER_BORDER = ("#fecdd3", "#501d24")
    
    # Tipografi
    TEXT_MAIN = ("#09090b", "#f4f4f5")
    TEXT_MUTED = ("#64748b", "#a1a1aa")
    TEXT_DIM = ("#94a3b8", "#71717a")
    
    # Alias kompatibilitas
    ACCENT_COLOR = BTN_PRIMARY_BG
    ACCENT_HOVER = BTN_PRIMARY_HOVER