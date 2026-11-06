import re
import customtkinter as ctk
from core.config import Config

class CardFrame(ctk.CTkFrame):
    """Container frame dengan styling kartu modern ber-elevasi bersih (Light/Dark adaptive)."""
    def __init__(self, master, **kwargs):
        kwargs.setdefault("fg_color", Config.CARD_BG)
        kwargs.setdefault("corner_radius", 12)
        kwargs.setdefault("border_width", 1)
        kwargs.setdefault("border_color", Config.CARD_BORDER)
        super().__init__(master, **kwargs)


class MediaPreviewCard(CardFrame):
    """
    Kartu Hero Horizontal (16:9 Landscape Layout)
    Sisi kiri: Thumbnail video/audio berasio 16:9 dengan border halus.
    Sisi kanan: Metadata terstruktur (Status, Judul, Channel, Durasi, dan Tipe Media).
    """
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        
        self.grid_columnconfigure(0, weight=0)  # Fixed width thumbnail
        self.grid_columnconfigure(1, weight=1)  # Expandable metadata info
        self.grid_rowconfigure(0, weight=1)
        
        # ---------------------------------------------------------------------
        # SISI KIRI: THUMBNAIL CONTAINER 16:9 (210x118 px)
        # ---------------------------------------------------------------------
        self.thumb_container = ctk.CTkFrame(
            self,
            fg_color=Config.INPUT_BG,
            corner_radius=10,
            border_width=1,
            border_color=Config.CARD_BORDER,
            width=210,
            height=118
        )
        self.thumb_container.grid(row=0, column=0, padx=14, pady=14, sticky="nsw")
        self.thumb_container.grid_columnconfigure(0, weight=1)
        self.thumb_container.grid_rowconfigure(0, weight=1)
        self.thumb_container.grid_propagate(False)
        
        self.thumbnail_label = ctk.CTkLabel(
            self.thumb_container,
            text="🎧\nTempel tautan untuk\nmelihat preview media",
            font=("Segoe UI", 11),
            text_color=Config.TEXT_DIM,
            anchor="center"
        )
        self.thumbnail_label.grid(row=0, column=0, sticky="nsew")
        
        # ---------------------------------------------------------------------
        # SISI KANAN: METADATA & BADGES (HARMONIS, RAPI, & SEIMBANG)
        # ---------------------------------------------------------------------
        self.info_container = ctk.CTkFrame(self, fg_color="transparent")
        self.info_container.grid(row=0, column=1, padx=(4, 18), pady=12, sticky="nsew")
        self.info_container.grid_columnconfigure(0, weight=1)
        
        # Baris 1: Header Baris Atas (Platform Pill di Kiri, Status Badge di Kanan)
        self.badge_row = ctk.CTkFrame(self.info_container, fg_color="transparent")
        self.badge_row.grid(row=0, column=0, sticky="ew", pady=(0, 6))
        self.badge_row.grid_columnconfigure(0, weight=1)
        
        # Platform Source Pill (Kiri Atas)
        self.platform_chip = ctk.CTkFrame(
            self.badge_row,
            fg_color=Config.CARD_BG_ELEVATED,
            corner_radius=6,
            border_width=1,
            border_color=Config.CARD_BORDER
        )
        self.platform_chip.pack(side="left")
        
        self.platform_label = ctk.CTkLabel(
            self.platform_chip,
            text="🌐 PREVIEW MEDIA",
            font=("Segoe UI", 9, "bold"),
            text_color=Config.BTN_PRIMARY_BG
        )
        self.platform_label.pack(padx=8, pady=2)
        
        # Status Badge Pill (Kanan Atas)
        self.status_chip = ctk.CTkFrame(
            self.badge_row,
            fg_color=Config.CARD_BG_ELEVATED,
            corner_radius=6,
            border_width=1,
            border_color=Config.CARD_BORDER
        )
        self.status_chip.pack(side="right")
        
        self.stream_label = ctk.CTkLabel(
            self.status_chip,
            text="Siap Diunduh",
            font=("Segoe UI", 9, "bold"),
            text_color=Config.TEXT_MUTED
        )
        self.stream_label.pack(padx=8, pady=2)
        
        # Baris 2: Judul Media (Title) - Typography Tajam & Spasi Luas
        self.title_label = ctk.CTkLabel(
            self.info_container,
            text="Belum Ada Media yang Dipilih",
            font=("Segoe UI", 13, "bold"),
            text_color=Config.TEXT_MAIN,
            anchor="w",
            wraplength=680,
            justify="left"
        )
        self.title_label.grid(row=1, column=0, sticky="ew", pady=(0, 4))
        
        # Baris 3: Channel / Uploader
        self.channel_label = ctk.CTkLabel(
            self.info_container,
            text="Channel / Uploader: -",
            font=("Segoe UI", 11),
            text_color=Config.TEXT_MUTED,
            anchor="w"
        )
        self.channel_label.grid(row=2, column=0, sticky="w", pady=(0, 10))
        
        # Baris 4: Chips Metadata (Durasi, Resolusi, Tipe, Format)
        self.chips_row = ctk.CTkFrame(self.info_container, fg_color="transparent")
        self.chips_row.grid(row=3, column=0, sticky="w")
        
        # 1. Duration Chip
        self.duration_chip = ctk.CTkFrame(
            self.chips_row,
            fg_color=Config.CARD_BG_ELEVATED,
            corner_radius=6,
            border_width=1,
            border_color=Config.CARD_BORDER
        )
        self.duration_chip.pack(side="left", padx=(0, 8))
        self.duration_label = ctk.CTkLabel(
            self.duration_chip,
            text="⏱️ --:--",
            font=("Segoe UI", 10, "bold"),
            text_color=Config.TEXT_MAIN
        )
        self.duration_label.pack(padx=8, pady=3)

        # 2. Resolution Badge Chip
        self.res_chip = ctk.CTkFrame(
            self.chips_row,
            fg_color=Config.CARD_BG_ELEVATED,
            corner_radius=6,
            border_width=1,
            border_color=Config.CARD_BORDER
        )
        self.res_chip.pack(side="left", padx=(0, 8))
        self.res_label = ctk.CTkLabel(
            self.res_chip,
            text="🎬 Resolusi: -",
            font=("Segoe UI", 10, "bold"),
            text_color=Config.TEXT_MAIN
        )
        self.res_label.pack(padx=8, pady=3)
        
        # 3. Track / Content Type Chip
        self.count_chip = ctk.CTkFrame(
            self.chips_row,
            fg_color=Config.CARD_BG_ELEVATED,
            corner_radius=6,
            border_width=1,
            border_color=Config.CARD_BORDER
        )
        self.count_chip.pack(side="left", padx=(0, 8))
        self.count_label = ctk.CTkLabel(
            self.count_chip,
            text="📁 Single Track",
            font=("Segoe UI", 10, "bold"),
            text_color=Config.TEXT_MAIN
        )
        self.count_label.pack(padx=8, pady=3)

        # 4. Format / Target Output Chip
        self.format_chip = ctk.CTkFrame(
            self.chips_row,
            fg_color=Config.CARD_BG_ELEVATED,
            corner_radius=6,
            border_width=1,
            border_color=Config.CARD_BORDER
        )
        self.format_chip.pack(side="left")
        self.format_label = ctk.CTkLabel(
            self.format_chip,
            text="📦 Format Siap",
            font=("Segoe UI", 10, "bold"),
            text_color=Config.TEXT_MAIN
        )
        self.format_label.pack(padx=8, pady=3)
        self.current_thumbnail_image = None

    def set_preview(self, title: str, channel: str, duration: str, count_text: str, image_obj=None, max_res: str = "-", platform_badge: str = None, format_hint: str = None):
        """Memperbarui kartu preview secara realtime dengan badge resolusi dan platform sumber media."""
        display_title = title if len(title) <= 90 else title[:87] + "..."
        self.title_label.configure(text=display_title)
        
        clean_channel = channel.strip()
        if not clean_channel.startswith("👤") and not clean_channel.startswith("@"):
            self.channel_label.configure(text=f"👤 {clean_channel}")
        else:
            self.channel_label.configure(text=clean_channel)
            
        self.duration_label.configure(text=f"⏱️ {duration}")
        
        clean_count = count_text.strip()
        if not clean_count.startswith("📁") and not clean_count.startswith("📑"):
            self.count_label.configure(text=f"📁 {clean_count}")
        else:
            self.count_label.configure(text=clean_count)
        
        # Update Resolusi Badge
        self.res_label.configure(text=f"🎬 {max_res}" if max_res and max_res != "-" else "🎬 Standard")
        
        # Update Format Output Hint
        if format_hint:
            self.format_label.configure(text=f"📦 {format_hint}")
        else:
            self.format_label.configure(text="📦 Siap Unduh")
        
        # Update Status Badge
        self.stream_label.configure(text="✓ Metadata Siap", text_color=Config.SUCCESS_COLOR)
        self.status_chip.configure(border_color=Config.SUCCESS_COLOR)
        
        if platform_badge:
            self.platform_label.configure(text=str(platform_badge).upper())
        else:
            self.platform_label.configure(text="🌐 PREVIEW MEDIA")
        
        # Simpan referensi kuat agar bebas garbage collection oleh Tkinter
        self.current_thumbnail_image = image_obj
        self.thumbnail_label.image = image_obj
        if hasattr(self.thumbnail_label, "_label"):
            self.thumbnail_label._label.image = image_obj

        if image_obj:
            try:
                self.thumbnail_label.configure(image=image_obj, text="")
            except Exception:
                if hasattr(self.thumbnail_label, "_label"):
                    try:
                        self.thumbnail_label._label.configure(image="")
                    except Exception:
                        pass
                self.thumbnail_label.configure(image=None, text="🎧\nNo Cover Available")
        else:
            if hasattr(self.thumbnail_label, "_label"):
                try:
                    self.thumbnail_label._label.configure(image="")
                except Exception:
                    pass
            self.thumbnail_label.configure(image=None, text="🎧\nNo Cover Available")

    def set_loading(self, message: str = "Memuat metadata..."):
        """Menampilkan indikator loading metadata."""
        self.current_thumbnail_image = None
        self.thumbnail_label.image = None
        if hasattr(self.thumbnail_label, "_label"):
            self.thumbnail_label._label.image = None
            try:
                self.thumbnail_label._label.configure(image="")
            except Exception:
                pass
        self.title_label.configure(text=message or "Menganalisis tautan media...")
        self.channel_label.configure(text="Mengambil data uploader & resolusi...")
        self.duration_label.configure(text="⏱️ --:--")
        self.res_label.configure(text="🎬 Resolusi: -")
        self.count_label.configure(text="📁 Menganalisis...")
        self.format_label.configure(text="📦 Memproses...")
        self.platform_label.configure(text="⏳ MENGANALISIS...")
        self.stream_label.configure(text="Memuat...", text_color=Config.TEXT_MUTED)
        self.status_chip.configure(border_color=Config.CARD_BORDER)
        self.thumbnail_label.configure(image=None, text="⏳\nMemuat metadata...")

    def set_error(self, message: str = "Gagal Memuat Metadata"):
        """Menampilkan indikator kegagalan pemuatan metadata."""
        self.current_thumbnail_image = None
        self.thumbnail_label.image = None
        if hasattr(self.thumbnail_label, "_label"):
            self.thumbnail_label._label.image = None
            try:
                self.thumbnail_label._label.configure(image="")
            except Exception:
                pass
        self.title_label.configure(text=message)
        self.channel_label.configure(text="Periksa kembali tautan atau koneksi internet")
        self.stream_label.configure(text="❌ Gagal", text_color=Config.DANGER_COLOR)
        self.status_chip.configure(border_color=Config.DANGER_COLOR)
        self.thumbnail_label.configure(image=None, text="❌\nGagal Memuat")

    def reset(self):
        """Reset kartu preview ke kondisi awal."""
        self.current_thumbnail_image = None
        self.thumbnail_label.image = None
        if hasattr(self.thumbnail_label, "_label"):
            self.thumbnail_label._label.image = None
            try:
                self.thumbnail_label._label.configure(image="")
            except Exception:
                pass
        self.title_label.configure(text="Belum Ada Media yang Dipilih")
        self.channel_label.configure(text="Channel / Uploader: -")
        self.duration_label.configure(text="⏱️ --:--")
        self.res_label.configure(text="🎬 Resolusi: -")
        self.count_label.configure(text="📁 Single Track")
        self.format_label.configure(text="📦 Format Siap")
        self.platform_label.configure(text="🌐 PREVIEW MEDIA")
        self.stream_label.configure(text="Siap Diunduh", text_color=Config.TEXT_MUTED)
        self.status_chip.configure(border_color=Config.CARD_BORDER)
        self.thumbnail_label.configure(image=None, text="🎧\nTempel tautan untuk\nmelihat preview media")
        self.channel_label.configure(text="Channel / Uploader: -")
        self.duration_label.configure(text="⏱️ --:--")
        self.res_label.configure(text="🎬 Resolusi: -")
        self.count_label.configure(text="Single Track")
        self.stream_label.configure(text="Siap Diunduh", text_color=Config.TEXT_MUTED)
        self.thumbnail_label.configure(image=None, text="🎧\nTempel tautan untuk\nmelihat preview media")


