"""
ReelLore AI — 4 Sequential Tasks (TPM-Optimized Single Predecessor Context)
==========================================================================
Engineered for Dual-Algorithm Virality across Instagram Reels and LinkedIn.
Each task receives ONLY the immediately preceding task as context (context=[prev_task])
to strictly prevent token bloat and keep prompt requests well under Groq free-tier
TPM limits (8,000 TPM limit).
"""

import os
from crewai import Task

OUTPUTS_DIR = "outputs"


def build_tasks(
    agents: dict,
    game_name: str,
    content_focus: str = "All-Rounder",
    specific_topic: str = "",
) -> list:
    """Create the four sequential tasks, passing only context=[prev_task] to prevent TPM limit spikes."""

    topic_str = f" [Topic: {specific_topic}]" if specific_topic else ""

    # ── Task 1: Lore & Trivia Scout ─────────────────────────────────
    task_1_lore = Task(
        description=(
            f"Research 3-4 surprising lore facts, secrets, or map details for **{game_name}**{topic_str}.\n"
            f"For each finding include:\n"
            f"1. Headline and concise breakdown.\n"
            f"2. Status tag: `[CONFIRMED]`, `[COMMUNITY]`, or `[SPECULATION]`.\n"
            f"3. Retrieved source URL link.\n"
            f"4. Suggested visual/trailer timestamp reference."
        ),
        expected_output=(
            f"3-4 structured lore findings for {game_name} with verification tags and source URLs."
        ),
        agent=agents["lore_scout"],
        output_file=os.path.join(OUTPUTS_DIR, "01_lore_findings.md"),
    )

    # ── Task 2: DevLog & Bug Archaeologist ──────────────────────────
    # Context: [task_1_lore] only
    task_2_devlog = Task(
        description=(
            f"Research 3-4 game engine feats, physics glitches, or developer workarounds for **{game_name}**{topic_str}.\n"
            f"Review the lore context and provide:\n"
            f"1. Headline and engineering tale.\n"
            f"2. Status tag (`[CONFIRMED]`, `[COMMUNITY]`, or `[SPECULATION]`).\n"
            f"3. Real Reddit, Steam, or article URL link.\n"
            f"4. Exact glitch or gameplay recreation cue."
        ),
        expected_output=(
            f"3-4 dev stories and engineering highlights for {game_name} with source links."
        ),
        agent=agents["devlog_archaeologist"],
        context=[task_1_lore],
        output_file=os.path.join(OUTPUTS_DIR, "02_dev_and_bugs.md"),
    )

    # ── Task 3: Dual-Platform Virality Scriptwriter ─────────────────
    # Context: [task_2_devlog] only
    task_3_scripts = Task(
        description=(
            f"Using the findings gathered for **{game_name}**{topic_str}, write **3 Complete Content Bundles**:\n\n"
            f"For each bundle provide:\n"
            f"### PART A: Instagram Reel Script (45-60s)\n"
            f"- **[00:00-00:03] Hook**: Scroll-stopping visual pattern interrupt + spoken line.\n"
            f"- **[00:03-00:15] Beat 1**: Curiosity gap & premise.\n"
            f"- **[00:15-00:35] Beat 2**: Rapid 2-4s beat pacing with the technical/lore twist.\n"
            f"- **[00:35-00:50] Beat 3**: Climax payoff.\n"
            f"- **[00:50-00:60] Loop & CTA**: Phrased so the ending loops back into the opening hook + save/share trigger.\n\n"
            f"### PART B: Companion LinkedIn Virality Post\n"
            f"- Opening 2-line hook before '...see more'.\n"
            f"- High-dwell professional narrative (game engineering, simulation scale, or developer leadership).\n"
            f"- 3 bullet takeaways.\n"
            f"- Discussion-driving comment CTA."
        ),
        expected_output=(
            f"3 Complete Content Bundles for {game_name} with time-coded Reel scripts and companion LinkedIn posts."
        ),
        agent=agents["scriptwriter"],
        context=[task_2_devlog],
        output_file=os.path.join(OUTPUTS_DIR, "03_reel_scripts.md"),
    )

    # ── Task 4: Production & Proof Director ─────────────────────────
    # Context: [task_3_scripts] only (prevents cumulative prompt bloat)
    task_4_production = Task(
        description=(
            f"Take the 3 Content Bundles for **{game_name}** and assemble the master production package:\n\n"
            f"1. **Shoot-Ready Production Sheets**: Visual B-roll cues, on-screen text overlays, "
            f"voiceover tone tags (`[intense]`, `[whisper]`), and Instagram captions + 15 hashtags.\n"
            f"2. **Human-Readable Proof of Content & Metadata** (plain English, no raw JSON):\n"
            f"- Where it was taken from: named sources with clickable URLs.\n"
            f"- Fact-Check & Confidence Matrix (🟢 Confirmed, 🟡 Community, 🔴 Speculation).\n"
            f"- Video & Visual Reference Guide: exact trailer timestamps and gameplay scenes for editors."
        ),
        expected_output=(
            f"Master production package for {game_name} with shoot sheets, captions, and verified Proof of Content."
        ),
        agent=agents["production_director"],
        context=[task_3_scripts],
        output_file=os.path.join(OUTPUTS_DIR, "04_production_package.md"),
    )

    return [task_1_lore, task_2_devlog, task_3_scripts, task_4_production]
