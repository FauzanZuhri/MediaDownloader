import re
import requests
from typing import Optional, Dict, Any

class MusicLinkParser:
    """
    Parser cerdas untuk tautan Spotify dan Apple Music.
    Mengekstrak judul, artis, album, dan cover art tanpa memerlukan API key resmi,
    lalu memetakan query pencarian ke YouTube Music / YouTube.
    """
    @staticmethod
    def parse(url: str) -> Dict[str, Any]:
        url = url.strip()
        result = {
            'is_music_link': False,
            'platform': None,
            'type': 'track',  # track, album, playlist
            'title': None,
            'artist': None,
            'album': None,
            'thumbnail_url': None,
            'search_query': None,
            'original_url': url
        }

        if not url:
            return result

        if "spotify.com" in url:
            result['is_music_link'] = True
            result['platform'] = 'spotify'

            if "/track/" in url:
                result['type'] = 'track'
            elif "/album/" in url:
                result['type'] = 'album'
            elif "/playlist/" in url:
                result['type'] = 'playlist'

            try:
                # 1. Gunakan oEmbed API resmi Spotify (Legal & Tanpa Token)
                oembed_url = f"https://open.spotify.com/oembed?url={url}"
                resp = requests.get(oembed_url, timeout=7)
                if resp.status_code == 200:
                    data = resp.json()
                    result['title'] = data.get("title")
                    result['thumbnail_url'] = data.get("thumbnail_url")

                # 2. Ambil HTML publik untuk mendapatkan nama Artis & Album yang akurat
                headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
                page = requests.get(url, headers=headers, timeout=7)
                if page.status_code == 200:
                    html = page.text
                    
                    # Pattern judul & artis di tag <title>
                    # Contoh: "Never Gonna Give You Up - song and lyrics by Rick Astley | Spotify"
                    m_title = re.search(r'<title>(.*?)\s*[-–|]\s*(?:Song|song|single|album|music|podcast).*?by\s+(.*?)\s*\|\s*Spotify</title>', html, re.I)
                    if m_title:
                        result['title'] = m_title.group(1).strip()
                        result['artist'] = m_title.group(2).strip()
                    else:
                        m_simple = re.search(r'<title>(.*?)\s*\|\s*Spotify</title>', html, re.I)
                        if m_simple:
                            parts = m_simple.group(1).split(" - ")
                            if len(parts) >= 2:
                                result['title'] = parts[0].strip()
                                result['artist'] = parts[1].strip()

                    # Fallback ambil nama artis dari meta og:description
                    if not result['artist']:
                        m_og = re.search(r'<meta\s+property=["\']og:description["\']\s+content=["\'](.*?)["\']', html)
                        if m_og:
                            desc = m_og.group(1)
                            parts = [p.strip() for p in desc.split("·")]
                            if len(parts) >= 2:
                                result['artist'] = parts[0]

            except Exception as e:
                print(f"[MusicLinkParser] Spotify error: {e}")

        elif "music.apple.com" in url:
            result['is_music_link'] = True
            result['platform'] = 'apple'
            try:
                headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
                page = requests.get(url, headers=headers, timeout=7)
                if page.status_code == 200:
                    html = page.text
                    # Apple Music format: "<title>Song Name by Artist on Apple Music</title>"
                    m_title = re.search(r'<title>(.*?)\s+by\s+(.*?)\s+(?:on|–|-)\s+Apple Music</title>', html, re.I)
                    if m_title:
                        result['title'] = m_title.group(1).strip()
                        result['artist'] = m_title.group(2).strip()

                    m_img = re.search(r'<meta\s+property=["\']og:image["\']\s+content=["\'](.*?)["\']', html)
                    if m_img:
                        result['thumbnail_url'] = m_img.group(1)
            except Exception as e:
                print(f"[MusicLinkParser] Apple Music error: {e}")

        if result['is_music_link'] and result['title']:
            if result['artist']:
                result['search_query'] = f"{result['artist']} - {result['title']} audio"
            else:
                result['search_query'] = f"{result['title']} audio"

        return result