class MultiStageProgress(CardFrame):
    """
    Komponen Pelacak Progress Multi-Tahap (Multi-Stage Progress Hub)
    Menampilkan visual stepper alur unduhan dengan gaya minimalis bersih:
    [1. Analisis] ➔ [2. Mengunduh] ➔ [3. Pemrosesan] ➔ [4. Selesai]
    """
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.grid_columnconfigure(0, weight=1)
        
        # 1. Baris Stepper Tahapan
        self.stepper_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.stepper_frame.grid(row=0, column=0, padx=16, pady=(14, 10), sticky="ew")
        
        self.stages = [
            {"id": 1, "name": "1. Analisis"},
            {"id": 2, "name": "2. Mengunduh"},
            {"id": 3, "name": "3. Pemrosesan"},
            {"id": 4, "name": "4. Selesai"}
        ]
        
        self.stage_widgets = []
        for i, s in enumerate(self.stages):
            pill = ctk.CTkFrame(
                self.stepper_frame,
                fg_color=Config.CARD_BG_ELEVATED,
                corner_radius=6,
                border_width=1,
                border_color=Config.CARD_BORDER
            )
            pill.pack(side="left", padx=(0, 8))
            
            lbl = ctk.CTkLabel(
                pill,
                text=s['name'],
                font=("Segoe UI", 10, "bold"),
                text_color=Config.TEXT_DIM
            )
            lbl.pack(padx=10, pady=3)
            self.stage_widgets.append((pill, lbl))
            
            # Panah penghubung antar tahapan
            if i < len(self.stages) - 1:
                arrow = ctk.CTkLabel(
                    self.stepper_frame,
                    text="›",
                    font=("Segoe UI", 12, "bold"),
                    text_color=Config.TEXT_DIM
                )
                arrow.pack(side="left", padx=(0, 8))

        # 2. Baris Status Detail & Stats
        self.stats_row = ctk.CTkFrame(self, fg_color="transparent")
        self.stats_row.grid(row=1, column=0, padx=16, pady=(0, 8), sticky="ew")
        self.stats_row.grid_columnconfigure(0, weight=1)
        
        self.status_text = ctk.CTkLabel(
            self.stats_row,
            text="Status: Idle (Menunggu instruksi)",
            font=("Segoe UI", 11, "bold"),
            text_color=Config.TEXT_MAIN,
            anchor="w"
        )
        self.status_text.grid(row=0, column=0, sticky="w")
        
        self.metrics_frame = ctk.CTkFrame(self.stats_row, fg_color="transparent")
        self.metrics_frame.grid(row=0, column=1, sticky="e")
        
        self.speed_label = ctk.CTkLabel(
            self.metrics_frame,
            text="Speed: 0 KB/s",
            font=("Segoe UI", 11),
            text_color=Config.TEXT_MUTED
        )
        self.speed_label.pack(side="left", padx=(0, 16))
        
        self.eta_label = ctk.CTkLabel(
            self.metrics_frame,
            text="ETA: 00:00",
            font=("Segoe UI", 11),
            text_color=Config.TEXT_MUTED
        )
        self.eta_label.pack(side="left", padx=(0, 16))
        
        self.percent_label = ctk.CTkLabel(
            self.metrics_frame,
            text="0%",
            font=("Segoe UI", 11, "bold"),
            text_color=Config.TEXT_MAIN
        )
        self.percent_label.pack(side="left")

        # 3. Baris Progress Bar Minimalis
        self.progress_bar = ctk.CTkProgressBar(
            self,
            height=6,
            corner_radius=3,
            fg_color=Config.CARD_BG_ELEVATED,
            progress_color=Config.BTN_PRIMARY_BG
        )
        self.progress_bar.grid(row=2, column=0, padx=16, pady=(0, 14), sticky="ew")
        self.progress_bar.set(0.0)

    def set_stage(self, stage_num: int):
        """Mengubah status visual stepper (1, 2, 3, 4)."""
        for i, (pill, lbl) in enumerate(self.stage_widgets):
            s_num = i + 1
            if s_num < stage_num:
                # Selesai
                pill.configure(fg_color=Config.SUCCESS_BG, border_color=Config.SUCCESS_BORDER)
                lbl.configure(text_color=Config.SUCCESS_COLOR)
            elif s_num == stage_num:
                # Aktif saat ini
                pill.configure(fg_color=Config.CARD_BG_ELEVATED, border_color=Config.BTN_PRIMARY_BG)
                lbl.configure(text_color=Config.BTN_PRIMARY_BG)
            else:
                # Menunggu
                pill.configure(fg_color=Config.CARD_BG_ELEVATED, border_color=Config.CARD_BORDER)
                lbl.configure(text_color=Config.TEXT_DIM)

    def update_progress(self, percentage: float, speed: str, eta: str, status_msg: str):
        """Update metrics dan progress bar."""
        self.progress_bar.set(percentage)
        percent_int = int(percentage * 100)
        self.percent_label.configure(text=f"{percent_int}%")
        
        # Bersihkan jika masih ada kode escape ANSI
        clean_speed = re.sub(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])', '', str(speed)).strip()
        clean_eta = re.sub(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])', '', str(eta)).strip()
        clean_status = re.sub(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])', '', str(status_msg)).strip()
        
        self.speed_label.configure(text=f"Speed: {clean_speed}")
        self.eta_label.configure(text=f"ETA: {clean_eta}")
        self.status_text.configure(text=clean_status)
        
        if percentage > 0.0 and percentage < 1.0:
            self.set_stage(2)
        elif percentage >= 1.0:
            self.set_stage(3)

    def mark_completed(self, message: str = "Unduhan berhasil diselesaikan!"):
        self.set_stage(4)
        self.progress_bar.set(1.0)
        self.percent_label.configure(text="100%", text_color=Config.SUCCESS_COLOR)
        self.status_text.configure(text=f"✓ {message}")
        self.speed_label.configure(text="Selesai")
        self.eta_label.configure(text="00:00")

    def reset(self):
        """Reset progress stepper ke idle."""
        for pill, lbl in self.stage_widgets:
            pill.configure(fg_color=Config.CARD_BG_ELEVATED, border_color=Config.CARD_BORDER)
            lbl.configure(text_color=Config.TEXT_DIM)
        self.progress_bar.set(0.0)
        self.percent_label.configure(text="0%", text_color=Config.TEXT_MAIN)
        self.speed_label.configure(text="Speed: 0 KB/s")
        self.eta_label.configure(text="ETA: 00:00")
        self.status_text.configure(text="Status: Idle (Menunggu instruksi)")


