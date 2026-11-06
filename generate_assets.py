import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter

def process_assets():
    assets_dir = os.path.abspath("assets")
    os.makedirs(assets_dir, exist_ok=True)
    png_path = os.path.join(assets_dir, "icon.png")

    if not os.path.exists(png_path):
        print("[!] icon.png tidak ditemukan di folder assets/!")
        return

    print(f"[*] Mengolah {png_path}...")
    icon_src = Image.open(png_path).convert("RGBA")

    # 1. Generate multi-resolution icon.ico
    ico_path = os.path.join(assets_dir, "icon.ico")
    icon_sizes = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (24, 24), (16, 16)]
    icon_src.save(ico_path, format="ICO", sizes=icon_sizes)
    print(f"[OK] Multi-size Icon ICO berhasil disimpan di {ico_path}")

    # 2. Generate logo banner profesional untuk README.md & rilis
    W, H = 1050, 260
    banner = Image.new("RGBA", (W, H), (9, 9, 11, 255))
    draw = ImageDraw.Draw(banner)

    # Border halus sekeliling banner
    draw.rounded_rectangle([(0, 0), (W - 1, H - 1)], radius=14, outline=(39, 39, 42, 255), width=2)

    # Ambient glow biru safir di belakang icon
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw_glow = ImageDraw.Draw(glow)
    draw_glow.ellipse([(20, 20), (280, 240)], fill=(37, 99, 235, 35))
    glow = glow.filter(ImageFilter.GaussianBlur(50))
    banner = Image.alpha_composite(banner, glow)
    draw = ImageDraw.Draw(banner)

    # Tempel icon user (170x170 px) terpusat vertikal
    icon_size = 170
    mini_icon = icon_src.resize((icon_size, icon_size), Image.Resampling.LANCZOS)
    icon_x = 45
    icon_y = (H - icon_size) // 2
    banner.paste(mini_icon, (icon_x, icon_y), mini_icon)

    # Inisialisasi Tipografi
    try:
        font_title = ImageFont.truetype("segoeui.ttf", 44)
        font_sub = ImageFont.truetype("segoeui.ttf", 17)
        font_badge_v = ImageFont.truetype("segoeuib.ttf", 13)
        font_pill = ImageFont.truetype("segoeuib.ttf", 12)
    except Exception:
        font_title = ImageFont.load_default()
        font_sub = ImageFont.load_default()
        font_badge_v = ImageFont.load_default()
        font_pill = ImageFont.load_default()

    text_x = icon_x + icon_size + 35
    title_y = 52

    # Judul: MediaDownloader
    draw.text((text_x, title_y), "MediaDownloader", font=font_title, fill=(248, 250, 252))

    # Posisi badge v2.0.0 persis di samping judul secara proporsional
    bbox = font_title.getbbox("MediaDownloader")
    title_w = bbox[2] - bbox[0]

    badge_v_x = text_x + title_w + 14
    badge_v_y = title_y + 12
    badge_v_w, badge_v_h = 70, 26
    draw.rounded_rectangle([(badge_v_x, badge_v_y), (badge_v_x + badge_v_w, badge_v_y + badge_v_h)], radius=6, fill=(37, 99, 235))

    v_bbox = font_badge_v.getbbox("v2.0.0")
    v_w = v_bbox[2] - v_bbox[0]
    v_h = v_bbox[3] - v_bbox[1]
    draw.text((badge_v_x + (badge_v_w - v_w)//2, badge_v_y + (badge_v_h - v_h)//2 - 1), "v2.0.0", font=font_badge_v, fill=(255, 255, 255))

    # Subtitle
    sub_y = title_y + 58
    draw.text((text_x, sub_y), "Universal Media Downloader & Offline Studio", font=font_sub, fill=(148, 163, 184))

    # Pill Badges dengan indikator dot warna (Bebas dari karakter kotak [] / missing glyph)
    pill_y = sub_y + 38
    pills = [
        ("Multi-Platform", (56, 189, 248)),       # Cyan
        ("4K UHD Video", (34, 197, 94)),          # Emerald
        ("Hi-Res Audio", (168, 85, 247)),        # Purple
        ("100% Offline Core", (251, 191, 36)),    # Amber
    ]

    curr_px = text_x
    for label, dot_color in pills:
        t_bbox = font_pill.getbbox(label)
        tw = t_bbox[2] - t_bbox[0]
        th = t_bbox[3] - t_bbox[1]
        
        pw = tw + 42
        ph = 28
        
        # Kotak pill container ber-elevasi
        draw.rounded_rectangle([(curr_px, pill_y), (curr_px + pw, pill_y + ph)], radius=6, fill=(18, 18, 22), outline=(39, 39, 42), width=1)
        
        # Titik dot indikator modern
        dot_radius = 4
        dot_cx = curr_px + 14
        dot_cy = pill_y + ph // 2
        draw.ellipse([(dot_cx - dot_radius, dot_cy - dot_radius), (dot_cx + dot_radius, dot_cy + dot_radius)], fill=dot_color)
        
        # Teks label
        draw.text((curr_px + 24, pill_y + (ph - th)//2 - 2), label, font=font_pill, fill=(226, 232, 240))
        
        curr_px += pw + 10

    banner_path = os.path.join(assets_dir, "logo_banner.png")
    banner.save(banner_path, "PNG")
    print(f"[OK] Logo Banner berhasil disimpan di {banner_path}")

if __name__ == "__main__":
    process_assets()
