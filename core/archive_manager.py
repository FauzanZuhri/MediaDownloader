import os
import shutil
from pathlib import Path
from core.config import Config

class ArchiveManager:
    @staticmethod
    def get_archive_path() -> Path:
        return Path(Config.ARCHIVE_FILE)

    @staticmethod
    def ensure_archive_exists():
        path = ArchiveManager.get_archive_path()
        if not path.exists():
            path.touch()

    @staticmethod
    def get_entries() -> list:
        """
        Membaca semua entri di download_archive.txt.
        Returns: list of dict [{"raw": str, "extractor": str, "id": str}]
        """
        ArchiveManager.ensure_archive_exists()
        path = ArchiveManager.get_archive_path()
        entries = []
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    stripped = line.strip()
                    if not stripped or stripped.startswith("#"):
                        continue
                    parts = stripped.split(maxsplit=1)
                    extractor = parts[0] if len(parts) > 1 else "media"
                    video_id = parts[1] if len(parts) > 1 else parts[0]
                    entries.append({
                        "raw": stripped,
                        "extractor": extractor,
                        "id": video_id
                    })
        except Exception as e:
            print(f"[ArchiveManager] Error membaca arsip: {e}")
        return entries

    @staticmethod
    def get_count() -> int:
        return len(ArchiveManager.get_entries())

    @staticmethod
    def remove_entry(entry_id: str) -> bool:
        """Menghapus entri spesifik dari arsip agar dapat diunduh ulang."""
        path = ArchiveManager.get_archive_path()
        if not path.exists():
            return False
        
        try:
            entries = ArchiveManager.get_entries()
            new_lines = [e["raw"] + "\n" for e in entries if e["id"] != entry_id and e["raw"] != entry_id]
            with open(path, "w", encoding="utf-8") as f:
                f.writelines(new_lines)
            return True
        except Exception as e:
            print(f"[ArchiveManager] Error menghapus entri: {e}")
            return False

    @staticmethod
    def clear_archive() -> bool:
        """Mengosongkan seluruh isi file riwayat arsip."""
        try:
            path = ArchiveManager.get_archive_path()
            with open(path, "w", encoding="utf-8") as f:
                f.write("")
            return True
        except Exception as e:
            print(f"[ArchiveManager] Error mengosongkan arsip: {e}")
            return False

    @staticmethod
    def export_archive(dest_path: str) -> bool:
        """Mengekspor file arsip ke lokasi tujuan pilihan pengguna."""
        try:
            path = ArchiveManager.get_archive_path()
            shutil.copy2(str(path), dest_path)
            return True
        except Exception as e:
            print(f"[ArchiveManager] Error ekspor arsip: {e}")
            return False
