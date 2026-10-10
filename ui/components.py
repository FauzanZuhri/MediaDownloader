import customtkinter as ctk
from core.config import Config

class CardFrame(ctk.CTkFrame):
    """Container frame dengan styling kartu modern ber-elevasi."""
    def __init__(self, master, **kwargs):
        # Default styling kartu obsidian
        kwargs.setdefault("fg_color", Config.CARD_BG)
        kwargs.setdefault("corner_radius", 14)
        kwargs.setdefault("border_width", 1)
        kwargs.setdefault("border_color", Config.CARD_BORDER)
        super().__init__(master, **kwargs)


class MediaPreviewCard(CardFrame):
    """Kartu Hero untuk menampilkan cover art dan detail media YouTube."""
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        
        self.grid_columnconfigure(0, weight=1)
        
        # Header kecil kartu
        self.card_header = ctk.CTkLabel(
            self,
            text="🎵 PREVIEW MEDIA",
            font=("Segoe UI", 11, "bold"),
            text_color=Config.ACCENT_COLOR,
            anchor="w"
        )
        self.card_header.grid(row=0, column=0, padx=16, pady=(14, 8), sticky="w")
        
        # Frame Thumbnail (16:9 Rasio)
        self.thumb_container = ctk.CTkFrame(
            self,
            fg_color="#0b0d13",
            corner_radius=10,
            border_width=1,
            border_color=Config.CARD_BORDER,
            height=130
        )
        self.thumb_container.grid(row=1, column=0, padx=16, pady=(0, 12), sticky="ew")
        self.thumb_container.grid_columnconfigure(0, weight=1)
        self.thumb_container.grid_rowconfigure(0, weight=1)
        self.thumb_container.grid_propagate(False)
        
        self.thumbnail_label = ctk.CTkLabel(
            self.thumb_container,
            text="🎧\nTempel link untuk melihat preview",
            font=("Segoe UI", 12),
            text_color=Config.TEXT_DIM,
            anchor="center"
        )
        self.thumbnail_label.grid(row=0, column=0, sticky="nsew")
        
        # Informasi Teks
        self.title_label = ctk.CTkLabel(
            self,
            text="Belum Ada Lagu Dipilih",
            font=("Segoe UI", 13, "bold"),
            text_color=Config.TEXT_MAIN,
            anchor="w",
            wraplength=340,
            justify="left"
        )
        self.title_label.grid(row=2, column=0, padx=16, pady=(0, 4), sticky="w")
        
        self.channel_label = ctk.CTkLabel(
            self,
            text="Channel / Uploader: -",
            font=("Segoe UI", 12),
            text_color=Config.TEXT_MUTED,
            anchor="w"
        )
        self.channel_label.grid(row=3, column=0, padx=16, pady=(0, 10), sticky="w")
        
        # Badge Chips Container (Durasi & Format/Jumlah)
        self.chips_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.chips_frame.grid(row=4, column=0, padx=16, pady=(0, 16), sticky="w")
        
        # Chip Durasi
        self.duration_chip = ctk.CTkFrame(
            self.chips_frame,
            fg_color="#202636",
            corner_radius=8,
            border_width=1,
            border_color="#2e374d"
        )
        self.duration_chip.pack(side="left", padx=(0, 8))
        self.duration_label = ctk.CTkLabel(
            self.duration_chip,
            text="⏱️ --:--",
            font=("Segoe UI", 11, "bold"),
            text_color=Config.TEXT_MAIN
        )
        self.duration_label.pack(padx=8, pady=3)
        
        # Chip Count / Status
        self.count_chip = ctk.CTkFrame(
            self.chips_frame,
            fg_color="#202636",
            corner_radius=8,
            border_width=1,
            border_color="#2e374d"
        )
        self.count_chip.pack(side="left")
        self.count_label = ctk.CTkLabel(
            self.count_chip,
            text="📦 Single Track",
            font=("Segoe UI", 11, "bold"),
            text_color=Config.TEXT_MAIN
        )
        self.count_label.pack(padx=8, pady=3)

    def set_preview(self, title: str, channel: str, duration: str, count_text: str, image_obj=None):
        """Memperbarui UI Preview dengan data lagu baru."""
        display_title = title if len(title) <= 75 else title[:72] + "..."
        self.title_label.configure(text=display_title)
        self.channel_label.configure(text=f"Channel: {channel}")
        self.duration_label.configure(text=f"⏱️ {duration}")
        self.count_label.configure(text=f"📦 {count_text}")
        
        if image_obj:
            self.thumbnail_label.configure(image=image_obj, text="")
        else:
            self.thumbnail_label.configure(image=None, text="🎧\nNo Cover Available")

    def reset(self):
        """Reset preview ke kondisi awal."""
        self.title_label.configure(text="Belum Ada Lagu Dipilih")
        self.channel_label.configure(text="Channel / Uploader: -")
        self.duration_label.configure(text="⏱️ --:--")
        self.count_label.configure(text="📦 Single Track")
        self.thumbnail_label.configure(image=None, text="🎧\nTempel link untuk melihat preview")


