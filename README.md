# Personal Music Downloader 🎵

Aplikasi desktop berbasis Python yang dirancang khusus untuk mengunduh musik atau video dari YouTube secara personal. Aplikasi ini ringan, modern, cepat, dan berfokus pada fungsionalitas serta kestabilan.

## 🚀 Fitur Utama (Progressive Development)
* **Single & Playlist Downloader**: Mengunduh video tunggal atau seluruh isi playlist YouTube secara otomatis.
* **Format Konversi Otomatis**: Mengonversi hasil unduhan langsung menjadi format MP3 murni kualitas tinggi menggunakan FFmpeg.
* **Real-Time Progress Tracker**: Menampilkan persentase unduhan, kecepatan internet, dan estimasi waktu selesai (ETA) secara langsung di UI.
* **Asynchronous Architecture**: Menggunakan *multithreading* agar UI tetap responsif dan tidak membeku (*not responding*) saat proses unduhan berjalan.
* **Smart Folder Structuring**: Otomatis membuat subfolder khusus berdasarkan nama playlist agar file lagu tertata rapi.

## 🛠️ Teknologi yang Digunakan
* **Python 3.12+** (Bahasa pemrograman utama)
* **CustomTkinter** (Framework UI modern & clean)
* **yt-dlp** (Mesin pengunduh video/audio yang bertenaga)
* **FFmpeg** (Alat pemroses dan konversi audio)
* **Pillow & Requests** (Pengolah data thumbnail untuk fitur live preview)

## 📦 Prasyarat & Instalasi

### 1. Clone Repositori
```bash
git clone https://github.com/FauzanZuhri/Personal-Music-Downloader.git
cd personal-music-downloader
```
### 2. Instal Dependency
Pastikan kamu menggunakan Python 3.12, lalu instal library yang dibutuhkan:
```bash
pip install -r requirements.txt
```
### 3. Setup FFmpeg (Wajib)
Aplikasi ini membutuhkan biner ffmpeg.exe dan ffprobe.exe untuk melakukan konversi ke MP3.
- Unduh biner FFmpeg untuk OS kamu.

- Letakkan file ffmpeg.exe dan ffprobe.exe langsung di dalam folder utama proyek ini (sejajar dengan main.py).


## 🎮 Cara Menjalankan Aplikasi
Jalankan perintah berikut di terminal pada direktori utama proyek:
```bash
python main.py
```
## 📈 Development Progress

**Overall Progress:** 70% (7/10 Phases Completed)

- ✅ Phase 1 — Planning & Architecture
- ✅ Phase 2 — UI Development
- ✅ Phase 3 — yt-dlp Integration
- ✅ Phase 4 — FFmpeg Integration
- ✅ Phase 5 — Video Preview
- ✅ Phase 6 — Download Progress
- ✅ Phase 7 — Playlist Download
- ⏳ Phase 8 — Playlist Synchronization
- ⏳ Phase 9 — Settings
- ⏳ Phase 10 — Build & Release

