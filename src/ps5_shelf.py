"""
ReelLore AI — PS5-Style Game Cover Shelf & GTA 6 Command Hub
============================================================
Curated game shelf metadata, cover art CDNs, dynamic Serper image search
(https://google.serper.dev/images with timeout=8), reliable SVG fallbacks,
and game-specific topic presets with primary hero focus on Grand Theft Auto VI.
"""

import os
import json
import urllib.parse
import requests

# Curated Game Shelf Catalog
GAME_SHELF = [
    {
        "id": "gta6",
        "title": "Grand Theft Auto VI",
        "short_name": "GTA 6",
        "tagline": "State of Leonida // Vice City",
        "release": "Fall 2025 / 2026",
        "studio": "Rockstar Games",
        "is_hero": True,
        "badge": "⭐ FEATURED HERO",
        "cover_url": "https://images.igdb.com/igdb/image/upload/t_720p/co6m9e.jpg",
        "fallback_cover": "https://images.igdb.com/igdb/image/upload/t_cover_big/co6m9e.jpg",
        "theme_accent": "#F43F5E",
        "default_topic": "Vice City map & Leonida ecosystem details, trailer breakdowns & leaks",
        "presets": [
            "🌴 Vice City Map & Leonida Wildlife Ecosystem",
            "🎬 Trailer 1 & 2 Frame-by-Frame Hidden Details",
            "🤖 Next-Gen AI NPC Routines & Euphoria Physics",
            "⏳ Rockstar Dev Timeline, 2022 Leaks & RAGE 9 Tech",
            "💰 Lucia & Jason Dynamics & Bonnie-and-Clyde Heists",
        ],
    },
    {
        "id": "rdr2",
        "title": "Red Dead Redemption 2",
        "short_name": "RDR 2",
        "tagline": "Outlaws for Life // Van der Linde Gang",
        "release": "2018",
        "studio": "Rockstar Games",
        "is_hero": False,
        "badge": "MASTERPIECE",
        "cover_url": "https://shared.fastly.steamstatic.com/store_item_assets/steam/apps/1174180/library_600x900.jpg",
        "fallback_cover": "https://upload.wikimedia.org/wikipedia/en/4/44/Red_Dead_Redemption_II.jpg",
        "theme_accent": "#DC2626",
        "default_topic": "Strange Man lore, cut mechanics & Mount Shann mystery",
        "presets": [
            "🎩 Strange Man & Hidden Supernatural Encounters",
            "🌲 Cut Guarma Content & Unfinished Map Zones",
            "🐴 Physics Glitches & Ragdoll Dev Workarounds",
            "📜 Arthur Morgan's Journal Secrets & Foreshadowing",
            "⚙️ Dynamic Weather & Animal AI Engineering Feats",
        ],
    },
    {
        "id": "cyberpunk2077",
        "title": "Cyberpunk 2077",
        "short_name": "Cyberpunk 2077",
        "tagline": "Night City // Phantom Liberty",
        "release": "2020 / 2.0 Update",
        "studio": "CD PROJEKT RED",
        "is_hero": False,
        "badge": "REDEMPTION ARC",
        "cover_url": "https://shared.fastly.steamstatic.com/store_item_assets/steam/apps/1091500/library_600x900.jpg",
        "fallback_cover": "https://upload.wikimedia.org/wikipedia/en/9/9f/Cyberpunk_2077_box_art.jpg",
        "theme_accent": "#FACC15",
        "default_topic": "FF:06:B5 Mystery, Night City lore & REDengine to Unreal 5",
        "presets": [
            "🔮 The Unsolved FF:06:B5 ARG Monolith Mystery",
            "🏙️ How Devs Fixed Night City in Update 2.0 & Phantom Liberty",
            "⚡ Infamous Launch Glitches & T-Pose Developer Stories",
            "🤖 Mr. Blue Eyes & Blackwall AI Conspiracy",
            "🚗 Cut Wall-Running & Monorail Mechanics",
        ],
    },
    {
        "id": "kcd2",
        "title": "Kingdom Come: Deliverance 2",
        "short_name": "KCD 2",
        "tagline": "Bohemian Medieval Realism // Henry's Return",
        "release": "2025",
        "studio": "Warhorse Studios",
        "is_hero": False,
        "badge": "ANTICIPATED RPG",
        "cover_url": "https://shared.fastly.steamstatic.com/store_item_assets/steam/apps/1771300/library_600x900.jpg",
        "fallback_cover": "https://images.igdb.com/igdb/image/upload/t_cover_big/co84vi.jpg",
        "theme_accent": "#B45309",
        "default_topic": "Kuttenberg scale, historical accuracy & CryEngine upgrades",
        "presets": [
            "🏰 Kuttenberg City Scale & Historical Dev Challenges",
            "⚔️ Crossbows, Early Firearms & Combat Physics Overhaul",
            "🍺 Mud, Bathhouses & Extreme Medieval Realism Details",
            "🗡️ Henry & Sir Hans Capon Buddy-Comedy Story Beats",
            "🛠️ Warhorse CryEngine Customization Secrets",
        ],
    },
    {
        "id": "eldenring",
        "title": "Elden Ring",
        "short_name": "Elden Ring",
        "tagline": "Lands Between // Shadow of the Erdtree",
        "release": "2022 / 2024",
        "studio": "FromSoftware",
        "is_hero": False,
        "badge": "GOTY TITAN",
        "cover_url": "https://shared.fastly.steamstatic.com/store_item_assets/steam/apps/1245620/library_600x900.jpg",
        "fallback_cover": "https://upload.wikimedia.org/wikipedia/en/b/b9/Elden_Ring_Box_art.jpg",
        "theme_accent": "#EAB308",
        "default_topic": "Miquella & Messmer lore, cut dream-collecting mechanic",
        "presets": [
            "🌳 Miquella & St. Trina Cut Quests & Dream Brew Lore",
            "⚔️ Let Me Solo Her Community Cultural Impact",
            "🐛 Teleportation & Wrong Warp Speedrunner Glitches",
            "🏰 Shadow Realm Architecture & George R.R. Martin Worldbuilding",
            "🏹 Poison Swamps & Miyazaki Dev Intentions",
        ],
    },
    {
        "id": "gtav",
        "title": "Grand Theft Auto V",
        "short_name": "GTA V",
        "tagline": "Los Santos & Blaine County // 3 Protagonists",
        "release": "2013 / Enhanced",
        "studio": "Rockstar Games",
        "is_hero": False,
        "badge": "RECORD BREAKER",
        "cover_url": "https://shared.fastly.steamstatic.com/store_item_assets/steam/apps/271590/library_600x900.jpg",
        "fallback_cover": "https://upload.wikimedia.org/wikipedia/en/a/a5/Grand_Theft_Auto_V.png",
        "theme_accent": "#10B981",
        "default_topic": "Mount Chiliad mystery, cut single-player DLC & physics bugs",
        "presets": [
            "🛸 Mount Chiliad Mural & The Jetpack Mystery Rabbit Hole",
            "🎬 How Steven Ogg Improvised Trevor Philips' Funniest Scenes",
            "🚁 Swing Set Glitch Legacy & Car Cannon Physics",
            "💾 The Canceled Single-Player Alien & Zombie DLCs",
            "📈 GTA Online Economic Balancing & Heists Dev Lessons",
        ],
    },
    {
        "id": "witcher3",
        "title": "The Witcher 3: Wild Hunt",
        "short_name": "The Witcher 3",
        "tagline": "White Wolf // Blood and Wine",
        "release": "2015 / Next-Gen",
        "studio": "CD PROJEKT RED",
        "is_hero": False,
        "badge": "CLASSIC RPG",
        "cover_url": "https://shared.fastly.steamstatic.com/store_item_assets/steam/apps/292030/library_600x900.jpg",
        "fallback_cover": "https://upload.wikimedia.org/wikipedia/en/0/0c/Witcher_3_cover_art.png",
        "theme_accent": "#3B82F6",
        "default_topic": "Bloody Baron quest design, Roach rooftop bugs & Gaunter O'Dimm",
        "presets": [
            "👹 Gaunter O'Dimm Hidden In Every Background Scene",
            "🐴 Roach On The Roof Physics & CDPR's April Fools Video",
            "⚔️ Bloody Baron Questline Writing Post-Mortem",
            "🐺 The Bovine Defense Force Cow-Exploit Monster Patch",
            "🍷 Toussaint Fairytale Easter Eggs & Unused Audio",
        ],
    },
]