class CollapsibleLogArea(CardFrame):
    """Area log aktivitas yt-dlp yang rapi dan dapat disembunyikan (collapsible)."""
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        
        self.is_expanded = True
        self.grid_columnconfigure(0, weight=1)
        
        # Header Log Bar
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.grid(row=0, column=0, padx=14, pady=10, sticky="ew")
        self.header_frame.grid_columnconfigure(0, weight=1)
        
        self.title_frame = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        self.title_frame.grid(row=0, column=0, sticky="w")
        
        self.dot_label = ctk.CTkLabel(
            self.title_frame, text="●", font=("Arial", 12), text_color=Config.SUCCESS_COLOR
        )
        self.dot_label.pack(side="left", padx=(0, 6))
        
        self.label = ctk.CTkLabel(
            self.title_frame, text="Activity Console", font=("Segoe UI", 12, "bold"), text_color=Config.TEXT_MAIN
        )
        self.label.pack(side="left")
        
        # Tombol Clear & Toggle
        self.btn_sub_frame = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        self.btn_sub_frame.grid(row=0, column=1, sticky="e")
        
        self.clear_btn = ctk.CTkButton(
            self.btn_sub_frame,
            text="Clear",
            width=55,
            height=24,
            font=("Segoe UI", 11),
            fg_color="transparent",
            hover_color=Config.CARD_HOVER,
            text_color=Config.TEXT_MUTED,
            command=self.clear_log
        )
        self.clear_btn.pack(side="left", padx=(0, 6))
        
        self.toggle_btn = ctk.CTkButton(
            self.btn_sub_frame,
            text="▼ Collapse",
            width=80,
            height=24,
            font=("Segoe UI", 11),
            fg_color="#202636",
            hover_color="#2c354a",
            text_color=Config.TEXT_MAIN,
            command=self.toggle_visibility
        )
        self.toggle_btn.pack(side="left")
        
        # Textbox untuk Output Log
        self.text_area = ctk.CTkTextbox(
            self,
            font=("Consolas", 11),
            fg_color="#0b0d13",
            text_color="#94a3b8",
            corner_radius=8,
            border_width=1,
            border_color="#1e2433",
            height=120
        )
        self.text_area.grid(row=1, column=0, padx=14, pady=(0, 12), sticky="nsew")
        self.text_area.configure(state="disabled")

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
        """Menulis baris baru ke log dengan auto-scroll."""
        self.text_area.configure(state="normal")
        self.text_area.insert("end", message + "\n")
        self.text_area.see("end")
        self.text_area.configure(state="disabled")

    def clear_log(self):
        """Membersihkan output log."""
        self.text_area.configure(state="normal")
        self.text_area.delete("1.0", "end")
        self.text_area.configure(state="disabled")


# Alias untuk backwards-compatibility
InfoPanel = MediaPreviewCard
LogArea = CollapsibleLogArea