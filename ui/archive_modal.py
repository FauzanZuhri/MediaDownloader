import os
import customtkinter as ctk
from tkinter import filedialog, messagebox
from core.config import Config
from core.archive_manager import ArchiveManager
from ui.components import CardFrame

class ArchiveModal(ctk.CTkToplevel):
    """Jendela modal untuk mengelola daftar riwayat unduhan (download_archive.txt)."""
    def __init__(self, master, on_change_callback=None):
        super().__init__(master)
        
        self.on_change_callback = on_change_callback
        
        self.title("🗄️ Manajer Cache & Arsip Unduhan")
        self.geometry("640x520")
        self.minsize(560, 460)
        self.transient(master)
        self.grab_set()  # Modal lock
        self.configure(fg_color=Config.BG_COLOR)
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        self._all_entries = []
        self._create_widgets()
        self._load_entries()
        
        # Center window
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
        # 1. Header
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.grid(row=0, column=0, padx=20, pady=(18, 12), sticky="ew")
        header_frame.grid_columnconfigure(0, weight=1)
        
        title_label = ctk.CTkLabel(
            header_frame,
            text="🗄️ Manajer Riwayat Arsip",
            font=("Segoe UI", 18, "bold"),
            text_color=Config.TEXT_MAIN
        )
        title_label.grid(row=0, column=0, sticky="w")
        
        self.subtitle_label = ctk.CTkLabel(
            header_frame,
            text="Daftar video yang telah diunduh untuk mencegah duplikasi (download_archive.txt)",
            font=("Segoe UI", 11),
            text_color=Config.TEXT_MUTED
        )
        self.subtitle_label.grid(row=1, column=0, sticky="w", pady=(2, 0))
        
        # 2. Search & Action Bar
        action_bar = ctk.CTkFrame(self, fg_color="transparent")
        action_bar.grid(row=1, column=0, padx=20, pady=(0, 10), sticky="ew")
        action_bar.grid_columnconfigure(0, weight=1)
        
        self.search_entry = ctk.CTkEntry(
            action_bar,
            placeholder_text="🔍 Cari ID video atau extractor...",
            font=("Segoe UI", 11),
            height=34,
            corner_radius=8,
            fg_color="#0b0d13",
            border_color=Config.CARD_BORDER
        )
        self.search_entry.grid(row=0, column=0, padx=(0, 8), sticky="ew")
        self.search_entry.bind("<KeyRelease>", lambda e: self._filter_entries())
        
        self.export_btn = ctk.CTkButton(
            action_bar,
            text="📤 Backup",
            width=80,
            height=34,
            corner_radius=8,
            font=("Segoe UI", 11, "bold"),
            fg_color="#202636",
            hover_color="#2c354a",
            text_color=Config.TEXT_MAIN,
            command=self._export_archive
        )
        self.export_btn.grid(row=0, column=1, padx=(0, 6), sticky="e")
        
        self.clear_btn = ctk.CTkButton(
            action_bar,
            text="🗑️ Kosongkan",
            width=90,
            height=34,
            corner_radius=8,
            font=("Segoe UI", 11, "bold"),
            fg_color=Config.DANGER_COLOR,
            hover_color=Config.DANGER_HOVER,
            text_color="#ffffff",
            command=self._clear_all_archive
        )
        self.clear_btn.grid(row=0, column=2, sticky="e")

        # 3. Scrollable List of Entries
        self.list_container = ctk.CTkScrollableFrame(
            self,
            fg_color="#0b0d13",
            corner_radius=10,
            border_width=1,
            border_color=Config.CARD_BORDER
        )
        self.list_container.grid(row=2, column=0, padx=20, pady=(0, 16), sticky="nsew")
        self.list_container.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)
        
        # 4. Footer Bar
        footer = ctk.CTkFrame(self, fg_color="transparent")
        footer.grid(row=3, column=0, padx=20, pady=(0, 16), sticky="ew")
        footer.grid_columnconfigure(0, weight=1)
        
        self.count_badge = ctk.CTkLabel(
            footer,
            text="Total: 0 video diarsipkan",
            font=("Segoe UI", 11, "bold"),
            text_color=Config.TEXT_MUTED
        )
        self.count_badge.grid(row=0, column=0, sticky="w")
        
        close_btn = ctk.CTkButton(
            footer,
            text="Tutup",
            width=90,
            height=32,
            corner_radius=8,
            font=("Segoe UI", 11, "bold"),
            fg_color="#202636",
            hover_color="#2c354a",
            command=self.destroy
        )
        close_btn.grid(row=0, column=1, sticky="e")

    def _load_entries(self):
        self._all_entries = ArchiveManager.get_entries()
        self._render_items(self._all_entries)

    def _render_items(self, entries):
        for widget in self.list_container.winfo_children():
            widget.destroy()
            
        total = len(self._all_entries)
        visible = len(entries)
        if visible == total:
            self.count_badge.configure(text=f"Total: {total} video tersimpan dalam arsip")
        else:
            self.count_badge.configure(text=f"Menampilkan: {visible} dari {total} video")

        if not entries:
            empty_lbl = ctk.CTkLabel(
                self.list_container,
                text="📭 Arsip kosong atau tidak ada item yang cocok dengan pencarian.",
                font=("Segoe UI", 12),
                text_color=Config.TEXT_DIM,
                pady=40
            )
            empty_lbl.pack(fill="x", expand=True)
            return

        for idx, item in enumerate(entries):
            row = ctk.CTkFrame(
                self.list_container,
                fg_color="#141822" if idx % 2 == 0 else "#11151f",
                corner_radius=6,
                height=38
            )
            row.pack(fill="x", pady=2, padx=4)
            row.grid_columnconfigure(1, weight=1)
            
            # Platform Tag
            tag_frame = ctk.CTkFrame(row, fg_color="#202636", corner_radius=4)
            tag_frame.grid(row=0, column=0, padx=(8, 10), pady=6)
            tag_lbl = ctk.CTkLabel(
                tag_frame,
                text=item["extractor"].upper()[:10],
                font=("Segoe UI", 9, "bold"),
                text_color=Config.ACCENT_COLOR
            )
            tag_lbl.pack(padx=6, pady=2)
            
            # Video ID
            id_lbl = ctk.CTkLabel(
                row,
                text=item["id"],
                font=("Consolas", 11),
                text_color=Config.TEXT_MAIN,
                anchor="w"
            )
            id_lbl.grid(row=0, column=1, sticky="w")
            
            # Delete Button
            del_btn = ctk.CTkButton(
                row,
                text="✕ Hapus",
                width=65,
                height=26,
                font=("Segoe UI", 10, "bold"),
                fg_color="#281f25",
                hover_color=Config.DANGER_HOVER,
                text_color=Config.DANGER_COLOR,
                command=lambda e_id=item["id"]: self._delete_entry(e_id)
            )
            del_btn.grid(row=0, column=2, padx=8, pady=4, sticky="e")

    def _filter_entries(self):
        query = self.search_entry.get().strip().lower()
        if not query:
            self._render_items(self._all_entries)
            return
            
        filtered = [
            e for e in self._all_entries 
            if query in e["id"].lower() or query in e["extractor"].lower() or query in e["raw"].lower()
        ]
        self._render_items(filtered)

    def _delete_entry(self, entry_id: str):
        if ArchiveManager.remove_entry(entry_id):
            self._load_entries()
            if self.on_change_callback:
                self.on_change_callback()

    def _clear_all_archive(self):
        if not self._all_entries:
            return
            
        confirm = messagebox.askyesno(
            "Konfirmasi Kosongkan Arsip",
            "Apakah Anda yakin ingin menghapus seluruh riwayat unduhan di download_archive.txt?\n\nSetelah dikosongkan, lagu/video yang pernah diunduh akan dapat diunduh ulang tanpa dicegah sistem.",
            parent=self
        )
        if confirm:
            ArchiveManager.clear_archive()
            self._load_entries()
            if self.on_change_callback:
                self.on_change_callback()
            messagebox.showinfo("Berhasil", "Riwayat arsip berhasil dikosongkan.", parent=self)

    def _export_archive(self):
        dest = filedialog.asksaveasfilename(
            parent=self,
            title="Simpan Cadangan Arsip",
            initialfile="download_archive_backup.txt",
            defaultextension=".txt",
            filetypes=[("Text File", "*.txt"), ("All Files", "*.*")]
        )
        if dest:
            if ArchiveManager.export_archive(dest):
                messagebox.showinfo("Sukses", f"Arsip berhasil diekspor ke:\n{dest}", parent=self)
            else:
                messagebox.showerror("Gagal", "Gagal mengekspor file arsip.", parent=self)
