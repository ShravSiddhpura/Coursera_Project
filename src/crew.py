"""
ReelLore AI — Crew Orchestration & Execution Engine
====================================================
Builds and kicks off the sequential 4-agent crew with real-time callbacks,
automatic model fallback chaining, inter-task rate-limit smoothing (time.sleep),
Shoot-Ready PDF generation via markdown-it-py + fpdf2, and persistent history storage.
"""

import os
import time
from datetime import datetime
from crewai import Crew, Process
from src.agents import build_agents
from src.tasks import build_tasks
from src.pdf_export import generate_production_pdf
from src.history_store import save_run


def _timestamp() -> str:
    return datetime.now().strftime("%H:%M:%S")


def run_crew(
    game_name: str,
    model_name: str = None,
    content_focus: str = "All-Rounder",
    specific_topic: str = "",
    log_callback=None,
    status_box=None,
    progress_callback=None,
    banner_callback=None,
) -> dict:
    """
    Build and execute the full 4-agent crew for Dual-Platform Content Generation.
    Uses inter-task pause to prevent Groq TPM limit spikes.
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

    if progress_callback:
        try:
            progress_callback(0.08, f"⏳ Agent 1/4: Lore & Trivia Scout is investigating {game_name}…")
        except Exception:
            pass

    if banner_callback:
        try:
            banner_callback("Agent 1/4: Lore & Trivia Scout", f"Initializing research for {game_name}…")
        except Exception:
            pass

    # Ensure outputs dir
    workspace_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    outputs_dir = os.path.join(workspace_root, "outputs")
    os.makedirs(outputs_dir, exist_ok=True)

    _log(f"🔧 Initializing multi-agent crew with model `{model_name or 'auto'}` (auto-fallback enabled)…")
    agents = build_agents(model_name)
    resolved_model = model_name or "auto-verified"
    _log(f"✅ 4 pipeline agents active with model={resolved_model} (max_iter=1, TPM-safe)")

    topic_desc = f" (Topic: {specific_topic})" if specific_topic else ""
    _log(f"📋 Building sequential tasks for **{game_name}**{topic_desc} [Focus: {content_focus}]")
    tasks = build_tasks(agents, game_name, content_focus, specific_topic=specific_topic)
    _log("✅ 4 sequential tasks compiled with single-predecessor context to prevent token spikes")

    task_files_mapping = [
        ("01_lore_findings.md", "Lore & Trivia Scout"),
        ("02_dev_and_bugs.md", "DevLog & Bug Archaeologist"),
        ("03_reel_scripts.md", "Dual-Platform Scriptwriter"),
        ("04_production_package.md", "Production & Proof Director"),
    ]
    task_tracker = {"count": 0}

    def step_callback(step_output):
        """Called after every agent reasoning step."""
        try:
            agent_role = getattr(step_output, "agent", None)
            if not agent_role and hasattr(step_output, "name"):
                agent_role = step_output.name
            if not agent_role:
                agent_role = "Agent"

            if hasattr(step_output, "log") and step_output.log:
                log_text = str(step_output.log).strip()[:180]
            elif hasattr(step_output, "output") and step_output.output:
                log_text = str(step_output.output).strip()[:180]
            elif hasattr(step_output, "thought") and step_output.thought:
                log_text = str(step_output.thought).strip()[:180]
            elif hasattr(step_output, "tool") and step_output.tool:
                log_text = f"Tool: {step_output.tool}"
            else:
                log_text = str(step_output).strip()[:180]

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
            _log(f"🤖 Agent Step → {str(step_output)[:140]}")

    def task_callback(task_output):
        """Called when a task finishes. Writes output to disk and applies inter-task pause."""
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
            elif "script" in agent_desc or "reel" in agent_desc or "virality" in agent_desc:
                fname, role_name = task_files_mapping[2]
            elif "production" in agent_desc or "director" in agent_desc or "proof" in agent_desc:
                fname, role_name = task_files_mapping[3]
            elif idx < len(task_files_mapping):
                fname, role_name = task_files_mapping[idx]
            else:
                fname, role_name = (f"task_{idx+1}_output.md", f"Agent {idx+1}")

            task_tracker["count"] += 1

            # Save immediately to outputs/
            target_path = os.path.join(outputs_dir, fname)
            with open(target_path, "w", encoding="utf-8") as f:
                f.write(raw_content)

            finish_msg = f"✅ [{role_name}] Completed → Saved `outputs/{fname}` ({len(raw_content.split())} words)"
            _log(finish_msg)

            completed_count = task_tracker["count"]
            if progress_callback:
                try:
                    if completed_count == 1:
                        progress_callback(0.35, "⏳ Agent 2/4: DevLog & Bug Archaeologist mining engine post-mortems…")
                    elif completed_count == 2:
                        progress_callback(0.60, "⏳ Agent 3/4: Dual-Platform Scriptwriter structuring Reel hooks & LinkedIn posts…")
                    elif completed_count == 3:
                        progress_callback(0.85, "⏳ Agent 4/4: Production Director compiling shoot sheets & Proof of Content…")
                    elif completed_count >= 4:
                        progress_callback(1.00, "✅ All 4 Agents completed successfully!")
                except Exception:
                    pass

            if banner_callback:
                try:
                    if completed_count == 1:
                        banner_callback("Agent 2/4: DevLog & Bug Archaeologist", "Mining engine post-mortems & bugs…")
                    elif completed_count == 2:
                        banner_callback("Agent 3/4: Dual-Platform Scriptwriter", "Crafting 0-3s pattern-interrupts & LinkedIn narrative…")
                    elif completed_count == 3:
                        banner_callback("Agent 4/4: Production & Proof Director", "Verifying citations & B-roll timestamps…")
                    elif completed_count >= 4:
                        banner_callback("Production Deck", "All agent deliverables completed!")
                except Exception:
                    pass

            # Inter-task rate-limit smoothing pause
            if completed_count < 4:
                _log("⏳ Applying TPM smoothing buffer (2s pause)…")
                time.sleep(2)

        except Exception as exc:
            _log(f"✅ Task Complete → {str(task_output)[:160]}")

    # Assemble & Kick-Off
    _log("🚀 Assembling CrewAI sequential pipeline and executing…")
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
        _log(f"🏁 Multi-Agent Crew finished in {elapsed}s")
    except Exception as exc:
        elapsed = round(time.time() - start_time, 1)
        _log(f"❌ Execution failed after {elapsed}s: {type(exc).__name__}: {str(exc)}")
        raise exc

    # Collect outputs
    task_labels = [
        "Lore & Trivia Scout",
        "DevLog & Bug Archaeologist",
        "Dual-Platform Virality Scriptwriter",
        "Production & Proof Director",
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
        file_content = None
        if os.path.exists(fpath):
            with open(fpath, "r", encoding="utf-8") as f:
                file_content = f.read()

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

    # Generate PDF via src/pdf_export.py
    clean_game_name = game_name.replace(" ", "_")
    pdf_filename = f"ReelLore_{clean_game_name}_Script_Packet.pdf"
    pdf_filepath = os.path.join(outputs_dir, pdf_filename)
    _log("📄 Generating Shoot-Ready PDF Script & Proof Packet…")
    try:
        pdf_bytes = generate_production_pdf(
            game_name=game_name,
            topic=specific_topic,
            model_name=resolved_model,
            content_focus=content_focus,
            final_package=final_output,
            task_outputs=task_outputs,
            output_filepath=pdf_filepath,
        )
        _log(f"✅ Generated Shoot-Ready PDF: `outputs/{pdf_filename}` ({len(pdf_bytes):,} bytes)")
    except Exception as pdf_err:
        _log(f"⚠️ PDF generation note: {pdf_err}")
        pdf_bytes = None

    # Save to history_store
    _log("💾 Persisting run to local `history/` store…")
    try:
        run_id = save_run(
            game_name=game_name,
            topic=specific_topic,
            model_name=resolved_model,
            content_focus=content_focus,
            final_output=final_output,
            task_outputs=task_outputs,
            logs=logs,
            elapsed_seconds=elapsed,
            pdf_bytes=pdf_bytes,
        )
        _log(f"✅ Run permanently saved to history: `{run_id}`")
    except Exception as hist_err:
        _log(f"⚠️ History save note: {hist_err}")
        run_id = f"run_{int(time.time())}"

    return {
        "final_output": final_output,
        "task_outputs": task_outputs,
        "logs": logs,
        "elapsed_seconds": elapsed,
        "pdf_bytes": pdf_bytes,
        "pdf_filename": pdf_filename,
        "run_id": run_id,
        "game_name": game_name,
        "topic": specific_topic,
        "model_name": resolved_model,
    }
