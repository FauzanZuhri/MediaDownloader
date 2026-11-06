import os
from typing import Optional, Callable
import customtkinter as ctk
from PIL import Image
from core.config import Config
from core.audio_player import AudioPlayer

class AudioPlayerBar(ctk.CTkFrame):
    """
    Floating Media Player Bar terintegrasi di bagian bawah workspace.
    Dilengkapi kontrol Play/Pause, Seekbar waktu interaktif, pengatur volume,
    serta penampil informasi judul & uploader/artis.
    """
    def __init__(self, master, on_close: Optional[Callable[[], None]] = None, **kwargs):
        kwargs.setdefault("fg_color", Config.CARD_BG_ELEVATED)
        kwargs.setdefault("corner_radius", 10)
        kwargs.setdefault("border_width", 1)
        kwargs.setdefault("border_color", Config.CARD_BORDER)
        kwargs.setdefault("height", 68)
        super().__init__(master, **kwargs)

        self.on_close_cb = on_close
        self._is_user_seeking = False
        self._current_file: Optional[str] = None
        self._duration_ms = 0

        # Inisialisasi engine audio native MCI
        self.player = AudioPlayer(
            on_position_change=self._on_audio_position_change,
            on_finished=self._on_audio_finished
        )

        self.grid_columnconfigure(0, weight=0)  # Left: Track Info (240px)
        self.grid_columnconfigure(1, weight=1)  # Center: Controls & Timeline (expand)
        self.grid_columnconfigure(2, weight=0)  # Right: Volume & Close (170px)
        self.grid_rowconfigure(0, weight=1)

        # ---------------------------------------------------------------------
        # 1. SISI KIRI: TRACK INFO & COVER ART
        # ---------------------------------------------------------------------
        self.left_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.left_frame.grid(row=0, column=0, padx=(12, 8), pady=8, sticky="w")

        # Mini cover frame
        self.cover_frame = ctk.CTkFrame(
            self.left_frame,
            width=44,
            height=44,
            corner_radius=6,
            fg_color=Config.INPUT_BG,
            border_width=1,
            border_color=Config.CARD_BORDER
        )
        self.cover_frame.pack(side="left", padx=(0, 10))
        self.cover_frame.pack_propagate(False)

        self.cover_label = ctk.CTkLabel(
            self.cover_frame,
            text="🎵",
            font=("Segoe UI", 16),
            text_color=Config.BTN_PRIMARY_BG
        )
        self.cover_label.pack(expand=True)

        # Track title & artist text
        self.meta_frame = ctk.CTkFrame(self.left_frame, fg_color="transparent")
        self.meta_frame.pack(side="left", fill="y", expand=True)

        self.title_label = ctk.CTkLabel(
            self.meta_frame,
            text="Tidak Ada Media Diputar",
            font=("Segoe UI", 11, "bold"),
            text_color=Config.TEXT_MAIN,
            anchor="w",
            wraplength=210
        )
        self.title_label.pack(anchor="w")

        self.artist_label = ctk.CTkLabel(
            self.meta_frame,
            text="Klik '▶️ Putar Sekarang' untuk memutar",
            font=("Segoe UI", 9),
            text_color=Config.TEXT_MUTED,
            anchor="w"
        )
        self.artist_label.pack(anchor="w")

        # ---------------------------------------------------------------------
        # 2. SISI TENGAH: KONTROL PLAYBACK & TIMELINE SEEKBAR
        # ---------------------------------------------------------------------
        self.center_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.center_frame.grid(row=0, column=1, padx=8, pady=6, sticky="ew")
        self.center_frame.grid_columnconfigure(0, weight=1)

        # Row A: Tombol Kontrol (Center Aligned)
        self.ctrl_btn_row = ctk.CTkFrame(self.center_frame, fg_color="transparent")
        self.ctrl_btn_row.pack(anchor="center", pady=(0, 2))

        # Seek Backward -5s
        self.btn_prev = ctk.CTkButton(
            self.ctrl_btn_row,
            text="⏪",
            font=("Segoe UI", 11),
            width=28,
            height=28,
            corner_radius=6,
            fg_color="transparent",
            hover_color=Config.CARD_HOVER,
            text_color=Config.TEXT_MAIN,
            command=self._seek_backward_5s
        )
        self.btn_prev.pack(side="left", padx=4)

        # Play / Pause Toggle
        self.btn_play_pause = ctk.CTkButton(
            self.ctrl_btn_row,
            text="▶",
            font=("Segoe UI", 13, "bold"),
            width=34,
            height=34,
            corner_radius=17,
            fg_color=Config.BTN_PRIMARY_BG,
            hover_color=Config.BTN_PRIMARY_HOVER,
            text_color=Config.BTN_PRIMARY_TEXT,
            command=self._toggle_play_pause
        )
        self.btn_play_pause.pack(side="left", padx=6)

        # Stop Button
        self.btn_stop = ctk.CTkButton(
            self.ctrl_btn_row,
            text="⏹",
            font=("Segoe UI", 11),
            width=28,
            height=28,
            corner_radius=6,
            fg_color="transparent",
            hover_color=Config.CARD_HOVER,
            text_color=Config.TEXT_MAIN,
            command=self.stop
        )
        self.btn_stop.pack(side="left", padx=4)

        # Seek Forward +5s
        self.btn_next = ctk.CTkButton(
            self.ctrl_btn_row,
            text="⏩",
            font=("Segoe UI", 11),
            width=28,
            height=28,
            corner_radius=6,
            fg_color="transparent",
            hover_color=Config.CARD_HOVER,
            text_color=Config.TEXT_MAIN,
            command=self._seek_forward_5s
        )
        self.btn_next.pack(side="left", padx=4)

        # Row B: Seekbar & Durasi
        self.timeline_row = ctk.CTkFrame(self.center_frame, fg_color="transparent")
        self.timeline_row.pack(fill="x", padx=10)
        self.timeline_row.grid_columnconfigure(1, weight=1)

        self.lbl_curr_time = ctk.CTkLabel(
            self.timeline_row,
            text="00:00",
            font=("Segoe UI", 9),
            text_color=Config.TEXT_MUTED,
            width=36,
            anchor="e"
        )
        self.lbl_curr_time.grid(row=0, column=0, padx=(0, 6))

        self.slider_seek = ctk.CTkSlider(
            self.timeline_row,
            from_=0,
            to=1000,
            height=12,
            thumb_size=12,
            progress_color=Config.BTN_PRIMARY_BG,
            fg_color=Config.INPUT_BG,
            button_color=Config.BTN_PRIMARY_BG,
            button_hover_color=Config.BTN_PRIMARY_HOVER,
            command=self._on_seek_slider_change
        )
        self.slider_seek.grid(row=0, column=1, sticky="ew")
        self.slider_seek.set(0)
        self.slider_seek.bind("<ButtonPress-1>", lambda e: self._on_seek_drag_start())
        self.slider_seek.bind("<ButtonRelease-1>", lambda e: self._on_seek_drag_end())

        self.lbl_total_time = ctk.CTkLabel(
            self.timeline_row,
            text="00:00",
            font=("Segoe UI", 9),
            text_color=Config.TEXT_MUTED,
            width=36,
            anchor="w"
        )
        self.lbl_total_time.grid(row=0, column=2, padx=(6, 0))

        # ---------------------------------------------------------------------
        # 3. SISI KANAN: VOLUME SLIDER & CLOSE
        # ---------------------------------------------------------------------
        self.right_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.right_frame.grid(row=0, column=2, padx=(8, 14), pady=8, sticky="e")

        self.lbl_vol_icon = ctk.CTkLabel(
            self.right_frame,
            text="🔊",
            font=("Segoe UI", 12),
            text_color=Config.TEXT_MUTED
        )
        self.lbl_vol_icon.pack(side="left", padx=(0, 4))

        self.slider_vol = ctk.CTkSlider(
            self.right_frame,
            from_=0,
            to=100,
            width=70,
            height=10,
            thumb_size=10,
            progress_color=Config.BTN_PRIMARY_BG,
            fg_color=Config.INPUT_BG,
            button_color=Config.BTN_PRIMARY_BG,
            button_hover_color=Config.BTN_PRIMARY_HOVER,
            command=self._on_volume_change
        )
        self.slider_vol.pack(side="left", padx=(0, 10))
        self.slider_vol.set(80)

        # Close Player Bar Button
        self.btn_close = ctk.CTkButton(
            self.right_frame,
            text="✕",
            font=("Segoe UI", 11, "bold"),
            width=26,
            height=26,
            corner_radius=6,
            fg_color="transparent",
            hover_color=Config.DANGER_BG,
            text_color=Config.TEXT_MUTED,
            command=self._action_close
        )
        self.btn_close.pack(side="left")

    # =========================================================================
    # PUBLIC API: PLAY, LOAD, STOP
    # =========================================================================
    def play_file(self, file_path: str, title: str = "", artist: str = ""):
        """Memuat dan langsung memutar file audio."""
        if not os.path.exists(file_path):
            return

        self._current_file = file_path
        filename = os.path.basename(file_path)

        display_title = title if title else os.path.splitext(filename)[0]
        if len(display_title) > 34:
            display_title = display_title[:31] + "..."
        self.title_label.configure(text=display_title)

        display_artist = artist if artist else "Audio Player"
        self.artist_label.configure(text=display_artist)

        # Load file ke audio player MCI
        if self.player.load(file_path):
            self._duration_ms = self.player.duration_ms
            total_sec = self._duration_ms / 1000.0
            self.lbl_total_time.configure(text=self._format_time(total_sec))
            self.slider_seek.configure(to=max(1000, self._duration_ms))
            self.slider_seek.set(0)
            self.player.play()
            self.btn_play_pause.configure(text="⏸")

    def stop(self):
        """Menghentikan audio dan mereset slider ke awal."""
        self.player.stop()
        self.btn_play_pause.configure(text="▶")
        self.slider_seek.set(0)
        self.lbl_curr_time.configure(text="00:00")

    def close_player(self):
        """Menutup player bar dan melepaskan resource audio MCI."""
        self.player.close()
        self._current_file = None
        self._duration_ms = 0
        self.btn_play_pause.configure(text="▶")
        self.slider_seek.set(0)
        self.lbl_curr_time.configure(text="00:00")
        self.lbl_total_time.configure(text="00:00")
        self.title_label.configure(text="Tidak Ada Media Diputar")
        self.artist_label.configure(text="Pilih media untuk diputar")

    # =========================================================================
    # INTERNAL HANDLERS
    # =========================================================================
    def _toggle_play_pause(self):
        if not self._current_file:
            return

        if self.player.is_playing():
            self.player.pause()
            self.btn_play_pause.configure(text="▶")
        elif self.player.is_paused():
            self.player.resume()
            self.btn_play_pause.configure(text="⏸")
        else:
            self.player.play()
            self.btn_play_pause.configure(text="⏸")

    def _seek_backward_5s(self):
        if not self._current_file or self._duration_ms <= 0:
            return
        curr_pos = self.player.get_position()
        new_pos = max(0, curr_pos - 5000)
        self.player.seek(new_pos)
        self.slider_seek.set(new_pos)

    def _seek_forward_5s(self):
        if not self._current_file or self._duration_ms <= 0:
            return
        curr_pos = self.player.get_position()
        new_pos = min(self._duration_ms, curr_pos + 5000)
        self.player.seek(new_pos)
        self.slider_seek.set(new_pos)

    def _on_seek_drag_start(self):
        self._is_user_seeking = True

    def _on_seek_drag_end(self):
        if self._current_file and self._duration_ms > 0:
            target_ms = int(self.slider_seek.get())
            self.player.seek(target_ms)
        self._is_user_seeking = False

    def _on_seek_slider_change(self, value):
        if self._is_user_seeking:
            sec = float(value) / 1000.0
            self.lbl_curr_time.configure(text=self._format_time(sec))

    def _on_volume_change(self, value):
        vol = int(value)
        self.player.set_volume(vol)
        if vol == 0:
            self.lbl_vol_icon.configure(text="🔇")
        elif vol < 50:
            self.lbl_vol_icon.configure(text="🔉")
        else:
            self.lbl_vol_icon.configure(text="🔊")

    def _on_audio_position_change(self, pos_ms: int, total_ms: int):
        if self._is_user_seeking:
            return
        # Panggil di main GUI thread Tkinter
        try:
            self.after(0, self._update_progress_ui, pos_ms, total_ms)
        except Exception:
            pass

    def _update_progress_ui(self, pos_ms: int, total_ms: int):
        if self._is_user_seeking:
            return
        self.slider_seek.set(pos_ms)
        self.lbl_curr_time.configure(text=self._format_time(pos_ms / 1000.0))

    def _on_audio_finished(self):
        try:
            self.after(0, self._handle_finished_ui)
        except Exception:
            pass

    def _handle_finished_ui(self):
        self.btn_play_pause.configure(text="▶")
        self.slider_seek.set(0)
        self.lbl_curr_time.configure(text="00:00")

    def _action_close(self):
        self.close_player()
        if self.on_close_cb:
            self.on_close_cb()

    @staticmethod
    def _format_time(seconds: float) -> str:
        s = int(max(0, seconds))
        m, s = divmod(s, 60)
        h, m = divmod(m, 60)
        if h > 0:
            return f"{h:02d}:{m:02d}:{s:02d}"
        return f"{m:02d}:{s:02d}"
