"""
ReelLore AI — Groq Model Discovery, True Meta Llama Filtering & Resilience
==========================================================================
Provides dynamic Groq model discovery, true Meta Llama prioritization,
filtering out non-Llama/non-chat models (including 'allam', 'whisper', 'guard',
'orpheus', 'playai', 'distil-whisper'), and automatic model fallback chaining
for high-throughput agent execution without stalling on 429s or 404s.
Ensures large TPM-constrained models (like openai/gpt-oss-120b) are never defaulted.
"""

import os
import time
import requests
import litellm

# Explicit keywords and prefixes to filter out from primary chat model selection.
# NOTE: 'allam-2-7b' is ALLaM (Arabic Large Language Model on Groq), NOT a typo for Meta Llama!
DISALLOWED_KEYWORDS = [
    "allam",
    "whisper",
    "guard",
    "prompt-guard",
    "safeguard",
    "orpheus",
    "playai",
    "distil-whisper",
    "audio",
    "speech",
    "tts",
    "embedding",
    "embed",
    "moderation",
]

# Standard candidate Meta Llama models to check and prioritize
KNOWN_META_LLAMA_MODELS = [
    "llama-3.1-8b-instant",
    "llama-3.3-70b-versatile",
    "meta-llama/llama-4-scout-17b-16e-instruct",
    "meta-llama/llama-4-maverick-17b-128e-instruct",
    "llama3-70b-8192",
    "llama3-8b-8192",
]

# Fast, high-TPM fallbacks (avoiding gpt-oss-120b which has a strict 8000 TPM limit)
FAST_FALLBACK_MODELS = [
    "qwen/qwen3.8-27b",
    "openai/gpt-oss-20b",
]

_DISCOVERED_MODELS_CACHE = None
_PING_RESULTS_CACHE = {}


def is_excluded_model(model_id: str) -> bool:
    """Check if model ID belongs to audio, safety, or non-Meta-Llama models like ALLaM."""
    mid = model_id.lower().strip()
    return any(bad in mid for bad in DISALLOWED_KEYWORDS)


def is_true_meta_llama(model_id: str) -> bool:
    """
    Check if model is a genuine Meta Llama model.
    Explicitly ensures ALLaM (Arabic model) and guard models are NOT treated as Llama.
    """
    mid = model_id.lower().strip()
    if is_excluded_model(mid):
        return False
    return "llama" in mid


def test_model_ping(model_id: str, api_key: str = None, timeout: float = 3.5) -> tuple[bool, float, str]:
    """Test if a model responds with HTTP 200 to a chat completion ping."""
    key = api_key or os.getenv("GROQ_API_KEY")
    if not key:
        return False, 999.0, "Missing GROQ_API_KEY"

    bare = model_id[5:] if model_id.startswith("groq/") else model_id
    if bare in _PING_RESULTS_CACHE:
        cached_ok, cached_lat, cached_err = _PING_RESULTS_CACHE[bare]
        return cached_ok, cached_lat, cached_err

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
            _PING_RESULTS_CACHE[bare] = (True, latency, "")
            return True, latency, ""

        try:
            err_msg = resp.json().get("error", {}).get("message", resp.text[:120])
        except Exception:
            err_msg = resp.text[:120]
        _PING_RESULTS_CACHE[bare] = (False, latency, err_msg)
        return False, latency, err_msg
    except Exception as e:
        _PING_RESULTS_CACHE[bare] = (False, 999.0, str(e))
        return False, 999.0, str(e)


