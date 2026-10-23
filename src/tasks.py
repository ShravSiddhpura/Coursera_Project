"""
ReelLore AI — 4 Sequential Tasks
==================================
Each task feeds its output as context to the next agent,
forming a sequential research → writing → production pipeline.
All individual outputs are saved to ./outputs/ for proof.
"""

import os
from crewai import Task

OUTPUTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "outputs")


def build_tasks(agents: dict, game_name: str, content_focus: str = "All-Rounder") -> list:
    """Create the four sequential tasks for the given game and content focus."""

    focus_hints = {
        "All-Rounder": "Cover a balanced mix of lore, Easter eggs, famous bugs, and dev stories.",
        "Lore & Easter Eggs": "Focus heavily on hidden lore, secret references, cut content, and Easter eggs.",
        "Famous Bugs & Patch Notes": "Prioritize legendary bugs, physics glitches, and memorable patch notes.",
        "Dev Stories": "Emphasize behind-the-scenes development stories, crunch tales, and engineering hacks.",
    }
    focus_note = focus_hints.get(content_focus, focus_hints["All-Rounder"])

    task_1_lore = Task(
        description=(
            f"Research the game **{game_name}** thoroughly.\n"
            f"Content Focus: {focus_note}\n\n"
            f"Find at least 5 obscure or surprising pieces of game lore, Easter eggs, "
            f"cut mechanics, hidden developer messages, or secret details about {game_name}. "
            f"For each finding, provide the source URL when available.\n"
            f"Structure your output with clear numbered headings."
        ),
        expected_output=(
            f"A detailed Markdown document listing 5+ fascinating lore findings about "
            f"{game_name}, each with a heading, explanation, and source link."
        ),
        agent=agents["lore_scout"],
        output_file=os.path.join(OUTPUTS_DIR, "01_lore_findings.md"),
    )

    task_2_devlog = Task(
        description=(
            f"Research developer logs, community bug reports, and Steam patch notes for **{game_name}**.\n"
            f"Content Focus: {focus_note}\n\n"
            f"Find at least 5 interesting stories: hilarious bugs, physics glitches, "
            f"creative developer workarounds, or 'how they faked it' engineering tales. "
            f"Include real patch note excerpts when available."
        ),
        expected_output=(
            f"A detailed Markdown document listing 5+ dev-log stories, bugs, or patch "
            f"note highlights for {game_name}, each with context and source references."
        ),
        agent=agents["devlog_archaeologist"],
        output_file=os.path.join(OUTPUTS_DIR, "02_dev_and_bugs.md"),
    )

    task_3_scripts = Task(
        description=(
            f"Using the lore findings and dev-log stories gathered about **{game_name}**, "
            f"write **3 distinct Instagram Reel scripts** (45-60 seconds each).\n\n"
            f"Each script MUST follow this structure:\n"
            f"- **Hook (0-3s):** A scroll-stopping opening line.\n"
            f"- **Body/Pacing (3-45s):** Rapid-fire storytelling with 3-4 key beats.\n"
            f"- **Loopable Climax/CTA (45-60s):** A mind-blowing payoff + call to action.\n\n"
            f"Make them sound natural, conversational, and shareable."
        ),
        expected_output=(
            f"3 complete Instagram Reel scripts for {game_name} in Markdown, "
            f"each clearly structured with Hook, Body, and Climax/CTA sections."
        ),
        agent=agents["scriptwriter"],
        context=[task_1_lore, task_2_devlog],
        output_file=os.path.join(OUTPUTS_DIR, "03_reel_scripts.md"),
    )

    task_4_production = Task(
        description=(
            f"Take the 3 Reel scripts for **{game_name}** and create a complete "
            f"**Production Package** for each script. Include:\n\n"
            f"1. **Visual B-Roll & Gameplay Cues** — Specific gameplay moments or footage to show.\n"
            f"2. **On-Screen Text Overlays** — Key phrases to display on screen with timing.\n"
            f"3. **Voiceover Tone Tags** — [excited], [whisper], [dramatic pause], etc.\n"
            f"4. **AI Visual Prompts** — Prompts to generate supplementary visuals.\n"
            f"5. **Instagram Caption & Hashtags** — SEO-optimized caption with 15-20 hashtags.\n"
        ),
        expected_output=(
            f"A comprehensive Markdown production package for all 3 Reel scripts about "
            f"{game_name}, with B-roll cues, text overlays, voiceover tags, AI prompts, "
            f"and Instagram SEO captions."
        ),
        agent=agents["production_director"],
        context=[task_3_scripts],
        output_file=os.path.join(OUTPUTS_DIR, "04_production_package.md"),
    )

    return [task_1_lore, task_2_devlog, task_3_scripts, task_4_production]
