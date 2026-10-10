import os
import customtkinter as ctk
from tkinter import filedialog
import threading
import requests
from io import BytesIO
from PIL import Image

from core.config import Config
from ui.components import CardFrame, MediaPreviewCard, CollapsibleLogArea
from core.downloader import YtdlpManager

class MainWindow(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title(f"{Config.APP_TITLE} {Config.VERSION}")
        self.geometry(Config.WINDOW_SIZE)
        self.minsize(920, 700)
        
        ctk.set_appearance_mode(Config.THEME)
        ctk.set_default_color_theme(Config.COLOR_THEME)
        self.configure(fg_color=Config.BG_COLOR)
        
        # Grid layout root
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)  # Area konten utama bisa expand
        
        self._create_widgets()
        
        self.downloader = YtdlpManager(
            log_callback=self.log_area.write_log,
            progress_callback=self._update_ui_progress
        )
        
        # Binding Event URL Preview
        self.url_entry.bind("<Return>", lambda e: self._start_preview_thread())
        self.url_entry.bind("<FocusOut>", lambda e: self._start_preview_thread())

    def _create_widgets(self):
        # =========================================================================
        # 1. HEADER BAR
        # =========================================================================
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.grid(row=0, column=0, padx=24, pady=(16, 10), sticky="ew")
        self.header_frame.grid_columnconfigure(0, weight=1)
        
        self.title_row = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        self.title_row.grid(row=0, column=0, sticky="w")
        
        self.logo_icon = ctk.CTkLabel(
            self.title_row,
            text="🎵",
            font=("Segoe UI Emoji", 24)
        )
        self.logo_icon.pack(side="left", padx=(0, 10))
        
        self.header_label = ctk.CTkLabel(
            self.title_row,
            text=Config.APP_TITLE,
            font=("Segoe UI", 20, "bold"),
            text_color=Config.TEXT_MAIN
        )
        self.header_label.pack(side="left", padx=(0, 10))
        
        self.version_badge = ctk.CTkFrame(
            self.title_row,
            fg_color="#202636",
            corner_radius=6,
            border_width=1,
            border_color="#2e374d"
        )
        self.version_badge.pack(side="left")
        
        self.version_label = ctk.CTkLabel(
            self.version_badge,
            text=Config.VERSION,
            font=("Segoe UI", 11, "bold"),
            text_color=Config.ACCENT_COLOR
        )
        self.version_label.pack(padx=8, pady=2)
        
        self.subtitle_label = ctk.CTkLabel(
            self.header_frame,
            text="Modern YouTube Music & Playlist Downloader with Pure ID3v2.3 Tagging",
            font=("Segoe UI", 12),
            text_color=Config.TEXT_MUTED
        )
        self.subtitle_label.grid(row=1, column=0, padx=(38, 0), sticky="w")

        # =========================================================================
        # 2. MAIN WORKSPACE (2-COLUMN GRID)
        # =========================================================================
        self.content_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.content_frame.grid(row=1, column=0, padx=24, pady=0, sticky="nsew")
        self.content_frame.grid_columnconfigure(0, weight=6)  # Kolom Kiri
        self.content_frame.grid_columnconfigure(1, weight=5)  # Kolom Kanan
        self.content_frame.grid_rowconfigure(0, weight=1)
        
        # -------------------------------------------------------------------------
        # KOLOM KIRI: INPUT & KONFIGURASI
        # -------------------------------------------------------------------------
        self.left_column = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        self.left_column.grid(row=0, column=0, padx=(0, 12), sticky="nsew")
        self.left_column.grid_columnconfigure(0, weight=1)
        
        # --- CARD 1: URL & DESTINATION ---
        self.source_card = CardFrame(self.left_column)
        self.source_card.grid(row=0, column=0, pady=(0, 12), sticky="ew")
        self.source_card.grid_columnconfigure(0, weight=1)
        
        self.source_card_title = ctk.CTkLabel(
            self.source_card,
            text="🔗 SUMBER & LOKASI PENYIMPANAN",
            font=("Segoe UI", 11, "bold"),
            text_color=Config.ACCENT_COLOR,
            anchor="w"
        )
        self.source_card_title.grid(row=0, column=0, padx=16, pady=(14, 8), sticky="w")
        
        # URL Input Row dengan Tombol Paste & Clear
        self.url_box_frame = ctk.CTkFrame(self.source_card, fg_color="transparent")
        self.url_box_frame.grid(row=1, column=0, padx=16, pady=(0, 10), sticky="ew")
        self.url_box_frame.grid_columnconfigure(0, weight=1)
        
        self.url_entry = ctk.CTkEntry(
            self.url_box_frame,
            placeholder_text="Tempel URL YouTube (Video atau Playlist)...",
            font=("Segoe UI", 12),
            height=36,
            corner_radius=8,
            fg_color="#0b0d13",
            border_color=Config.CARD_BORDER
        )
        self.url_entry.grid(row=0, column=0, padx=(0, 8), sticky="ew")
        
        self.paste_btn = ctk.CTkButton(
            self.url_box_frame,
            text="📋 Paste",
            width=70,
            height=36,
            corner_radius=8,
            font=("Segoe UI", 11, "bold"),
            fg_color="#202636",
            hover_color="#2c354a",
            text_color=Config.TEXT_MAIN,
            command=self._paste_from_clipboard
        )
        self.paste_btn.grid(row=0, column=1, padx=(0, 6), sticky="e")
        
        self.clear_btn = ctk.CTkButton(
            self.url_box_frame,
            text="✖",
            width=36,
            height=36,
            corner_radius=8,
            font=("Segoe UI", 12),
            fg_color="#202636",
            hover_color="#2c354a",
            text_color=Config.TEXT_MUTED,
            command=self._clear_url
        )
        self.clear_btn.grid(row=0, column=2, sticky="e")
        
        # Destination Folder Row
        self.folder_box_frame = ctk.CTkFrame(self.source_card, fg_color="transparent")
        self.folder_box_frame.grid(row=2, column=0, padx=16, pady=(0, 14), sticky="ew")
        self.folder_box_frame.grid_columnconfigure(0, weight=1)
        
        self.path_entry = ctk.CTkEntry(
            self.folder_box_frame,
            font=("Segoe UI", 11),
            height=34,
            corner_radius=8,
            fg_color="#0b0d13",
            border_color=Config.CARD_BORDER
        )
        self.path_entry.grid(row=0, column=0, padx=(0, 8), sticky="ew")
        self.path_entry.insert(0, Config.DEFAULT_DOWNLOAD_DIR)
        
        self.browse_btn = ctk.CTkButton(
            self.folder_box_frame,
            text="📂 Browse",
            width=90,
            height=34,
            corner_radius=8,
            font=("Segoe UI", 11, "bold"),
            fg_color="#202636",
            hover_color="#2c354a",
            text_color=Config.TEXT_MAIN,
            command=self._browse_folder
        )
        self.browse_btn.grid(row=0, column=1, sticky="e")

        # --- CARD 2: PENGATURAN FORMAT & OPSI ---
        self.options_card = CardFrame(self.left_column)
        self.options_card.grid(row=1, column=0, sticky="ew")
        self.options_card.grid_columnconfigure(0, weight=1)
        
        self.options_card_title = ctk.CTkLabel(
            self.options_card,
            text="⚙️ FORMAT & KUALITAS AUDIO",
            font=("Segoe UI", 11, "bold"),
            text_color=Config.ACCENT_COLOR,
            anchor="w"
        )
        self.options_card_title.grid(row=0, column=0, padx=16, pady=(14, 10), sticky="w")
        
        # Format Radios & Quality Dropdown
        self.fmt_row = ctk.CTkFrame(self.options_card, fg_color="transparent")
        self.fmt_row.grid(row=1, column=0, padx=16, pady=(0, 12), sticky="ew")
        self.fmt_row.grid_columnconfigure(2, weight=1)
        
        self.format_var = ctk.StringVar(value="MP3")
        self.mp3_radio = ctk.CTkRadioButton(
            self.fmt_row,
            text="MP3 (Audio)",
            variable=self.format_var,
            value="MP3",
            font=("Segoe UI", 12, "bold"),
            text_color=Config.TEXT_MAIN,
            fg_color=Config.ACCENT_COLOR,
            hover_color=Config.ACCENT_HOVER
        )
        self.mp3_radio.grid(row=0, column=0, padx=(0, 18), sticky="w")
        
        self.mp4_radio = ctk.CTkRadioButton(
            self.fmt_row,
            text="MP4 (Video)",
            variable=self.format_var,
            value="MP4",
            font=("Segoe UI", 12, "bold"),
            text_color=Config.TEXT_MAIN,
            fg_color=Config.ACCENT_COLOR,
            hover_color=Config.ACCENT_HOVER
        )
        self.mp4_radio.grid(row=0, column=1, padx=(0, 20), sticky="w")
        
        self.quality_dropdown = ctk.CTkComboBox(
            self.fmt_row,
            values=["Best Audio", "320kbps", "192kbps", "128kbps"],
            font=("Segoe UI", 11),
            dropdown_font=("Segoe UI", 11),
            corner_radius=8,
            fg_color="#0b0d13",
            border_color=Config.CARD_BORDER,
            button_color="#202636",
            button_hover_color="#2c354a",
            width=120,
            height=32
        )
        self.quality_dropdown.set("Best Audio")
        self.quality_dropdown.grid(row=0, column=2, sticky="e")
        
        # Checkbox Options (Metadata, Cover, Archive)
        self.checkbox_row = ctk.CTkFrame(self.options_card, fg_color="transparent")
        self.checkbox_row.grid(row=2, column=0, padx=16, pady=(0, 16), sticky="ew")
        
        self.meta_cb = ctk.CTkCheckBox(
            self.checkbox_row,
            text="Embed ID3 Tags",
            font=("Segoe UI", 11),
            text_color=Config.TEXT_MAIN,
            fg_color=Config.ACCENT_COLOR,
            hover_color=Config.ACCENT_HOVER,
            corner_radius=6
        )
        self.meta_cb.select()
        self.meta_cb.pack(side="left", padx=(0, 14))
        
        self.thumb_cb = ctk.CTkCheckBox(
            self.checkbox_row,
            text="Embed Cover Art",
            font=("Segoe UI", 11),
            text_color=Config.TEXT_MAIN,
            fg_color=Config.ACCENT_COLOR,
            hover_color=Config.ACCENT_HOVER,
            corner_radius=6
        )
        self.thumb_cb.select()
        self.thumb_cb.pack(side="left", padx=(0, 14))
        
        self.archive_cb = ctk.CTkCheckBox(
            self.checkbox_row,
            text="Skip Existing",
            font=("Segoe UI", 11),
            text_color=Config.TEXT_MAIN,
            fg_color=Config.ACCENT_COLOR,
            hover_color=Config.ACCENT_HOVER,
            corner_radius=6
        )
        self.archive_cb.select()
        self.archive_cb.pack(side="left")

        # -------------------------------------------------------------------------
        # KOLOM KANAN: LIVE MEDIA PREVIEW CARD
        # -------------------------------------------------------------------------
        self.right_column = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        self.right_column.grid(row=0, column=1, padx=(12, 0), sticky="nsew")
        self.right_column.grid_columnconfigure(0, weight=1)
        
        self.info_panel = MediaPreviewCard(self.right_column)
        self.info_panel.grid(row=0, column=0, sticky="nsew")

        # =========================================================================
        # 3. PROGRESS & CONTROL HUB (BOTTOM)
        # =========================================================================
        self.hub_card = CardFrame(self)
        self.hub_card.grid(row=2, column=0, padx=24, pady=(12, 8), sticky="ew")
        self.hub_card.grid_columnconfigure(0, weight=1)
        
        # Baris Status Informasi & Stats
        self.stats_row = ctk.CTkFrame(self.hub_card, fg_color="transparent")
        self.stats_row.grid(row=0, column=0, padx=16, pady=(12, 6), sticky="ew")
        self.stats_row.grid_columnconfigure(0, weight=1)
        
        self.status_label = ctk.CTkLabel(
            self.stats_row,
            text="Status: Idle",
            font=("Segoe UI", 11, "bold"),
            text_color=Config.TEXT_MAIN,
            anchor="w"
        )
        self.status_label.grid(row=0, column=0, sticky="w")
        
        self.speed_label = ctk.CTkLabel(
            self.stats_row,
            text="Speed: 0 KB/s",
            font=("Segoe UI", 11),
            text_color=Config.TEXT_MUTED
        )
        self.speed_label.grid(row=0, column=1, padx=(0, 16), sticky="e")
        
        self.eta_label = ctk.CTkLabel(
            self.stats_row,
            text="ETA: 00:00",
            font=("Segoe UI", 11),
            text_color=Config.TEXT_MUTED
        )
        self.eta_label.grid(row=0, column=2, sticky="e")
        
        # Progress Bar Modern
        self.progress_bar = ctk.CTkProgressBar(
            self.hub_card,
            height=8,
            corner_radius=4,
            fg_color="#0b0d13",
            progress_color=Config.ACCENT_COLOR
        )
        self.progress_bar.grid(row=1, column=0, padx=16, pady=(0, 12), sticky="ew")
        self.progress_bar.set(0.0)
        
        # Tombol Aksi Download / Cancel / Open Folder
        self.actions_row = ctk.CTkFrame(self.hub_card, fg_color="transparent")
        self.actions_row.grid(row=2, column=0, padx=16, pady=(0, 12), sticky="ew")
        self.actions_row.grid_columnconfigure(0, weight=1)
        
        self.btn_left_frame = ctk.CTkFrame(self.actions_row, fg_color="transparent")
        self.btn_left_frame.grid(row=0, column=0, sticky="w")
        
        self.download_btn = ctk.CTkButton(
            self.btn_left_frame,
            text="⬇ Unduh Sekarang",
            font=("Segoe UI", 12, "bold"),
            width=150,
            height=36,
            corner_radius=8,
            fg_color=Config.ACCENT_COLOR,
            hover_color=Config.ACCENT_HOVER,
            command=self._start_download_thread
        )
        self.download_btn.pack(side="left", padx=(0, 10))
        
        self.cancel_btn = ctk.CTkButton(
            self.btn_left_frame,
            text="⏹ Batal",
            font=("Segoe UI", 11, "bold"),
            width=90,
            height=36,
            corner_radius=8,
            fg_color=Config.DANGER_COLOR,
            hover_color=Config.DANGER_HOVER,
            state="disabled",
            command=self._cancel_download
        )
        self.cancel_btn.pack(side="left")
        
        self.open_folder_btn = ctk.CTkButton(
            self.actions_row,
            text="📂 Buka Folder",
            font=("Segoe UI", 11, "bold"),
            width=120,
            height=36,
            corner_radius=8,
            fg_color=Config.SECONDARY_BTN,
            hover_color=Config.SECONDARY_HOVER,
            text_color=Config.TEXT_MAIN,
            command=self.open_download_folder
        )
        self.open_folder_btn.grid(row=0, column=1, sticky="e")

        # =========================================================================
        # 4. COLLAPSIBLE ACTIVITY CONSOLE (FOOTER)
        # =========================================================================
        self.log_area = CollapsibleLogArea(self)
        self.log_area.grid(row=3, column=0, padx=24, pady=(0, 16), sticky="ew")

    # =========================================================================
    # LOGIKA & HELPER
    # =========================================================================
    def _paste_from_clipboard(self):
        """Ambil URL dari clipboard sistem dan picu preview otomatis."""
        try:
            clipboard_text = self.clipboard_get().strip()
            if clipboard_text:
                self.url_entry.delete(0, "end")
                self.url_entry.insert(0, clipboard_text)
                self._start_preview_thread()
        except Exception:
            pass

    def _clear_url(self):
        """Bersihkan kolom input URL dan reset preview."""
        self.url_entry.delete(0, "end")
        self.info_panel.reset()
        self.status_label.configure(text="Status: Idle")

    def _start_preview_thread(self):
        """Menjalankan preview media di background thread."""
        url = self.url_entry.get().strip()
        # Validasi: URL harus berawalan protokol web
        if not url or not url.startswith(("http://", "https://")):
            return
            
        self.status_label.configure(text="Status: Mengambil preview...")
        preview_thread = threading.Thread(target=self._load_preview_data, args=(url,), daemon=True)
        preview_thread.start()

    def _load_preview_data(self, url: str):
        info = self.downloader.fetch_metadata(url)
        if not info:
            self.status_label.configure(text="Status: Gagal memuat info.")
            return

        title = info.get('title', 'Unknown Title')
        channel = info.get('uploader', 'Unknown Channel')
        is_playlist = 'entries' in info
        
        if is_playlist:
            duration_text = "N/A"
            video_count = f"Playlist ({len(info.get('entries', []))} items)"
        else:
            duration = info.get('duration', 0)
            duration_text = f"{duration // 60}:{duration % 60:02d}"
            video_count = "Single Track"

        thumbnails = info.get('thumbnails', [])
        thumb_url = thumbnails[-1]['url'] if thumbnails else None

        ctk_img = None
        if thumb_url:
            try:
                res = requests.get(thumb_url, timeout=5)
                if res.status_code == 200:
                    raw_img = Image.open(BytesIO(res.content))
                    ctk_img = ctk.CTkImage(light_image=raw_img, dark_image=raw_img, size=(220, 124))
            except Exception:
                ctk_img = None

        # Update UI dari background thread secara aman
        self.info_panel.set_preview(title, channel, duration_text, video_count, ctk_img)
        self.status_label.configure(text="Status: Preview siap.")

    def _start_download_thread(self):
        url = self.url_entry.get().strip()
        output_dir = self.path_entry.get().strip()
        format_type = self.format_var.get()
        quality_setting = self.quality_dropdown.get()
        embed_meta = bool(self.meta_cb.get())   
        embed_thumb = bool(self.thumb_cb.get()) 
        use_archive = bool(self.archive_cb.get())
        
        if not url:
            self.log_area.write_log("[Error] Silakan masukkan URL YouTube terlebih dahulu!")
            self.status_label.configure(text="Status: URL Kosong!")
            return
            
        # Update status tombol UI
        self.download_btn.configure(state="disabled")
        self.cancel_btn.configure(state="normal")
        self.status_label.configure(text="Status: Memulai unduhan...")
        
        download_thread = threading.Thread(
            target=self._run_download,
            args=(url, output_dir, format_type, quality_setting, embed_meta, embed_thumb, use_archive),
            daemon=True
        )
        download_thread.start()

    def _run_download(self, url, output_dir, format_type, quality_setting, embed_meta, embed_thumb, use_archive):
        try:
            self.downloader.download(
                url=url,
                output_dir=output_dir,
                format_type=format_type,
                quality_setting=quality_setting,
                embed_meta=embed_meta,
                embed_thumb=embed_thumb,
                use_archive=use_archive
            )
        finally:
            # Kembalikan kondisi tombol setelah selesai / batal
            self.download_btn.configure(state="normal")
            self.cancel_btn.configure(state="disabled")

    def _cancel_download(self):
        """Batalkan proses download yang sedang berjalan."""
        self.downloader.cancel()
        self.status_label.configure(text="Status: Membatalkan...")

    def _browse_folder(self):
        """Dialog pemilih folder unduhan."""
        selected_dir = filedialog.askdirectory(initialdir=self.path_entry.get())
        if selected_dir:
            self.path_entry.delete(0, "end")
            self.path_entry.insert(0, selected_dir)

    def open_download_folder(self):
        """Membuka folder unduhan di Windows Explorer."""
        folder_path = self.path_entry.get().strip()
        if not os.path.exists(folder_path):
            try:
                os.makedirs(folder_path, exist_ok=True)
            except Exception:
                pass
                
        if os.path.exists(folder_path):
            os.startfile(folder_path)
        else:
            self.log_area.write_log("[Error] Folder tujuan tidak dapat dibuka atau tidak ditemukan!")

    def _update_ui_progress(self, data: dict):
        """Memperbarui visual progress bar, kecepatan, dan status."""
        percentage = data.get('percentage', 0.0)
        speed = data.get('speed', '0 KB/s')
        eta = data.get('eta', '00:00')
        status = data.get('status', 'Status: Idle')

        self.progress_bar.set(percentage)
        self.speed_label.configure(text=f"Speed: {speed}")
        self.eta_label.configure(text=f"ETA: {eta}")
        self.status_label.configure(text=status)