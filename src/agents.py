"""
ReelLore AI — 4 CrewAI Agents
===============================
Each agent is role-playing a specialist in the game-content pipeline,
powered exclusively by Groq LLaMA models.
"""

import os
import time
import requests
import litellm
import crewai.llms.cache
from crewai import Agent, LLM
from src.tools import serper_game_search, reddit_miner, steam_patch_notes

# 1. Strip cache_breakpoint to avoid Groq 400 BadRequestError ('property cache_breakpoint is unsupported')
crewai.llms.cache.mark_cache_breakpoint = lambda message: message


def _strip_cache_breakpoint(kwargs):
    if "messages" in kwargs:
        for m in kwargs["messages"]:
            if isinstance(m, dict):
                m.pop("cache_breakpoint", None)


litellm.input_callback = [_strip_cache_breakpoint]
litellm.num_retries = 3

_AVAILABLE_GROQ_MODELS = None
_WORKING_MODELS_CACHE = {}


def test_model_ping(model_id: str, api_key: str = None, timeout: float = 3.0) -> tuple[bool, float, str]:
    """Test if a model responds with HTTP 200 to a chat completion ping."""
    key = api_key or os.getenv("GROQ_API_KEY")
    if not key:
        return False, 999.0, "Missing API Key"
    bare = model_id[5:] if model_id.startswith("groq/") else model_id
    try:
        t0 = time.time()
        resp = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json={"model": bare, "messages": [{"role": "user", "content": "ping"}], "max_tokens": 3},
            timeout=timeout,
        )
        latency = round(time.time() - t0, 3)
        if resp.status_code == 200:
            return True, latency, ""
        err_msg = resp.json().get("error", {}).get("message", resp.text[:120])
        return False, latency, err_msg
    except Exception as e:
        return False, 999.0, str(e)


def get_available_groq_models(api_key: str = None) -> list[str]:
    """
    Fetch all active chat/text models available to this GROQ_API_KEY.
    Filters out whisper/audio/guard/speech models and sorts Llama models to the very top,
    followed by Qwen, Gemma, and GPT-OSS.
    """
    global _AVAILABLE_GROQ_MODELS
    if _AVAILABLE_GROQ_MODELS is not None:
        return _AVAILABLE_GROQ_MODELS

    key = api_key or os.getenv("GROQ_API_KEY")
    discovered_models = []

    if key:
        try:
            resp = requests.get(
                "https://api.groq.com/openai/v1/models",
                headers={"Authorization": f"Bearer {key}"},
                timeout=5,
            )
            if resp.status_code == 200:
                data = resp.json().get("data", [])
                bad_kw = [
                    "whisper", "guard", "prompt-guard", "safeguard",
                    "orpheus", "audio", "speech", "tts", "embedding"
                ]
                for m in data:
                    mid = m.get("id", "")
                    # Filter out non-chat / audio / safety models
                    if any(b in mid.lower() for b in bad_kw):
                        continue
                    out_mods = m.get("output_modalities", ["text"])
                    if "text" not in out_mods:
                        continue
                    discovered_models.append(mid)
        except Exception:
            pass

    # Ensure candidate fast Llama models are always available for selection
    candidates = [
        "llama-3.1-8b-instant",
        "meta-llama/llama-4-scout-17b-16e-instruct",
        "meta-llama/llama-4-maverick-17b-128e-instruct",
        "llama-3.3-70b-versatile",
    ]
    for c in candidates:
        if c not in discovered_models:
            discovered_models.append(c)

    # Sort Llama models to the very top, followed by Qwen, Gemma, GPT-OSS
    def _model_sort_key(mid: str):
        m = mid.lower()
        if "llama" in m:
            if "instant" in m or "8b" in m or "scout" in m or "17b" in m:
                return (0, 0, m)
            return (0, 1, m)
        if "qwen" in m:
            return (1, 0, m)
        if "gemma" in m:
            return (2, 0, m)
        if "20b" in m:
            return (3, 0, m)
        if "120b" in m:
            return (3, 1, m)
        return (4, 0, m)

    discovered_models.sort(key=_model_sort_key)
    _AVAILABLE_GROQ_MODELS = discovered_models
    return discovered_models


