"""
ReelLore AI — Custom Tools for Multi-Agent Game Research
=========================================================
Three custom tools that gather real-time data from Google (Serper),
Reddit JSON API, and Steam Web API without relying on any
third-party LangChain / CrewAI tool packages.
"""

import os
import json
import requests
from crewai.tools import tool


# ───────────────────────────────── 1. Serper Google Search ──────────
@tool("SerperGameSearchTool")
def serper_game_search(query: str) -> str:
    """Search the web for game lore, Easter eggs, dev interviews, and behind-the-scenes stories using Google via Serper API.
    Input should be a descriptive search query string about a video game topic."""
    api_key = os.getenv("SERPER_API_KEY")
    if not api_key:
        return "ERROR: SERPER_API_KEY not found in environment variables."

    url = "https://google.serper.dev/search"
    headers = {
        "X-API-KEY": api_key,
        "Content-Type": "application/json",
    }
    payload = json.dumps({"q": query, "num": 6})

    try:
        response = requests.post(url, headers=headers, data=payload, timeout=15)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as exc:
        return f"Serper search failed: {exc}"[:1200]

    results = []
    for item in data.get("organic", []):
        title = item.get("title", "No Title")
        snippet = item.get("snippet", "")
        link = item.get("link", "")
        results.append(f"**{title}**\n{snippet}\nSource: {link}")

    if not results:
        return "No search results found."

    text = "\n\n---\n\n".join(results)
    return text[:1200]


# ───────────────────────────────── 2. Reddit JSON Miner ─────────────
@tool("RedditMinerTool")
def reddit_miner(game_name: str) -> str:
    """Mine Reddit for community discussions about game bugs, Easter eggs, dev stories, and glitches.
    Input should be the name of a video game."""
    headers = {"User-Agent": "ReelLoreAI/1.0"}
    search_terms = f"{game_name} bug OR easter egg OR dev story"
    reddit_url = (
        f"https://www.reddit.com/search.json"
        f"?q={requests.utils.quote(search_terms)}&limit=8&sort=relevance"
    )

    try:
        resp = requests.get(reddit_url, headers=headers, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        posts = data.get("data", {}).get("children", [])
        if not posts:
            raise ValueError("Empty Reddit results")

        results = []
        for post in posts:
            d = post.get("data", {})
            title = d.get("title", "No Title")
            selftext = (d.get("selftext") or "")[:300]
            subreddit = d.get("subreddit_name_prefixed", "")
            permalink = f"https://reddit.com{d.get('permalink', '')}"
            score = d.get("score", 0)
            results.append(
                f"**{title}** ({subreddit}, ↑{score})\n{selftext}\nLink: {permalink}"
            )

        text = "\n\n---\n\n".join(results)
        return text[:1200]

    except Exception:
        # Fallback: use Serper with site:reddit.com
        fallback_query = f"site:reddit.com {game_name} bug OR easter egg OR dev story"
        res = serper_game_search.run(fallback_query)
        return str(res)[:1200]


# ───────────────────────────────── 3. Steam Patch Notes ─────────────
@tool("SteamPatchNotesTool")
def steam_patch_notes(game_name: str) -> str:
    """Fetch real developer patch notes, bug fixes, and update logs from the Steam API for a given game.
    Input should be the name of a video game."""
    # Step 1 — Find the Steam App ID
    search_url = (
        f"https://store.steampowered.com/api/storesearch/"
        f"?term={requests.utils.quote(game_name)}&l=english&cc=US"
    )
    try:
        resp = requests.get(search_url, timeout=15)
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as exc:
        return f"Steam store search failed: {exc}"[:1200]

    items = data.get("items", [])
    if not items:
        return f"No Steam app found for '{game_name}'."[:1200]

    appid = items[0].get("id")
    app_name = items[0].get("name", game_name)

    # Step 2 — Fetch news / patch notes
    news_url = (
        f"https://api.steampowered.com/ISteamNews/GetNewsForApp/v0002/"
        f"?appid={appid}&count=5&maxlength=600&format=json"
    )
    try:
        resp = requests.get(news_url, timeout=15)
        resp.raise_for_status()
        news_data = resp.json()
    except requests.RequestException as exc:
        return f"Steam news fetch failed: {exc}"[:1200]

    news_items = (
        news_data.get("appnews", {}).get("newsitems", [])
    )
    if not news_items:
        return f"No patch notes found for '{app_name}' (appid {appid})."[:1200]

    results = []
    for item in news_items:
        title = item.get("title", "Untitled")
        contents = (item.get("contents") or "")[:500]
        url = item.get("url", "")
        author = item.get("author", "Unknown")
        results.append(
            f"**{title}** (by {author})\n{contents}\nLink: {url}"
        )

    text = f"## Steam Patch Notes for {app_name} (AppID: {appid})\n\n" + "\n\n---\n\n".join(results)
    return text[:1200]
