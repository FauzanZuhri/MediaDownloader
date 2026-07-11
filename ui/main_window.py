import customtkinter as ctk
from tkinter import filedialog
import threading
import requests
from io import BytesIO
from PIL import Image
from core.config import Config
from ui.components import InfoPanel, LogArea
from core.downloader import YtdlpManager

class MainWindow(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title(Config.APP_TITLE)
        self.geometry(Config.WINDOW_SIZE)
        ctk.set_appearance_mode(Config.THEME)
        ctk.set_default_color_theme(Config.COLOR_THEME)
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(8, weight=1)
        
        self._create_widgets()
        
        self.downloader = YtdlpManager(log_callback=self.log_area.write_log)
        
        # BINDING EVENT: Memicu preview saat user menekan Enter atau klik di luar text box
        self.url_entry.bind("<Return>", lambda e: self._start_preview_thread())
        self.url_entry.bind("<FocusOut>", lambda e: self._start_preview_thread())
        
    def _create_widgets(self):
        # ... (Gunakan widget dari Tahap 2 & 3, pastikan nama komponennya sama) ...
        self.header_label = ctk.CTkLabel(self, text=Config.APP_TITLE, font=("Arial", 20, "bold"))
        self.header_label.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="w")
        
        self.url_label = ctk.CTkLabel(self, text="YouTube URL / Playlist URL:", font=("Arial", 12, "bold"))
        self.url_label.grid(row=1, column=0, padx=20, pady=(10, 2), sticky="w")
        
        self.url_entry = ctk.CTkEntry(self, placeholder_text="Paste link YouTube lalu tekan Enter...")
        self.url_entry.grid(row=2, column=0, padx=20, pady=(0, 10), sticky="ew")
        
        self.folder_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.folder_frame.grid(row=3, column=0, padx=20, pady=5, sticky="ew")
        self.folder_frame.grid_columnconfigure(0, weight=1)
        
        self.path_entry = ctk.CTkEntry(self.folder_frame)
        self.path_entry.grid(row=0, column=0, padx=(0, 10), sticky="ew")
        self.path_entry.insert(0, Config.DEFAULT_DOWNLOAD_DIR)
        
        self.browse_btn = ctk.CTkButton(self.folder_frame, text="Browse", width=100, command=self._browse_folder)
        self.browse_btn.grid(row=0, column=1, sticky="e")
        
        self.settings_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.settings_frame.grid(row=4, column=0, padx=20, pady=10, sticky="ew")
        
        self.format_var = ctk.StringVar(value="MP3")
        self.mp3_radio = ctk.CTkRadioButton(self.settings_frame, text="MP3 (Audio)", variable=self.format_var, value="MP3")
        self.mp3_radio.grid(row=0, column=0, padx=(0, 20), sticky="w")
        self.mp4_radio = ctk.CTkRadioButton(self.settings_frame, text="MP4 (Video)", variable=self.format_var, value="MP4")
        self.mp4_radio.grid(row=0, column=1, padx=20, sticky="w")
        
        self.quality_dropdown = ctk.CTkComboBox(self.settings_frame, values=["Best Audio", "128kbps", "192kbps", "320kbps"])
        self.quality_dropdown.grid(row=0, column=2, padx=20, sticky="w")
        
        self.options_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.options_frame.grid(row=5, column=0, padx=20, pady=5, sticky="ew")
        
        self.meta_cb = ctk.CTkCheckBox(self.options_frame, text="Embed Metadata")
        self.meta_cb.select()
        self.meta_cb.grid(row=0, column=0, padx=(0, 20), pady=5, sticky="w")
        
        self.thumb_cb = ctk.CTkCheckBox(self.options_frame, text="Embed Thumbnail")
        self.thumb_cb.select()
        self.thumb_cb.grid(row=0, column=1, padx=20, pady=5, sticky="w")
        
        self.archive_cb = ctk.CTkCheckBox(self.options_frame, text="Skip Existing (Archive Mode)")
        self.archive_cb.select()
        self.archive_cb.grid(row=1, column=0, padx=(0, 20), pady=5, sticky="w")
        
        self.info_panel = InfoPanel(self)
        self.info_panel.grid(row=6, column=0, padx=20, pady=10, sticky="ew")
        
        self.progress_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.progress_frame.grid(row=7, column=0, padx=20, pady=5, sticky="ew")
        self.progress_frame.grid_columnconfigure(0, weight=1)
        
        self.progress_bar = ctk.CTkProgressBar(self.progress_frame)
        self.progress_bar.grid(row=0, column=0, columnspan=3, pady=(0, 5), sticky="ew")
        self.progress_bar.set(0.0)
        
        self.status_label = ctk.CTkLabel(self.progress_frame, text="Status: Idle", font=("Arial", 11))
        self.status_label.grid(row=1, column=0, sticky="w")
        
        self.speed_label = ctk.CTkLabel(self.progress_frame, text="Speed: 0 KB/s", font=("Arial", 11))
        self.speed_label.grid(row=1, column=1, padx=20, sticky="w")
        
        self.eta_label = ctk.CTkLabel(self.progress_frame, text="ETA: 00:00", font=("Arial", 11))
        self.eta_label.grid(row=1, column=2, sticky="e")
        
        self.log_area = LogArea(self)
        self.log_area.grid(row=8, column=0, padx=20, pady=10, sticky="nsew")
        
        self.btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.btn_frame.grid(row=9, column=0, padx=20, pady=(5, 20), sticky="ew")
        
        self.download_btn = ctk.CTkButton(self.btn_frame, text="Download", width=120, fg_color="#1f538d", command=self._start_download_thread)
        self.download_btn.grid(row=0, column=0, padx=(0, 10))
        
        self.cancel_btn = ctk.CTkButton(self.btn_frame, text="Cancel", width=120, fg_color="#a83232", hover_color="#822222")
        self.cancel_btn.grid(row=0, column=1, padx=10)
        
        self.open_folder_btn = ctk.CTkButton(self.btn_frame, text="Open Folder", width=120, fg_color="#333333", hover_color="#444444")
        self.open_folder_btn.grid(row=0, column=2, padx=10)

    # ==========================================
    # LOGIC BARU UNTUK FITUR PREVIEW (TAHAP 5)
    # ==========================================
    def _start_preview_thread(self):
        """Menjalankan pengambilan metadata di thread terpisah agar UI tidak lag saat mengetik."""
        url = self.url_entry.get().strip()
        if not url:
            return
            
        self.status_label.configure(text="Status: Mengambil preview...")
        preview_thread = threading.Thread(target=self._load_preview_data, args=(url,), daemon=True)
        preview_thread.start()

    def _load_preview_data(self, url):
        info = self.downloader.fetch_metadata(url)
        if not info:
            self.status_label.configure(text="Status: Gagal memuat info.")
            return

        # Mengurai data info dari yt-dlp
        title = info.get('title', 'Unknown Title')
        channel = info.get('uploader', 'Unknown Channel')
        
        # Mengecek apakah ini playlist atau single video
        is_playlist = 'entries' in info
        
        if is_playlist:
            duration_text = "N/A (Playlist)"
            video_count = len(info.get('entries', []))
        else:
            duration = info.get('duration', 0)
            # Konversi durasi detik ke format Menit:Detik
            duration_text = f"{duration // 60}:{duration % 60:02d}"
            video_count = "1 (Single Video)"

        # Ambil URL Thumbnail teratas
        thumbnails = info.get('thumbnails', [])
        thumb_url = thumbnails[-1]['url'] if thumbnails else None

        # Update teks di UI InfoPanel
        self.info_panel.title_label.configure(text=f"Judul: {title[:50]}...")
        self.info_panel.channel_label.configure(text=f"Channel: {channel}")
        self.info_panel.duration_label.configure(text=f"Durasi: {duration_text}")
        self.info_panel.count_label.configure(text=f"Jumlah Video: {video_count}")
        self.status_label.configure(text="Status: Preview siap.")

        # Update Gambar Thumbnail ke UI jika ada
        if thumb_url:
            try:
                response = requests.get(thumb_url, timeout=5)
                img_data = Image.open(BytesIO(response.content))
                
                # Bungkus dengan CTkImage agar kompatibel dengan CustomTkinter dan auto-scale
                ctk_image = ctk.CTkImage(light_image=img_data, dark_image=img_data, size=(160, 90))
                
                # Pasang ke label thumbnail di komponen info_panel
                self.info_panel.thumbnail_label.configure(image=ctk_image, text="")
            except Exception as e:
                self.info_panel.thumbnail_label.configure(text="No Image")

    def _start_download_thread(self):
        url = self.url_entry.get()
        output_dir = self.path_entry.get()
        format_type = self.format_var.get()
        
        self.status_label.configure(text="Status: Downloading...")
        download_thread = threading.Thread(
            target=self.downloader.download,
            args=(url, output_dir, format_type),
            daemon=True
        )
        download_thread.start()

    def _browse_folder(self):
        selected_dir = filedialog.askdirectory(initialdir=self.path_entry.get())
        if selected_dir:
            self.path_entry.delete(0, "end")
            self.path_entry.insert(0, selected_dir)