def get_fastest_working_model(api_key: str = None) -> str:
    """
    Test candidate models and return the fastest working Llama model if available,
    otherwise the fastest overall working chat model (e.g. qwen/qwen3.8-27b or openai/gpt-oss-20b).
    """
    models = get_available_groq_models(api_key)
    working_llama = []
    working_other = []

    for m in models:
        is_ok, latency, _ = test_model_ping(m, api_key=api_key, timeout=3.0)
        if is_ok:
            if "llama" in m.lower():
                working_llama.append((latency, m))
            else:
                working_other.append((latency, m))

    if working_llama:
        working_llama.sort()
        return working_llama[0][1]

    if working_other:
        working_other.sort()
        return working_other[0][1]

    return "qwen/qwen3.8-27b"


def _resolve_model(model_name: str) -> str:
    """
    Pass user's selected sidebar model directly to CrewAI / LiteLLM without hardcoded overrides.
    """
    if not model_name:
        default_model = get_fastest_working_model()
        return f"groq/{default_model}"
    clean = model_name.strip()
    if clean.startswith("groq/"):
        return clean
    return f"groq/{clean}"


def _get_llm(model_name: str = None) -> LLM:
    """Create a CrewAI-compatible LLM instance pointing directly at Groq."""
    target_model = _resolve_model(model_name)
    return LLM(
        model=target_model,
        api_key=os.getenv("GROQ_API_KEY"),
        temperature=0.7,
        num_retries=3,
    )


def build_agents(model_name: str = None) -> dict:
    """Return a dict of the four pipeline agents, keyed by their role slugs."""
    llm = _get_llm(model_name)

    lore_scout = Agent(
        role="Lore_And_Trivia_Scout",
        goal=(
            "Uncover obscure Easter eggs, cut mechanics, hidden developer messages, "
            "secret lore details, and behind-the-scenes trivia about the target game."
        ),
        backstory=(
            "You are a veteran gaming archaeologist who has spent years digging through "
            "developer interviews, data-mined assets, and obscure wiki footnotes. "
            "You find the stories that 99% of gamers never hear about."
        ),
        tools=[serper_game_search],
        llm=llm,
        max_iter=2,
        max_rpm=10,
        verbose=True,
    )

    devlog_archaeologist = Agent(
        role="DevLog_And_Bug_Archaeologist",
        goal=(
            "Find the funniest bugs, most creative developer workarounds, physics "
            "glitches, patch note stories, and 'how they faked it' engineering tales."
        ),
        backstory=(
            "You are a game-development historian who obsesses over patch notes, "
            "community bug reports, and developer post-mortems. You know every "
            "infamous glitch and the hilarious hacks devs used to ship on time."
        ),
        tools=[reddit_miner, steam_patch_notes],
        llm=llm,
        max_iter=2,
        max_rpm=10,
        verbose=True,
    )

    scriptwriter = Agent(
        role="Viral_Reel_Scriptwriter",
        goal=(
            "Transform raw lore findings and dev-log stories into three punchy, "
            "scroll-stopping 45-60 second Instagram Reel scripts with a Hook, "
            "Body, and Loopable Climax structure."
        ),
        backstory=(
            "You are a viral short-form content creator with 2M+ followers. "
            "You know exactly how to open with a hook that stops the scroll, "
            "build tension with rapid-fire storytelling, and end with a CTA "
            "that makes viewers loop or share."
        ),
        tools=[],
        llm=llm,
        max_iter=2,
        max_rpm=10,
        verbose=True,
    )

    production_director = Agent(
        role="Production_And_SEO_Director",
        goal=(
            "Create a full production package: visual B-roll cues, on-screen text "
            "overlays, voiceover tone tags, AI image/video prompts, and optimized "
            "Instagram captions with SEO hashtags."
        ),
        backstory=(
            "You are a professional content production director and Instagram SEO "
            "specialist. You turn scripts into shoot-ready production sheets that "
            "any editor can follow, and you write captions that push Reels into "
            "the Explore page algorithm."
        ),
        tools=[],
        llm=llm,
        max_iter=2,
        max_rpm=10,
        verbose=True,
    )

    return {
        "lore_scout": lore_scout,
        "devlog_archaeologist": devlog_archaeologist,
        "scriptwriter": scriptwriter,
        "production_director": production_director,
    }
