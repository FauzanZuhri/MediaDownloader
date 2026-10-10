# 🗺️ Roadmap & Rencana Pengembangan Jangka Panjang

Dokumen ini memuat visi jangka panjang, standar versi (*Semantic Versioning*), dan peta rilis bertahap dari aplikasi yang bertransformasi dari sekadar music downloader menjadi **Universal Media Hub (Audio & Video Multi-Platform)**.

---

## 📌 Standar Penomoran Versi (Semantic Versioning)

Project ini mengikuti spesifikasi **[Semantic Versioning 2.0.0](https://semver.org/)** dengan format:

$$\text{v}\mathbf{MAJOR}.\mathbf{MINOR}.\mathbf{PATCH}$$

* **MAJOR (v2.0.0):** Rebranding nama project, perombakan arsitektur besar, atau integrasi multi-platform menyeluruh.
* **MINOR (v1.2.0, v1.3.0, v1.4.0):** Penambahan fitur media baru (Video 4K, format lossless audio, selector playlist, multi-source).
* **PATCH (v1.1.1):** Pemangkasan ukuran file (*size reduction*), perbaikan bug (*bug fixes*), atau update solver YouTube.

---

## 🚀 Rencana Rilis & Target Milestone

### 🔹 [v1.1.0] - *Current Stable Release* ✅
- [x] Antarmuka modern 2-kolom (*Obsidian Dark & Indigo Theme*).
- [x] Live Media Preview Card 16:9 dengan metadata uploader & durasi.
- [x] Tombol cepat *Paste from Clipboard* dan *Clear*.
- [x] Tombol *Cancel Download* yang terintegrasi aman dengan engine.
- [x] *Collapsible Activity Console* dengan fitur *Clear Log*.
- [x] Perbaikan YouTube `HTTP Error 403: Forbidden` via *remote challenge solver*.
- [x] Auto-tagging ID3v2.3 murni (*Title, Artist, Album, Cover Art*).

---

### 🔹 [v1.1.1] - *Binary Optimization & Size Reduction (Patch)* 🎯
Fokus: **Memangkas ukuran file rilis executable (ZIP) hingga ~50% tanpa mengurangi fungsi.**
- [ ] **Eliminasi `ffprobe.exe`:** Menghapus `ffprobe` dari bundel PyInstaller (menghemat ~35–40 MB).
- [ ] **Kompresi Biner UPX:** Mengompres file biner `ffmpeg.exe` via UPX packer.
- [ ] **Target Ukuran:** Menurunkan ukuran file ZIP rilis dari **~98 MB menjadi ~45–55 MB**.

---

### 🔹 [v1.2.0] - *Full Video Engine & Quality Selector (Minor)* 🎬
Fokus: **Membuka kapabilitas download VIDEO secara penuh (tidak hanya audio MP3).**
- [ ] **Pilihan Resolusi Video Fleksibel:**
  - Selector kualitas MP4/MKV: **480p, 720p, 1080p Full HD, 1440p (2K), hingga 2160p (4K 60fps)**.
  - Penggabungan (*muxing*) otomatis stream video terbaik + stream audio terbaik via FFmpeg.
- [ ] **Dukungan Subtitle:** Opsi unduh dan sematkan takarir (*subtitles / closed captions* `.srt`/`.vtt`).
- [ ] **Halaman Pengaturan (Settings Modal):**
  - Pengaturan folder download default permanen.
  - Pola penamaan file dinamis (misal: `{artist} - {title}` atau `{title} [{resolution}]`).
- [ ] **Manajer Cache Arsip:** Antarmuka untuk melihat dan menghapus daftar riwayat `download_archive.txt`.

---

### 🔹 [v1.3.0] - *Lossless Audio & Smart Playlist Selector* 🎧
Fokus: **Kualitas audio audiophile dan kontrol seleksi konten playlist.**
- [ ] **Format Audio Hi-Res & Lossless:**
  - Dukungan ekspor ke format: **FLAC (Lossless)**, **M4A/AAC (Apple Audio)**, **WAV**, dan **Opus/OGG**.
- [ ] **Playlist Interactive Track Selector:**
  - Tampilan daftar isi playlist (checklist lagu/video) sehingga pengguna dapat memilih hanya mengunduh item-item tertentu tanpa harus mengunduh seluruh isi playlist.
- [ ] **Normalisasi Volume Audio (Loudness Matching):**
  - Integrasi filter audio `loudnorm` (EBU R128) agar volume suara antar lagu seimbang saat diputar.
- [ ] **Editor Metadata Manual:**
  - Opsi mengubah Judul, Artis, Album, dan Gambar Cover sebelum proses unduhan disimpan.

---

### 🔹 [v1.4.0] - *Multi-Platform Source Expansions* 🌐
Fokus: **Mendukung unduhan media dari beragam platform di luar YouTube.**
- [ ] **YouTube Shorts & Clips:** Deteksi format vertikal otomatis.
- [ ] **SoundCloud & Bandcamp:** Unduh stream audio dan artwork resmi.
- [ ] **TikTok & Instagram Reels:** Unduh video pendek tanpa watermark.
- [ ] **Bilibili & Vimeo:** Dukungan ekstraksi video resolusi tinggi.
- [ ] **Opsi Auto-Download FFmpeg (Installer Ultra-Ringan ~15 MB):**
  - Varian build kecil yang otomatis mengunduh FFmpeg hanya jika belum tersedia di sistem user.

---

### 🔹 [v2.0.0] - *Rebranding & Universal Media Studio* 🌟
Fokus: **Rebranding identitas aplikasi, media player internal, dan utilitas konversi.**
- [ ] **Rebranding Resmi:** Mengganti nama aplikasi dari "Music Downloader" menjadi identitas media universal yang baru.
- [ ] **Built-in Media Player:**
  - Pemutar audio & video mini langsung di dalam aplikasi untuk preview instan setelah unduh.
- [ ] **Local Media Converter & Audio Extractor:**
  - Fitur drag-and-drop file video lokal milik pengguna untuk diekstrak menjadi audio MP3/FLAC secara offline.
- [ ] **Dukungan Multi-Bahasa (i18n):**
  - Bahasa Indonesia & English.
- [ ] **Auto-Update Checker:**
  - Notifikasi otomatis jika versi terbaru telah rilis di GitHub Releases dengan tombol unduh langsung.
