"""
ReelLore AI — Persistent Run History Store (Local + Session + Exportable)
========================================================================
Persists completed multi-agent generation runs to ./history/ directory as
JSON metadata, full Markdown package, and Shoot-Ready PDF packets.
Allows one-click reload and instant PDF download across refreshes without
clobbering st.session_state.latest_run.
"""

import os
import json
import re
from datetime import datetime

HISTORY_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "history")


def _ensure_history_dir():
    os.makedirs(HISTORY_DIR, exist_ok=True)


def _slugify(text: str) -> str:
    s = re.sub(r"[^\w\s-]", "", str(text)).strip().lower()
    return re.sub(r"[-\s]+", "_", s)[:24]


def save_run(
    game_name: str,
    topic: str = "",
    model_name: str = "groq",
    content_focus: str = "All-Rounder",
    final_output: str = "",
    task_outputs: list[dict] = None,
    logs: list[str] = None,
    elapsed_seconds = "--",
    pdf_bytes: bytes = None,
    **kwargs,
) -> str:
    """
    Save a completed generation run to the local history/ directory.
    Returns the generated run_id.
    """
    _ensure_history_dir()
    now = datetime.now()
    timestamp_slug = now.strftime("%Y%m%d_%H%M%S")
    game_slug = _slugify(game_name)
    run_id = f"run_{timestamp_slug}_{game_slug}"

    resolved_output = final_output or kwargs.get("final_package", "")

    # Calculate total words across all agent task outputs
    total_words = 0
    if task_outputs:
        total_words = sum(t.get("word_count", len(t.get("output", "").split())) for t in task_outputs)
    if total_words == 0 and resolved_output:
        total_words = len(resolved_output.split())

    has_pdf = False
    if pdf_bytes:
        pdf_path = os.path.join(HISTORY_DIR, f"{run_id}.pdf")
        try:
            with open(pdf_path, "wb") as f:
                f.write(pdf_bytes)
            has_pdf = True
        except Exception:
            has_pdf = False

    # Save full markdown package
    md_path = os.path.join(HISTORY_DIR, f"{run_id}.md")
    try:
        full_md = f"# REELLORE AI PRODUCTION PACKAGE // {game_name}\n"
        full_md += f"**Topic**: {topic or 'General'}\n"
        full_md += f"**Model**: {model_name} | **Date**: {now.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        full_md += f"{'='*60}\n\n"
        for t in task_outputs or []:
            full_md += f"## {t.get('agent', 'Agent')}\n\n{t.get('output', '')}\n\n{'='*60}\n\n"
        if not task_outputs:
            full_md += resolved_output or ""
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(full_md)
    except Exception:
        pass

    # Save JSON metadata & full payload
    meta = {
        "run_id": run_id,
        "created_at": now.isoformat(),
        "display_date": now.strftime("%b %d, %Y - %H:%M"),
        "game_name": game_name,
        "topic": topic or "General Research",
        "model_name": model_name,
        "content_focus": content_focus,
        "elapsed_seconds": elapsed_seconds,
        "total_words": total_words,
        "final_output": resolved_output,
        "task_outputs": task_outputs or [],
        "logs": logs or [],
        "has_pdf": has_pdf,
    }

    json_path = os.path.join(HISTORY_DIR, f"{run_id}.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2, ensure_ascii=False)

    return run_id


def list_runs() -> list[dict]:
    """
    List all saved runs in history/ sorted newest first.
    Returns lightweight summary dicts for fast UI rendering.
    """
    _ensure_history_dir()
    runs = []

    for fname in os.listdir(HISTORY_DIR):
        if not fname.endswith(".json"):
            continue
        fpath = os.path.join(HISTORY_DIR, fname)
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                data = json.load(f)
            runs.append({
                "run_id": data.get("run_id", fname[:-5]),
                "created_at": data.get("created_at", ""),
                "display_date": data.get("display_date", "Unknown Date"),
                "game_name": data.get("game_name", "Unknown Game"),
                "topic": data.get("topic", "General"),
                "model_name": data.get("model_name", "groq"),
                "content_focus": data.get("content_focus", "All-Rounder"),
                "elapsed_seconds": data.get("elapsed_seconds", "--"),
                "total_words": data.get("total_words", 0),
                "has_pdf": data.get("has_pdf", False),
            })
        except Exception:
            continue

    runs.sort(key=lambda r: r.get("created_at", ""), reverse=True)
    return runs


def load_run(run_id: str) -> dict:
    """Load a full run by run_id including its task outputs and optional PDF bytes."""
    _ensure_history_dir()
    json_path = os.path.join(HISTORY_DIR, f"{run_id}.json")
    if not os.path.exists(json_path):
        return None

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Attach PDF bytes if available
    pdf_path = os.path.join(HISTORY_DIR, f"{run_id}.pdf")
    if os.path.exists(pdf_path):
        try:
            with open(pdf_path, "rb") as pf:
                data["pdf_bytes"] = pf.read()
        except Exception:
            data["pdf_bytes"] = None
    else:
        data["pdf_bytes"] = None

    return data


def delete_run(run_id: str) -> bool:
    """Delete a run from history/."""
    _ensure_history_dir()
    deleted = False
    for ext in [".json", ".md", ".pdf"]:
        p = os.path.join(HISTORY_DIR, f"{run_id}{ext}")
        if os.path.exists(p):
            try:
                os.remove(p)
                deleted = True
            except Exception:
                pass
    return deleted