_SERPER_IMAGE_CACHE = {}


def fetch_serper_game_cover(game_name: str, api_key: str = None) -> str:
    """
    Fetch real game cover artwork dynamically via Serper Images API
    (https://google.serper.dev/images with timeout=8).
    """
    clean_name = game_name.strip()
    if not clean_name:
        return ""

    if clean_name in _SERPER_IMAGE_CACHE:
        return _SERPER_IMAGE_CACHE[clean_name]

    key = api_key or os.getenv("SERPER_API_KEY")
    if not key:
        return ""

    try:
        url = "https://google.serper.dev/images"
        headers = {
            "X-API-KEY": key,
            "Content-Type": "application/json",
        }
        payload = json.dumps({"q": f"{clean_name} video game official cover art box", "num": 3})
        resp = requests.post(url, headers=headers, data=payload, timeout=8)
        if resp.status_code == 200:
            images = resp.json().get("images", [])
            for img in images:
                u = img.get("imageUrl") or img.get("link")
                if u and u.startswith("http"):
                    # Avoid social media or dynamic video thumbnails
                    if not any(bad in u.lower() for bad in ["youtube.com", "facebook.com", "tiktok.com"]):
                        _SERPER_IMAGE_CACHE[clean_name] = u
                        return u
    except Exception:
        pass

    return ""