def get_available_groq_models(api_key: str = None) -> list[str]:
    """
    Fetch all active chat models available to this GROQ_API_KEY.
    - Excludes 'allam', 'whisper', 'guard', 'orpheus', 'playai', 'distil-whisper'.
    - Prioritizes true Meta Llama models at the very top (3.1-8b-instant, 3.3-70b-versatile, llama-4).
    - Follows with fast Qwen (qwen3.8-27b) and GPT-OSS (gpt-oss-20b).
    - Places gpt-oss-120b at the bottom and never as default (due to 8000 TPM limit).
    """
    global _DISCOVERED_MODELS_CACHE
    if _DISCOVERED_MODELS_CACHE is not None:
        return _DISCOVERED_MODELS_CACHE

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
                for m in data:
                    mid = m.get("id", "")
                    if is_excluded_model(mid):
                        continue
                    out_mods = m.get("output_modalities", ["text"])
                    if "text" not in out_mods:
                        continue
                    discovered_models.append(mid)
        except Exception:
            pass

    # Ensure known Meta Llama and fast fallback models are included in candidates
    for c in KNOWN_META_LLAMA_MODELS + FAST_FALLBACK_MODELS:
        if c not in discovered_models and not is_excluded_model(c):
            discovered_models.append(c)

    # Sort hierarchy:
    # 0: True Meta Llama fast/instant (llama-3.1-8b-instant, llama-4-scout)
    # 1: True Meta Llama large (llama-3.3-70b-versatile, llama-4-maverick)
    # 2: Fast Qwen (qwen/qwen3.8-27b)
    # 3: Fast GPT-OSS (openai/gpt-oss-20b)
    # 4: Other models
    # 5: openai/gpt-oss-120b (strictly at bottom to prevent 8000 TPM limit crash)
    def _model_sort_key(mid: str):
        m = mid.lower()
        if "120b" in m:
            return (5, 0, m)
        if is_true_meta_llama(m):
            if "instant" in m or "8b" in m or "scout" in m:
                return (0, 0, m)
            return (1, 0, m)
        if "qwen" in m:
            return (2, 0, m)
        if "gpt-oss-20b" in m or "20b" in m:
            return (3, 0, m)
        return (4, 0, m)

    discovered_models.sort(key=_model_sort_key)
    _DISCOVERED_MODELS_CACHE = discovered_models
    return discovered_models


def get_verified_working_models(api_key: str = None) -> list[str]:
    """Test candidate models and return all models that currently return HTTP 200, prioritizing Llama and fast models."""
    candidates = get_available_groq_models(api_key)
    working_llama = []
    working_fast_fallback = []
    working_other = []

    for m in candidates:
        is_ok, latency, _ = test_model_ping(m, api_key=api_key, timeout=3.0)
        if is_ok:
            if is_true_meta_llama(m):
                working_llama.append((latency, m))
            elif "qwen" in m.lower() or "20b" in m.lower():
                working_fast_fallback.append((latency, m))
            elif "120b" not in m.lower():
                working_other.append((latency, m))

    working_llama.sort()
    working_fast_fallback.sort()
    working_other.sort()

    res = (
        [m for _, m in working_llama]
        + [m for _, m in working_fast_fallback]
        + [m for _, m in working_other]
    )

    if not res:
        # High-throughput safe default
        return ["qwen/qwen3.8-27b", "openai/gpt-oss-20b"]
    return res


def get_fastest_working_model(api_key: str = None) -> str:
    """
    Return the fastest working true Meta Llama model if active,
    otherwise the fastest high-throughput chat model (e.g. qwen/qwen3.8-27b or gpt-oss-20b).
    Strictly avoids openai/gpt-oss-120b to prevent TPM limit errors.
    """
    verified = get_verified_working_models(api_key)
    for m in verified:
        if is_true_meta_llama(m):
            return m
    # Return fastest verified fallback (qwen3.8-27b or gpt-oss-20b)
    for m in verified:
        if "120b" not in m.lower():
            return m
    return verified[0]


def get_fallback_chain(preferred_model: str, api_key: str = None) -> list[str]:
    """
    Build an ordered fallback chain for the chosen model.
    If the preferred model hits rate limits (429) or transient errors,
    LiteLLM / CrewAI seamlessly steps through this list.
    """
    clean_pref = preferred_model[5:] if preferred_model.startswith("groq/") else preferred_model
    verified = get_verified_working_models(api_key)

    chain = []
    for m in verified:
        clean_m = m[5:] if m.startswith("groq/") else m
        # Skip preferred model and avoid 120b in fallback
        if clean_m != clean_pref and "120b" not in clean_m.lower():
            chain.append(f"groq/{clean_m}")

    if not chain:
        chain = ["groq/qwen/qwen3.8-27b", "groq/openai/gpt-oss-20b"]

    return chain


def configure_litellm_fallbacks(preferred_model: str, api_key: str = None) -> list[str]:
    """Configure LiteLLM global fallback routes so that 429s/404s trigger immediate model rotation."""
    target_key = f"groq/{preferred_model}" if not preferred_model.startswith("groq/") else preferred_model
    fallbacks = get_fallback_chain(preferred_model, api_key)

    try:
        litellm.fallbacks = [{target_key: fallbacks}]
    except Exception:
        pass

    return fallbacks
