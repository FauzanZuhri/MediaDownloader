import os
import threading
import customtkinter as ctk
from tkinter import filedialog, messagebox
from core.config import Config
from core.settings import SettingsManager, ACCENT_PRESETS, NAMING_PRESETS
from core.updater import YtdlpUpdater
from core.archive_manager import ArchiveManager
from ui.archive_modal import ArchiveModal
from ui.components import CardFrame

class SettingsModal(ctk.CTkToplevel):
    """Jendela modal Pengaturan (Settings) untuk MediaDownloader v1.2.0."""
    def __init__(self, master, on_save_callback=None):
        super().__init__(master)
        
        self.on_save_callback = on_save_callback
        
        self.title("⚙️ Pengaturan MediaDownloader")
        self.geometry("680x560")
        self.minsize(620, 500)
        self.transient(master)
        self.grab_set()
        self.configure(fg_color=Config.BG_COLOR)
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        # Load current settings into working copy
        self._current_settings = dict(SettingsManager.load())
        self._selected_accent = self._current_settings.get("accent_name", "Indigo")
        
        self._create_widgets()
        self.after(50, self._center_window)

    def _center_window(self):
        self.update_idletasks()
        w = self.winfo_width()
        h = self.winfo_height()
        master_x = self.master.winfo_x()
        master_y = self.master.winfo_y()
        master_w = self.master.winfo_width()
        master_h = self.master.winfo_height()
        x = master_x + (master_w - w) // 2
        y = master_y + (master_h - h) // 2
        self.geometry(f"+{x}+{y}")

    def _create_widgets(self):
        # 1. Header Bar
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, padx=24, pady=(18, 10), sticky="ew")
        header.grid_columnconfigure(0, weight=1)
        
        title_lbl = ctk.CTkLabel(
            header,
            text="⚙️ Pengaturan Aplikasi",
            font=("Segoe UI", 18, "bold"),
            text_color=Config.TEXT_MAIN
        )
        title_lbl.grid(row=0, column=0, sticky="w")
        
        subtitle_lbl = ctk.CTkLabel(
            header,
            text="Kelola lokasi unduhan, format nama file, tema visual, dan engine yt-dlp",
            font=("Segoe UI", 11),
            text_color=Config.TEXT_MUTED
        )
        subtitle_lbl.grid(row=1, column=0, sticky="w", pady=(2, 0))

        # 2. Segmented Navigation Tabs
        self.tabview = ctk.CTkTabview(
            self,
            fg_color=Config.CARD_BG,
            segmented_button_fg_color="#0b0d13",
            segmented_button_selected_color=Config.ACCENT_COLOR,
            segmented_button_selected_hover_color=Config.ACCENT_HOVER,
            corner_radius=12
        )
        self.tabview.grid(row=1, column=0, padx=24, pady=(0, 16), sticky="nsew")
        
        self.tab_general = self.tabview.add("📁 Umum & Unduhan")
        self.tab_theme = self.tabview.add("🎨 Tampilan & Tema")
        self.tab_engine = self.tabview.add("🔄 yt-dlp Engine")
        self.tab_archive = self.tabview.add("🗄️ Cache & Arsip")

        self._build_general_tab()
        self._build_theme_tab()
        self._build_engine_tab()
        self._build_archive_tab()

        # 3. Footer Bar with Save & Cancel Buttons
        footer = ctk.CTkFrame(self, fg_color="transparent")
        footer.grid(row=2, column=0, padx=24, pady=(0, 18), sticky="ew")
        footer.grid_columnconfigure(0, weight=1)
        
        self.status_lbl = ctk.CTkLabel(
            footer,
            text="",
            font=("Segoe UI", 11),
            text_color=Config.SUCCESS_COLOR
        )
        self.status_lbl.grid(row=0, column=0, sticky="w")
        
        cancel_btn = ctk.CTkButton(
            footer,
            text="Batal",
            width=90,
            height=34,
            corner_radius=8,
            font=("Segoe UI", 11),
            fg_color="#202636",
            hover_color="#2c354a",
            command=self.destroy
        )
        cancel_btn.grid(row=0, column=1, padx=(0, 8), sticky="e")
        
        save_btn = ctk.CTkButton(
            footer,
            text="💾 Simpan Pengaturan",
            width=150,
            height=34,
            corner_radius=8,
            font=("Segoe UI", 11, "bold"),
            fg_color=Config.ACCENT_COLOR,
            hover_color=Config.ACCENT_HOVER,
            command=self._save_settings
        )
        save_btn.grid(row=0, column=2, sticky="e")

    # -------------------------------------------------------------------------
    # TAB 1: UMUM & UNDUHAN
    # -------------------------------------------------------------------------
    def _build_general_tab(self):
        container = self.tab_general
        container.grid_columnconfigure(0, weight=1)
        
        # Section A: Folder Unduhan Default
        sec1_lbl = ctk.CTkLabel(
            container,
            text="📂 Folder Unduhan Default Permanen",
            font=("Segoe UI", 12, "bold"),
            text_color=Config.TEXT_MAIN,
            anchor="w"
        )
        sec1_lbl.pack(fill="x", padx=12, pady=(12, 4))
        
        desc1_lbl = ctk.CTkLabel(
            container,
            text="Folder default yang otomatis digunakan setiap kali aplikasi dibuka:",
            font=("Segoe UI", 11),
            text_color=Config.TEXT_MUTED,
            anchor="w"
        )
        desc1_lbl.pack(fill="x", padx=12, pady=(0, 6))
        
        folder_frame = ctk.CTkFrame(container, fg_color="transparent")
        folder_frame.pack(fill="x", padx=12, pady=(0, 16))
        folder_frame.grid_columnconfigure(0, weight=1)
        
        self.folder_entry = ctk.CTkEntry(
            folder_frame,
            font=("Segoe UI", 11),
            height=34,
            corner_radius=8,
            fg_color="#0b0d13",
            border_color=Config.CARD_BORDER
        )
        self.folder_entry.grid(row=0, column=0, padx=(0, 8), sticky="ew")
        self.folder_entry.insert(0, self._current_settings.get("download_dir", Config.DEFAULT_DOWNLOAD_DIR))
        
        browse_btn = ctk.CTkButton(
            folder_frame,
            text="📂 Cari Folder",
            width=100,
            height=34,
            corner_radius=8,
            font=("Segoe UI", 11, "bold"),
            fg_color="#202636",
            hover_color="#2c354a",
            command=self._browse_dir
        )
        browse_btn.grid(row=0, column=1, sticky="e")
        
        # Section B: Pola Template Penamaan File
        sec2_lbl = ctk.CTkLabel(
            container,
            text="🏷️ Format Penamaan File Otomatis",
            font=("Segoe UI", 12, "bold"),
            text_color=Config.TEXT_MAIN,
            anchor="w"
        )
        sec2_lbl.pack(fill="x", padx=12, pady=(6, 4))
        
        desc2_lbl = ctk.CTkLabel(
            container,
            text="Pilih struktur nama file hasil unduhan yang paling sesuai dengan selera Anda:",
            font=("Segoe UI", 11),
            text_color=Config.TEXT_MUTED,
            anchor="w"
        )
        desc2_lbl.pack(fill="x", padx=12, pady=(0, 8))
        
        preset_values = [p[0] for p in NAMING_PRESETS]
        preset_labels = {p[0]: p[1] for p in NAMING_PRESETS}
        
        current_tpl = self._current_settings.get("naming_template", "{title}")
        
        self.template_menu = ctk.CTkOptionMenu(
            container,
            values=[preset_labels[k] for k in preset_values],
            font=("Segoe UI", 11),
            height=34,
            corner_radius=8,
            fg_color="#202636",
            button_color="#2a3349",
            button_hover_color="#36415d",
            command=self._on_template_change
        )
        self.template_menu.pack(fill="x", padx=12, pady=(0, 10))
        
        # Set selected label
        selected_label = preset_labels.get(current_tpl, preset_labels["{title}"])
        self.template_menu.set(selected_label)
        
        # Live Preview Box
        self.preview_box = ctk.CTkFrame(
            container,
            fg_color="#0b0d13",
            corner_radius=8,
            border_width=1,
            border_color=Config.CARD_BORDER
        )
        self.preview_box.pack(fill="x", padx=12, pady=(4, 12))
        
        preview_title = ctk.CTkLabel(
            self.preview_box,
            text="Preview Contoh Nama File:",
            font=("Segoe UI", 10, "bold"),
            text_color=Config.ACCENT_COLOR
        )
        preview_title.pack(anchor="w", padx=12, pady=(8, 2))
        
        self.preview_text = ctk.CTkLabel(
            self.preview_box,
            text="",
            font=("Consolas", 11),
            text_color="#38bdf8"
        )
        self.preview_text.pack(anchor="w", padx=12, pady=(0, 8))
        self._update_naming_preview(current_tpl)

    def _on_template_change(self, choice_label):
        for pattern, label in NAMING_PRESETS:
            if label == choice_label:
                self._update_naming_preview(pattern)
                break

    def _update_naming_preview(self, pattern):
        examples = {
            "{title}": "Alan Walker - Faded.mp3",
            "{artist} - {title}": "Alan Walker - Faded.mp3",
            "{title} [{id}]": "Faded [60ItHLz5WEA].mp3",
            "{index}. {title}": "01. Faded.mp3  (atau 'Faded.mp3' jika single)",
        }
        self.preview_text.configure(text=examples.get(pattern, "Faded.mp3"))

    def _browse_dir(self):
        chosen = filedialog.askdirectory(parent=self, initialdir=self.folder_entry.get())
        if chosen:
            self.folder_entry.delete(0, "end")
            self.folder_entry.insert(0, chosen)

    # -------------------------------------------------------------------------
    # TAB 2: TAMPILAN & TEMA
    # -------------------------------------------------------------------------
    def _build_theme_tab(self):
        container = self.tab_theme
        container.grid_columnconfigure(0, weight=1)
        
        theme_title = ctk.CTkLabel(
            container,
            text="🎨 Warna Aksen Aplikasi",
            font=("Segoe UI", 12, "bold"),
            text_color=Config.TEXT_MAIN,
            anchor="w"
        )
        theme_title.pack(fill="x", padx=12, pady=(14, 4))
        
        theme_desc = ctk.CTkLabel(
            container,
            text="Pilih warna aksen sorotan utama untuk tombol, status bar, dan badge:",
            font=("Segoe UI", 11),
            text_color=Config.TEXT_MUTED,
            anchor="w"
        )
        theme_desc.pack(fill="x", padx=12, pady=(0, 14))
        
        self.swatch_frame = ctk.CTkFrame(container, fg_color="transparent")
        self.swatch_frame.pack(fill="x", padx=12, pady=(0, 16))
        
        self.swatch_buttons = {}
        for idx, (name, colors) in enumerate(ACCENT_PRESETS.items()):
            btn = ctk.CTkButton(
                self.swatch_frame,
                text=f"● {name}",
                font=("Segoe UI", 11, "bold"),
                width=95,
                height=36,
                corner_radius=8,
                fg_color=colors["accent"] if name == self._selected_accent else "#181d28",
                hover_color=colors["hover"],
                text_color="#ffffff" if name == self._selected_accent else colors["accent"],
                border_width=2 if name == self._selected_accent else 1,
                border_color=colors["accent"],
                command=lambda n=name: self._select_accent(n)
            )
            btn.grid(row=idx // 3, column=idx % 3, padx=6, pady=6, sticky="ew")
            self.swatch_buttons[name] = btn
            self.swatch_frame.grid_columnconfigure(idx % 3, weight=1)

    def _select_accent(self, name: str):
        self._selected_accent = name
        for btn_name, btn in self.swatch_buttons.items():
            preset = ACCENT_PRESETS[btn_name]
            if btn_name == name:
                btn.configure(
                    fg_color=preset["accent"],
                    text_color="#ffffff",
                    border_width=2,
                    border_color="#ffffff"
                )
            else:
                btn.configure(
                    fg_color="#181d28",
                    text_color=preset["accent"],
                    border_width=1,
                    border_color=preset["accent"]
                )

    # -------------------------------------------------------------------------
    # TAB 3: YT-DLP CORE ENGINE
    # -------------------------------------------------------------------------
    def _build_engine_tab(self):
        container = self.tab_engine
        container.grid_columnconfigure(0, weight=1)
        
        eng_card = CardFrame(container)
        eng_card.pack(fill="x", padx=12, pady=(14, 12))
        eng_card.grid_columnconfigure(1, weight=1)
        
        ctk.CTkLabel(
            eng_card,
            text="⚡ Core Downloader Engine:",
            font=("Segoe UI", 12, "bold"),
            text_color=Config.ACCENT_COLOR
        ).grid(row=0, column=0, padx=14, pady=(12, 4), sticky="w")
        
        curr_ver = YtdlpUpdater.get_current_version()
        self.ver_lbl = ctk.CTkLabel(
            eng_card,
            text=f"yt-dlp versi: {curr_ver}",
            font=("Consolas", 12),
            text_color=Config.TEXT_MAIN
        )
        self.ver_lbl.grid(row=0, column=1, padx=14, pady=(12, 4), sticky="e")
        
        desc_lbl = ctk.CTkLabel(
            eng_card,
            text="Pembaruan rutin yt-dlp memastikan aplikasi tetap dapat mengunduh video saat YouTube mengubah sistem tantangan proteksinya.",
            font=("Segoe UI", 11),
            text_color=Config.TEXT_MUTED,
            wraplength=520,
            justify="left"
        )
        desc_lbl.grid(row=1, column=0, columnspan=2, padx=14, pady=(0, 12), sticky="w")
        
        # Action Buttons & Status
        action_row = ctk.CTkFrame(container, fg_color="transparent")
        action_row.pack(fill="x", padx=12, pady=(0, 10))
        action_row.grid_columnconfigure(0, weight=1)
        
        self.update_status_lbl = ctk.CTkLabel(
            action_row,
            text="Status: Siap memeriksa pembaruan",
            font=("Segoe UI", 11),
            text_color=Config.TEXT_MUTED,
            anchor="w"
        )
        self.update_status_lbl.grid(row=0, column=0, sticky="w")
        
        self.check_btn = ctk.CTkButton(
            action_row,
            text="🔍 Periksa & Update",
            font=("Segoe UI", 11, "bold"),
            width=140,
            height=34,
            corner_radius=8,
            fg_color="#202636",
            hover_color="#2c354a",
            command=self._start_update_thread
        )
        self.check_btn.grid(row=0, column=1, sticky="e")
        
        # Log Output yt-dlp update
        self.update_log_box = ctk.CTkTextbox(
            container,
            font=("Consolas", 10),
            fg_color="#0b0d13",
            text_color="#94a3b8",
            corner_radius=8,
            border_width=1,
            border_color="#1e2433",
            height=85
        )
        self.update_log_box.pack(fill="x", padx=12, pady=(0, 12))
        self.update_log_box.configure(state="disabled")

    def _start_update_thread(self):
        self.check_btn.configure(state="disabled", text="⏳ Memeriksa...")
        self.update_status_lbl.configure(text="Menghubungi PyPI...")
        threading.Thread(target=self._run_engine_update, daemon=True).start()

    def _log_update(self, msg: str):
        self.after(0, self._append_log, msg)

    def _append_log(self, msg: str):
        self.update_log_box.configure(state="normal")
        self.update_log_box.insert("end", msg + "\n")
        self.update_log_box.see("end")
        self.update_log_box.configure(state="disabled")

    def _run_engine_update(self):
        curr, latest, has_update, err = YtdlpUpdater.check_latest_version()
        if err:
            self._log_update(f"[Error] Gagal cek versi: {err}")
            self.after(0, lambda: self.update_status_lbl.configure(text="Gagal memeriksa pembaruan."))
            self.after(0, lambda: self.check_btn.configure(state="normal", text="🔍 Periksa & Update"))
            return
            
        self._log_update(f"[Info] Versi saat ini: {curr}")
        self._log_update(f"[Info] Versi terbaru: {latest}")
        
        if not has_update:
            self._log_update("[Info] yt-dlp sudah versi paling mutakhir!")
            self.after(0, lambda: self.update_status_lbl.configure(text="✅ Versi sudah paling mutakhir."))
            self.after(0, lambda: self.check_btn.configure(state="normal", text="🔍 Periksa & Update"))
            return
            
        self._log_update(f"[Info] Versi baru ditemukan ({latest})! Memulai upgrade...")
        self.after(0, lambda: self.update_status_lbl.configure(text="Sedang mengunduh & memperbarui..."))
        
        success, msg = YtdlpUpdater.run_update(log_callback=self._log_update)
        if success:
            new_ver = YtdlpUpdater.get_current_version()
            self.after(0, lambda: self.ver_lbl.configure(text=f"yt-dlp versi: {new_ver}"))
            self.after(0, lambda: self.update_status_lbl.configure(text="✅ Berhasil diperbarui!"))
        else:
            self.after(0, lambda: self.update_status_lbl.configure(text=f"❌ Gagal: {msg}"))
            
        self.after(0, lambda: self.check_btn.configure(state="normal", text="🔍 Periksa & Update"))

    # -------------------------------------------------------------------------
    # TAB 4: CACHE & ARSIP
    # -------------------------------------------------------------------------
    def _build_archive_tab(self):
        container = self.tab_archive
        container.grid_columnconfigure(0, weight=1)
        
        card = CardFrame(container)
        card.pack(fill="x", padx=12, pady=(14, 12))
        card.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(
            card,
            text="🗄️ Status Arsip Pencegah Duplikasi:",
            font=("Segoe UI", 12, "bold"),
            text_color=Config.ACCENT_COLOR
        ).grid(row=0, column=0, padx=14, pady=(12, 4), sticky="w")
        
        self.archive_stat_lbl = ctk.CTkLabel(
            card,
            text="",
            font=("Segoe UI", 12),
            text_color=Config.TEXT_MAIN
        )
        self.archive_stat_lbl.grid(row=1, column=0, padx=14, pady=(0, 6), sticky="w")
        self._refresh_archive_stats()
        
        ctk.CTkLabel(
            card,
            text="File riwayat: download_archive.txt. Menyimpan ID unik video yang pernah berhasil diunduh.",
            font=("Segoe UI", 10),
            text_color=Config.TEXT_MUTED
        ).grid(row=2, column=0, padx=14, pady=(0, 12), sticky="w")
        
        btn_row = ctk.CTkFrame(container, fg_color="transparent")
        btn_row.pack(fill="x", padx=12, pady=(4, 0))
        btn_row.grid_columnconfigure(0, weight=1)
        
        open_mgr_btn = ctk.CTkButton(
            btn_row,
            text="📋 Buka Manajer Arsip Lengkap",
            font=("Segoe UI", 11, "bold"),
            height=34,
            corner_radius=8,
            fg_color="#202636",
            hover_color="#2c354a",
            command=self._open_archive_manager
        )
        open_mgr_btn.grid(row=0, column=0, sticky="w")
        
        clear_quick_btn = ctk.CTkButton(
            btn_row,
            text="🗑️ Kosongkan Arsip",
            font=("Segoe UI", 11, "bold"),
            height=34,
            corner_radius=8,
            fg_color=Config.DANGER_COLOR,
            hover_color=Config.DANGER_HOVER,
            command=self._quick_clear_archive
        )
        clear_quick_btn.grid(row=0, column=1, sticky="e")

    def _refresh_archive_stats(self):
        count = ArchiveManager.get_count()
        self.archive_stat_lbl.configure(text=f"Saat ini terdapat {count} item lagu/video yang pernah diunduh.")

    def _open_archive_manager(self):
        ArchiveModal(self, on_change_callback=self._refresh_archive_stats)

    def _quick_clear_archive(self):
        confirm = messagebox.askyesno(
            "Konfirmasi Kosongkan Arsip",
            "Apakah Anda yakin ingin mengosongkan seluruh riwayat arsip unduhan?",
            parent=self
        )
        if confirm:
            ArchiveManager.clear_archive()
            self._refresh_archive_stats()
            messagebox.showinfo("Berhasil", "Arsip unduhan telah dikosongkan.", parent=self)

    # -------------------------------------------------------------------------
    # SIMPAN PENGATURAN
    # -------------------------------------------------------------------------
    def _save_settings(self):
        chosen_dir = self.folder_entry.get().strip()
        if not chosen_dir or not os.path.isdir(chosen_dir):
            messagebox.showwarning("Peringatan", "Folder unduhan tidak valid atau tidak ditemukan!", parent=self)
            return
            
        selected_label = self.template_menu.get()
        chosen_pattern = "{title}"
        for pattern, label in NAMING_PRESETS:
            if label == selected_label:
                chosen_pattern = pattern
                break

        new_settings = {
            "download_dir": chosen_dir,
            "naming_template": chosen_pattern,
            "accent_name": self._selected_accent,
        }
        
        SettingsManager.save(new_settings)
        self.status_lbl.configure(text="✅ Pengaturan berhasil disimpan!")
        
        if self.on_save_callback:
            self.on_save_callback(new_settings)
            
        self.after(500, self.destroy)