def get_game_by_title(title: str) -> dict:
    """Find a game from the shelf catalog or create a custom entry."""
    clean = title.strip().lower()
    for g in GAME_SHELF:
        if clean in g["title"].lower() or clean in g["short_name"].lower() or g["id"] == clean:
            return g

    # Return structured entry for custom games
    custom_title = title.strip()
    cover = fetch_serper_game_cover(custom_title) or get_dynamic_cover_url(custom_title)

    return {
        "id": "custom",
        "title": custom_title,
        "short_name": custom_title,
        "tagline": "Custom Studio Focus",
        "release": "Community Selected",
        "studio": "Game Studio",
        "is_hero": False,
        "badge": "CUSTOM GAME",
        "cover_url": cover,
        "fallback_cover": "",
        "theme_accent": "#6366F1",
        "default_topic": f"Hidden lore, cut mechanics and infamous dev glitches in {custom_title}",
        "presets": [
            f"🔍 Obscure Lore & Secret Easter Eggs in {custom_title}",
            f"🐛 Physics Glitches & Hilarious Bugs in {custom_title}",
            f"🛠️ Behind-The-Scenes Dev Stories & Workarounds in {custom_title}",
            f"⚡ Speedrun Sequence Breaks & Exploits in {custom_title}",
            f"🎬 Viral Dual-Platform Reel & LinkedIn Script Packet for {custom_title}",
        ],
    }


def get_dynamic_cover_url(game_name: str) -> str:
    """Generate a clean SVG cover card for custom games as a reliable fallback."""
    for g in GAME_SHELF:
        if game_name.lower() in g["title"].lower() or game_name.lower() in g["short_name"].lower():
            return g["cover_url"]

    encoded_title = urllib.parse.quote(game_name[:24])
    svg = f"""<svg xmlns='http://www.w3.org/2000/svg' width='600' height='900' viewBox='0 0 600 900'>
        <defs>
            <linearGradient id='grad' x1='0%' y1='0%' x2='100%' y2='100%'>
                <stop offset='0%' stop-color='#1E1B4B' />
                <stop offset='50%' stop-color='#312E81' />
                <stop offset='100%' stop-color='#0F172A' />
            </linearGradient>
        </defs>
        <rect width='600' height='900' fill='url(#grad)' />
        <rect x='30' y='30' width='540' height='840' rx='16' fill='none' stroke='#6366F1' stroke-width='2' stroke-opacity='0.4' />
        <circle cx='300' cy='360' r='90' fill='#4338CA' fill-opacity='0.5' />
        <text x='300' y='380' font-family='sans-serif' font-size='60' font-weight='bold' fill='#FFFFFF' text-anchor='middle'>🎮</text>
        <text x='300' y='520' font-family='sans-serif' font-size='32' font-weight='800' fill='#F8FAFC' text-anchor='middle'>{game_name[:20]}</text>
        <text x='300' y='570' font-family='sans-serif' font-size='18' font-weight='600' fill='#94A3B8' text-anchor='middle'>REELLORE AI STUDIO</text>
    </svg>"""
    return f"data:image/svg+xml;utf8,{urllib.parse.quote(svg)}"
