import os
import sys
import threading
import webbrowser
import requests
from io import BytesIO
from PIL import Image, ImageOps
import customtkinter as ctk
from tkinter import filedialog, messagebox

from core.config import Config
from core.settings import SettingsManager, NAMING_PRESETS
from core.archive_manager import ArchiveManager
from core.updater import YtdlpUpdater
from core.downloader import YtdlpManager
from core.queue_manager import BatchQueueManager, QueueItem, QueueStatus
from core.platform_helper import PlatformHelper
from core.tray_manager import SystemTrayManager
from ui.playlist_modal import PlaylistSelectorModal
from ui.components import CardFrame, MediaPreviewCard, MultiStageProgress, CollapsibleLogArea


class MainWindow(ctk.CTk):
    """
    Antarmuka Utama MediaDownloader v1.3.0 (Clean Minimalist Edition)
    Menghadirkan Segmented Capsule Navbar, palet clean Dark/Light mode,
    dan visual hierarchy yang tenang, rapi, serta bebas elemen norak.
    """
    def __init__(self):
        super().__init__()
        
        # Load user settings
        self.settings = SettingsManager.load()
        self.current_theme = self.settings.get("appearance_mode", Config.THEME)
        
        self.title(f"{Config.APP_TITLE}")
        self.geometry(Config.WINDOW_SIZE)
        self.minsize(940, 720)
        
        ctk.set_appearance_mode(self.current_theme)
        ctk.set_default_color_theme(Config.COLOR_THEME)
        self.configure(fg_color=Config.BG_COLOR)
        
        # Set Window Icon resmi
        icon_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "assets", "icon.ico"))
        if os.path.exists(icon_path):
            try:
                self.iconbitmap(icon_path)
            except Exception:
                pass

        # Grid layout utama window
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)  # Area konten utama dinamis
        
        # Inisialisasi engine & state
        self.downloader = None
        self._last_detected_clipboard = ""
        self._active_tab = "downloader"
        self._queue_widget_rows = {}
        self._preview_debounce_timer = None

        # Setup batch queue engine dengan callbacks
        self.queue_manager = BatchQueueManager(
            on_item_updated=self._on_queue_item_updated,
            on_queue_finished=self._on_queue_finished,
            log_callback=lambda msg: self.log_area.write_log(msg)
        )
        
        self._create_layout()
        
        # Setup downloader engine dengan callbacks
        self.downloader = YtdlpManager(
            log_callback=self.log_area.write_log,
            progress_callback=self._update_ui_progress
        )
        
        # Setup clipboard sniffer
        self.bind("<FocusIn>", lambda e: self._check_clipboard_sniff())
        
        # System Tray Manager (Integrasi background Windows)
        self.tray_manager = SystemTrayManager(
            on_show=lambda: self.after(0, self._restore_from_tray),
            on_open_folder=self._open_downloads_folder_tray,
            on_quit=lambda: self.after(0, self._quit_application)
        )
        self.protocol("WM_DELETE_WINDOW", self._on_window_close)
        
        # Mulai monitor clipboard aktif di latar belakang (interval 1.5 detik)
        self.after(1500, self._poll_clipboard_background)
        
        # Switch ke tab awal
        self._switch_tab("downloader")

    # =========================================================================
    # ARSITEKTUR LAYOUT UTAMA (HEADER, NAVBAR CAPSULE, WORKSPACE, FOOTER)
    # =========================================================================
    def _create_layout(self):
        # ---------------------------------------------------------------------
        # 1. HEADER BAR (HANYA LOGO DAN JUDUL DI KIRI, AKSI DI KANAN)
        # ---------------------------------------------------------------------
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.grid(row=0, column=0, padx=24, pady=(16, 8), sticky="ew")
        self.header_frame.grid_columnconfigure(0, weight=1)
        
        # Brand Left (HANYA LOGO DAN JUDUL APLIKASI)
        self.brand_row = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        self.brand_row.grid(row=0, column=0, sticky="w")
        
        self.logo_icon = ctk.CTkLabel(
            self.brand_row,
            text="📥",
            font=("Segoe UI Emoji", 20)
        )
        self.logo_icon.pack(side="left", padx=(0, 8))
        
        self.title_label = ctk.CTkLabel(
            self.brand_row,
            text=Config.APP_TITLE,
            font=("Segoe UI", 18, "bold"),
            text_color=Config.TEXT_MAIN
        )
        self.title_label.pack(side="left")
        
        # Header Right Actions: Toggle Mode Tema & Buka Folder
        self.header_actions = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        self.header_actions.grid(row=0, column=1, sticky="e")
        
        # Tombol Buka Folder Cepat
        self.quick_folder_btn = ctk.CTkButton(
            self.header_actions,
            text="📂 Buka Folder",
            font=("Segoe UI", 11, "bold"),
            width=105,
            height=32,
            corner_radius=7,
            fg_color=Config.SECONDARY_BTN,
            hover_color=Config.SECONDARY_HOVER,
            text_color=Config.SECONDARY_TEXT,
            command=self._open_download_folder
        )
        self.quick_folder_btn.pack(side="right", padx=(8, 0))
        
        # Tombol Sakelar Tema (Dark / Light Mode)
        theme_btn_text = "☀️ Light" if self.current_theme.lower() == "dark" else "🌙 Dark"
        self.theme_toggle_btn = ctk.CTkButton(
            self.header_actions,
            text=theme_btn_text,
            font=("Segoe UI", 11, "bold"),
            width=85,
            height=32,
            corner_radius=7,
            fg_color=Config.SECONDARY_BTN,
            hover_color=Config.SECONDARY_HOVER,
            text_color=Config.SECONDARY_TEXT,
            command=self._toggle_theme_mode
        )
        self.theme_toggle_btn.pack(side="right")

        # ---------------------------------------------------------------------
        # 2. TOP NAVIGATION CAPSULE BAR (BERBENTUK DOCK NYATA / SEGMENTED)
        # ---------------------------------------------------------------------
        self.nav_wrapper = ctk.CTkFrame(self, fg_color="transparent")
        self.nav_wrapper.grid(row=1, column=0, padx=24, pady=(4, 14), sticky="ew")
        
        # Kontainer Dock Kapsul
        self.nav_dock = ctk.CTkFrame(
            self.nav_wrapper,
            fg_color=Config.NAV_TRACK_BG,
            corner_radius=9,
            border_width=1,
            border_color=Config.NAV_TRACK_BORDER,
            height=42
        )
        self.nav_dock.pack(side="left")
        
        self.tab_buttons = {}
        tab_definitions = [
            ("downloader", "📥 Quick Downloader"),
            ("batch", "📋 Batch Queue"),
            ("history", "📁 Riwayat & Arsip"),
            ("settings", "⚙️ Pengaturan")
        ]
        
        for tab_id, tab_label in tab_definitions:
            btn = ctk.CTkButton(
                self.nav_dock,
                text=tab_label,
                font=("Segoe UI", 11, "bold"),
                height=32,
                corner_radius=7,
                border_width=0,
                fg_color="transparent",
                hover_color=Config.NAV_TAB_HOVER,
                text_color=Config.NAV_TAB_INACTIVE_TEXT,
                command=lambda tid=tab_id: self._switch_tab(tid)
            )
            btn.pack(side="left", padx=3, pady=4)
            self.tab_buttons[tab_id] = btn

        # ---------------------------------------------------------------------
        # 3. WORKSPACE CONTAINER (MEMUAT HALAMAN AKTIF)
        # ---------------------------------------------------------------------
        self.workspace = ctk.CTkFrame(self, fg_color="transparent")
        self.workspace.grid(row=2, column=0, padx=24, pady=0, sticky="nsew")
        self.workspace.grid_columnconfigure(0, weight=1)
        self.workspace.grid_rowconfigure(0, weight=1)
        
        # Inisialisasi setiap View
        self._init_downloader_view()
        self._init_batch_view()
        self._init_history_view()
        self._init_settings_view()

        # ---------------------------------------------------------------------
        # 4. COLLAPSIBLE ACTIVITY CONSOLE (DRAWER BAWAH)
        # ---------------------------------------------------------------------
        self.log_area = CollapsibleLogArea(self)
        self.log_area.grid(row=3, column=0, padx=24, pady=(10, 16), sticky="ew")

    # =========================================================================
    # TOGGLE THEME MODE (DARK / LIGHT) - INSTANT IN-PLACE TRANSITION
    # =========================================================================
    def _toggle_theme_mode(self):
        """Beralih secara instan antara Dark Mode dan Light Mode tanpa jeda/flicker."""
        new_mode = "light" if self.current_theme.lower() == "dark" else "dark"
        self.current_theme = new_mode
        
        # 1. Update mode tampilan in-place di CustomTkinter (tanpa unmap / remap)
        ctk.set_appearance_mode(new_mode)
        
        # 2. Update teks tombol toggle di header
        self.theme_toggle_btn.configure(
            text="☀️ Light" if new_mode == "dark" else "🌙 Dark"
        )
        
        # 3. Sinkronkan radio button di Settings jika ada
        if hasattr(self, "theme_mode_var"):
            self.theme_mode_var.set("Dark" if new_mode == "dark" else "Light")
            
        # 4. Simpan preferensi secara asinkron di background thread
        self.settings["appearance_mode"] = new_mode
        threading.Thread(target=SettingsManager.save, args=(self.settings, False), daemon=True).start()

    def _windows_set_titlebar_color(self, color_mode: str):
        """
        Ganti warna titlebar Windows secara native via DWM API tanpa super().withdraw().
        Menghilangkan kedipan / jeda layar putih 1 detik sepenuhnya.
        """
        if not sys.platform.startswith("win"):
            return
            
        value = 1 if color_mode.lower() == "dark" else 0
        try:
            import ctypes
            hwnd = ctypes.windll.user32.GetParent(self.winfo_id())
            # DWMWA_USE_IMMERSIVE_DARK_MODE = 20 (Windows 10 20H1+ & Windows 11)
            # DWMWA_USE_IMMERSIVE_DARK_MODE_BEFORE_20H1 = 19
            res = ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd, 20, ctypes.byref(ctypes.c_int(value)), ctypes.sizeof(ctypes.c_int(value))
            )
            if res != 0:
                ctypes.windll.dwmapi.DwmSetWindowAttribute(
                    hwnd, 19, ctypes.byref(ctypes.c_int(value)), ctypes.sizeof(ctypes.c_int(value))
                )
            # Refresh non-client frame Windows secara instan tanpa menyembunyikan window
            SWP_NOMOVE = 0x0002
            SWP_NOSIZE = 0x0001
            SWP_NOZORDER = 0x0004
            SWP_FRAMECHANGED = 0x0020
            ctypes.windll.user32.SetWindowPos(hwnd, 0, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE | SWP_NOZORDER | SWP_FRAMECHANGED)
        except Exception:
            pass

    # =========================================================================
    # VIEW 1: TOP-DOWN STREAMLINED QUICK DOWNLOADER
    # =========================================================================
    def _init_downloader_view(self):
        self.view_downloader = ctk.CTkScrollableFrame(
            self.workspace,
            fg_color="transparent",
            scrollbar_button_color=Config.SECONDARY_BTN,
            scrollbar_button_hover_color=Config.SECONDARY_HOVER
        )
        self.view_downloader.grid_columnconfigure(0, weight=1)
        
        # ---------------------------------------------------------------------
        # TINGKAT 1: SMART URL HERO INPUT BAR
        # ---------------------------------------------------------------------
        self.url_card = CardFrame(self.view_downloader)
        self.url_card.grid(row=0, column=0, pady=(0, 12), sticky="ew")
        self.url_card.grid_columnconfigure(0, weight=1)
        
        # Header bar kartu URL
        self.url_card_header = ctk.CTkFrame(self.url_card, fg_color="transparent")
        self.url_card_header.grid(row=0, column=0, padx=16, pady=(12, 6), sticky="ew")
        self.url_card_header.grid_columnconfigure(0, weight=1)
        
        self.url_title = ctk.CTkLabel(
            self.url_card_header,
            text="TAUTAN SUMBER MEDIA",
            font=("Segoe UI", 11, "bold"),
            text_color=Config.TEXT_MAIN
        )
        self.url_title.grid(row=0, column=0, sticky="w")
        
        # Chip Clipboard Sniffer
        self.clip_sniff_chip = ctk.CTkButton(
            self.url_card_header,
            text="📋 Tautan terdeteksi di clipboard (Klik untuk tempel)",
            font=("Segoe UI", 10, "bold"),
            height=24,
            corner_radius=6,
            fg_color=Config.SUCCESS_BG,
            border_width=1,
            border_color=Config.SUCCESS_BORDER,
            text_color=Config.SUCCESS_COLOR,
            command=self._paste_from_clipboard
        )
        
        # Input row
        self.url_row = ctk.CTkFrame(self.url_card, fg_color="transparent")
        self.url_row.grid(row=1, column=0, padx=16, pady=(0, 14), sticky="ew")
        self.url_row.grid_columnconfigure(0, weight=1)
        
        self.url_entry = ctk.CTkEntry(
            self.url_row,
            placeholder_text="Tempel URL YouTube, Spotify, atau Apple Music...",
            font=("Segoe UI", 11),
            height=36,
            corner_radius=7,
            fg_color=Config.INPUT_BG,
            border_color=Config.INPUT_BORDER,
            text_color=Config.TEXT_MAIN
        )
        self.url_entry.grid(row=0, column=0, padx=(0, 8), sticky="ew")
        self.url_entry.bind("<Return>", lambda e: self._start_preview_thread(force=True))
        self.url_entry.bind("<KeyRelease>", self._on_url_key_release)
        self.url_entry.bind("<<Paste>>", self._on_url_paste)
        
        self.paste_btn = ctk.CTkButton(
            self.url_row,
            text="Paste",
            width=70,
            height=36,
            corner_radius=7,
            font=("Segoe UI", 11, "bold"),
            fg_color=Config.SECONDARY_BTN,
            hover_color=Config.SECONDARY_HOVER,
            text_color=Config.SECONDARY_TEXT,
            command=self._paste_from_clipboard
        )
        self.paste_btn.grid(row=0, column=1, padx=(0, 6), sticky="e")
        
        self.clear_btn = ctk.CTkButton(
            self.url_row,
            text="Clear",
            width=60,
            height=36,
            corner_radius=7,
            font=("Segoe UI", 11),
            fg_color=Config.SECONDARY_BTN,
            hover_color=Config.SECONDARY_HOVER,
            text_color=Config.TEXT_MUTED,
            command=self._clear_url
        )
        self.clear_btn.grid(row=0, column=2, sticky="e")

        # ---------------------------------------------------------------------
        # TINGKAT 2: HORIZONTAL LIVE MEDIA PREVIEW CARD (16:9 LANDSCAPE)
        # ---------------------------------------------------------------------
        self.info_panel = MediaPreviewCard(self.view_downloader)
        self.info_panel.grid(row=1, column=0, pady=(0, 12), sticky="ew")

        # ---------------------------------------------------------------------
        # TINGKAT 3: DOWNLOAD CONTROL & FORMAT CENTER
        # ---------------------------------------------------------------------
        self.control_card = CardFrame(self.view_downloader)
        self.control_card.grid(row=2, column=0, pady=(0, 12), sticky="ew")
        self.control_card.grid_columnconfigure(0, weight=1)
        
        # Sub-Header Control
        self.ctrl_header = ctk.CTkLabel(
            self.control_card,
            text="PILIHAN FORMAT & LOKASI UNDUHAN",
            font=("Segoe UI", 11, "bold"),
            text_color=Config.TEXT_MAIN,
            anchor="w"
        )
        self.ctrl_header.grid(row=0, column=0, padx=16, pady=(14, 10), sticky="w")
        
        # Baris Opsi Format & Kualitas
        # Baris Opsi Format & Kualitas (Audio MP3, Video MP4)
        self.format_row = ctk.CTkFrame(self.control_card, fg_color="transparent")
        self.format_row.grid(row=1, column=0, padx=16, pady=(0, 10), sticky="ew")
        self.format_row.grid_columnconfigure(3, weight=1)
        
        self.format_var = ctk.StringVar(value="MP3")
        
        self.audio_radio = ctk.CTkRadioButton(
            self.format_row,
            text="Audio (MP3)",
            variable=self.format_var,
            value="MP3",
            font=("Segoe UI", 11, "bold"),
            text_color=Config.TEXT_MAIN,
            fg_color=Config.BTN_PRIMARY_BG,
            hover_color=Config.BTN_PRIMARY_HOVER,
            command=self._on_format_changed
        )
        self.audio_radio.grid(row=0, column=0, padx=(0, 18), sticky="w")
        
        self.video_mp4_radio = ctk.CTkRadioButton(
            self.format_row,
            text="Video (MP4)",
            variable=self.format_var,
            value="MP4",
            font=("Segoe UI", 11, "bold"),
            text_color=Config.TEXT_MAIN,
            fg_color=Config.BTN_PRIMARY_BG,
            hover_color=Config.BTN_PRIMARY_HOVER,
            command=self._on_format_changed
        )
        self.video_mp4_radio.grid(row=0, column=1, padx=(0, 24), sticky="w")
        
        self.quality_label = ctk.CTkLabel(
            self.format_row,
            text="Kualitas / Resolusi:",
            font=("Segoe UI", 11),
            text_color=Config.TEXT_MUTED
        )
        self.quality_label.grid(row=0, column=2, padx=(0, 8), sticky="w")
        
        self.quality_dropdown = ctk.CTkComboBox(
            self.format_row,
            values=["Best Audio", "320kbps", "256kbps", "192kbps", "128kbps"],
            font=("Segoe UI", 11),
            dropdown_font=("Segoe UI", 11),
            corner_radius=7,
            fg_color=Config.INPUT_BG,
            border_color=Config.INPUT_BORDER,
            button_color=Config.SECONDARY_BTN,
            button_hover_color=Config.SECONDARY_HOVER,
            text_color=Config.TEXT_MAIN,
            width=165,
            height=32
        )
        self.quality_dropdown.set("Best Audio")
        self.quality_dropdown.grid(row=0, column=3, sticky="w")

        # Checkbox Options Row
        self.options_row = ctk.CTkFrame(self.control_card, fg_color="transparent")
        self.options_row.grid(row=2, column=0, padx=16, pady=(0, 12), sticky="ew")
        
        self.meta_cb = ctk.CTkCheckBox(
            self.options_row,
            text="Suntik ID3 Tags",
            font=("Segoe UI", 11),
            text_color=Config.TEXT_MAIN,
            fg_color=Config.BTN_PRIMARY_BG,
            hover_color=Config.BTN_PRIMARY_HOVER,
            checkmark_color=Config.BTN_PRIMARY_TEXT,
            corner_radius=5
        )
        self.meta_cb.select()
        self.meta_cb.pack(side="left", padx=(0, 14))
        
        self.thumb_cb = ctk.CTkCheckBox(
            self.options_row,
            text="Sematkan Cover Art",
            font=("Segoe UI", 11),
            text_color=Config.TEXT_MAIN,
            fg_color=Config.BTN_PRIMARY_BG,
            hover_color=Config.BTN_PRIMARY_HOVER,
            checkmark_color=Config.BTN_PRIMARY_TEXT,
            corner_radius=5
        )
        self.thumb_cb.select()
        self.thumb_cb.pack(side="left", padx=(0, 14))
        
        self.archive_cb = ctk.CTkCheckBox(
            self.options_row,
            text="Lewati Jika Ada (Archive)",
            font=("Segoe UI", 11),
            text_color=Config.TEXT_MAIN,
            fg_color=Config.BTN_PRIMARY_BG,
            hover_color=Config.BTN_PRIMARY_HOVER,
            checkmark_color=Config.BTN_PRIMARY_TEXT,
            corner_radius=5
        )
        self.archive_cb.select()
        self.archive_cb.pack(side="left", padx=(0, 14))

        self.norm_cb = ctk.CTkCheckBox(
            self.options_row,
            text="Normalisasi Suara (EBU R128)",
            font=("Segoe UI", 11),
            text_color=Config.TEXT_MAIN,
            fg_color=Config.BTN_PRIMARY_BG,
            hover_color=Config.BTN_PRIMARY_HOVER,
            checkmark_color=Config.BTN_PRIMARY_TEXT,
            corner_radius=5
        )
        if self.settings.get("normalize_audio", False):
            self.norm_cb.select()
        self.norm_cb.pack(side="left")
        
        # Folder Destination Row
        self.folder_row = ctk.CTkFrame(self.control_card, fg_color="transparent")
        self.folder_row.grid(row=3, column=0, padx=16, pady=(0, 14), sticky="ew")
        self.folder_row.grid_columnconfigure(0, weight=1)
        
        default_dir = self.settings.get("download_dir", Config.DEFAULT_DOWNLOAD_DIR)
        self.path_entry = ctk.CTkEntry(
            self.folder_row,
            font=("Segoe UI", 11),
            height=34,
            corner_radius=7,
            fg_color=Config.INPUT_BG,
            border_color=Config.INPUT_BORDER,
            text_color=Config.TEXT_MAIN
        )
        self.path_entry.grid(row=0, column=0, padx=(0, 8), sticky="ew")
        self.path_entry.insert(0, default_dir)
        
        self.browse_btn = ctk.CTkButton(
            self.folder_row,
            text="Ganti Folder",
            width=100,
            height=34,
            corner_radius=7,
            font=("Segoe UI", 11, "bold"),
            fg_color=Config.SECONDARY_BTN,
            hover_color=Config.SECONDARY_HOVER,
            text_color=Config.SECONDARY_TEXT,
            command=self._browse_folder
        )
        self.browse_btn.grid(row=0, column=1, sticky="e")
        
        # Primary Action Bar (Download & Cancel)
        self.action_bar = ctk.CTkFrame(self.control_card, fg_color=Config.CARD_BG_ELEVATED, corner_radius=9)
        self.action_bar.grid(row=4, column=0, padx=16, pady=(0, 14), sticky="ew")
        self.action_bar.grid_columnconfigure(0, weight=1)
        
        self.action_btn_container = ctk.CTkFrame(self.action_bar, fg_color="transparent")
        self.action_btn_container.pack(fill="x", padx=12, pady=10)
        
        # Tombol Unduh Utama (High-Contrast Minimalist)
        self.download_btn = ctk.CTkButton(
            self.action_btn_container,
            text="⬇ Unduh Sekarang",
            font=("Segoe UI", 12, "bold"),
            width=165,
            height=36,
            corner_radius=7,
            fg_color=Config.BTN_PRIMARY_BG,
            hover_color=Config.BTN_PRIMARY_HOVER,
            text_color=Config.BTN_PRIMARY_TEXT,
            command=self._start_download_thread
        )
        self.download_btn.pack(side="left", padx=(0, 10))
        
        # Tombol Batal Unduh (Subtle Danger)
        self.cancel_btn = ctk.CTkButton(
            self.action_btn_container,
            text="⏹ Batal Unduh",
            font=("Segoe UI", 11, "bold"),
            width=110,
            height=36,
            corner_radius=7,
            fg_color=Config.DANGER_BG,
            border_width=1,
            border_color=Config.DANGER_BORDER,
            text_color=Config.DANGER_COLOR,
            hover_color=Config.DANGER_HOVER,
            state="disabled",
            command=self._cancel_download
        )
        self.cancel_btn.pack(side="left", padx=(0, 10))

        # Tombol Buka Pemilih Trek Playlist
        self.playlist_selector_btn = ctk.CTkButton(
            self.action_btn_container,
            text="📑 Pilih Trek Playlist",
            font=("Segoe UI", 11, "bold"),
            width=160,
            height=36,
            corner_radius=7,
            fg_color=Config.SECONDARY_BTN,
            hover_color=Config.SECONDARY_HOVER,
            text_color=Config.SECONDARY_TEXT,
            command=self._open_playlist_selector
        )
        self.playlist_selector_btn.pack(side="left")

        # ---------------------------------------------------------------------
        # TINGKAT 4: MULTI-STAGE PROGRESS STEPPER
        # ---------------------------------------------------------------------
        self.progress_hub = MultiStageProgress(self.view_downloader)
        self.progress_hub.grid(row=3, column=0, pady=(0, 6), sticky="ew")

    # =========================================================================
    # VIEW 2: BATCH QUEUE & MULTI-DOWNLOAD MANAGER (v1.5.0)
    # =========================================================================
    def _init_batch_view(self):
        self.view_batch = ctk.CTkScrollableFrame(self.workspace, fg_color="transparent")
        self.view_batch.grid_columnconfigure(0, weight=1)
        
        # ---------------------------------------------------------------------
        # KARTU 1: INPUT MULTI-LINK & IMPORT FILE
        # ---------------------------------------------------------------------
        card_input = CardFrame(self.view_batch)
        card_input.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        card_input.grid_columnconfigure(0, weight=1)
        
        header_row = ctk.CTkFrame(card_input, fg_color="transparent")
        header_row.grid(row=0, column=0, padx=20, pady=(16, 6), sticky="ew")
        header_row.grid_columnconfigure(0, weight=1)
        
        title_box = ctk.CTkFrame(header_row, fg_color="transparent")
        title_box.pack(side="left")
        
        title = ctk.CTkLabel(
            title_box,
            text="Batch Queue & Media Hub",
            font=("Segoe UI", 16, "bold"),
            text_color=Config.TEXT_MAIN
        )
        title.pack(side="left")
        
        desc = ctk.CTkLabel(
            card_input,
            text="Tempel banyak tautan (YouTube, Spotify, Apple Music) sekaligus atau impor file .txt untuk mengunduh secara otomatis dalam antrean sekuensial.",
            font=("Segoe UI", 11),
            text_color=Config.TEXT_MUTED,
            justify="left"
        )
        desc.grid(row=1, column=0, padx=20, pady=(0, 10), sticky="w")
        
        self.batch_textbox = ctk.CTkTextbox(
            card_input,
            height=130,
            font=("Consolas", 11),
            fg_color=Config.INPUT_BG,
            border_width=1,
            border_color=Config.INPUT_BORDER,
            text_color=Config.TEXT_MAIN,
            corner_radius=7
        )
        self.batch_textbox.grid(row=2, column=0, padx=20, pady=(0, 10), sticky="ew")
        
        input_actions = ctk.CTkFrame(card_input, fg_color="transparent")
        input_actions.grid(row=3, column=0, padx=20, pady=(0, 16), sticky="ew")
        input_actions.grid_columnconfigure(3, weight=1)
        
        btn_paste_clip = ctk.CTkButton(
            input_actions,
            text="📋 Tempel Clipboard",
            font=("Segoe UI", 11, "bold"),
            height=32,
            corner_radius=7,
            fg_color=Config.SECONDARY_BTN,
            hover_color=Config.SECONDARY_HOVER,
            text_color=Config.SECONDARY_TEXT,
            command=self._batch_paste_clipboard
        )
        btn_paste_clip.pack(side="left", padx=(0, 8))
        
        btn_import_file = ctk.CTkButton(
            input_actions,
            text="📁 Import .txt",
            font=("Segoe UI", 11, "bold"),
            height=32,
            corner_radius=7,
            fg_color=Config.SECONDARY_BTN,
            hover_color=Config.SECONDARY_HOVER,
            text_color=Config.SECONDARY_TEXT,
            command=self._batch_import_txt
        )
        btn_import_file.pack(side="left", padx=(0, 8))
        
        btn_clear_input = ctk.CTkButton(
            input_actions,
            text="Bersihkan Input",
            font=("Segoe UI", 11),
            height=32,
            corner_radius=7,
            fg_color=Config.SECONDARY_BTN,
            hover_color=Config.SECONDARY_HOVER,
            text_color=Config.TEXT_MUTED,
            command=self._batch_clear_input
        )
        btn_clear_input.pack(side="left", padx=(0, 8))
        
        btn_add_queue = ctk.CTkButton(
            input_actions,
            text="➕ Masukkan ke Antrean",
            font=("Segoe UI", 11, "bold"),
            height=32,
            corner_radius=7,
            fg_color=Config.BTN_PRIMARY_BG,
            hover_color=Config.BTN_PRIMARY_HOVER,
            text_color=Config.BTN_PRIMARY_TEXT,
            command=self._batch_add_to_queue
        )
        btn_add_queue.pack(side="right")

        # ---------------------------------------------------------------------
        # KARTU 2: PENGATURAN BATCH & KONTROL ANTREAN
        # ---------------------------------------------------------------------
        card_ctrl = CardFrame(self.view_batch)
        card_ctrl.grid(row=1, column=0, sticky="ew", pady=(0, 12))
        card_ctrl.grid_columnconfigure(0, weight=1)
        
        ctrl_top = ctk.CTkFrame(card_ctrl, fg_color="transparent")
        ctrl_top.grid(row=0, column=0, padx=20, pady=(14, 10), sticky="ew")
        ctrl_top.grid_columnconfigure(1, weight=1)
        
        # Pilihan Format & Kualitas untuk Batch
        opts_box = ctk.CTkFrame(ctrl_top, fg_color="transparent")
        opts_box.grid(row=0, column=0, sticky="w")
        
        self.batch_format_var = ctk.StringVar(value="MP3")
        
        self.batch_radio_mp3 = ctk.CTkRadioButton(
            opts_box,
            text="Audio (MP3)",
            variable=self.batch_format_var,
            value="MP3",
            font=("Segoe UI", 11, "bold"),
            text_color=Config.TEXT_MAIN,
            fg_color=Config.BTN_PRIMARY_BG,
            hover_color=Config.BTN_PRIMARY_HOVER,
            command=self._on_batch_format_changed
        )
        self.batch_radio_mp3.pack(side="left", padx=(0, 16))
        
        self.batch_radio_mp4 = ctk.CTkRadioButton(
            opts_box,
            text="Video (MP4)",
            variable=self.batch_format_var,
            value="MP4",
            font=("Segoe UI", 11, "bold"),
            text_color=Config.TEXT_MAIN,
            fg_color=Config.BTN_PRIMARY_BG,
            hover_color=Config.BTN_PRIMARY_HOVER,
            command=self._on_batch_format_changed
        )
        self.batch_radio_mp4.pack(side="left", padx=(0, 16))
        
        lbl_q = ctk.CTkLabel(opts_box, text="Kualitas:", font=("Segoe UI", 11), text_color=Config.TEXT_MUTED)
        lbl_q.pack(side="left", padx=(0, 6))
        
        self.batch_quality_combo = ctk.CTkComboBox(
            opts_box,
            values=["Best Audio", "320kbps", "256kbps", "192kbps", "128kbps"],
            font=("Segoe UI", 11),
            dropdown_font=("Segoe UI", 11),
            height=30,
            width=150,
            corner_radius=6,
            fg_color=Config.INPUT_BG,
            border_color=Config.INPUT_BORDER,
            button_color=Config.SECONDARY_BTN,
            button_hover_color=Config.SECONDARY_HOVER,
            text_color=Config.TEXT_MAIN
        )
        self.batch_quality_combo.set("Best Audio")
        self.batch_quality_combo.pack(side="left")
        
        # Summary Counter Right
        self.batch_summary_lbl = ctk.CTkLabel(
            ctrl_top,
            text="Total: 0 item  •  Pending: 0",
            font=("Segoe UI", 11, "bold"),
            text_color=Config.TEXT_MAIN
        )
        self.batch_summary_lbl.grid(row=0, column=1, sticky="e")
        
        # Tombol-tombol Kontrol Antrean
        ctrl_actions = ctk.CTkFrame(card_ctrl, fg_color=Config.CARD_BG_ELEVATED, corner_radius=8)
        ctrl_actions.grid(row=1, column=0, padx=20, pady=(0, 14), sticky="ew")
        ctrl_actions.grid_columnconfigure(0, weight=1)
        
        action_inner = ctk.CTkFrame(ctrl_actions, fg_color="transparent")
        action_inner.pack(fill="x", padx=10, pady=8)
        
        self.batch_start_btn = ctk.CTkButton(
            action_inner,
            text="▶ Mulai Antrean",
            font=("Segoe UI", 11, "bold"),
            height=34,
            width=140,
            corner_radius=7,
            fg_color=Config.BTN_PRIMARY_BG,
            hover_color=Config.BTN_PRIMARY_HOVER,
            text_color=Config.BTN_PRIMARY_TEXT,
            command=self._batch_start_queue
        )
        self.batch_start_btn.pack(side="left", padx=(0, 8))
        
        self.batch_stop_btn = ctk.CTkButton(
            action_inner,
            text="⏹ Hentikan",
            font=("Segoe UI", 11, "bold"),
            height=34,
            width=100,
            corner_radius=7,
            fg_color=Config.DANGER_BG,
            border_width=1,
            border_color=Config.DANGER_BORDER,
            text_color=Config.DANGER_COLOR,
            hover_color=Config.DANGER_HOVER,
            state="disabled",
            command=self._batch_stop_queue
        )
        self.batch_stop_btn.pack(side="left", padx=(0, 8))
        
        btn_retry_failed = ctk.CTkButton(
            action_inner,
            text="🔄 Ulangi yang Gagal",
            font=("Segoe UI", 11),
            height=34,
            corner_radius=7,
            fg_color=Config.SECONDARY_BTN,
            hover_color=Config.SECONDARY_HOVER,
            text_color=Config.SECONDARY_TEXT,
            command=self._batch_retry_failed
        )
        btn_retry_failed.pack(side="left", padx=(0, 8))
        
        btn_clear_done = ctk.CTkButton(
            action_inner,
            text="🧹 Hapus Selesai",
            font=("Segoe UI", 11),
            height=34,
            corner_radius=7,
            fg_color=Config.SECONDARY_BTN,
            hover_color=Config.SECONDARY_HOVER,
            text_color=Config.SECONDARY_TEXT,
            command=self._batch_clear_completed
        )
        btn_clear_done.pack(side="right", padx=(8, 0))
        
        btn_clear_all = ctk.CTkButton(
            action_inner,
            text="🗑 Kosongkan Antrean",
            font=("Segoe UI", 11),
            height=34,
            corner_radius=7,
            fg_color=Config.SECONDARY_BTN,
            hover_color=Config.SECONDARY_HOVER,
            text_color=Config.TEXT_MUTED,
            command=self._batch_clear_all
        )
        btn_clear_all.pack(side="right")

        # ---------------------------------------------------------------------
        # KARTU 3: DAFTAR ITEM ANTREAN (DYNAMIC QUEUE ITEMS)
        # ---------------------------------------------------------------------
        self.queue_card = CardFrame(self.view_batch)
        self.queue_card.grid(row=2, column=0, sticky="ew", pady=(0, 14))
        self.queue_card.grid_columnconfigure(0, weight=1)
        
        q_hdr = ctk.CTkFrame(self.queue_card, fg_color="transparent")
        q_hdr.grid(row=0, column=0, padx=20, pady=(14, 8), sticky="ew")
        
        q_title = ctk.CTkLabel(
            q_hdr,
            text="DAFTAR ANTREAN UNDUHAN",
            font=("Segoe UI", 11, "bold"),
            text_color=Config.TEXT_MAIN
        )
        q_title.pack(side="left")
        
        self.queue_items_frame = ctk.CTkFrame(self.queue_card, fg_color="transparent")
        self.queue_items_frame.grid(row=1, column=0, padx=20, pady=(0, 16), sticky="ew")
        self.queue_items_frame.grid_columnconfigure(0, weight=1)
        
        # Render tampilan awal antrean
        self._render_batch_queue_list()

    # =========================================================================
    # LOGIKA & INTERAKSI BATCH QUEUE
    # =========================================================================
    def _batch_paste_clipboard(self):
        try:
            text = self.clipboard_get()
            if text:
                self.batch_textbox.insert("end", ("\n" if self.batch_textbox.get("1.0", "end").strip() else "") + text.strip())
        except Exception:
            pass

    def _batch_import_txt(self):
        path = filedialog.askopenfilename(
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")]
        )
        if path:
            try:
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                self.batch_textbox.insert("end", ("\n" if self.batch_textbox.get("1.0", "end").strip() else "") + content.strip())
            except Exception as e:
                messagebox.showerror("Error", f"Gagal membaca file: {e}")

    def _batch_clear_input(self):
        self.batch_textbox.delete("1.0", "end")

    def _on_batch_format_changed(self):
        fmt = self.batch_format_var.get()
        if fmt == "MP3":
            self.batch_quality_combo.configure(values=["Best Audio", "320kbps", "256kbps", "192kbps", "128kbps"])
            self.batch_quality_combo.set("Best Audio")
        else:
            self.batch_quality_combo.configure(values=[
                "Best (4K/Max)", "2160p (4K UHD)", "1440p (2K QHD)", 
                "1080p (Full HD)", "720p (HD)", "480p (SD)", "360p"
            ])
            self.batch_quality_combo.set("1080p (Full HD)")

    def _batch_add_to_queue(self):
        content = self.batch_textbox.get("1.0", "end").strip()
        lines = [line.strip() for line in content.splitlines() if line.strip() and not line.strip().startswith("#")]
        valid_links = [l for l in lines if l.startswith(("http://", "https://"))]
        
        if not valid_links:
            messagebox.showwarning("Perhatian", "Tidak ada tautan URL yang valid ditemukan dalam input teks.")
            return

        fmt = self.batch_format_var.get()
        qty = self.batch_quality_combo.get()
        embed_meta = bool(self.meta_cb.get())
        embed_thumb = bool(self.thumb_cb.get())

        added_count = self.queue_manager.add_urls(
            urls=valid_links,
            format_type=fmt,
            quality_setting=qty,
            embed_meta=embed_meta,
            embed_thumb=embed_thumb
        )
        self.batch_textbox.delete("1.0", "end")
        self._render_batch_queue_list()
        self.log_area.write_log(f"[BatchQueue] Berhasil menambahkan {added_count} tautan ke antrean.")

    def _batch_start_queue(self):
        if not self.queue_manager.items:
            messagebox.showinfo("Antrean Kosong", "Masukkan tautan ke antrean terlebih dahulu.")
            return
        self.batch_start_btn.configure(state="disabled")
        self.batch_stop_btn.configure(state="normal")
        self.queue_manager.start()

    def _batch_stop_queue(self):
        self.queue_manager.stop()
        self.batch_start_btn.configure(state="normal")
        self.batch_stop_btn.configure(state="disabled")

    def _batch_retry_failed(self):
        self.queue_manager.retry_failed()
        if self.queue_manager.is_running:
            self.batch_start_btn.configure(state="disabled")
            self.batch_stop_btn.configure(state="normal")

    def _batch_clear_completed(self):
        self.queue_manager.clear_completed()
        self._render_batch_queue_list()

    def _batch_clear_all(self):
        if self.queue_manager.is_running:
            confirm = messagebox.askyesno("Konfirmasi", "Proses antrean sedang berjalan. Hentikan dan bersihkan seluruh antrean?")
            if not confirm:
                return
        self.queue_manager.clear_all()
        self.batch_start_btn.configure(state="normal")
        self.batch_stop_btn.configure(state="disabled")
        self._render_batch_queue_list()

    def _render_batch_queue_list(self):
        for w in self.queue_items_frame.winfo_children():
            w.destroy()
        self._queue_widget_rows.clear()

        if not self.queue_manager.items:
            empty_lbl = ctk.CTkLabel(
                self.queue_items_frame,
                text="Antrean kosong. Tempel link di atas atau gunakan 'Import .txt'.",
                font=("Segoe UI", 11, "italic"),
                text_color=Config.TEXT_MUTED
            )
            empty_lbl.pack(pady=20)
            self._update_queue_summary_labels()
            return

        for idx, item in enumerate(self.queue_manager.items):
            self._create_queue_item_row(idx, item)

        self._update_queue_summary_labels()

    def _create_queue_item_row(self, idx: int, item: QueueItem):
        row_frame = ctk.CTkFrame(
            self.queue_items_frame,
            fg_color=Config.CARD_BG_ELEVATED,
            corner_radius=7,
            height=44
        )
        row_frame.pack(fill="x", pady=3)
        row_frame.grid_columnconfigure(1, weight=1)

        # Status badge
        badge = ctk.CTkLabel(
            row_frame,
            text=item.status,
            font=("Segoe UI", 10, "bold"),
            width=85,
            height=24,
            corner_radius=5,
            fg_color=Config.CARD_BG,
            text_color=Config.TEXT_MUTED[1]
        )
        badge.grid(row=0, column=0, padx=(10, 8), pady=8)

        # Title & Meta info
        title_box = ctk.CTkFrame(row_frame, fg_color="transparent")
        title_box.grid(row=0, column=1, sticky="w", padx=(0, 10))

        disp_title = item.title if len(item.title) <= 45 else item.title[:42] + "..."
        title_lbl = ctk.CTkLabel(
            title_box,
            text=f"#{idx+1}  {disp_title}",
            font=("Segoe UI", 11, "bold"),
            text_color=Config.TEXT_MAIN,
            anchor="w"
        )
        title_lbl.pack(anchor="w")

        info_sub = f"{item.format_type} • {item.quality_setting} • {item.url[:40]}..."
        sub_lbl = ctk.CTkLabel(
            title_box,
            text=info_sub,
            font=("Segoe UI", 9),
            text_color=Config.TEXT_MUTED,
            anchor="w"
        )
        sub_lbl.pack(anchor="w")

        # Progress bar & metrics
        prog_box = ctk.CTkFrame(row_frame, fg_color="transparent")
        prog_box.grid(row=0, column=2, padx=(0, 10))

        pbar = ctk.CTkProgressBar(
            prog_box,
            width=110,
            height=8,
            corner_radius=4,
            fg_color=Config.INPUT_BG,
            progress_color=Config.BTN_PRIMARY_BG
        )
        pbar.set(item.progress)
        pbar.pack(pady=(2, 2))

        metrics_lbl = ctk.CTkLabel(
            prog_box,
            text="",
            font=("Consolas", 9),
            text_color=Config.TEXT_MUTED
        )
        metrics_lbl.pack()

        # Delete button
        del_btn = ctk.CTkButton(
            row_frame,
            text="✕",
            width=28,
            height=28,
            corner_radius=5,
            font=("Segoe UI", 10, "bold"),
            fg_color=Config.DANGER_BG,
            hover_color=Config.DANGER_HOVER,
            text_color=Config.DANGER_COLOR,
            command=lambda iid=item.id: self._remove_queue_item(iid)
        )
        del_btn.grid(row=0, column=3, padx=(0, 10))

        self._queue_widget_rows[item.id] = {
            "row_frame": row_frame,
            "badge": badge,
            "title_lbl": title_lbl,
            "pbar": pbar,
            "metrics_lbl": metrics_lbl
        }

    def _remove_queue_item(self, item_id: str):
        self.queue_manager.remove_item(item_id)
        self._render_batch_queue_list()

    def _update_queue_summary_labels(self):
        s = self.queue_manager.get_summary()
        txt = f"Total: {s['total']}  •  ⏳ Pending: {s['pending']}  •  ⬇ Aktif: {s['downloading']}  •  ✅ Selesai: {s['completed']}  •  ❌ Gagal: {s['failed']}"
        self.batch_summary_lbl.configure(text=txt)

    def _on_queue_item_updated(self, item: QueueItem):
        self.after(0, lambda: self._apply_queue_item_update(item))

    def _apply_queue_item_update(self, item: QueueItem):
        widgets = self._queue_widget_rows.get(item.id)
        if not widgets:
            self._render_batch_queue_list()
            return

        badge = widgets.get("badge")
        if badge:
            badge.configure(text=item.status)
            if "Selesai" in item.status:
                badge.configure(fg_color=Config.SUCCESS_BG, text_color=Config.SUCCESS_COLOR)
            elif "Gagal" in item.status:
                badge.configure(fg_color=Config.DANGER_BG, text_color=Config.DANGER_COLOR)
            elif "Dibatalkan" in item.status:
                badge.configure(fg_color=Config.CARD_BG, text_color=Config.TEXT_MUTED[1])
            elif "Mengunduh" in item.status:
                badge.configure(fg_color=Config.CARD_BG, text_color=Config.BTN_PRIMARY_BG[1])

        pbar = widgets.get("pbar")
        if pbar:
            pbar.set(item.progress)

        metrics_lbl = widgets.get("metrics_lbl")
        if metrics_lbl:
            if item.speed or item.eta:
                metrics_lbl.configure(text=f"{int(item.progress*100)}% • {item.speed} • ETA {item.eta}")
            elif "Selesai" in item.status:
                metrics_lbl.configure(text="100% Selesai")
            elif "Gagal" in item.status:
                metrics_lbl.configure(text=item.error_msg[:25] if item.error_msg else "Error")
            else:
                metrics_lbl.configure(text="")

        self._update_queue_summary_labels()

    def _on_queue_finished(self):
        self.after(0, self._handle_queue_finished)

    def _handle_queue_finished(self):
        self.batch_start_btn.configure(state="normal")
        self.batch_stop_btn.configure(state="disabled")
        self._update_queue_summary_labels()
        self.log_area.write_log("[BatchQueue] Seluruh proses antrean unduhan selesai.")

    def _open_playlist_selector(self):
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showwarning("Perhatian", "Masukkan tautan playlist YouTube terlebih dahulu pada kolom URL.")
            return

        def _fetch_task():
            self.log_area.write_log(f"[Playlist] Menganalisis daftar isi playlist: {url}...")
            p_info = self.downloader.fetch_playlist_tracks(url)
            if not p_info or not p_info.get("entries"):
                self.after(0, lambda: messagebox.showerror("Error", "Gagal memuat isi playlist atau playlist kosong / bersifat privat."))
                return

            def _show_modal():
                def _handle_selected(selected_tracks):
                    if not selected_tracks:
                        return
                    urls = [t['url'] for t in selected_tracks]
                    self.queue_manager.add_urls(
                        urls=urls,
                        format_type=self.format_var.get(),
                        quality_setting=self.quality_dropdown.get(),
                        embed_meta=bool(self.meta_cb.get()),
                        embed_thumb=bool(self.thumb_cb.get())
                    )
                    self._switch_tab("batch")
                    self._render_batch_queue_list()
                    self.log_area.write_log(f"[Playlist] {len(urls)} trek dari playlist berhasil dimasukkan ke Batch Queue!")

                PlaylistSelectorModal(self, p_info, _handle_selected)

            self.after(0, _show_modal)

        threading.Thread(target=_fetch_task, daemon=True).start()

    # =========================================================================
    # VIEW 3: RIWAYAT & ARSIP UNDUHAN (INTEGRASI PENUH)
    # =========================================================================
    def _init_history_view(self):
        self.view_history = ctk.CTkFrame(self.workspace, fg_color="transparent")
        self.view_history.grid_columnconfigure(0, weight=1)
        self.view_history.grid_rowconfigure(2, weight=1)
        
        header_card = CardFrame(self.view_history)
        header_card.grid(row=0, column=0, pady=(0, 10), sticky="ew")
        header_card.grid_columnconfigure(0, weight=1)
        
        h_row = ctk.CTkFrame(header_card, fg_color="transparent")
        h_row.grid(row=0, column=0, padx=16, pady=12, sticky="ew")
        h_row.grid_columnconfigure(0, weight=1)
        
        title_box = ctk.CTkFrame(h_row, fg_color="transparent")
        title_box.grid(row=0, column=0, sticky="w")
        
        title = ctk.CTkLabel(title_box, text="Riwayat Arsip Unduhan", font=("Segoe UI", 15, "bold"), text_color=Config.TEXT_MAIN)
        title.pack(side="left", padx=(0, 10))
        
        self.hist_count_badge = ctk.CTkLabel(title_box, text="Total: 0 item", font=("Segoe UI", 11), text_color=Config.TEXT_MUTED)
        self.hist_count_badge.pack(side="left")
        
        act_box = ctk.CTkFrame(h_row, fg_color="transparent")
        act_box.grid(row=0, column=1, sticky="e")
        
        refresh_btn = ctk.CTkButton(
            act_box, text="Refresh", width=75, height=30, corner_radius=6,
            font=("Segoe UI", 10, "bold"), fg_color=Config.SECONDARY_BTN, hover_color=Config.SECONDARY_HOVER,
            text_color=Config.SECONDARY_TEXT, command=self._load_history_entries
        )
        refresh_btn.pack(side="left", padx=(0, 6))
        
        export_btn = ctk.CTkButton(
            act_box, text="Ekspor .txt", width=85, height=30, corner_radius=6,
            font=("Segoe UI", 10, "bold"), fg_color=Config.SECONDARY_BTN, hover_color=Config.SECONDARY_HOVER,
            text_color=Config.SECONDARY_TEXT, command=self._export_history
        )
        export_btn.pack(side="left", padx=(0, 6))
        
        clear_btn = ctk.CTkButton(
            act_box, text="Bersihkan Arsip", width=110, height=30, corner_radius=6,
            font=("Segoe UI", 10, "bold"), fg_color=Config.DANGER_BG, border_width=1, border_color=Config.DANGER_BORDER,
            text_color=Config.DANGER_COLOR, hover_color=Config.DANGER_HOVER, command=self._clear_history_all
        )
        clear_btn.pack(side="left")
        
        # Search Bar
        search_card = CardFrame(self.view_history)
        search_card.grid(row=1, column=0, pady=(0, 10), sticky="ew")
        search_card.grid_columnconfigure(0, weight=1)
        
        self.hist_search_entry = ctk.CTkEntry(
            search_card,
            placeholder_text="Cari berdasarkan ID video atau platform...",
            font=("Segoe UI", 11),
            height=34,
            corner_radius=7,
            fg_color=Config.INPUT_BG,
            border_color=Config.INPUT_BORDER,
            text_color=Config.TEXT_MAIN
        )
        self.hist_search_entry.pack(fill="x", padx=14, pady=10)
        self.hist_search_entry.bind("<KeyRelease>", lambda e: self._filter_history_entries())
        
        # Scrollable List
        self.hist_scroll = ctk.CTkScrollableFrame(
            self.view_history,
            fg_color=Config.CARD_BG,
            corner_radius=10,
            border_width=1,
            border_color=Config.CARD_BORDER
        )
        self.hist_scroll.grid(row=2, column=0, sticky="nsew")
        self.hist_scroll.grid_columnconfigure(0, weight=1)

    def _load_history_entries(self):
        for widget in self.hist_scroll.winfo_children():
            widget.destroy()
            
        entries = ArchiveManager.get_entries()
        self._all_history_entries = entries
        self.hist_count_badge.configure(text=f"Total: {len(entries)} item")
        
        if not entries:
            empty_lbl = ctk.CTkLabel(
                self.hist_scroll,
                text="Belum ada riwayat unduhan di dalam arsip.\nItem yang telah selesai diunduh akan tercatat di sini secara otomatis.",
                font=("Segoe UI", 11),
                text_color=Config.TEXT_MUTED
            )
            empty_lbl.pack(pady=40)
            return

        self._render_history_items(entries)

    def _filter_history_entries(self):
        query = self.hist_search_entry.get().strip().lower()
        if not hasattr(self, "_all_history_entries"):
            return
            
        if not query:
            filtered = self._all_history_entries
        else:
            filtered = [
                e for e in self._all_history_entries
                if query in e.get("id", "").lower() or query in e.get("extractor", "").lower()
            ]
        self._render_history_items(filtered)

    def _render_history_items(self, entries):
        for widget in self.hist_scroll.winfo_children():
            widget.destroy()
            
        for i, item in enumerate(entries):
            row_frame = ctk.CTkFrame(
                self.hist_scroll,
                fg_color=Config.CARD_BG_ELEVATED,
                corner_radius=7,
                height=38
            )
            row_frame.pack(fill="x", padx=8, pady=3)
            row_frame.grid_columnconfigure(1, weight=1)
            
            icon_lbl = ctk.CTkLabel(row_frame, text="🎬", font=("Segoe UI Emoji", 11))
            icon_lbl.grid(row=0, column=0, padx=(10, 6), pady=6)
            
            id_text = f"[{item.get('extractor', 'youtube').upper()}]  {item.get('id', '')}"
            id_lbl = ctk.CTkLabel(row_frame, text=id_text, font=("Consolas", 10), text_color=Config.TEXT_MAIN, anchor="w")
            id_lbl.grid(row=0, column=1, sticky="w", pady=6)
            
            btn_box = ctk.CTkFrame(row_frame, fg_color="transparent")
            btn_box.grid(row=0, column=2, padx=8, sticky="e")
            
            open_btn = ctk.CTkButton(
                btn_box, text="Buka", width=50, height=24, font=("Segoe UI", 10),
                corner_radius=5, fg_color=Config.SECONDARY_BTN, hover_color=Config.SECONDARY_HOVER,
                text_color=Config.SECONDARY_TEXT, command=lambda vid=item.get("id"): self._open_youtube_link(vid)
            )
            open_btn.pack(side="left", padx=(0, 6))
            
            del_btn = ctk.CTkButton(
                btn_box, text="✕", width=30, height=24, font=("Segoe UI", 10),
                corner_radius=5, fg_color=Config.DANGER_BG, hover_color=Config.DANGER_HOVER,
                text_color=Config.DANGER_COLOR, command=lambda eid=item.get("id"): self._delete_history_item(eid)
            )
            del_btn.pack(side="left")

    def _open_youtube_link(self, video_id: str):
        if video_id:
            url = f"https://www.youtube.com/watch?v={video_id}"
            webbrowser.open(url)

    def _delete_history_item(self, entry_id: str):
        if ArchiveManager.remove_entry(entry_id):
            self._load_history_entries()
            self.log_area.write_log(f"[Arsip] ID '{entry_id}' dihapus.")

    def _clear_history_all(self):
        confirm = messagebox.askyesno(
            "Konfirmasi Hapus Arsip",
            "Apakah Anda yakin ingin mengosongkan seluruh riwayat arsip?\n(File yang sudah terunduh di komputer tetap aman)."
        )
        if confirm:
            ArchiveManager.clear_archive()
            self._load_history_entries()
            self.log_area.write_log("[Arsip] Seluruh riwayat arsip telah dikosongkan.")

    def _export_history(self):
        dest = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text File", "*.txt")],
            initialfile="download_archive_backup.txt"
        )
        if dest:
            if ArchiveManager.export_archive(dest):
                messagebox.showinfo("Sukses", f"Arsip berhasil diekspor ke:\n{dest}")

    # =========================================================================
    # VIEW 4: PENGATURAN & VERSI APLIKASI (INFORMASI VERSI DI SINI)
    # =========================================================================
    def _init_settings_view(self):
        self.view_settings = ctk.CTkScrollableFrame(self.workspace, fg_color="transparent")
        self.view_settings.grid_columnconfigure(0, weight=1)
        
        # ---------------------------------------------------------------------
        # KARTU 1: INFORMASI & VERSI APLIKASI (DIPINDAHKAN DARI HEADER)
        # ---------------------------------------------------------------------
        card_about = CardFrame(self.view_settings)
        card_about.grid(row=0, column=0, pady=(0, 12), sticky="ew")
        card_about.grid_columnconfigure(0, weight=1)
        
        about_header = ctk.CTkFrame(card_about, fg_color="transparent")
        about_header.grid(row=0, column=0, padx=16, pady=(16, 6), sticky="ew")
        
        app_logo = ctk.CTkLabel(about_header, text="📥", font=("Segoe UI Emoji", 24))
        app_logo.pack(side="left", padx=(0, 10))
        
        app_name = ctk.CTkLabel(about_header, text=Config.APP_TITLE, font=("Segoe UI", 16, "bold"), text_color=Config.TEXT_MAIN)
        app_name.pack(side="left", padx=(0, 10))
        
        # Version Badge Resmi Aplikasi
        ver_badge = ctk.CTkFrame(about_header, fg_color=Config.CARD_BG_ELEVATED, corner_radius=6, border_width=1, border_color=Config.CARD_BORDER)
        ver_badge.pack(side="left")
        ver_lbl = ctk.CTkLabel(ver_badge, text=Config.VERSION, font=("Segoe UI", 10, "bold"), text_color=Config.TEXT_MAIN)
        ver_lbl.pack(padx=8, pady=2)
        
        app_desc = ctk.CTkLabel(
            card_about,
            text="Universal Audio & Video Media Studio with Auto Metadata & FFmpeg Processing.\nDibangun secara native dan ringan untuk performa unduhan audio & video berkualitas tinggi.",
            font=("Segoe UI", 11),
            text_color=Config.TEXT_MUTED,
            justify="left"
        )
        app_desc.grid(row=1, column=0, padx=16, pady=(0, 16), sticky="w")
        
        # ---------------------------------------------------------------------
        # KARTU 2: TAMPILAN & MODE TEMA (DARK / LIGHT MODE)
        # ---------------------------------------------------------------------
        card_theme = CardFrame(self.view_settings)
        card_theme.grid(row=1, column=0, pady=(0, 12), sticky="ew")
        card_theme.grid_columnconfigure(0, weight=1)
        
        theme_title = ctk.CTkLabel(card_theme, text="TAMPILAN TEMA (APPEARANCE)", font=("Segoe UI", 11, "bold"), text_color=Config.TEXT_MAIN)
        theme_title.grid(row=0, column=0, padx=16, pady=(14, 6), sticky="w")
        
        theme_row = ctk.CTkFrame(card_theme, fg_color="transparent")
        theme_row.grid(row=1, column=0, padx=16, pady=(0, 16), sticky="w")
        
        self.theme_mode_var = ctk.StringVar(value="Dark" if self.current_theme.lower() == "dark" else "Light")
        
        self.theme_dark_radio = ctk.CTkRadioButton(
            theme_row,
            text="🌙 Dark Mode",
            variable=self.theme_mode_var,
            value="Dark",
            font=("Segoe UI", 11, "bold"),
            text_color=Config.TEXT_MAIN,
            fg_color=Config.BTN_PRIMARY_BG,
            hover_color=Config.BTN_PRIMARY_HOVER,
            command=self._on_theme_radio_changed
        )
        self.theme_dark_radio.pack(side="left", padx=(0, 24))
        
        self.theme_light_radio = ctk.CTkRadioButton(
            theme_row,
            text="☀️ Light Mode",
            variable=self.theme_mode_var,
            value="Light",
            font=("Segoe UI", 11, "bold"),
            text_color=Config.TEXT_MAIN,
            fg_color=Config.BTN_PRIMARY_BG,
            hover_color=Config.BTN_PRIMARY_HOVER,
            command=self._on_theme_radio_changed
        )
        self.theme_light_radio.pack(side="left")

        # ---------------------------------------------------------------------
        # KARTU 3: LOKASI UNDUHAN & FORMAT NAMA FILE
        # ---------------------------------------------------------------------
        card_storage = CardFrame(self.view_settings)
        card_storage.grid(row=2, column=0, pady=(0, 12), sticky="ew")
        card_storage.grid_columnconfigure(0, weight=1)
        
        c_title = ctk.CTkLabel(card_storage, text="LOKASI UNDUHAN & FORMAT NAMA FILE", font=("Segoe UI", 11, "bold"), text_color=Config.TEXT_MAIN)
        c_title.grid(row=0, column=0, padx=16, pady=(14, 8), sticky="w")
        
        f_lbl = ctk.CTkLabel(card_storage, text="Folder Unduhan Default Permanen:", font=("Segoe UI", 11), text_color=Config.TEXT_MUTED)
        f_lbl.grid(row=1, column=0, padx=16, pady=(0, 4), sticky="w")
        
        f_row = ctk.CTkFrame(card_storage, fg_color="transparent")
        f_row.grid(row=2, column=0, padx=16, pady=(0, 12), sticky="ew")
        f_row.grid_columnconfigure(0, weight=1)
        
        self.sett_folder_entry = ctk.CTkEntry(
            f_row, font=("Segoe UI", 11), height=34, corner_radius=7,
            fg_color=Config.INPUT_BG, border_color=Config.INPUT_BORDER, text_color=Config.TEXT_MAIN
        )
        self.sett_folder_entry.grid(row=0, column=0, padx=(0, 8), sticky="ew")
        self.sett_folder_entry.insert(0, self.settings.get("download_dir", Config.DEFAULT_DOWNLOAD_DIR))
        
        sett_browse_btn = ctk.CTkButton(
            f_row, text="Browse", width=90, height=34, corner_radius=7, font=("Segoe UI", 11, "bold"),
            fg_color=Config.SECONDARY_BTN, hover_color=Config.SECONDARY_HOVER, text_color=Config.SECONDARY_TEXT,
            command=self._settings_browse_folder
        )
        sett_browse_btn.grid(row=0, column=1, sticky="e")
        
        # Naming Presets
        t_lbl = ctk.CTkLabel(card_storage, text="Format Penamaan File Otomatis:", font=("Segoe UI", 11), text_color=Config.TEXT_MUTED)
        t_lbl.grid(row=3, column=0, padx=16, pady=(0, 4), sticky="w")
        
        self.naming_labels = [p[1] for p in NAMING_PRESETS]
        self.naming_dict = {p[1]: p[0] for p in NAMING_PRESETS}
        self.naming_rev_dict = {p[0]: p[1] for p in NAMING_PRESETS}
        
        current_tpl = self.settings.get("naming_template", "{title}")
        default_label = self.naming_rev_dict.get(current_tpl, self.naming_labels[0])
        
        self.naming_combo = ctk.CTkComboBox(
            card_storage,
            values=self.naming_labels,
            font=("Segoe UI", 11),
            dropdown_font=("Segoe UI", 11),
            height=34,
            corner_radius=7,
            fg_color=Config.INPUT_BG,
            border_color=Config.INPUT_BORDER,
            button_color=Config.SECONDARY_BTN,
            button_hover_color=Config.SECONDARY_HOVER,
            text_color=Config.TEXT_MAIN
        )
        self.naming_combo.set(default_label)
        self.naming_combo.grid(row=4, column=0, padx=16, pady=(0, 16), sticky="ew")

        # ---------------------------------------------------------------------
        # KARTU 4: YT-DLP CORE UPDATER
        # ---------------------------------------------------------------------
        card_upd = CardFrame(self.view_settings)
        card_upd.grid(row=3, column=0, pady=(0, 12), sticky="ew")
        card_upd.grid_columnconfigure(0, weight=1)
        
        upd_title = ctk.CTkLabel(card_upd, text="ENGINE YT-DLP CORE UPDATER", font=("Segoe UI", 11, "bold"), text_color=Config.TEXT_MAIN)
        upd_title.grid(row=0, column=0, padx=16, pady=(14, 8), sticky="w")
        
        upd_row = ctk.CTkFrame(card_upd, fg_color="transparent")
        upd_row.grid(row=1, column=0, padx=16, pady=(0, 14), sticky="ew")
        upd_row.grid_columnconfigure(0, weight=1)
        
        curr_ytdlp = YtdlpUpdater.get_current_version()
        self.ytdlp_ver_lbl = ctk.CTkLabel(
            upd_row,
            text=f"Versi yt-dlp saat ini: {curr_ytdlp}",
            font=("Segoe UI", 11, "bold"),
            text_color=Config.TEXT_MAIN
        )
        self.ytdlp_ver_lbl.grid(row=0, column=0, sticky="w")
        
        self.check_upd_btn = ctk.CTkButton(
            upd_row, text="Cek Update Terbaru", font=("Segoe UI", 11, "bold"),
            width=150, height=32, corner_radius=7, fg_color=Config.SECONDARY_BTN, hover_color=Config.SECONDARY_HOVER,
            text_color=Config.SECONDARY_TEXT, command=self._check_ytdlp_update
        )
        self.check_upd_btn.grid(row=0, column=1, sticky="e")
        
        self.ytdlp_status_lbl = ctk.CTkLabel(card_upd, text="", font=("Segoe UI", 11), text_color=Config.TEXT_MUTED)
        self.ytdlp_status_lbl.grid(row=2, column=0, padx=16, pady=(0, 12), sticky="w")
        
        # ---------------------------------------------------------------------
        # KARTU 4.5: AKSELERASI & ENGINE AUDIO (v1.5)
        # ---------------------------------------------------------------------
        card_audio_eng = CardFrame(self.view_settings)
        card_audio_eng.grid(row=4, column=0, pady=(0, 12), sticky="ew")
        card_audio_eng.grid_columnconfigure(0, weight=1)

        eng_title = ctk.CTkLabel(card_audio_eng, text="PENGATURAN ENGINE & AKSELERASI UNDUHAN", font=("Segoe UI", 11, "bold"), text_color=Config.TEXT_MAIN)
        eng_title.grid(row=0, column=0, padx=16, pady=(14, 8), sticky="w")

        self.sett_norm_cb = ctk.CTkCheckBox(
            card_audio_eng,
            text="Aktifkan Penyeragaman Volume Suara Otomatis (EBU R128 loudnorm)",
            font=("Segoe UI", 11, "bold"),
            text_color=Config.TEXT_MAIN,
            fg_color=Config.BTN_PRIMARY_BG,
            hover_color=Config.BTN_PRIMARY_HOVER,
            checkmark_color=Config.BTN_PRIMARY_TEXT,
            corner_radius=5
        )
        if self.settings.get("normalize_audio", False):
            self.sett_norm_cb.select()
        self.sett_norm_cb.grid(row=1, column=0, padx=16, pady=(0, 4), sticky="w")

        norm_desc = ctk.CTkLabel(
            card_audio_eng,
            text="Menyeimbangkan kenyaringan suara antar musik secara otomatis menggunakan filter audio FFmpeg standar penyiaran agar tidak ada lagu yang terlalu pelan atau keras.",
            font=("Segoe UI", 10),
            text_color=Config.TEXT_MUTED,
            justify="left"
        )
        norm_desc.grid(row=2, column=0, padx=16, pady=(0, 10), sticky="w")

        self.sett_turbo_cb = ctk.CTkCheckBox(
            card_audio_eng,
            text="Turbo Speed",
            font=("Segoe UI", 11, "bold"),
            text_color=Config.TEXT_MAIN,
            fg_color=Config.BTN_PRIMARY_BG,
            hover_color=Config.BTN_PRIMARY_HOVER,
            checkmark_color=Config.BTN_PRIMARY_TEXT,
            corner_radius=5
        )
        if self.settings.get("turbo_speed", True):
            self.sett_turbo_cb.select()
        self.sett_turbo_cb.grid(row=3, column=0, padx=16, pady=(0, 4), sticky="w")

        turbo_desc = ctk.CTkLabel(
            card_audio_eng,
            text="Mengunduh potongan media secara paralel dengan 4 koneksi simultan untuk memaksimalkan pemanfaatan bandwidth internet.",
            font=("Segoe UI", 10),
            text_color=Config.TEXT_MUTED,
            justify="left"
        )
        turbo_desc.grid(row=4, column=0, padx=16, pady=(0, 14), sticky="w")

        # ---------------------------------------------------------------------
        # KARTU 5: INTEGRASI SISTEM & WORKFLOW OTOMASI (v1.6)
        # ---------------------------------------------------------------------
        card_sys = CardFrame(self.view_settings)
        card_sys.grid(row=5, column=0, pady=(0, 12), sticky="ew")
        card_sys.grid_columnconfigure(0, weight=1)

        sys_title = ctk.CTkLabel(card_sys, text="INTEGRASI SISTEM & WORKFLOW OTOMASI", font=("Segoe UI", 11, "bold"), text_color=Config.TEXT_MAIN)
        sys_title.grid(row=0, column=0, padx=16, pady=(14, 8), sticky="w")

        self.sett_tray_cb = ctk.CTkCheckBox(
            card_sys,
            text="Minimize ke System Tray saat Ditutup (Background Running)",
            font=("Segoe UI", 11, "bold"),
            text_color=Config.TEXT_MAIN,
            fg_color=Config.BTN_PRIMARY_BG,
            hover_color=Config.BTN_PRIMARY_HOVER,
            checkmark_color=Config.BTN_PRIMARY_TEXT,
            corner_radius=5
        )
        if self.settings.get("minimize_to_tray", False):
            self.sett_tray_cb.select()
        self.sett_tray_cb.grid(row=1, column=0, padx=16, pady=(0, 4), sticky="w")

        tray_desc = ctk.CTkLabel(
            card_sys,
            text="Menyembunyikan jendela ke tray area notifikasi Windows saat ditutup agar antrean unduhan tetap aktif berjalan di latar belakang.",
            font=("Segoe UI", 10),
            text_color=Config.TEXT_MUTED,
            justify="left"
        )
        tray_desc.grid(row=2, column=0, padx=16, pady=(0, 10), sticky="w")

        self.sett_clip_cb = ctk.CTkCheckBox(
            card_sys,
            text="Monitor Clipboard Otomatis (Auto-Detect Media Link)",
            font=("Segoe UI", 11, "bold"),
            text_color=Config.TEXT_MAIN,
            fg_color=Config.BTN_PRIMARY_BG,
            hover_color=Config.BTN_PRIMARY_HOVER,
            checkmark_color=Config.BTN_PRIMARY_TEXT,
            corner_radius=5
        )
        if self.settings.get("auto_clipboard_monitor", True):
            self.sett_clip_cb.select()
        self.sett_clip_cb.grid(row=3, column=0, padx=16, pady=(0, 4), sticky="w")

        clip_desc = ctk.CTkLabel(
            card_sys,
            text="Mendeteksi secara proaktif tautan media dari YouTube, TikTok, Spotify, Instagram, dll yang disalin di Windows dan memuat preview secara otomatis.",
            font=("Segoe UI", 10),
            text_color=Config.TEXT_MUTED,
            justify="left"
        )
        clip_desc.grid(row=4, column=0, padx=16, pady=(0, 10), sticky="w")

        self.sett_auto_fmt_cb = ctk.CTkCheckBox(
            card_sys,
            text="Adaptasi Format Otomatis Sesuai Platform",
            font=("Segoe UI", 11, "bold"),
            text_color=Config.TEXT_MAIN,
            fg_color=Config.BTN_PRIMARY_BG,
            hover_color=Config.BTN_PRIMARY_HOVER,
            checkmark_color=Config.BTN_PRIMARY_TEXT,
            corner_radius=5
        )
        if self.settings.get("auto_switch_format", True):
            self.sett_auto_fmt_cb.select()
        self.sett_auto_fmt_cb.grid(row=5, column=0, padx=16, pady=(0, 4), sticky="w")

        fmt_desc = ctk.CTkLabel(
            card_sys,
            text="Beralih otomatis ke format MP3 untuk platform musik (SoundCloud, Bandcamp, Spotify) dan format MP4 untuk video sosial (TikTok, Instagram, Twitter/X).",
            font=("Segoe UI", 10),
            text_color=Config.TEXT_MUTED,
            justify="left"
        )
        fmt_desc.grid(row=6, column=0, padx=16, pady=(0, 14), sticky="w")

        # ---------------------------------------------------------------------
        # TOMBOL SIMPAN PENGATURAN
        # ---------------------------------------------------------------------
        save_card = CardFrame(self.view_settings)
        save_card.grid(row=6, column=0, pady=(0, 16), sticky="ew")
        save_card.grid_columnconfigure(0, weight=1)
        
        save_box = ctk.CTkFrame(save_card, fg_color="transparent")
        save_box.pack(fill="x", padx=16, pady=12)
        
        save_btn = ctk.CTkButton(
            save_box, text="Simpan Pengaturan", font=("Segoe UI", 12, "bold"),
            width=160, height=36, corner_radius=7, fg_color=Config.BTN_PRIMARY_BG, hover_color=Config.BTN_PRIMARY_HOVER,
            text_color=Config.BTN_PRIMARY_TEXT, command=self._save_settings_action
        )
        save_btn.pack(side="left", padx=(0, 12))
        
        self.settings_save_lbl = ctk.CTkLabel(save_box, text="", font=("Segoe UI", 11, "bold"), text_color=Config.SUCCESS_COLOR)
        self.settings_save_lbl.pack(side="left")

    def _on_theme_radio_changed(self):
        choice = self.theme_mode_var.get().lower()
        if choice != self.current_theme.lower():
            self._toggle_theme_mode()

    def _settings_browse_folder(self):
        selected = filedialog.askdirectory(initialdir=self.sett_folder_entry.get())
        if selected:
            self.sett_folder_entry.delete(0, "end")
            self.sett_folder_entry.insert(0, selected)

    def _save_settings_action(self):
        new_dir = self.sett_folder_entry.get().strip()
        chosen_label = self.naming_combo.get()
        new_tpl = self.naming_dict.get(chosen_label, "{title}")
        norm_val = bool(self.sett_norm_cb.get())
        turbo_val = bool(self.sett_turbo_cb.get())
        tray_val = bool(self.sett_tray_cb.get())
        clip_val = bool(self.sett_clip_cb.get())
        auto_fmt_val = bool(self.sett_auto_fmt_cb.get())
        
        self.settings["download_dir"] = new_dir
        self.settings["naming_template"] = new_tpl
        self.settings["appearance_mode"] = self.current_theme
        self.settings["normalize_audio"] = norm_val
        self.settings["turbo_speed"] = turbo_val
        self.settings["minimize_to_tray"] = tray_val
        self.settings["auto_clipboard_monitor"] = clip_val
        self.settings["auto_switch_format"] = auto_fmt_val
        
        SettingsManager.save(self.settings)
        
        # Sync folder entry & toggle normalisasi di halaman Downloader
        self.path_entry.delete(0, "end")
        self.path_entry.insert(0, new_dir)
        if hasattr(self, "norm_cb"):
            if norm_val:
                self.norm_cb.select()
            else:
                self.norm_cb.deselect()
        
        self.settings_save_lbl.configure(text="✓ Pengaturan berhasil disimpan secara permanen!")
        self.log_area.write_log(f"[Settings] Pengaturan disimpan. Template: '{new_tpl}', Folder: {new_dir}, Normalisasi: {norm_val}, Tray: {tray_val}")

    def _check_ytdlp_update(self):
        self.ytdlp_status_lbl.configure(text="Memeriksa versi terbaru dari PyPI...")
        threading.Thread(target=self._run_check_update_thread, daemon=True).start()

    def _run_check_update_thread(self):
        curr, latest, has_upd, err = YtdlpUpdater.check_latest_version()
        if err:
            self.ytdlp_status_lbl.configure(text=f"Gagal memeriksa update: {err}", text_color=Config.DANGER_COLOR)
            return
            
        if has_upd:
            self.ytdlp_status_lbl.configure(
                text=f"Versi baru tersedia! (Terpasang: {curr} ➔ Terbaru: {latest})",
                text_color=Config.TEXT_MAIN
            )
            self.check_upd_btn.configure(
                text="Perbarui yt-dlp",
                fg_color=Config.BTN_PRIMARY_BG,
                hover_color=Config.BTN_PRIMARY_HOVER,
                text_color=Config.BTN_PRIMARY_TEXT,
                command=self._execute_ytdlp_update
            )
        else:
            self.ytdlp_status_lbl.configure(
                text=f"yt-dlp sudah versi paling mutakhir ({curr}).",
                text_color=Config.SUCCESS_COLOR
            )

    def _execute_ytdlp_update(self):
        self.check_upd_btn.configure(state="disabled", text="Memperbarui...")
        self.ytdlp_status_lbl.configure(text="Mengunduh dan memperbarui modul engine yt-dlp...")
        threading.Thread(target=self._run_execute_update_thread, daemon=True).start()

    def _run_execute_update_thread(self):
        success, msg = YtdlpUpdater.run_update(log_callback=self.log_area.write_log)
        self.check_upd_btn.configure(
            state="normal", text="Cek Update Terbaru", fg_color=Config.SECONDARY_BTN,
            hover_color=Config.SECONDARY_HOVER, text_color=Config.SECONDARY_TEXT, command=self._check_ytdlp_update
        )
        if success:
            curr_ver = YtdlpUpdater.get_current_version()
            self.ytdlp_ver_lbl.configure(text=f"Versi yt-dlp saat ini: {curr_ver}")
            self.ytdlp_status_lbl.configure(text="✓ Pembaruan berhasil diselesaikan!", text_color=Config.SUCCESS_COLOR)
        else:
            self.ytdlp_status_lbl.configure(text=f"Gagal memperbarui: {msg}", text_color=Config.DANGER_COLOR)

    # =========================================================================
    # NAVIGASI & TAB SWITCHER (DOCK CAPSULE TRACK)
    # =========================================================================
    def _switch_tab(self, tab_id: str):
        self._active_tab = tab_id
        
        # Sembunyikan semua views
        self.view_downloader.grid_forget()
        self.view_batch.grid_forget()
        self.view_history.grid_forget()
        self.view_settings.grid_forget()
        
        # Update visual segmented button
        for tid, btn in self.tab_buttons.items():
            if tid == tab_id:
                btn.configure(
                    fg_color=Config.NAV_TAB_ACTIVE_BG,
                    text_color=Config.NAV_TAB_ACTIVE_TEXT,
                    border_width=1,
                    border_color=Config.NAV_TAB_ACTIVE_BORDER
                )
            else:
                btn.configure(
                    fg_color="transparent",
                    text_color=Config.NAV_TAB_INACTIVE_TEXT,
                    border_width=0
                )
                
        # Tampilkan view aktif
        if tab_id == "downloader":
            self.view_downloader.grid(row=0, column=0, sticky="nsew")
        elif tab_id == "batch":
            self.view_batch.grid(row=0, column=0, sticky="nsew")
        elif tab_id == "history":
            self.view_history.grid(row=0, column=0, sticky="nsew")
            self._load_history_entries()
        elif tab_id == "settings":
            self.view_settings.grid(row=0, column=0, sticky="nsew")

    # =========================================================================
    # LOGIKA DOWNLOADER WORKSPACE
    # =========================================================================
    def _check_clipboard_sniff(self):
        try:
            cb_text = self.clipboard_get().strip()
            if cb_text and cb_text.startswith(("http://", "https://")) and cb_text != self.url_entry.get().strip():
                if cb_text != self._last_detected_clipboard:
                    self._last_detected_clipboard = cb_text
                    short_url = cb_text if len(cb_text) <= 45 else cb_text[:42] + "..."
                    self.clip_sniff_chip.configure(text=f"📋 Tautan terdeteksi: {short_url} (Klik untuk tempel)")
                    self.clip_sniff_chip.grid(row=0, column=1, sticky="e")
        except Exception:
            pass

    def _paste_from_clipboard(self):
        try:
            clipboard_text = self.clipboard_get().strip()
            if clipboard_text:
                self.url_entry.delete(0, "end")
                self.url_entry.insert(0, clipboard_text)
                self.clip_sniff_chip.grid_forget()
                self._start_preview_thread(force=True)
        except Exception:
            pass

    def _clear_url(self):
        self._current_loaded_url = None
        self._loading_preview_url = None
        self._preview_token = getattr(self, "_preview_token", 0) + 1
        if self._preview_debounce_timer:
            try:
                self.after_cancel(self._preview_debounce_timer)
            except Exception:
                pass
        self.url_entry.delete(0, "end")
        self.info_panel.reset()
        self.progress_hub.reset()
        self.clip_sniff_chip.grid_forget()

    def _on_format_changed(self):
        fmt = self.format_var.get()
        if fmt == "MP3":
            self.quality_dropdown.configure(values=["Best Audio", "320kbps", "256kbps", "192kbps", "128kbps"])
            self.quality_dropdown.set("Best Audio")
            self.meta_cb.configure(text="Suntik ID3 Tags")
            self.thumb_cb.configure(state="normal")
        else:
            self.quality_dropdown.configure(values=[
                "Best (4K/Max)", "2160p (4K UHD)", "1440p (2K QHD)", 
                "1080p (Full HD)", "720p (HD)", "480p (SD)", "360p"
            ])
            self.quality_dropdown.set("1080p (Full HD)")
            self.meta_cb.configure(text="Suntik Video Tags")
            self.thumb_cb.configure(state="disabled")

        if hasattr(self, "info_panel") and hasattr(self.info_panel, "format_label"):
            self.info_panel.format_label.configure(text=f"📦 {fmt} Audio" if fmt == "MP3" else f"📦 {fmt} Video")

    def _on_url_key_release(self, event=None):
        if event and event.keysym in ("Return", "Up", "Down", "Left", "Right", "Control_L", "Control_R", "Shift_L", "Shift_R", "Alt_L", "Alt_R"):
            return
        if self._preview_debounce_timer:
            try:
                self.after_cancel(self._preview_debounce_timer)
            except Exception:
                pass
        self._preview_debounce_timer = self.after(600, lambda: self._start_preview_thread(force=False))

    def _on_url_paste(self, event=None):
        if self._preview_debounce_timer:
            try:
                self.after_cancel(self._preview_debounce_timer)
            except Exception:
                pass
        self.after(80, lambda: self._start_preview_thread(force=True))

    def _start_preview_thread(self, force: bool = False):
        url = self.url_entry.get().strip()
        if not url or not url.startswith(("http://", "https://")):
            return
            
        # Cek apakah URL yang sama sudah pernah dimuat atau sedang dalam proses antrean
        if not force and getattr(self, "_current_loaded_url", None) == url:
            return
        if getattr(self, "_loading_preview_url", None) == url:
            return

        self._loading_preview_url = url
        self._preview_token = getattr(self, "_preview_token", 0) + 1
        current_token = self._preview_token
            
        self.info_panel.set_loading("Menganalisis tautan media...")
        self.progress_hub.set_stage(1)
        self.progress_hub.status_text.configure(text="Status: Mengambil metadata media...")
        
        # Fast-Path: Untuk link YouTube, langsung ekstrak cover HQ dalam <100ms
        yt_match = re.search(r'(?:v=|\/shorts\/|\/embed\/|youtu\.be\/)([a-zA-Z0-9_-]{11})', url)
        if yt_match:
            vid_id = yt_match.group(1)
            threading.Thread(target=self._fast_load_youtube_thumb, args=(vid_id, current_token), daemon=True).start()

        threading.Thread(target=self._load_preview_data, args=(url, current_token), daemon=True).start()

    def _fast_load_youtube_thumb(self, vid_id: str, token: int):
        """Fast-path loader: mengambil thumbnail YouTube langsung dalam <100ms tanpa menunggu yt-dlp."""
        try:
            thumb_url = f"https://i.ytimg.com/vi/{vid_id}/hqdefault.jpg"
            resp = requests.get(thumb_url, timeout=3)
            if resp.status_code == 200 and token == getattr(self, "_preview_token", 0):
                raw_img = Image.open(BytesIO(resp.content))
                img_padded = ImageOps.pad(raw_img, (210, 118), color=(18, 18, 22), method=Image.Resampling.LANCZOS)
                photo = ctk.CTkImage(light_image=img_padded, dark_image=img_padded, size=(210, 118))
                self.after(0, lambda: self._apply_fast_thumbnail(photo, token))
        except Exception:
            pass

    def _apply_fast_thumbnail(self, photo, token: int):
        """Menerapkan thumbnail instan jika proses analisis utama masih berlangsung."""
        if token == getattr(self, "_preview_token", 0) and getattr(self, "_loading_preview_url", None) is not None:
            self.info_panel.thumbnail_label.image = photo
            if hasattr(self.info_panel.thumbnail_label, "_label"):
                self.info_panel.thumbnail_label._label.image = photo
            self.info_panel.thumbnail_label.configure(image=photo, text="")

    def _load_preview_data(self, url: str, token: int):
        try:
            info = self.downloader.fetch_metadata(url)
            # Cek apakah request token masih relevan (hindari balapan thread lama menimpa URL baru)
            if token != getattr(self, "_preview_token", 0):
                return

            if not info:
                self.after(0, lambda tok=token: self._on_preview_failed(tok))
                return

            title = info.get('title', 'Unknown Title')
            channel = info.get('uploader', 'Unknown Channel')
            is_playlist = 'entries' in info and len(info.get('entries', [])) > 1
            
            if is_playlist:
                duration_text = "N/A"
                video_count = f"Playlist ({len(info.get('entries', []))} items)"
            else:
                duration = info.get('duration', 0)
                duration_text = f"{duration // 60}:{duration % 60:02d}" if duration else "--:--"
                video_count = "Single Track"

            max_res = info.get('_max_res', '-')
            platform_info = info.get('_platform_info') or PlatformHelper.detect(url)
            platform_badge = platform_info.get('badge')
            platform_type = platform_info.get('type')

            # Kumpulkan kandidat URL thumbnail dengan fallback bertingkat
            candidate_urls = []
            vid_id = info.get('id')
            extractor = str(info.get('extractor', '')).lower()
            is_yt = 'youtube' in extractor or platform_info.get('id') == 'youtube'
            
            if is_yt and vid_id:
                candidate_urls.append(f"https://i.ytimg.com/vi/{vid_id}/maxresdefault.jpg")
                candidate_urls.append(f"https://i.ytimg.com/vi/{vid_id}/hqdefault.jpg")
                candidate_urls.append(f"https://i.ytimg.com/vi_webp/{vid_id}/maxresdefault.webp")
                candidate_urls.append(f"https://i.ytimg.com/vi_webp/{vid_id}/hqdefault.webp")

            primary_thumb = info.get('thumbnail')
            if primary_thumb and primary_thumb not in candidate_urls:
                candidate_urls.append(primary_thumb)
                if "maxresdefault" in primary_thumb:
                    candidate_urls.append(primary_thumb.replace("maxresdefault", "hqdefault"))

            for t in reversed(info.get('thumbnails', [])):
                u = t.get('url')
                if u and u not in candidate_urls:
                    candidate_urls.append(u)

            raw_img = None
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8'
            }
            for candidate in candidate_urls[:6]:
                try:
                    res = requests.get(candidate, headers=headers, timeout=6)
                    if res.status_code == 200 and len(res.content) > 500:
                        img = Image.open(BytesIO(res.content))
                        img.load()
                        # Pastikan format warna sesuai untuk Tkinter
                        if img.mode in ("RGBA", "LA", "P"):
                            bg = Image.new("RGB", img.size, (18, 18, 22))
                            if img.mode == "P":
                                img = img.convert("RGBA")
                            if "A" in img.mode:
                                bg.paste(img, mask=img.split()[-1])
                            else:
                                bg.paste(img)
                            img = bg
                        elif img.mode != "RGB":
                            img = img.convert("RGB")
                        raw_img = img
                        break
                except Exception as e:
                    print(f"[Cover Fetch Error] {candidate}: {e}")
                    continue

            # Dispatch pembaruan UI dan pembuatan CTkImage ke main thread agar bebas TclError
            self.after(
                0,
                lambda t=title, c=channel, d=duration_text, vc=video_count, img=raw_img, mr=max_res, u=url, pb=platform_badge, pt=platform_type, tok=token:
                    self._apply_preview_ui(t, c, d, vc, img, mr, u, pb, pt, tok)
            )
        except Exception as e:
            print(f"[Preview Error] {e}")
            self.after(0, lambda tok=token: self._on_preview_failed(tok))
        finally:
            if getattr(self, "_loading_preview_url", None) == url:
                self._loading_preview_url = None

    def _apply_preview_ui(self, title, channel, duration_text, video_count, raw_img, max_res, loaded_url, platform_badge=None, platform_type=None, token=None):
        if token is not None and token != getattr(self, "_preview_token", 0):
            return

        self._current_loaded_url = loaded_url
        self._loading_preview_url = None
        ctk_img = None
        if raw_img:
            try:
                # Menjaga rasio aspek alami gambar (letterbox canvas gelap untuk video vertikal TikTok/Reels)
                fitted_img = ImageOps.pad(raw_img, (210, 118), color=(18, 18, 22), method=Image.Resampling.LANCZOS)
                ctk_img = ctk.CTkImage(light_image=fitted_img, dark_image=fitted_img, size=(210, 118))
            except Exception as e:
                print(f"[Thumbnail Fit Error] {e}")
                ctk_img = None

        # Format hint yang ramah untuk chip info
        fmt_hint = "MP3 Audio" if self.format_var.get() == "MP3" else "MP4 Video"
        self.info_panel.set_preview(title, channel, duration_text, video_count, ctk_img, max_res, platform_badge=platform_badge, format_hint=fmt_hint)
        self.progress_hub.status_text.configure(text="Status: Metadata siap.")

        # Adaptasi format otomatis jika diaktifkan di Settings
        if self.settings.get("auto_switch_format", True) and platform_type:
            if platform_type == "audio" and self.format_var.get() != "MP3":
                self.format_var.set("MP3")
                self._on_format_changed()
                self.log_area.write_log(f"[Auto Format] Format dialihkan otomatis ke MP3 ({platform_badge or 'Audio Platform'})")
            elif platform_type == "video" and self.format_var.get() != "MP4":
                self.format_var.set("MP4")
                self._on_format_changed()
                self.log_area.write_log(f"[Auto Format] Format dialihkan otomatis ke MP4 ({platform_badge or 'Video Platform'})")

    def _on_preview_failed(self, token=None):
        if token is not None and token != getattr(self, "_preview_token", 0):
            return
        self._current_loaded_url = None
        self._loading_preview_url = None
        self.info_panel.set_error("Gagal Memuat Metadata")
        self.progress_hub.status_text.configure(text="Status: Gagal mengambil preview.")

    def _start_download_thread(self):
        url = self.url_entry.get().strip()
        output_dir = self.path_entry.get().strip()
        format_type = self.format_var.get()
        quality_setting = self.quality_dropdown.get()
        embed_meta = bool(self.meta_cb.get())   
        embed_thumb = bool(self.thumb_cb.get()) 
        use_archive = bool(self.archive_cb.get())
        normalize_audio = bool(self.norm_cb.get())
        
        if not url:
            self.log_area.write_log("[Error] Silakan masukkan URL terlebih dahulu!")
            self.progress_hub.status_text.configure(text="Status: URL Kosong!")
            return
            
        self.download_btn.configure(state="disabled")
        self.cancel_btn.configure(state="normal")
        self.progress_hub.reset()
        self.progress_hub.set_stage(2)
        self.progress_hub.status_text.configure(text="Status: Menyiapkan download engine...")
        
        threading.Thread(
            target=self._run_download,
            args=(url, output_dir, format_type, quality_setting, embed_meta, embed_thumb, use_archive, normalize_audio),
            daemon=True
        ).start()

    def _run_download(self, url, output_dir, format_type, quality_setting, embed_meta, embed_thumb, use_archive, normalize_audio):
        try:
            self.downloader.download(
                url=url,
                output_dir=output_dir,
                format_type=format_type,
                quality_setting=quality_setting,
                embed_meta=embed_meta,
                embed_thumb=embed_thumb,
                use_archive=use_archive,
                normalize_audio=normalize_audio
            )
            self.progress_hub.mark_completed("Proses unduhan berhasil diselesaikan!")
        except Exception as e:
            self.progress_hub.status_text.configure(text=f"Status: {str(e)}")
        finally:
            self.download_btn.configure(state="normal")
            self.cancel_btn.configure(state="disabled")
            self._current_loaded_url = url

    def _cancel_download(self):
        if self.downloader:
            self.downloader.cancel()
            self.progress_hub.status_text.configure(text="Status: Membatalkan unduhan...")

    def _browse_folder(self):
        selected_dir = filedialog.askdirectory(initialdir=self.path_entry.get())
        if selected_dir:
            self.path_entry.delete(0, "end")
            self.path_entry.insert(0, selected_dir)

    def _open_download_folder(self):
        folder_path = self.path_entry.get().strip()
        if not os.path.exists(folder_path):
            try:
                os.makedirs(folder_path, exist_ok=True)
            except Exception:
                pass
        if os.path.exists(folder_path):
            os.startfile(folder_path)
        else:
            self.log_area.write_log("[Error] Folder tujuan tidak dapat dibuka!")

    def _update_ui_progress(self, data: dict):
        percentage = data.get('percentage', 0.0)
        speed = data.get('speed', '0 KB/s')
        eta = data.get('eta', '00:00')
        status = data.get('status', 'Status: Mengunduh...')
        self.progress_hub.update_progress(percentage, speed, eta, status)

    # =========================================================================
    # SYSTEM TRAY & WORKFLOW INTEGRATION (v1.6)
    # =========================================================================
    def _on_window_close(self):
        """Menangani event tombol close (X). Minimize ke tray jika opsi aktif."""
        if self.settings.get("minimize_to_tray", False):
            self._minimize_to_tray()
        else:
            self._quit_application()

    def _minimize_to_tray(self):
        """Sembunyikan window utama dan aktifkan icon sistem tray."""
        self.withdraw()
        if hasattr(self, "tray_manager"):
            self.tray_manager.start()

    def _restore_from_tray(self):
        """Pulihkan window utama dari sistem tray ke layar depan."""
        self.deiconify()
        self.lift()
        self.focus_force()
        self.state("normal")
        if hasattr(self, "tray_manager"):
            self.tray_manager.stop()

    def _open_downloads_folder_tray(self):
        """Aksi buka folder unduhan dari menu konteks tray icon."""
        folder = self.settings.get("download_dir", Config.DEFAULT_DOWNLOAD_DIR)
        if not os.path.exists(folder):
            try:
                os.makedirs(folder, exist_ok=True)
            except Exception:
                pass
        if os.path.exists(folder):
            os.startfile(folder)

    def _quit_application(self):
        """Tutup aplikasi secara bersih dan hentikan background tray thread."""
        if hasattr(self, "tray_manager"):
            self.tray_manager.stop()
        self.destroy()
        sys.exit(0)

    def _poll_clipboard_background(self):
        """
        Background clipboard monitor loop (v1.6).
        Mendeteksi jika pengguna menyalin URL media yang didukung di Windows,
        dan secara otomatis memasukkannya ke Quick Downloader.
        """
        if self.settings.get("auto_clipboard_monitor", True):
            try:
                cb_text = self.clipboard_get().strip()
                if cb_text and cb_text.startswith(("http://", "https://")):
                    if PlatformHelper.is_supported(cb_text, strict_media=True):
                        current_val = self.url_entry.get().strip()
                        if cb_text != self._last_detected_clipboard and cb_text != current_val:
                            self._last_detected_clipboard = cb_text
                            self.url_entry.delete(0, "end")
                            self.url_entry.insert(0, cb_text)
                            self.clip_sniff_chip.grid_forget()
                            self._start_preview_thread(force=True)
                            self.log_area.write_log(f"[Clipboard Monitor] Mendeteksi tautan media: {cb_text}")
                            self.progress_hub.status_text.configure(text=f"Status: Tautan terdeteksi dari clipboard: {cb_text[:35]}...")
            except Exception:
                pass
        self.after(1200, self._poll_clipboard_background)