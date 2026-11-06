import os
import threading
import uuid
from dataclasses import dataclass, field
from typing import Optional, Callable, List, Dict, Any

from core.downloader import YtdlpManager
from core.settings import SettingsManager
from core.spotify_parser import MusicLinkParser

class QueueStatus:
    PENDING = "⏳ Pending"
    DOWNLOADING = "⬇ Mengunduh"
    COMPLETED = "✅ Selesai"
    FAILED = "❌ Gagal"
    CANCELED = "⏹ Dibatalkan"

@dataclass
class QueueItem:
    id: str
    url: str
    format_type: str = "MP3"
    quality_setting: str = "Best Audio"
    embed_meta: bool = True
    embed_thumb: bool = True
    title: str = "Menunggu antrean..."
    uploader: str = ""
    progress: float = 0.0
    speed: str = ""
    eta: str = ""
    status: str = QueueStatus.PENDING
    error_msg: str = ""
    custom_meta: Optional[Dict[str, Any]] = None

class BatchQueueManager:
    """
    Manajer Antrean Pengunduhan Massal (Batch Queue Engine).
    Mendukung eksekusi berantai yang aman (sekuensial), pelacakan progres per-item,
    pembatalan thread-safe, dan pengulangan (retry) otomatis untuk unduhan yang gagal.
    """
    def __init__(self, on_item_updated: Callable[[QueueItem], None] = None,
                 on_queue_finished: Callable[[], None] = None,
                 log_callback: Callable[[str], None] = None):
        self.items: List[QueueItem] = []
        self.on_item_updated = on_item_updated
        self.on_queue_finished = on_queue_finished
        self.log_callback = log_callback
        
        self.is_running = False
        self.current_downloader: Optional[YtdlpManager] = None
        self._worker_thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()

    def _log(self, msg: str):
        if self.log_callback:
            self.log_callback(f"[BatchQueue] {msg}")

    def add_url(self, url: str, format_type: str = "MP3", quality_setting: str = "Best Audio",
                embed_meta: bool = True, embed_thumb: bool = True,
                title: str = None, custom_meta: dict = None) -> QueueItem:
        with self._lock:
            clean_url = url.strip()
            item_id = str(uuid.uuid4())[:8]
            item_title = title or clean_url
            
            # Deteksi cepat nama track jika merupakan Spotify/Apple Music
            if not title:
                music_data = MusicLinkParser.parse(clean_url)
                if music_data.get('is_music_link') and music_data.get('title'):
                    item_title = f"{music_data.get('artist', '')} - {music_data.get('title')}".strip(" -")
                    custom_meta = music_data

            item = QueueItem(
                id=item_id,
                url=clean_url,
                format_type=format_type,
                quality_setting=quality_setting,
                embed_meta=embed_meta,
                embed_thumb=embed_thumb,
                title=item_title,
                status=QueueStatus.PENDING,
                custom_meta=custom_meta
            )
            self.items.append(item)
            return item

    def add_urls(self, urls: List[str], format_type: str = "MP3", quality_setting: str = "Best Audio",
                 embed_meta: bool = True, embed_thumb: bool = True) -> int:
        count = 0
        for u in urls:
            u_clean = u.strip()
            if u_clean and not u_clean.startswith("#"):
                self.add_url(u_clean, format_type, quality_setting, embed_meta, embed_thumb)
                count += 1
        return count

    def remove_item(self, item_id: str):
        with self._lock:
            self.items = [i for i in self.items if i.id != item_id]

    def clear_completed(self):
        with self._lock:
            self.items = [i for i in self.items if i.status not in (QueueStatus.COMPLETED, QueueStatus.CANCELED)]

    def clear_all(self):
        if self.is_running:
            self.stop()
        with self._lock:
            self.items.clear()

    def retry_failed(self):
        with self._lock:
            for item in self.items:
                if item.status in (QueueStatus.FAILED, QueueStatus.CANCELED):
                    item.status = QueueStatus.PENDING
                    item.progress = 0.0
                    item.speed = ""
                    item.eta = ""
                    item.error_msg = ""
                    if self.on_item_updated:
                        self.on_item_updated(item)
        if not self.is_running:
            self.start()

    def start(self):
        if self.is_running:
            return
        self.is_running = True
        self._worker_thread = threading.Thread(target=self._run_worker, daemon=True)
        self._worker_thread.start()
        self._log("Proses antrean batch dimulai.")

    def stop(self):
        self.is_running = False
        if self.current_downloader:
            self.current_downloader.cancel()
        self._log("Permintaan penghentian antrean batch dikirim.")

    def get_summary(self) -> Dict[str, int]:
        with self._lock:
            total = len(self.items)
            completed = sum(1 for i in self.items if i.status == QueueStatus.COMPLETED)
            failed = sum(1 for i in self.items if i.status == QueueStatus.FAILED)
            pending = sum(1 for i in self.items if i.status == QueueStatus.PENDING)
            downloading = sum(1 for i in self.items if i.status == QueueStatus.DOWNLOADING)
            return {
                "total": total,
                "completed": completed,
                "failed": failed,
                "pending": pending,
                "downloading": downloading
            }

    def _run_worker(self):
        output_dir = SettingsManager.get("download_dir", os.path.expanduser("~/Downloads"))
        normalize_audio = SettingsManager.get("normalize_audio", False)

        while self.is_running:
            # Ambil item pending berikutnya
            target_item: Optional[QueueItem] = None
            with self._lock:
                for item in self.items:
                    if item.status == QueueStatus.PENDING:
                        target_item = item
                        break

            if not target_item or not self.is_running:
                break

            # Mulai download target_item
            target_item.status = QueueStatus.DOWNLOADING
            target_item.progress = 0.0
            if self.on_item_updated:
                self.on_item_updated(target_item)

            self._log(f"Memproses [{target_item.id}]: {target_item.url}")

            # Callback progress khusus item aktif
            def _progress_cb(p_data):
                if not self.is_running:
                    return
                pct = p_data.get('percentage', 0.0)
                target_item.progress = pct
                target_item.speed = p_data.get('speed', '')
                target_item.eta = p_data.get('eta', '')
                if self.on_item_updated:
                    self.on_item_updated(target_item)

            self.current_downloader = YtdlpManager(
                log_callback=self.log_callback,
                progress_callback=_progress_cb
            )

            try:
                self.current_downloader.download(
                    url=target_item.url,
                    output_dir=output_dir,
                    format_type=target_item.format_type,
                    quality_setting=target_setting if (target_setting := target_item.quality_setting) else "Best Audio",
                    embed_meta=target_item.embed_meta,
                    embed_thumb=target_item.embed_thumb,
                    use_archive=True,
                    normalize_audio=normalize_audio,
                    override_meta=target_item.custom_meta
                )

                if self.current_downloader.cancel_requested:
                    target_item.status = QueueStatus.CANCELED
                    self._log(f"[{target_item.id}] Dibatalkan oleh pengguna.")
                else:
                    target_item.status = QueueStatus.COMPLETED
                    target_item.progress = 1.0
                    target_item.speed = ""
                    target_item.eta = ""
                    self._log(f"[{target_item.id}] Selesai diunduh.")

            except Exception as e:
                target_item.status = QueueStatus.FAILED
                target_item.error_msg = str(e)
                self._log(f"[{target_item.id}] Gagal: {str(e)}")

            if self.on_item_updated:
                self.on_item_updated(target_item)

        self.is_running = False
        self.current_downloader = None
        self._log("Seluruh proses antrean batch selesai atau dihentikan.")
        if self.on_queue_finished:
            self.on_queue_finished()

