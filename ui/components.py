import customtkinter as ctk

class InfoPanel(ctk.CTkFrame):
    """Komponen untuk menampilkan informasi/preview video atau playlist."""
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        
        # Grid layout untuk info panel
        self.grid_columnconfigure(1, weight=1)
        
        # Placeholder untuk Thumbnail (sementara menggunakan frame abu-abu)
        self.thumbnail_label = ctk.CTkLabel(
            self, width=160, height=90, fg_color="#2b2b2b", text="No Thumbnail"
        )
        self.thumbnail_label.grid(row=0, column=0, rowspan=4, padx=10, pady=10, sticky="nsew")
        
        # Label Informasi
        self.title_label = ctk.CTkLabel(self, text="Judul: -", font=("Arial", 13, "bold"), anchor="w")
        self.title_label.grid(row=0, column=1, padx=10, pady=(10, 2), sticky="w")
        
        self.channel_label = ctk.CTkLabel(self, text="Channel: -", anchor="w")
        self.channel_label.grid(row=1, column=1, padx=10, pady=2, sticky="w")
        
        self.duration_label = ctk.CTkLabel(self, text="Durasi: -", anchor="w")
        self.duration_label.grid(row=2, column=1, padx=10, pady=2, sticky="w")
        
        self.count_label = ctk.CTkLabel(self, text="Jumlah Video: -", anchor="w")
        self.count_label.grid(row=3, column=1, padx=10, pady=(2, 10), sticky="w")


class LogArea(ctk.CTkFrame):
    """Komponen untuk menampilkan log output dari proses yt-dlp."""
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        # Label Judul Log
        self.label = ctk.CTkLabel(self, text="Output Log", font=("Arial", 12, "bold"))
        self.label.grid(row=0, column=0, padx=10, pady=(5, 0), sticky="w")
        
        # Textbox untuk Log (Read-Only secara default)
        self.text_area = ctk.CTkTextbox(self, font=("Courier New", 12))
        self.text_area.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        self.text_area.configure(state="disabled")
        
    def write_log(self, message: str):
        """Fungsi pembantu untuk menulis log dari luar kelas."""
        self.text_area.configure(state="normal")
        self.text_area.insert("end", message + "\n")
        self.text_area.see("end")  # Auto-scroll ke paling bawah
        self.text_area.configure(state="disabled")