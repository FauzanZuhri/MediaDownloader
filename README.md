# 🎵 Personal Music Downloader

> **Modern Desktop Music Downloader** untuk Windows yang dapat mengunduh lagu maupun playlist dari YouTube, mengubahnya menjadi **MP3 berkualitas tinggi**, serta menambahkan **metadata lengkap** dan **cover album** secara otomatis.

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
Personal-Music-Downloader/
│
├── core/
│   ├── config.py
│   └── downloader.py
│
├── ui/
│   ├── components.py
│   └── main_window.py
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
git clone https://github.com/FauzanZuhri/Personal-Music-Downloader.git

cd Personal-Music-Downloader
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

Rencana detail pengembangan dan pembagian versi dapat dilihat di [ROADMAP.md](ROADMAP.md).

- [x] Single Download
- [x] Playlist Download
- [x] Automatic MP3 Conversion
- [x] Metadata Injection
- [x] Cover Art
- [x] Download Progress Bar & Live Stats
- [x] Live Media Preview & Quick Actions
- [ ] Settings Page
- [ ] Update Checker
- [ ] Multi-language Support

---

# 🤝 Contributing

Pull Request selalu diterima.

Jika menemukan bug atau memiliki ide fitur baru, silakan buat **Issue** terlebih dahulu sebelum membuat Pull Request.

---

# ⭐ Support

Jika project ini bermanfaat, jangan lupa berikan ⭐ pada repository ini.

Terima kasih ❤️