class CollapsibleLogArea(CardFrame):
    """Area log aktivitas yt-dlp & FFmpeg dengan quick status ticker di header."""
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        
        self.is_expanded = False
        self.grid_columnconfigure(0, weight=1)
        
        # Header Log Bar
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.grid(row=0, column=0, padx=14, pady=8, sticky="ew")
        self.header_frame.grid_columnconfigure(0, weight=0)
        self.header_frame.grid_columnconfigure(1, weight=1)
        self.header_frame.grid_columnconfigure(2, weight=0)
        
        # Kolom 0: Title Bar (Dot + Text)
        self.title_frame = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        self.title_frame.grid(row=0, column=0, sticky="w")
        
        self.dot_label = ctk.CTkLabel(
            self.title_frame, text="●", font=("Arial", 10), text_color=Config.SUCCESS_COLOR
        )
        self.dot_label.pack(side="left", padx=(0, 6))
        
        self.label = ctk.CTkLabel(
            self.title_frame, text="Activity Console", font=("Segoe UI", 11, "bold"), text_color=Config.TEXT_MAIN
        )
        self.label.pack(side="left")
        
        # Kolom 1: Quick Status Ticker (Tengah, tidak bertumpuk)
        self.ticker_label = ctk.CTkLabel(
            self.header_frame,
            text="Sistem siap",
            font=("Consolas", 10),
            text_color=Config.TEXT_MUTED,
            anchor="w"
        )
        self.ticker_label.grid(row=0, column=1, padx=(14, 14), sticky="ew")
        
        # Kolom 2: Tombol Clear & Toggle (Kanan)
        self.btn_sub_frame = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        self.btn_sub_frame.grid(row=0, column=2, sticky="e")
        
        self.clear_btn = ctk.CTkButton(
            self.btn_sub_frame,
            text="Clear",
            width=48,
            height=24,
            corner_radius=6,
            font=("Segoe UI", 10),
            fg_color="transparent",
            hover_color=Config.CARD_HOVER,
            text_color=Config.TEXT_MUTED,
            command=self.clear_log
        )
        self.clear_btn.pack(side="left", padx=(0, 6))
        
        self.toggle_btn = ctk.CTkButton(
            self.btn_sub_frame,
            text="▲ Expand",
            width=80,
            height=24,
            corner_radius=6,
            font=("Segoe UI", 10, "bold"),
            fg_color=Config.SECONDARY_BTN,
            hover_color=Config.SECONDARY_HOVER,
            text_color=Config.SECONDARY_TEXT,
            command=self.toggle_visibility
        )
        self.toggle_btn.pack(side="left")
        
        # Textbox Output Log
        self.text_area = ctk.CTkTextbox(
            self,
            font=("Consolas", 10),
            fg_color=Config.INPUT_BG,
            text_color=Config.TEXT_MUTED,
            corner_radius=8,
            border_width=1,
            border_color=Config.CARD_BORDER,
            height=120
        )
        self.text_area.grid(row=1, column=0, padx=14, pady=(0, 12), sticky="nsew")
        self.text_area.configure(state="disabled")
        self.text_area.grid_remove()

    def toggle_visibility(self):
        """Buka / tutup area textbox log."""
        if self.is_expanded:
            self.text_area.grid_remove()
            self.toggle_btn.configure(text="▲ Expand")
            self.is_expanded = False
        else:
            self.text_area.grid()
            self.toggle_btn.configure(text="▼ Collapse")
            self.is_expanded = True

    def write_log(self, message: str):
        """Menulis baris baru ke log dan mengupdate status ticker."""
        clean_msg = message.strip()
        if clean_msg:
            short_ticker = clean_msg if len(clean_msg) <= 65 else clean_msg[:62] + "..."
            self.ticker_label.configure(text=short_ticker)
            
        self.text_area.configure(state="normal")
        self.text_area.insert("end", message + "\n")
        self.text_area.see("end")
        self.text_area.configure(state="disabled")

    def clear_log(self):
        self.text_area.configure(state="normal")
        self.text_area.delete("1.0", "end")
        self.text_area.configure(state="disabled")
        self.ticker_label.configure(text="Console dibersihkan")


InfoPanel = MediaPreviewCard
LogArea = CollapsibleLogArea