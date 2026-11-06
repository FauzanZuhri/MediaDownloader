import re
from typing import Dict, Any, Optional

PLATFORM_PATTERNS = [
    {
        "id": "youtube",
        "name": "YouTube",
        "badge": "▶️ YouTube",
        "type": "universal",  # audio & video
        "regex": r"(?:https?://)?(?:www\.|m\.)?(?:youtube\.com|youtu\.be)/(?:watch\?v=|embed/|v/|shorts/|playlist\?list=)?([a-zA-Z0-9_-]+)",
    },
    {
        "id": "spotify",
        "name": "Spotify",
        "badge": "🟢 Spotify",
        "type": "audio",
        "regex": r"(?:https?://)?open\.spotify\.com/(?:intl-[a-z]+/)?(track|album|playlist|artist)/([a-zA-Z0-9]+)",
    },
    {
        "id": "apple_music",
        "name": "Apple Music",
        "badge": "🍎 Apple Music",
        "type": "audio",
        "regex": r"(?:https?://)?music\.apple\.com/([a-z]{2}/)?(album|playlist|song)/[a-zA-Z0-9-]+/([0-9]+)",
    },
    {
        "id": "tiktok",
        "name": "TikTok",
        "badge": "🎵 TikTok",
        "type": "video",
        "regex": r"(?:https?://)?(?:www\.|m\.|vm\.|vt\.)?tiktok\.com/(?:@[\w.-]+/video/\d+|[\w.-]+|v/\d+)",
    },
    {
        "id": "instagram",
        "name": "Instagram",
        "badge": "📸 Instagram",
        "type": "video",
        "regex": r"(?:https?://)?(?:www\.)?instagram\.com/(?:p|reel|tv)/([a-zA-Z0-9_-]+)",
    },
    {
        "id": "soundcloud",
        "name": "SoundCloud",
        "badge": "☁️ SoundCloud",
        "type": "audio",
        "regex": r"(?:https?://)?(?:www\.|m\.)?soundcloud\.com/[\w-]+/[\w-]+",
    },
    {
        "id": "bandcamp",
        "name": "Bandcamp",
        "badge": "🎸 Bandcamp",
        "type": "audio",
        "regex": r"https?://[\w-]+\.bandcamp\.com/(?:track|album)/[\w-]+",
    },
    {
        "id": "twitter",
        "name": "X (Twitter)",
        "badge": "🐦 X / Twitter",
        "type": "video",
        "regex": r"(?:https?://)?(?:www\.|mobile\.)?(?:twitter\.com|x\.com)/[\w]+/status/(\d+)",
    },
    {
        "id": "facebook",
        "name": "Facebook",
        "badge": "📘 Facebook",
        "type": "video",
        "regex": r"(?:https?://)?(?:www\.|m\.|fb\.)?(?:facebook\.com|fb\.watch)/(?:reel/|watch/\?v=|\S+/videos/)?(\d+)?",
    },
    {
        "id": "bilibili",
        "name": "Bilibili",
        "badge": "📺 Bilibili",
        "type": "video",
        "regex": r"(?:https?://)?(?:www\.)?(?:bilibili\.com/video/|b23\.tv/)([a-zA-Z0-9]+)",
    },
    {
        "id": "vimeo",
        "name": "Vimeo",
        "badge": "🎥 Vimeo",
        "type": "video",
        "regex": r"(?:https?://)?(?:www\.)?vimeo\.com/(\d+)",
    },
    {
        "id": "pinterest",
        "name": "Pinterest",
        "badge": "📌 Pinterest",
        "type": "video",
        "regex": r"(?:https?://)?(?:www\.|pin\.)?(?:pinterest\.com/pin/|pin\.it/)(\S+)",
    },
]

class PlatformHelper:
    """
    Detektor platform media universal.
    Mengenali tautan media dari YouTube, TikTok, Instagram, SoundCloud, Bandcamp,
    Spotify, Apple Music, Twitter/X, Facebook, Bilibili, dan Vimeo.
    """
    @staticmethod
    def is_supported(url: str, strict_media: bool = False) -> bool:
        """
        Memeriksa apakah URL yang diberikan didukung oleh downloader.
        Jika strict_media=True, hanya mengembalikan True untuk platform media spesifik
        (YouTube, TikTok, Instagram, Spotify, SoundCloud, dll.) dan mengabaikan link web umum.
        """
        if not url or not str(url).strip():
            return False
        det = PlatformHelper.detect(url)
        if strict_media:
            return det.get("is_supported", False) and det.get("id") not in ("generic", "unknown")
        return bool(det.get("is_supported", False))

    @staticmethod
    def detect(url: str) -> Dict[str, Any]:
        url = (url or "").strip()
        if not url:
            return {
                "id": "unknown",
                "name": "Unknown",
                "badge": "🌐 Universal Media",
                "type": "universal",
                "is_supported": False,
            }

        url_lower = url.lower()
        for p in PLATFORM_PATTERNS:
            if re.search(p["regex"], url, re.IGNORECASE):
                return {
                    "id": p["id"],
                    "name": p["name"],
                    "badge": p["badge"],
                    "type": p["type"],
                    "is_supported": True,
                }
                
        # Fallback domain check
        if "tiktok.com" in url_lower:
            return {"id": "tiktok", "name": "TikTok", "badge": "🎵 TikTok", "type": "video", "is_supported": True}
        if "instagram.com" in url_lower:
            return {"id": "instagram", "name": "Instagram", "badge": "📸 Instagram", "type": "video", "is_supported": True}
        if "soundcloud.com" in url_lower:
            return {"id": "soundcloud", "name": "SoundCloud", "badge": "☁️ SoundCloud", "type": "audio", "is_supported": True}
        if "bandcamp.com" in url_lower:
            return {"id": "bandcamp", "name": "Bandcamp", "badge": "🎸 Bandcamp", "type": "audio", "is_supported": True}
        if "twitter.com" in url_lower or "x.com" in url_lower:
            return {"id": "twitter", "name": "X (Twitter)", "badge": "🐦 X / Twitter", "type": "video", "is_supported": True}
        if "facebook.com" in url_lower or "fb.watch" in url_lower:
            return {"id": "facebook", "name": "Facebook", "badge": "📘 Facebook", "type": "video", "is_supported": True}
        if "bilibili.com" in url_lower or "b23.tv" in url_lower:
            return {"id": "bilibili", "name": "Bilibili", "badge": "📺 Bilibili", "type": "video", "is_supported": True}
        if "vimeo.com" in url_lower:
            return {"id": "vimeo", "name": "Vimeo", "badge": "🎥 Vimeo", "type": "video", "is_supported": True}
        if "pinterest.com" in url_lower or "pin.it" in url_lower:
            return {"id": "pinterest", "name": "Pinterest", "badge": "📌 Pinterest", "type": "video", "is_supported": True}

        # Jika link web biasa yang valid
        if url.startswith(("http://", "https://")):
            return {
                "id": "generic",
                "name": "Web Media",
                "badge": "🌐 Web Media",
                "type": "universal",
                "is_supported": True,
            }

        return {
            "id": "unknown",
            "name": "Unknown",
            "badge": "🌐 Media",
            "type": "universal",
            "is_supported": False,
        }

