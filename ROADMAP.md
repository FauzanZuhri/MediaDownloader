# 🗺️ Roadmap & Rencana Pengembangan Masa Depan

Dokumen ini memuat peta jalan (*future plan*), strategi penomoran versi (*versioning strategy*), dan daftar target fitur untuk rilis mendatang dari **Personal Music Downloader**.

---

## 📌 Standar Penomoran Versi (Semantic Versioning)

Project ini mengikuti spesifikasi **[Semantic Versioning 2.0.0](https://semver.org/)** dengan format:

$$\text{v}\mathbf{MAJOR}.\mathbf{MINOR}.\mathbf{PATCH}$$

* **MAJOR (v2.0.0):** Perubahan arsitektur besar, perubahan UI fundamental, atau fitur yang mengubah alur kerja utama.
* **MINOR (v1.2.0):** Penambahan fitur baru, peningkatan antarmuka, atau fungsionalitas baru yang tetap kompatibel (*backwards-compatible*).
* **PATCH (v1.1.1):** Perbaikan bug (*bug fixes*), optimasi ukuran biner, pembaruan keamanan, atau perbaikan dependensi kecil.

---

## 🚀 Rencana Rilis & Target Milestone

### 🔹 [v1.1.0] - *Current Stable Release* ✅
- [x] Perombakan UI modern 2-kolom (*Obsidian & Indigo Theme*).
- [x] Live Hero Media Preview Card dengan rasio aspek 16:9.
- [x] Tombol cepat *Paste from Clipboard* dan *Clear*.
- [x] Tombol *Cancel Download* yang terhubung ke interupsi *engine*.
- [x] *Collapsible Activity Console* dengan tombol *Clear Log*.
- [x] Perbaikan error YouTube `HTTP Error 403: Forbidden` via *remote challenge solver*.
- [x] Tagging ID3v2.3 otomatis murni (*Title, Artist, Album, Cover Art*).

---

### 🔹 [v1.1.1] - *Optimization & Size Reduction (Patch)* 🎯
Fokus: **Memangkas ukuran file rilis executable (ZIP) tanpa mengubah fungsionalitas.**
- [ ] **Eliminasi `ffprobe.exe`:** Menghapus dependensi `ffprobe` dari build PyInstaller karena alur YouTube-to-MP3 hanya memerlukan `ffmpeg.exe` (menghemat ~35-40 MB).
- [ ] **Kompresi Biner UPX:** Mengompres file biner `ffmpeg.exe` menggunakan *Ultimate Packer for eXecutables* (UPX) untuk mengurangi ukuran biner hingga 50%.
- [ ] **Optimalisasi Dependensi:** Mengurangi modul yang tidak terpakai pada file `.spec`.
- [ ] **Target Ukuran:** Menurunkan ukuran file ZIP rilis dari **~98 MB menjadi ~45-55 MB**.

---

### 🔹 [v1.2.0] - *Settings Page & Smart Engine (Minor Feature)* ⚙️
Fokus: **Pengaturan pengguna yang fleksibel dan installer ultra-ringan.**
- [ ] **Halaman Pengaturan (Settings Modal):**
  - Pemilihan tema warna (Dark Obsidian, Midnight Blue, Emerald Forest).
  - Pengaturan default folder download permanen.
  - Opsi format nama file hasil download (misal: `{artist} - {title}.mp3` atau `{title}.mp3`).
- [ ] **Opsi Auto-Download FFmpeg (Portable Ultra-Light ~15 MB):**
  - Menyediakan varian build *Ultra-Lightweight*: file ZIP hanya berisi aplikasi Python (~15 MB).
  - Jika `ffmpeg.exe` belum ada, aplikasi akan menampilkan dialog konfirmasi dan otomatis mengunduh FFmpeg sekali saja di latar belakang.
- [ ] **Pembersih Cache Arsip:** Tombol pada UI untuk melihat dan mengelola isi `download_archive.txt`.

---

### 🔹 [v1.3.0] - *Audio Customization & Playlist Management* 🎧
Fokus: **Fleksibilitas audio dan kontrol playlist.**
- [ ] **Multi-Format Export:**
  - Tambahan dukungan format audio berkualitas tinggi: **FLAC (Lossless)**, **M4A/AAC**, dan **OGG/Opus**.
- [ ] **Editor Metadata Manual (Opsional):**
  - Modal untuk mengedit Judul, Artis, dan Nama Album sebelum tombol download dieksekusi.
- [ ] **Playlist Item Selector:**
  - Menampilkan daftar checklist lagu dalam playlist sehingga pengguna bisa memilih hanya mengunduh beberapa lagu tertentu dari playlist.
- [ ] **Normalisasi Volume Audio (ReplayGain / Loudness Matching):**
  - Mengaktifkan filter FFmpeg `loudnorm` agar semua lagu yang diunduh memiliki tingkat volume suara yang seragam.

---

### 🔹 [v2.0.0] - *Major Evolution & Next-Gen Experience* 🌟
Fokus: **Ekosistem multi-platform, integrasi layanan, dan pemutar musik internal.**
- [ ] **Mini Music Player Internal:**
  - Pemutar audio bawaan di dalam aplikasi untuk langsung mendengarkan lagu yang baru saja selesai diunduh.
- [ ] **Dukungan Multi-Bahasa (i18n):**
  - Pilihan Bahasa Indonesia dan Bahasa Inggris pada antarmuka.
- [ ] **Auto-Update Checker:**
  - Notifikasi otomatis jika versi baru dirilis di GitHub Release dengan tautan unduhan langsung.
- [ ] **Integrasi Link Eksternal:**
  - Kemampuan parsing tautan audio dari platform lain (SoundCloud, Bandcamp).
