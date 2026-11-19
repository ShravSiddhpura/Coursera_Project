"""
ReelLore AI — Custom Tools for Multi-Agent Game Research
=========================================================
Three custom tools that gather real-time data from Google (Serper),
Reddit JSON API, and Steam Web API with concise token footprints (~700 chars max)
and 10s timeouts to strictly prevent Groq TPM rate limit errors.
"""

import os
import json
import requests
from crewai.tools import tool


# ───────────────────────────────── 1. Serper Google Search ──────────
@tool("SerperGameSearchTool")
def serper_game_search(query: str) -> str:
    """Search the web for game lore, Easter eggs, dev interviews, and behind-the-scenes stories using Google via Serper API.
    Input should be a concise descriptive search query string about a video game topic."""
    api_key = os.getenv("SERPER_API_KEY")
    if not api_key:
        return "ERROR: SERPER_API_KEY not found in environment."

    url = "https://google.serper.dev/search"
    headers = {
        "X-API-KEY": api_key,
        "Content-Type": "application/json",
    }
    payload = json.dumps({"q": query, "num": 4})

    try:
        response = requests.post(url, headers=headers, data=payload, timeout=10)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as exc:
        return f"Serper search note: {exc}"[:300]

    results = []
    for item in data.get("organic", [])[:3]:
        title = item.get("title", "No Title")
        snippet = (item.get("snippet", "") or "")[:120]
        link = item.get("link", "")
        results.append(f"• **{title}**: {snippet} | Link: {link}")

    if not results:
        return "No specific search results found."

    text = "\n".join(results)
    # Strict 700 char limit to protect Groq TPM budget
    return text[:700]


# ───────────────────────────────── 2. Reddit JSON Miner ─────────────
@tool("RedditMinerTool")
def reddit_miner(query: str) -> str:
    """Mine Reddit for community discussions about game bugs, Easter eggs, dev stories, leaks, and glitches.
    Input should be the game name or concise topic."""
    headers = {"User-Agent": "ReelLoreAI/1.0"}
    clean_query = query.strip()
    search_terms = f"{clean_query} bug OR easter egg OR leak"
    reddit_url = (
        f"https://www.reddit.com/search.json"
        f"?q={requests.utils.quote(search_terms)}&limit=4&sort=relevance"
    )

    try:
        resp = requests.get(reddit_url, headers=headers, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        posts = data.get("data", {}).get("children", [])
        if not posts:
            raise ValueError("Empty Reddit results")

        results = []
        for post in posts[:3]:
            d = post.get("data", {})
            title = d.get("title", "No Title")[:80]
            selftext = (d.get("selftext") or "")[:100]
            permalink = f"https://reddit.com{d.get('permalink', '')}"
            results.append(f"• [Reddit] **{title}**: {selftext} | Link: {permalink}")

        text = "\n".join(results)
        return text[:700]

    except Exception:
        # Fast fallback: concise Serper search
        fallback_query = f"site:reddit.com {clean_query} bug OR easter egg"
        res = serper_game_search.run(fallback_query)
        return str(res)[:700]


# ───────────────────────────────── 3. Steam Patch Notes ─────────────
@tool("SteamPatchNotesTool")
def steam_patch_notes(game_name: str) -> str:
    """Fetch developer patch notes, bug fixes, and update logs from the Steam API for a given game.
    Input should be the name of a video game."""
    # Step 1 — Find the Steam App ID
    search_url = (
        f"https://store.steampowered.com/api/storesearch/"
        f"?term={requests.utils.quote(game_name)}&l=english&cc=US"
    )
    try:
        resp = requests.get(search_url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as exc:
        return f"Steam store search note: {exc}"[:300]

    items = data.get("items", [])
    if not items:
        return f"No Steam app found for '{game_name}'. (Note: Non-Steam titles like GTA 6 are researched via dev interviews)."

    appid = items[0].get("id")
    app_name = items[0].get("name", game_name)

    # Step 2 — Fetch news / patch notes
    news_url = (
        f"https://api.steampowered.com/ISteamNews/GetNewsForApp/v0002/"
        f"?appid={appid}&count=2&maxlength=250&format=json"
    )
    try:
        resp = requests.get(news_url, timeout=10)
        resp.raise_for_status()
        news_data = resp.json()
    except requests.RequestException as exc:
        return f"Steam news fetch note: {exc}"[:300]

    news_items = news_data.get("appnews", {}).get("newsitems", [])
    if not news_items:
        return f"No patch notes found for '{app_name}' (AppID {appid})."

    results = []
    for item in news_items[:2]:
        title = item.get("title", "Untitled")[:80]
        contents = (item.get("contents") or "")[:150]
        url = item.get("url", "")
        results.append(f"• [Steam] **{title}**: {contents} | Link: {url}")

    text = f"Steam Notes ({app_name}):\n" + "\n".join(results)
    return text[:700]
