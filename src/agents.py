"""
ReelLore AI — 4 CrewAI Agents
===============================
Specialist agents in the game-content pipeline, powered by Groq LPU models
with automatic model fallback chaining and true Meta Llama prioritization.
Configured with max_iter=1 to strictly enforce high throughput and keep token
usage well within Groq free-tier TPM limits.
"""

import os
import litellm
import crewai.llms.cache
from crewai import Agent, LLM
from src.tools import serper_game_search, reddit_miner, steam_patch_notes
from src.models import (
    get_available_groq_models,
    get_fastest_working_model,
    get_fallback_chain,
    configure_litellm_fallbacks,
)

# 1. Strip cache_breakpoint to avoid Groq 400 BadRequestError ('property cache_breakpoint is unsupported')
crewai.llms.cache.mark_cache_breakpoint = lambda message: message


def _strip_cache_breakpoint(kwargs):
    if "messages" in kwargs:
        for m in kwargs["messages"]:
            if isinstance(m, dict):
                m.pop("cache_breakpoint", None)


litellm.input_callback = [_strip_cache_breakpoint]
litellm.num_retries = 3


def _resolve_model(model_name: str = None) -> str:
    """Resolve model name with fallback to the fastest working active model."""
    if not model_name:
        default_model = get_fastest_working_model()
        return f"groq/{default_model}"
    clean = model_name.strip()
    if clean.startswith("groq/"):
        return clean
    return f"groq/{clean}"


def _get_llm(model_name: str = None) -> LLM:
    """
    Create a CrewAI-compatible LLM instance pointing directly at Groq
    with automatic model fallback chaining.
    """
    target_model = _resolve_model(model_name)
    fallbacks = configure_litellm_fallbacks(target_model)

    return LLM(
        model=target_model,
        api_key=os.getenv("GROQ_API_KEY"),
        temperature=0.7,
        num_retries=3,
        fallbacks=fallbacks,
    )


def build_agents(model_name: str = None) -> dict:
    """
    Return a dict of the four pipeline agents, keyed by their role slugs.
    Uses max_iter=1 to keep TPM usage well under free-tier limits.
    """
    llm = _get_llm(model_name)

    lore_scout = Agent(
        role="Lore_And_Trivia_Scout",
        goal=(
            "Uncover 3-4 obscure Easter eggs, cut mechanics, and lore secrets "
            "about the target game and topic with verifiable source links."
        ),
        backstory=(
            "You are a gaming archaeologist who uncovers hidden secrets, cut mechanics, "
            "and map details with exact source attribution and verification notes."
        ),
        tools=[serper_game_search],
        llm=llm,
        max_iter=1,  # Strict limit to prevent TPM limit spikes
        max_rpm=10,
        verbose=True,
    )

    devlog_archaeologist = Agent(
        role="DevLog_And_Bug_Archaeologist",
        goal=(
            "Find 3-4 fascinating game engineering feats, physics engine quirks, "
            "and developer workarounds with community and dev citations."
        ),
        backstory=(
            "You are a game development historian who documents engine feats, "
            "physics bugs, and developer workarounds with real sources."
        ),
        tools=[reddit_miner, steam_patch_notes],
        llm=llm,
        max_iter=1,  # Strict limit to prevent TPM limit spikes
        max_rpm=10,
        verbose=True,
    )

    scriptwriter = Agent(
        role="Dual_Platform_Virality_Scriptwriter",
        goal=(
            "Transform research into 3 complete content bundles: time-coded "
            "Instagram Reel scripts (0-3s hook, beat pacing, loop ending) AND "
            "algorithmic high-dwell LinkedIn posts (professional storytelling, comment CTA)."
        ),
        backstory=(
            "You are an elite short-form scriptwriter and LinkedIn strategist who crafts "
            "scroll-stopping hooks, seamless audio loops, and high-dwell professional posts."
        ),
        tools=[],
        llm=llm,
        max_iter=1,
        max_rpm=10,
        verbose=True,
    )

    production_director = Agent(
        role="Production_And_Proof_Director",
        goal=(
            "Deliver a shoot-ready production package and human-readable Proof of Content "
            "with B-roll cues, voiceover tags, Instagram captions, and clickable sources."
        ),
        backstory=(
            "You are a Senior Creative Director who turns scripts into shoot sheets with "
            "kinetic text overlays, B-roll cues, and a verified Proof of Content matrix."
        ),
        tools=[],
        llm=llm,
        max_iter=1,
        max_rpm=10,
        verbose=True,
    )

    return {
        "lore_scout": lore_scout,
        "devlog_archaeologist": devlog_archaeologist,
        "scriptwriter": scriptwriter,
        "production_director": production_director,
    }
