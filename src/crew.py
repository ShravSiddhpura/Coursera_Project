"""
ReelLore AI — Crew Orchestration
==================================
Builds and kicks off the sequential 4-agent crew with callback hooks
for real-time Streamlit telemetry.
"""

import os
import time
from datetime import datetime
from crewai import Crew, Process
from src.agents import build_agents
from src.tasks import build_tasks


def _timestamp() -> str:
    return datetime.now().strftime("%H:%M:%S")


def run_crew(
    game_name: str,
    model_name: str = None,
    content_focus: str = "All-Rounder",
    log_callback=None,
    status_box=None,
    progress_callback=None,
    banner_callback=None,
):
    """
    Build and execute the full 4-agent crew.

    Parameters
    ----------
    game_name : str
        The video game to research.
    model_name : str, optional
        Groq model identifier (e.g. ``groq/llama-3.1-8b-instant`` or ``groq/qwen/qwen3.8-27b``).
    content_focus : str
        Content direction hint for the agents.
    log_callback : callable, optional
        ``log_callback(msg: str)`` — called on every step / task event.
    status_box : Streamlit delta placeholder or status container, optional
        Interactive status box for real-time progress updates.
    progress_callback : callable, optional
        ``progress_callback(percentage: float, label: str)`` for real-time animated progress bar.
    banner_callback : callable, optional
        ``banner_callback(agent_name: str, current_action: str)`` for pulsing loader banner.

    Returns
    -------
    dict
        ``{"final_output": str, "task_outputs": list[dict], "logs": list[str]}``
    """

    logs: list[str] = []

    def _log(msg: str):
        entry = f"[{_timestamp()}] {msg}"
        logs.append(entry)
        if log_callback:
            try:
                log_callback(entry)
            except Exception:
                pass
        if status_box:
            try:
                status_box.write(entry)
            except Exception:
                pass

    # ── Initial Progress & Banner ───────────────────────────────────
    if progress_callback:
        try:
            progress_callback(0.10, "⏳ Agent 1/4: Lore & Trivia Scout is searching wikis & trivia...")
        except Exception:
            pass

    if banner_callback:
        try:
            banner_callback("Agent 1/4: Lore & Trivia Scout", "Initializing agent pipeline and tools...")
        except Exception:
            pass

    # ── Ensure outputs dir ──────────────────────────────────────────
    outputs_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "outputs")
    os.makedirs(outputs_dir, exist_ok=True)

    # ── Build agents & tasks ────────────────────────────────────────
    _log("🔧 Building agents …")
    agents = build_agents(model_name)
    resolved_model = model_name or "default"
    _log(f"✅ 4 agents initialized with model={resolved_model}")

    _log(f"📋 Building tasks for game: {game_name} (focus: {content_focus})")
    tasks = build_tasks(agents, game_name, content_focus)
    _log("✅ 4 tasks created")

    task_files_mapping = [
        ("01_lore_findings.md", "Lore & Trivia Scout"),
        ("02_dev_and_bugs.md", "DevLog & Bug Archaeologist"),
        ("03_reel_scripts.md", "Viral Reel Scriptwriter"),
        ("04_production_package.md", "Production & SEO Director"),
    ]
    task_tracker = {"count": 0}

    # ── Callbacks ───────────────────────────────────────────────────
    def step_callback(step_output):
        """Called after every agent reasoning step."""
        try:
            agent_role = getattr(step_output, "agent", None)
            if not agent_role and hasattr(step_output, "name"):
                agent_role = step_output.name
            if not agent_role:
                agent_role = "Agent"

            # Handle different step output formats across crewai versions
            if hasattr(step_output, "log") and step_output.log:
                log_text = str(step_output.log).strip()[:200]
            elif hasattr(step_output, "output") and step_output.output:
                log_text = str(step_output.output).strip()[:200]
            elif hasattr(step_output, "thought") and step_output.thought:
                log_text = str(step_output.thought).strip()[:200]
            elif hasattr(step_output, "tool") and step_output.tool:
                log_text = f"Tool: {step_output.tool}"
            else:
                log_text = str(step_output).strip()[:200]

            msg = f"🤖 [{agent_role}] Step → {log_text}"
            _log(msg)

            if banner_callback:
                try:
                    tool_name = getattr(step_output, "tool", None)
                    action_summary = f"Tool: {tool_name}" if tool_name else log_text
                    banner_callback(f"Active Agent: {agent_role}", action_summary)
                except Exception:
                    pass
        except Exception:
            _log(f"🤖 Agent Step → {str(step_output)[:150]}")

    def task_callback(task_output):
        """Called when a task finishes. Immediately writes output to disk and updates status."""
        try:
            raw_content = ""
            if hasattr(task_output, "raw") and task_output.raw:
                raw_content = str(task_output.raw)
            else:
                raw_content = str(task_output)

            agent_desc = str(getattr(task_output, "agent", "")).lower()
            idx = task_tracker["count"]

            if "lore" in agent_desc:
                fname, role_name = task_files_mapping[0]
            elif "dev" in agent_desc or "bug" in agent_desc or "archaeologist" in agent_desc:
                fname, role_name = task_files_mapping[1]
            elif "script" in agent_desc or "reel" in agent_desc:
                fname, role_name = task_files_mapping[2]
            elif "production" in agent_desc or "director" in agent_desc or "seo" in agent_desc:
                fname, role_name = task_files_mapping[3]
            elif idx < len(task_files_mapping):
                fname, role_name = task_files_mapping[idx]
            else:
                fname, role_name = (f"task_{idx+1}_output.md", f"Agent {idx+1}")

            task_tracker["count"] += 1

            # Immediately write output to file
            target_path = os.path.join(outputs_dir, fname)
            with open(target_path, "w", encoding="utf-8") as f:
                f.write(raw_content)

            finish_msg = f"✅ [{role_name}] Completed → Saved `outputs/{fname}` ({len(raw_content.split())} words)"
            _log(finish_msg)

            # Update progress bar and banner for next agent
            completed_count = task_tracker["count"]
            if progress_callback:
                try:
                    if completed_count == 1:
                        progress_callback(0.30, "⏳ Agent 2/4: DevLog & Bug Archaeologist is mining patch notes & Reddit...")
                    elif completed_count == 2:
                        progress_callback(0.55, "⏳ Agent 3/4: Viral Reel Scriptwriter is drafting 3 scripts...")
                    elif completed_count == 3:
                        progress_callback(0.80, "⏳ Agent 4/4: Production & SEO Director is generating B-roll & tags...")
                    elif completed_count >= 4:
                        progress_callback(1.00, "✅ All 4 Agents completed successfully!")
                except Exception:
                    pass

            if banner_callback:
                try:
                    if completed_count == 1:
                        banner_callback("Agent 2/4: DevLog & Bug Archaeologist", "Mining community discussions & patch notes...")
                    elif completed_count == 2:
                        banner_callback("Agent 3/4: Viral Reel Scriptwriter", "Structuring Hook, Body & Loopable Climax...")
                    elif completed_count == 3:
                        banner_callback("Agent 4/4: Production & SEO Director", "Building B-roll cues & Instagram captions...")
                    elif completed_count >= 4:
                        banner_callback("Production Pipeline", "Finished all 4 agents successfully!")
                except Exception:
                    pass

        except Exception as exc:
            _log(f"✅ Task Complete → {str(task_output)[:200]}")

    # ── Assemble & Kick-Off ─────────────────────────────────────────
    _log("🚀 Assembling crew and starting sequential execution …")
    start_time = time.time()

    crew = Crew(
        agents=list(agents.values()),
        tasks=tasks,
        process=Process.sequential,
        verbose=True,
        step_callback=step_callback,
        task_callback=task_callback,
        max_rpm=10,
    )

    try:
        result = crew.kickoff()
        elapsed = round(time.time() - start_time, 1)
        _log(f"🏁 Crew finished in {elapsed}s")
    except Exception as exc:
        elapsed = round(time.time() - start_time, 1)
        _log(f"❌ Execution failed after {elapsed}s: {type(exc).__name__}: {str(exc)}")
        raise exc

    # ── Collect individual task outputs ──────────────────────────────
    task_labels = [
        "Lore & Trivia Scout",
        "DevLog & Bug Archaeologist",
        "Viral Reel Scriptwriter",
        "Production & SEO Director",
    ]
    task_files = [
        "01_lore_findings.md",
        "02_dev_and_bugs.md",
        "03_reel_scripts.md",
        "04_production_package.md",
    ]

    task_outputs = []
    for label, fname, task_obj in zip(task_labels, task_files, tasks):
        fpath = os.path.join(outputs_dir, fname)
        # Try reading from file first (most reliable)
        file_content = None
        if os.path.exists(fpath):
            with open(fpath, "r", encoding="utf-8") as f:
                file_content = f.read()
        # Fallback to task output object
        raw = file_content or (
            str(task_obj.output.raw) if hasattr(task_obj, "output") and hasattr(task_obj.output, "raw")
            else str(task_obj.output) if hasattr(task_obj, "output")
            else "Output not captured."
        )
        task_outputs.append({
            "agent": label,
            "file": fname,
            "output": raw,
            "word_count": len(raw.split()),
            "char_count": len(raw),
        })

    final_output = str(result.raw) if hasattr(result, "raw") else str(result)

    return {
        "final_output": final_output,
        "task_outputs": task_outputs,
        "logs": logs,
        "elapsed_seconds": elapsed,
    }
