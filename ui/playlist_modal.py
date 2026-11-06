import customtkinter as ctk
from typing import List, Dict, Any, Callable
from core.config import Config

class PlaylistSelectorModal(ctk.CTkToplevel):
    """
    Modal Dialog Interaktif Pemilih Trek Playlist YouTube.
    Memungkinkan pengguna memilih/membatalkan trek tertentu dalam playlist
    sebelum dikirim ke Batch Queue untuk diunduh.
    """
    def __init__(self, parent, playlist_info: Dict[str, Any], on_submit: Callable[[List[Dict[str, Any]]], None]):
        super().__init__(parent)
        self.parent = parent
        self.playlist_info = playlist_info
        self.on_submit = on_submit
        self.entries = playlist_info.get("entries", [])
        
        # State tracking checkbox untuk setiap item: {entry_id: ctk.BooleanVar}
        self.item_vars: Dict[str, ctk.BooleanVar] = {}
        self.entry_widgets = []

        self.title("📑 Pemilih Trek Playlist")
        self.geometry("740x580")
        self.minsize(620, 480)
        self.configure(fg_color=Config.BG_COLOR)

        # Modal configuration
        self.transient(parent)
        self.grab_set()

        self._create_ui()
        self._update_counter()

    def _create_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # ---------------------------------------------------------------------
        # 1. HEADER INFO PLAYLIST
        # ---------------------------------------------------------------------
        header_frame = ctk.CTkFrame(self, fg_color=Config.CARD_BG, corner_radius=10, border_width=1, border_color=Config.CARD_BORDER)
        header_frame.grid(row=0, column=0, padx=20, pady=(18, 12), sticky="ew")
        header_frame.grid_columnconfigure(0, weight=1)

        title_lbl = ctk.CTkLabel(
            header_frame,
            text=self.playlist_info.get("title", "Daftar Isi Playlist"),
            font=("Segoe UI", 15, "bold"),
            text_color=Config.TEXT_MAIN,
            anchor="w"
        )
        title_lbl.grid(row=0, column=0, padx=16, pady=(12, 2), sticky="w")

        uploader_lbl = ctk.CTkLabel(
            header_frame,
            text=f"Saluran / Pembuat: {self.playlist_info.get('uploader', 'Unknown')} • Total {len(self.entries)} trek",
            font=("Segoe UI", 11),
            text_color=Config.TEXT_MUTED,
            anchor="w"
        )
        uploader_lbl.grid(row=1, column=0, padx=16, pady=(0, 12), sticky="w")

        # ---------------------------------------------------------------------
        # 2. TOOLBAR AKSI CEPAT (SELECT ALL, DESELECT, INVERT, FILTER)
        # ---------------------------------------------------------------------
        toolbar = ctk.CTkFrame(self, fg_color="transparent")
        toolbar.grid(row=1, column=0, padx=20, pady=(0, 10), sticky="ew")
        toolbar.grid_columnconfigure(3, weight=1)

        btn_select_all = ctk.CTkButton(
            toolbar,
            text="☑ Pilih Semua",
            font=("Segoe UI", 10, "bold"),
            height=28,
            width=95,
            corner_radius=6,
            fg_color=Config.SECONDARY_BTN,
            hover_color=Config.SECONDARY_HOVER,
            text_color=Config.SECONDARY_TEXT,
            command=self._select_all
        )
        btn_select_all.grid(row=0, column=0, padx=(0, 6), sticky="w")

        btn_deselect_all = ctk.CTkButton(
            toolbar,
            text="☐ Batalkan",
            font=("Segoe UI", 10, "bold"),
            height=28,
            width=85,
            corner_radius=6,
            fg_color=Config.SECONDARY_BTN,
            hover_color=Config.SECONDARY_HOVER,
            text_color=Config.SECONDARY_TEXT,
            command=self._deselect_all
        )
        btn_deselect_all.grid(row=0, column=1, padx=(0, 6), sticky="w")

        btn_invert = ctk.CTkButton(
            toolbar,
            text="🔄 Balikkan",
            font=("Segoe UI", 10, "bold"),
            height=28,
            width=85,
            corner_radius=6,
            fg_color=Config.SECONDARY_BTN,
            hover_color=Config.SECONDARY_HOVER,
            text_color=Config.SECONDARY_TEXT,
            command=self._invert_selection
        )
        btn_invert.grid(row=0, column=2, padx=(0, 10), sticky="w")

        # Search / Filter Box
        self.search_var = ctk.StringVar()
        self.search_var.trace_add("write", lambda *_: self._filter_items())
        self.search_entry = ctk.CTkEntry(
            toolbar,
            textvariable=self.search_var,
            placeholder_text="🔍 Cari judul trek...",
            height=28,
            corner_radius=6,
            fg_color=Config.INPUT_BG,
            border_color=Config.INPUT_BORDER,
            text_color=Config.TEXT_MAIN
        )
        self.search_entry.grid(row=0, column=3, sticky="ew")

        # ---------------------------------------------------------------------
        # 3. DAFTAR TREK (SCROLLABLE LIST)
        # ---------------------------------------------------------------------
        self.list_frame = ctk.CTkScrollableFrame(
            self,
            fg_color=Config.CARD_BG,
            corner_radius=10,
            border_width=1,
            border_color=Config.CARD_BORDER
        )
        self.list_frame.grid(row=2, column=0, padx=20, pady=(0, 12), sticky="nsew")
        self.list_frame.grid_columnconfigure(1, weight=1)

        self._populate_entries()

        # ---------------------------------------------------------------------
        # 4. FOOTER ACTIONS
        # ---------------------------------------------------------------------
        footer_frame = ctk.CTkFrame(self, fg_color="transparent")
        footer_frame.grid(row=3, column=0, padx=20, pady=(0, 18), sticky="ew")
        footer_frame.grid_columnconfigure(0, weight=1)

        self.selected_count_lbl = ctk.CTkLabel(
            footer_frame,
            text="0 trek dipilih",
            font=("Segoe UI", 11, "bold"),
            text_color=Config.TEXT_MAIN
        )
        self.selected_count_lbl.grid(row=0, column=0, sticky="w")

        btn_cancel = ctk.CTkButton(
            footer_frame,
            text="Tutup",
            font=("Segoe UI", 11, "bold"),
            height=34,
            width=85,
            corner_radius=7,
            fg_color=Config.SECONDARY_BTN,
            hover_color=Config.SECONDARY_HOVER,
            text_color=Config.SECONDARY_TEXT,
            command=self.destroy
        )
        btn_cancel.grid(row=0, column=1, padx=(0, 8), sticky="e")

        btn_submit = ctk.CTkButton(
            footer_frame,
            text="📥 Masukkan ke Batch Queue",
            font=("Segoe UI", 11, "bold"),
            height=34,
            width=210,
            corner_radius=7,
            fg_color=Config.BTN_PRIMARY_BG,
            hover_color=Config.BTN_PRIMARY_HOVER,
            text_color=Config.BTN_PRIMARY_TEXT,
            command=self._submit_selection
        )
        btn_submit.grid(row=0, column=2, sticky="e")

    def _populate_entries(self):
        for idx, entry in enumerate(self.entries):
            entry_id = str(entry.get("id") or idx)
            var = ctk.BooleanVar(value=True)  # Default checked
            var.trace_add("write", lambda *_: self._update_counter())
            self.item_vars[entry_id] = var

            dur_sec = entry.get("duration", 0)
            dur_str = f"{int(dur_sec)//60}:{int(dur_sec)%60:02d}" if dur_sec else "--:--"

            row_frame = ctk.CTkFrame(self.list_frame, fg_color="transparent")
            row_frame.grid(row=idx, column=0, columnspan=3, sticky="ew", padx=8, pady=3)
            row_frame.grid_columnconfigure(1, weight=1)

            cb = ctk.CTkCheckBox(
                row_frame,
                text="",
                variable=var,
                width=24,
                checkbox_width=18,
                checkbox_height=18,
                corner_radius=4,
                border_width=1,
                border_color=Config.CARD_BORDER,
                fg_color=Config.BTN_PRIMARY_BG,
                hover_color=Config.BTN_PRIMARY_HOVER
            )
            cb.grid(row=0, column=0, padx=(4, 8), sticky="w")

            title_txt = f"{entry.get('index', idx+1):02d}. {entry.get('title', 'Unknown Title')}"
            lbl = ctk.CTkLabel(
                row_frame,
                text=title_txt,
                font=("Segoe UI", 11),
                text_color=Config.TEXT_MAIN,
                anchor="w"
            )
            lbl.grid(row=0, column=1, sticky="w")

            dur_lbl = ctk.CTkLabel(
                row_frame,
                text=dur_str,
                font=("Consolas", 10),
                text_color=Config.TEXT_MUTED
            )
            dur_lbl.grid(row=0, column=2, padx=(8, 4), sticky="e")

            self.entry_widgets.append((row_frame, entry))

    def _filter_items(self):
        query = self.search_var.get().strip().lower()
        for row_frame, entry in self.entry_widgets:
            title = (entry.get("title") or "").lower()
            if not query or query in title:
                row_frame.grid()
            else:
                row_frame.grid_remove()

    def _select_all(self):
        for var in self.item_vars.values():
            var.set(True)

    def _deselect_all(self):
        for var in self.item_vars.values():
            var.set(False)

    def _invert_selection(self):
        for var in self.item_vars.values():
            var.set(not var.get())

    def _update_counter(self):
        selected = sum(1 for v in self.item_vars.values() if v.get())
        total = len(self.item_vars)
        if hasattr(self, "selected_count_lbl"):
            self.selected_count_lbl.configure(text=f"✓ {selected} dari {total} trek dipilih")

    def _submit_selection(self):
        selected_entries = []
        for idx, entry in enumerate(self.entries):
            entry_id = str(entry.get("id") or idx)
            var = self.item_vars.get(entry_id)
            if var and var.get():
                selected_entries.append(entry)

        if self.on_submit:
            self.on_submit(selected_entries)
        self.destroy()

