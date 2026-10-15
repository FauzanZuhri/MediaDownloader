import os
import json
from pathlib import Path
from core.config import Config

SETTINGS_FILE = Path(__file__).parent.parent / "settings.json"

ACCENT_PRESETS = {
    "Indigo": {"accent": "#6366f1", "hover": "#4f46e5"},
    "Emerald": {"accent": "#10b981", "hover": "#059669"},
    "Crimson": {"accent": "#f43f5e", "hover": "#e11d48"},
    "Cyan": {"accent": "#06b6d4", "hover": "#0891b2"},
    "Violet": {"accent": "#8b5cf6", "hover": "#7c3aed"},
    "Amber": {"accent": "#f59e0b", "hover": "#d97706"},
}

NAMING_PRESETS = [
    ("{title}", "Judul Saja (Contoh: Lagu Keren.mp3)"),
    ("{artist} - {title}", "Artis - Judul (Contoh: Artis - Lagu Keren.mp3)"),
    ("{title} [{id}]", "Judul [ID YouTube] (Contoh: Lagu Keren [dQw4w9WgXcQ].mp3)"),
    ("{index}. {title}", "Nomor Playlist - Judul (Contoh: 01. Lagu Keren.mp3)"),
]

DEFAULT_SETTINGS = {
    "download_dir": str(Path.home() / "Downloads"),
    "naming_template": "{title}",
    "accent_name": "Indigo",
    "auto_check_update": True,
}

class SettingsManager:
    _data = {}

    @classmethod
    def load(cls):
        """Memuat pengaturan dari settings.json dengan fallback ke default."""
        cls._data = dict(DEFAULT_SETTINGS)
        if SETTINGS_FILE.exists():
            try:
                with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                    saved = json.load(f)
                    cls._data.update(saved)
            except Exception as e:
                print(f"[SettingsManager] Gagal membaca settings.json: {e}")
        
        # Sinkronisasi ke runtime Config
        cls.apply_to_config()
        return cls._data

    @classmethod
    def save(cls, new_settings: dict = None):
        """Menyimpan pengaturan ke file settings.json."""
        if new_settings:
            cls._data.update(new_settings)
        
        try:
            with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump(cls._data, f, indent=4)
        except Exception as e:
            print(f"[SettingsManager] Gagal menulis settings.json: {e}")
            
        cls.apply_to_config()

    @classmethod
    def get(cls, key: str, default=None):
        if not cls._data:
            cls.load()
        return cls._data.get(key, default)

    @classmethod
    def set(cls, key: str, value):
        if not cls._data:
            cls.load()
        cls._data[key] = value
        cls.save()

    @classmethod
    def apply_to_config(cls):
        """Menerapkan preferensi warna & path ke runtime Config."""
        accent_name = cls.get("accent_name", "Indigo")
        if accent_name in ACCENT_PRESETS:
            preset = ACCENT_PRESETS[accent_name]
            Config.ACCENT_COLOR = preset["accent"]
            Config.ACCENT_HOVER = preset["hover"]
            
        custom_dl = cls.get("download_dir")
        if custom_dl and os.path.isdir(custom_dl):
            Config.DEFAULT_DOWNLOAD_DIR = custom_dl

# Muat saat module di-import
SettingsManager.load()
