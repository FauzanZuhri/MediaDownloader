# -*- mode: python ; coding: utf-8 -*-

import os

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[
        ('ffmpeg.exe', '.'),
    ],
    datas=[
        ('.venv/Lib/site-packages/customtkinter', 'customtkinter/'),
        ('assets', 'assets/'),
    ],
    hiddenimports=[
        'pystray',
        'PIL',
        'PIL.Image',
        'PIL.ImageDraw',
        'mutagen',
        'mutagen.mp3',
        'mutagen.id3',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'ffprobe.exe',
        'tkinter.test',
        'unittest',
        'test',
        'distutils',
        'setuptools',
        'wheel',
        'pip',
        'pydoc',
        'doctest',
    ],
    noarchive=False,
    optimize=1,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='MediaDownloader',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/icon.ico',
    version='file_version_info.txt',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='MediaDownloader',
)
