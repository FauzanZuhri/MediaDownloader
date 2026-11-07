import os
import sys
import shutil
import zipfile
import subprocess
from core.config import Config

def build():
    print(f"==================================================")
    print(f" 🚀 Building {Config.APP_TITLE} {Config.VERSION} Release")
    print(f"==================================================")

    # 1. Pastikan aset icon tersedia
    icon_path = os.path.join("assets", "icon.ico")
    if not os.path.exists(icon_path):
        print("[!] Generating assets first...")
        subprocess.run([sys.executable, "generate_assets.py"], check=True)

    # 2. Jalankan PyInstaller menggunakan MediaDownloader.spec
    spec_file = "MediaDownloader.spec"
    print(f"[*] Running PyInstaller with {spec_file}...")
    cmd = [sys.executable, "-m", "PyInstaller", "--noconfirm", "--upx-dir", ".", spec_file]
    res = subprocess.run(cmd)
    if res.returncode != 0:
        print("[X] Build failed!")
        sys.exit(1)

    dist_folder = os.path.join("dist", "MediaDownloader")
    if not os.path.exists(dist_folder):
        print(f"[X] Dist folder not found: {dist_folder}")
        sys.exit(1)

    # 3. Buat file arsip ZIP untuk distribusi
    zip_filename = f"{Config.APP_TITLE}-{Config.VERSION}-windows-x64.zip"
    zip_path = os.path.join("dist", zip_filename)
    print(f"[*] Packaging release into {zip_path}...")

    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as zipf:
        for root, dirs, files in os.walk(dist_folder):
            for file in files:
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, "dist")
                zipf.write(full_path, rel_path)

    zip_size_mb = os.path.getsize(zip_path) / (1024 * 1024)
    print(f"==================================================")
    print(f" ✅ Build Sukses!")
    print(f" 📦 Output Folder: {dist_folder}")
    print(f" 📦 Release ZIP:   {zip_path} ({zip_size_mb:.2f} MB)")
    print(f"==================================================")

if __name__ == "__main__":
    build()
