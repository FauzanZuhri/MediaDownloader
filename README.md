# 📥 MediaDownloader

> **Modern Desktop Media Downloader** untuk Windows yang dapat mengunduh audio (lagu/playlist) maupun video dari YouTube dan platform lainnya, mengubahnya secara otomatis dengan **kualitas tinggi**, serta menyematkan **metadata lengkap** dan **cover art**.

---

## ✨ Features

- 🎵 **Single & Playlist Download**
  - Download satu lagu atau seluruh playlist sekaligus.

- 🎧 **Automatic MP3 Conversion**
  - Audio langsung dikonversi ke format MP3 menggunakan FFmpeg.

- 🏷️ **Automatic Metadata**
  - Menambahkan informasi:
    - Judul Lagu
    - Artis
    - Album
    - Cover Art

- 🚫 **Download Archive**
  - Mencegah lagu yang sama terunduh dua kali.

- 🎨 **Modern User Interface**
  - Dibangun menggunakan **CustomTkinter** dengan tampilan modern dan Dark Mode.

- 📂 **Open Download Folder**
  - Membuka folder hasil download hanya dengan satu klik.

---

# 🚀 Download

Tidak perlu menginstal Python ataupun FFmpeg.

### Langkah Instalasi

1. Buka halaman **Releases**
2. Download file `.zip` terbaru
3. Ekstrak file
4. Jalankan **main.exe**

> 📦 Semua dependency sudah termasuk di dalam aplikasi.

---

# 🛠️ Developer Guide

Panduan ini ditujukan bagi developer yang ingin memodifikasi aplikasi.

## Prasyarat

- Python **3.12**
- FFmpeg

Struktur folder:

```
MediaDownloader/
│
├── core/
│   ├── archive_manager.py
│   ├── config.py
│   ├── downloader.py
│   ├── settings.py
│   └── updater.py
│
├── ui/
│   ├── archive_modal.py
│   ├── components.py
│   ├── main_window.py
│   └── settings_modal.py
│
├── main.py
├── requirements.txt
├── README.md
├── ffmpeg.exe
└── download_archive.txt
```

---

## 1️⃣ Clone Repository

```bash
git clone https://github.com/FauzanZuhri/MediaDownloader.git

cd MediaDownloader
```

---

## 2️⃣ Buat Virtual Environment

```bash
python -m venv .venv
```

Windows

```bash
.venv\Scripts\activate
```

Mac / Linux

```bash
source .venv/bin/activate
```

---

## 3️⃣ Install Dependency

```bash
pip install -r requirements.txt
```

---

## 4️⃣ Jalankan Aplikasi

```bash
python main.py
```

---

# 📦 Build Menjadi EXE

Gunakan PyInstaller.

```bash
pyinstaller ^
--noconfirm ^
--onedir ^
--windowed ^
--add-data ".venv/Lib/site-packages/customtkinter;customtkinter/" ^
--add-binary "ffmpeg.exe;." ^
main.py
```

---

# 🧰 Built With

| Teknologi | Fungsi |
|-----------|--------|
| CustomTkinter | Modern GUI |
| yt-dlp | Download Engine |
| FFmpeg | Audio Conversion |
| Mutagen | Metadata Injection |
| Pillow | Cover Art Processing |
| PyInstaller | Build EXE |

---

# 📂 Output

Setelah proses selesai, file MP3 akan berisi:

- ✅ Judul Lagu
- ✅ Nama Artis
- ✅ Album
- ✅ Cover Art
- ✅ Metadata ID3 v2.3

Siap diputar di:

- Spotify Local Files
- AIMP
- MusicBee
- Windows Media Player
- Android Music Player

---

# 📌 Roadmap

- [x] Single Download
- [x] Playlist Download
- [x] Automatic MP3 Conversion
- [x] Metadata Injection
- [x] Cover Art
- [x] Download Progress Bar & Live Stats
- [x] Live Media Preview & Quick Actions
- [x] **App Rebranding & Identity Refresh (MediaDownloader)**
- [x] Settings Page, Template Penamaan File & yt-dlp Updater
- [ ] **Complete UI/UX 2.0 Overhaul (Next Focus)**
- [ ] Full Video Engine (4K MP4/MKV) & Subtitles
- [ ] Hi-Res Lossless Audio & Chapter Splitter
- [ ] Batch Queue & Smart Playlist Selector
- [ ] Multi-Platform (TikTok, SoundCloud, Instagram)
- [ ] Built-in Media Player & Converter Toolkit

---

# 🤝 Contributing

Pull Request selalu diterima.

Jika menemukan bug atau memiliki ide fitur baru, silakan buat **Issue** terlebih dahulu sebelum membuat Pull Request.

---

# ⭐ Support

Jika project ini bermanfaat, jangan lupa berikan ⭐ pada repository ini.

Terima kasih ❤️