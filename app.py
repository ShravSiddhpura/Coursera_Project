"""
ReelLore AI — Editorial Media Studio & Multi-Agent Production Deck
===================================================================
A high-throughput, production-ready Reel & LinkedIn Short-Form Content Engine
powered by CrewAI × Groq LPU with automatic model fallback, PS5-style game cover shelf,
dedicated GTA 6 Command Hub, dual-platform virality, human-readable Proof of Content,
Shoot-Ready PDF export, and Streamlit multipage routing (st.Page & st.navigation).
"""

import os
import sys
import time
import html
import re
import threading
import streamlit as st
from dotenv import load_dotenv

# Load environment variables with fallback to st.secrets
load_dotenv()


def _get_key(name: str) -> str:
    """Get API key from env vars with st.secrets fallback."""
    val = os.getenv(name)
    if not val:
        try:
            val = st.secrets.get(name)
        except Exception:
            pass
    return val or ""


# Import backend modules
from src.models import (
    get_available_groq_models,
    get_fastest_working_model,
    get_fallback_chain,
    test_model_ping,
    is_true_meta_llama,
)
from src.ps5_shelf import (
    GAME_SHELF,
    get_game_by_title,
    get_dynamic_cover_url,
    fetch_serper_game_cover,
)
from src.pdf_export import generate_production_pdf
from src.history_store import save_run, list_runs, load_run, delete_run


# ── Page Configuration ──────────────────────────────────────────────
st.set_page_config(
    page_title="ReelLore AI — Editorial Production Deck",
    page_icon="🎮",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ── Editorial Media Studio Styling (UI/UX Pro Max) ──────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;700&display=swap');

    /* Global Typography & Surface Tokens */
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        color: #F1F5F9;
    }

    /* Top Studio Header */
    .studio-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        background: #141722;
        border: 1px solid #242938;
        border-radius: 14px;
        padding: 20px 26px;
        margin-bottom: 22px;
    }
    .studio-title {
        font-size: 2.1rem;
        font-weight: 800;
        letter-spacing: -0.03em;
        color: #F8FAFC;
        margin: 0;
        display: flex;
        align-items: center;
        gap: 12px;
    }
    .studio-subtitle {
        font-size: 0.92rem;
        color: #94A3B8;
        margin-top: 4px;
        font-weight: 400;
    }
    .studio-badge {
        font-size: 0.72rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        padding: 4px 10px;
        border-radius: 6px;
        background: rgba(99, 102, 241, 0.15);
        color: #818CF8;
        border: 1px solid rgba(99, 102, 241, 0.35);
    }

    /* PS5 Shelf Hero & Game Cards */
    .shelf-container-title {
        font-size: 1.05rem;
        font-weight: 700;
        letter-spacing: -0.01em;
        color: #E2E8F0;
        margin: 18px 0 12px 0;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .hero-gta6-card {
        background: linear-gradient(135deg, #1C1929 0%, #151824 100%);
        border: 2px solid #F43F5E;
        border-radius: 14px;
        padding: 16px 20px;
        margin-bottom: 18px;
        box-shadow: 0 8px 24px rgba(244, 63, 94, 0.12);
        display: flex;
        align-items: center;
        gap: 20px;
    }
    .hero-badge-pill {
        background: #F43F5E;
        color: #FFFFFF;
        font-size: 0.72rem;
        font-weight: 800;
        padding: 3px 8px;
        border-radius: 4px;
        letter-spacing: 0.05em;
        text-transform: uppercase;
    }
    .hero-telemetry-tag {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.78rem;
        color: #FCA5A5;
        background: rgba(244, 63, 94, 0.12);
        padding: 3px 8px;
        border-radius: 4px;
    }

    /* Standard Game Cover Card */
    .game-card-slot {
        background: #161922;
        border: 1px solid #262B3B;
        border-radius: 12px;
        padding: 10px;
        text-align: center;
        transition: transform 0.2s ease, border-color 0.2s ease;
    }
    .game-card-slot:hover {
        border-color: #6366F1;
        transform: translateY(-2px);
    }
    .game-card-slot.active {
        border: 2px solid #6366F1;
        background: #1B1E2B;
    }
    .game-cover-img {
        width: 100%;
        height: 145px;
        object-fit: cover;
        border-radius: 8px;
        margin-bottom: 8px;
    }
    .game-title-text {
        font-size: 0.82rem;
        font-weight: 700;
        color: #F1F5F9;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    .game-sub-text {
        font-size: 0.72rem;
        color: #94A3B8;
        margin-top: 2px;
    }

    /* Live Telemetry & Pulsing Active Agent Banner */
    @keyframes pulseSoft {
        0%, 100% { border-color: #6366F1; box-shadow: 0 0 10px rgba(99, 102, 241, 0.15); }
        50% { border-color: #818CF8; box-shadow: 0 0 18px rgba(99, 102, 241, 0.35); }
    }
    .pulse-banner {
        background: #171A26;
        border: 1.5px solid #6366F1;
        border-radius: 12px;
        padding: 16px 20px;
        margin: 14px 0 18px 0;
        animation: pulseSoft 2.5s infinite ease-in-out;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .pulse-title {
        font-weight: 700;
        font-size: 0.95rem;
        color: #F8FAFC;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    .pulse-dot {
        width: 10px;
        height: 10px;
        border-radius: 50%;
        background-color: #10B981;
        display: inline-block;
        box-shadow: 0 0 8px #10B981;
    }
    .pulse-sub {
        font-size: 0.82rem;
        color: #94A3B8;
        margin-top: 4px;
    }
    .pulse-timer {
        font-family: 'JetBrains Mono', monospace;
        font-size: 1.1rem;
        font-weight: 700;
        color: #818CF8;
        background: rgba(99, 102, 241, 0.12);
        padding: 6px 14px;
        border-radius: 8px;
        border: 1px solid rgba(99, 102, 241, 0.3);
    }

    /* Monospace Live Stream Terminal */
    .live-terminal-stream {
        background: #0B0D13;
        border: 1px solid #1F2433;
        border-radius: 10px;
        padding: 14px 18px;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.77rem;
        color: #CBD5E1;
        max-height: 320px;
        overflow-y: auto;
        line-height: 1.6;
        white-space: pre-wrap;
        word-break: break-all;
    }

    /* Metric Cards */
    .metric-row {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 12px;
        margin-bottom: 20px;
    }
    .metric-card {
        background: #161922;
        border: 1px solid #242838;
        border-radius: 12px;
        padding: 16px;
        text-align: center;
    }
    .metric-value {
        font-size: 1.7rem;
        font-weight: 800;
        color: #F8FAFC;
    }
    .metric-label {
        font-size: 0.74rem;
        color: #94A3B8;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        margin-top: 4px;
    }

    /* History & Proof Cards */
    .history-card {
        background: #141722;
        border: 1px solid #242938;
        border-left: 4px solid #6366F1;
        border-radius: 10px;
        padding: 16px 20px;
        margin-bottom: 14px;
    }
    .history-title {
        font-weight: 700;
        font-size: 0.95rem;
        color: #F8FAFC;
    }
    .history-body {
        font-size: 0.82rem;
        color: #94A3B8;
        margin-top: 6px;
    }

    /* Status Badges */
    .status-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 4px 10px;
        border-radius: 6px;
        font-size: 0.76rem;
        font-weight: 600;
        margin-bottom: 6px;
    }
    .badge-green {
        background: rgba(16, 185, 129, 0.12);
        color: #10B981;
        border: 1px solid rgba(16, 185, 129, 0.3);
    }
    .badge-red {
        background: rgba(239, 68, 68, 0.12);
        color: #EF4444;
        border: 1px solid rgba(239, 68, 68, 0.3);
    }

    /* Sidebar Agent Cards */
    .sidebar-agent-card {
        background: #161922;
        border: 1px solid #232838;
        border-radius: 10px;
        padding: 12px 14px;
        margin-bottom: 8px;
    }
    .sidebar-agent-name {
        font-weight: 700;
        font-size: 0.82rem;
        color: #818CF8;
    }
    .sidebar-agent-desc {
        font-size: 0.72rem;
        color: #94A3B8;
        margin-top: 3px;
        line-height: 1.4;
    }

    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)


# ── Terminal Capture Class ──────────────────────────────────────────
class StreamlitOutputCapture:
    """Tees sys.stdout and sys.stderr into a live monospace terminal."""

    def __init__(self, placeholder, max_lines=160):
        self.placeholder = placeholder
        self.max_lines = max_lines
        self.lines = []
        self._orig_stdout = sys.stdout
        self._orig_stderr = sys.stderr
        self._lock = threading.Lock()

    def write(self, text, is_error=False):
        target = self._orig_stderr if is_error else self._orig_stdout
        if target:
            try:
                target.write(text)
                target.flush()
            except Exception:
                pass

        if not text:
            return

        with self._lock:
            clean = re.sub(r"\x1b\[[0-9;]*[a-zA-Z]", "", str(text))
            for raw_line in clean.splitlines():
                line = raw_line.strip()
                if not line:
                    continue
                is_err = is_error or any(
                    k in line.lower()
                    for k in ["error", "exception", "failed", "429", "400", "404", "traceback"]
                )
                self.lines.append((line, is_err))
                if len(self.lines) > self.max_lines:
                    self.lines.pop(0)
            self.render()

    def render(self):
        rendered = []
        for line, is_err in self.lines[-45:]:
            escaped = html.escape(line)
            if is_err:
                rendered.append(f'<div style="color:#EF4444; font-weight:700;">🚨 {escaped}</div>')
            elif line.startswith("🤖") or line.startswith("✅") or line.startswith("🚀") or line.startswith("⏳"):
                rendered.append(f'<div style="color:#818CF8; font-weight:600;">{escaped}</div>')
            elif "tool" in line.lower() or "search" in line.lower() or "step" in line.lower():
                rendered.append(f'<div style="color:#10B981;">{escaped}</div>')
            else:
                rendered.append(f'<div style="color:#94A3B8;">{escaped}</div>')
        body = "".join(rendered) if rendered else '<div style="color:#64748B;">Ready for multi-agent execution…</div>'
        try:
            self.placeholder.markdown(
                f'<div class="live-terminal-stream">{body}</div>',
                unsafe_allow_html=True,
            )
        except Exception:
            pass

    def start(self):
        class _Proxy:
            def __init__(p_self, cap, is_err):
                p_self.cap = cap
                p_self.is_err = is_err

            def write(p_self, s):
                p_self.cap.write(s, p_self.is_err)

            def flush(p_self):
                pass

        sys.stdout = _Proxy(self, False)
        sys.stderr = _Proxy(self, True)

    def stop(self):
        sys.stdout = self._orig_stdout
        sys.stderr = self._orig_stderr


# ── Session State Setup ─────────────────────────────────────────────
if "game_name" not in st.session_state:
    st.session_state.game_name = "Grand Theft Auto VI"

if "specific_topic" not in st.session_state:
    st.session_state.specific_topic = "Vice City map & Leonida ecosystem details, trailer breakdowns & leaks"

if "active_shelf_id" not in st.session_state:
    st.session_state.active_shelf_id = "gta6"

if "latest_run" not in st.session_state:
    st.session_state.latest_run = None

if "viewing_historical_run" not in st.session_state:
    st.session_state.viewing_historical_run = None


def set_game_shelf(game_entry: dict):
    st.session_state.game_name = game_entry["title"]
    st.session_state.specific_topic = game_entry.get("default_topic", "")
    st.session_state.active_shelf_id = game_entry.get("id", "custom")


def set_topic_preset(preset_text: str):
    clean = re.sub(r"^[^\w\s]+\s*", "", preset_text)
    st.session_state.specific_topic = clean


# ── Shared Sidebar ──────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ Studio Control Deck")

    groq_key = _get_key("GROQ_API_KEY")
    serper_key = _get_key("SERPER_API_KEY")

    if groq_key:
        st.markdown('<div class="status-badge badge-green">🟢 GROQ LPU: Connected</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="status-badge badge-red">🔴 GROQ_API_KEY: Missing in .env</div>', unsafe_allow_html=True)

    if serper_key:
        st.markdown('<div class="status-badge badge-green">🟢 SERPER API: Connected</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="status-badge badge-red">🔴 SERPER_API_KEY: Missing in .env</div>', unsafe_allow_html=True)

    st.divider()

    # Dynamic Groq Model Selection with True Meta Llama Priority
    available_models = get_available_groq_models(groq_key)
    fastest_model = get_fastest_working_model(groq_key)
    default_idx = available_models.index(fastest_model) if fastest_model in available_models else 0

    model_choice = st.selectbox(
        "🧠 Groq LLM Engine",
        options=available_models,
        index=default_idx,
        help="Dynamic discovery queries Groq directly. Meta Llama models are prioritized; ALLaM, whisper, and guard models are filtered out. Automatic fallback to fast Qwen/GPT-OSS prevents 429 stalls. Large models (120B) are not defaulted.",
    )

    fallback_chain = get_fallback_chain(model_choice, groq_key)
    if fallback_chain:
        st.caption(f"⚡ **Auto-Fallback Chain**: `{fallback_chain[0]}`")

    content_focus = st.selectbox(
        "🎯 Content Engine Focus",
        options=[
            "Dual-Platform Virality (IG Reels + LinkedIn)",
            "All-Rounder",
            "Lore & Easter Eggs",
            "Famous Bugs & Patch Notes",
            "Dev Stories & Engineering Feats",
        ],
        index=0,
    )

    st.divider()

    st.markdown("### 🤖 Active 4-Agent Crew")
    crew_agents = [
        ("🔍 Lore & Trivia Scout", "Searches wikis & developer interviews with clickable links"),
        ("🐛 DevLog & Bug Archaeologist", "Mines Reddit & patch notes for engine feats & glitches"),
        ("✍️ Dual-Platform Scriptwriter", "Engineers 3 Reel scripts + 3 companion LinkedIn posts"),
        ("🎬 Production & Proof Director", "Builds B-roll cues, captions, and Human-Readable Proof"),
    ]
    for aname, adesc in crew_agents:
        st.markdown(
            f'<div class="sidebar-agent-card">'
            f'<div class="sidebar-agent-name">{aname}</div>'
            f'<div class="sidebar-agent-desc">{adesc}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )


# ═════════════════════════════════════════════════════════════════════
# PAGE 1: STUDIO (LATEST RUN)
# ═════════════════════════════════════════════════════════════════════
def render_studio_page():
    # Top Header
    st.markdown("""
    <div class="studio-header">
        <div>
            <div class="studio-title">🎮 ReelLore AI <span class="studio-badge">Production Deck</span></div>
            <div class="studio-subtitle">Multi-Agent Short-Form Virality Engine for Instagram Reels & LinkedIn · CrewAI × Groq LPU</div>
        </div>
        <div style="text-align:right;">
            <span class="status-badge badge-green" style="font-size:0.8rem;">● High-Throughput Ready</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Historical Viewing Notice if viewing an older run
    if st.session_state.viewing_historical_run:
        h_run = st.session_state.viewing_historical_run
        st.info(
            f"📂 **Viewing Historical Run**: **{h_run.get('game_name')}** ({h_run.get('display_date', 'Past Run')}) | Topic: *{h_run.get('topic', 'General')}*"
        )
        if st.button("⬅️ Return to Latest Studio Run", type="primary", use_container_width=True):
            st.session_state.viewing_historical_run = None
            st.rerun()

    # PS5-Style Game Cover Shelf
    st.markdown('<div class="shelf-container-title">🕹️ PS5-Style Game Shelf & Cover Selector</div>', unsafe_allow_html=True)

    current_game_entry = get_game_by_title(st.session_state.game_name)
    is_gta6_active = "gta" in st.session_state.game_name.lower() and ("vi" in st.session_state.game_name.lower() or "6" in st.session_state.game_name)

    if is_gta6_active:
        st.markdown("""
        <div class="hero-gta6-card">
            <img src="https://images.igdb.com/igdb/image/upload/t_720p/co6m9e.jpg" style="width:110px; height:150px; object-fit:cover; border-radius:10px; border:1px solid #F43F5E;" alt="GTA 6 Cover" />
            <div style="flex:1;">
                <div style="display:flex; align-items:center; gap:10px; margin-bottom:6px;">
                    <span class="hero-badge-pill">⭐ FEATURED HERO</span>
                    <span class="hero-telemetry-tag">RAGE 9 Engine</span>
                    <span class="hero-telemetry-tag">State of Leonida // Vice City</span>
                </div>
                <h2 style="margin:0; font-size:1.6rem; font-weight:800; color:#F8FAFC;">Grand Theft Auto VI</h2>
                <p style="margin:6px 0 0 0; font-size:0.88rem; color:#FDA4AF; line-height:1.5;">
                    Primary focus of ReelLore AI. Research trailer breakdowns, AI NPC density, physics leaks, and map scope for maximum virality across Instagram Reels and LinkedIn.
                </p>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Horizontal shelf cards
    cols = st.columns(len(GAME_SHELF))
    for idx, g in enumerate(GAME_SHELF):
        is_active = (g["id"] == st.session_state.active_shelf_id) or (g["title"].lower() == st.session_state.game_name.lower())
        with cols[idx]:
            st.markdown(
                f"""
                <div class="game-card-slot {'active' if is_active else ''}">
                    <img src="{g['cover_url']}" class="game-cover-img" alt="{g['short_name']}" onerror="this.src='{g.get('fallback_cover', '')}'" />
                    <div class="game-title-text">{g['short_name']}</div>
                    <div class="game-sub-text">{g['release']}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.button(
                "Select" if not is_active else "Active ✓",
                key=f"shelf_btn_{g['id']}",
                on_click=set_game_shelf,
                args=(g,),
                use_container_width=True,
                type="primary" if is_active else "secondary",
            )

    # Game & Topic Search
    st.markdown('<div class="shelf-container-title">🎯 Game & Topic Command Hub</div>', unsafe_allow_html=True)

    cmd_col1, cmd_col2 = st.columns([1, 2])
    with cmd_col1:
        st.text_input(
            "🎮 Target Game Title (or type custom game):",
            key="game_name",
            help="Select a game above or enter any custom title.",
        )

    with cmd_col2:
        st.text_input(
            f"🔍 Research Topic & Virality Angle for {st.session_state.game_name}:",
            key="specific_topic",
            placeholder="e.g., Vice City map details, AI NPC physics, trailer frame breakdown, engine workarounds…",
            help="Scopes the Lore Scout and DevLog Archaeologist specifically to this topic.",
        )

    # Quick Presets
    st.markdown(f"**⚡ Quick Presets for {st.session_state.game_name}:**")
    cur_presets = current_game_entry.get("presets", [
        "Obscure Lore & Hidden Secrets",
        "Physics Glitches & Dev Hacks",
        "Trailer Breakdown & Cut Content",
        "Engine Architecture & Post-Mortem",
        "Viral Dual-Platform Script Packet",
    ])

    preset_cols = st.columns(len(cur_presets))
    for p_idx, p_text in enumerate(cur_presets):
        with preset_cols[p_idx]:
            st.button(
                p_text,
                key=f"preset_btn_{p_idx}",
                on_click=set_topic_preset,
                args=(p_text,),
                use_container_width=True,
            )

    st.markdown("---")

    # Launch & Load Action Controls
    launch_disabled = not groq_key or not serper_key
    if launch_disabled:
        st.warning("⚠️ Both `GROQ_API_KEY` and `SERPER_API_KEY` must be configured in `.env` (or `st.secrets`) to launch the crew.")

    action_col1, action_col2 = st.columns([3, 2])
    with action_col1:
        launch = st.button(
            f"🚀 Launch Multi-Agent Studio Crew for {st.session_state.game_name}",
            disabled=launch_disabled,
            use_container_width=True,
            type="primary",
        )
    with action_col2:
        load_saved = st.button(
            "📂 Load Last Saved Run from `outputs/`",
            use_container_width=True,
        )

    # Load from outputs/ logic
    if load_saved:
        outputs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "outputs")
        task_specs = [
            ("01_lore_findings.md", "Lore & Trivia Scout"),
            ("02_dev_and_bugs.md", "DevLog & Bug Archaeologist"),
            ("03_reel_scripts.md", "Dual-Platform Scriptwriter"),
            ("04_production_package.md", "Production & Proof Director"),
        ]
        task_outputs = []
        found_files = 0
        for fname, label in task_specs:
            fpath = os.path.join(outputs_dir, fname)
            if os.path.exists(fpath):
                with open(fpath, "r", encoding="utf-8") as f:
                    content = f.read()
                if content.strip():
                    found_files += 1
            else:
                content = f"*(File `{fname}` not found in outputs/ directory)*"
            task_outputs.append({
                "agent": label,
                "file": fname,
                "output": content,
                "word_count": len(content.split()),
                "char_count": len(content),
            })

        if found_files > 0:
            final_out = task_outputs[3]["output"] if task_outputs[3]["char_count"] > 100 else task_outputs[2]["output"]
            saved_logs = [
                f"[{time.strftime('%H:%M:%S')}] 📂 Restored run from outputs/ directory.",
                f"[{time.strftime('%H:%M:%S')}] ✅ Loaded 01_lore_findings.md ({task_outputs[0]['word_count']} words)",
                f"[{time.strftime('%H:%M:%S')}] ✅ Loaded 02_dev_and_bugs.md ({task_outputs[1]['word_count']} words)",
                f"[{time.strftime('%H:%M:%S')}] ✅ Loaded 03_reel_scripts.md ({task_outputs[2]['word_count']} words)",
                f"[{time.strftime('%H:%M:%S')}] ✅ Loaded 04_production_package.md ({task_outputs[3]['word_count']} words)",
            ]

            clean_gname = st.session_state.game_name.replace(" ", "_")
            pdf_path = os.path.join(outputs_dir, f"ReelLore_{clean_gname}_Script_Packet.pdf")
            pdf_bytes = None
            if os.path.exists(pdf_path):
                with open(pdf_path, "rb") as pf:
                    pdf_bytes = pf.read()
            else:
                try:
                    pdf_bytes = generate_production_pdf(
                        game_name=st.session_state.game_name,
                        topic=st.session_state.specific_topic,
                        model_name=model_choice,
                        content_focus=content_focus,
                        final_package=final_out,
                        task_outputs=task_outputs,
                        output_filepath=pdf_path,
                    )
                except Exception:
                    pass

            run_bundle = {
                "final_output": final_out,
                "task_outputs": task_outputs,
                "logs": saved_logs,
                "elapsed_seconds": "Saved",
                "pdf_bytes": pdf_bytes,
                "game_name": st.session_state.game_name,
                "topic": st.session_state.specific_topic,
                "model_name": model_choice,
            }
            st.session_state.latest_run = run_bundle
            st.session_state.viewing_historical_run = None
            st.success(f"✅ Restored {found_files} agent deliverables from `outputs/` into Latest Run!")
        else:
            st.warning("⚠️ No completed runs found in `outputs/`. Click Launch to run the crew!")

    # Execution kickoff
    if launch:
        st.session_state.viewing_historical_run = None
        banner_placeholder = st.empty()
        progress_placeholder = st.empty()
        live_progress = progress_placeholder.progress(
            0.08, text=f"⏳ Agent 1/4: Lore & Trivia Scout is investigating {st.session_state.game_name}…"
        )

        terminal_expander = st.expander("📡 Live Agent Telemetry & Groq LPU Stream", expanded=True)
        with terminal_expander:
            terminal_stream_placeholder = st.empty()
            terminal_stream_placeholder.markdown(
                f'<div class="live-terminal-stream">🚀 Connecting to Groq engine (`{model_choice}`) with auto-fallback… Initializing 4 agents for {st.session_state.game_name}…</div>',
                unsafe_allow_html=True,
            )

        output_capture = StreamlitOutputCapture(terminal_stream_placeholder)
        output_capture.start()

        run_start_time = time.time()

        def update_banner(agent_role: str, action_desc: str):
            elapsed = round(time.time() - run_start_time, 1)
            safe_agent = html.escape(str(agent_role))
            safe_action = html.escape(str(action_desc))
            banner_placeholder.markdown(
                f"""
                <div class="pulse-banner">
                    <div>
                        <div class="pulse-title"><span class="pulse-dot"></span> {safe_agent}</div>
                        <div class="pulse-sub">⚡ {safe_action}</div>
                    </div>
                    <div class="pulse-timer">⏱️ {elapsed:.1f}s</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        def update_progress(val: float, text: str):
            live_progress.progress(val, text=text)

        update_banner("Agent 1/4: Lore & Trivia Scout", f"Scouting lore & verified sources for {st.session_state.game_name}…")

        with st.status(f"🚀 Running 4-Agent Studio Crew for **{st.session_state.game_name}**…", expanded=True) as status_box:
            status_box.write(f"Connected to model `{model_choice}` on Groq LPU (TPM-safe, Auto-fallback)…")

            try:
                from src.crew import run_crew

                result = run_crew(
                    game_name=st.session_state.game_name,
                    model_name=model_choice,
                    content_focus=content_focus,
                    specific_topic=st.session_state.specific_topic,
                    log_callback=output_capture.write,
                    status_box=status_box,
                    progress_callback=update_progress,
                    banner_callback=update_banner,
                )
                st.session_state.latest_run = result
                status_box.update(label=f"✅ Crew completed in {result['elapsed_seconds']}s!", state="complete")
                banner_placeholder.markdown(
                    f"""
                    <div class="pulse-banner" style="border-color:#10B981;">
                        <div>
                            <div class="pulse-title"><span class="pulse-dot" style="background:#10B981; box-shadow:0 0 10px #10B981;"></span> All 4 Agents Completed!</div>
                            <div class="pulse-sub">✅ Dual-Platform scripts, Shoot-Ready PDF, and Proof of Content assembled</div>
                        </div>
                        <div class="pulse-timer" style="color:#10B981; border-color:#10B981;">⏱️ {result['elapsed_seconds']}s</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            except Exception as exc:
                status_box.update(label="❌ Crew execution interrupted", state="error")
                st.error(f"❌ Execution Error: {type(exc).__name__}: {str(exc)}")
                st.exception(exc)

                banner_placeholder.markdown(
                    f"""
                    <div class="pulse-banner" style="border-color:#EF4444;">
                        <div>
                            <div class="pulse-title"><span class="pulse-dot" style="background:#EF4444; box-shadow:0 0 10px #EF4444;"></span> Execution Paused</div>
                            <div class="pulse-sub">❌ Error: {html.escape(str(exc)[:120])}</div>
                        </div>
                        <div class="pulse-timer" style="color:#EF4444; border-color:#EF4444;">FAIL</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            finally:
                output_capture.stop()

    # Active Result to display: either viewing historical run or latest completed run
    active_result = st.session_state.viewing_historical_run or st.session_state.latest_run

    if active_result:
        display_results_view(active_result)


def display_results_view(result: dict):
    """Render metrics, download buttons, and the 6 deliverable tabs for a run."""
    elapsed_display = (
        f"{result['elapsed_seconds']}s"
        if isinstance(result.get("elapsed_seconds"), (int, float))
        else str(result.get("elapsed_seconds", "Saved"))
    )
    total_words = sum(t.get("word_count", 0) for t in result.get("task_outputs", []))

    st.markdown(
        f"""
        <div class="metric-row">
            <div class="metric-card">
                <div class="metric-value">4</div>
                <div class="metric-label">Agents Executed</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{elapsed_display}</div>
                <div class="metric-label">Execution Time</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{total_words:,}</div>
                <div class="metric-label">Total Words Produced</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{len(result.get('logs', []))}</div>
                <div class="metric-label">Execution Trace Events</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Export Action Bar
    pdf_bytes = result.get("pdf_bytes")
    if not pdf_bytes:
        try:
            pdf_bytes = generate_production_pdf(
                game_name=result.get("game_name", st.session_state.game_name),
                topic=result.get("topic", st.session_state.specific_topic),
                model_name=result.get("model_name", "groq"),
                content_focus="Dual-Platform Virality",
                final_package=result.get("final_output", ""),
                task_outputs=result.get("task_outputs", []),
            )
            result["pdf_bytes"] = pdf_bytes
        except Exception:
            pdf_bytes = None

    exp_col1, exp_col2, exp_col3 = st.columns([2, 2, 2])
    with exp_col1:
        if pdf_bytes:
            st.download_button(
                label="📄 Download Shoot-Ready PDF Packet",
                data=pdf_bytes,
                file_name=f"ReelLore_{result.get('game_name', 'Game').replace(' ', '_')}_Script_Packet.pdf",
                mime="application/pdf",
                use_container_width=True,
                type="primary",
            )
        else:
            st.info("PDF generating…")

    with exp_col2:
        full_package_md = ""
        for t in result.get("task_outputs", []):
            full_package_md += f"# {t['agent']}\n\n{t['output']}\n\n{'='*60}\n\n"
        if not full_package_md:
            full_package_md = result.get("final_output", "")

        st.download_button(
            label="⬇️ Download Markdown Package (.md)",
            data=full_package_md,
            file_name=f"ReelLore_{result.get('game_name', 'Game').replace(' ', '_')}_Package.md",
            mime="text/markdown",
            use_container_width=True,
        )

    with exp_col3:
        log_text = "\n".join(result.get("logs", []))
        st.download_button(
            label="📡 Download Trace Log (.txt)",
            data=log_text,
            file_name="execution_trace_log.txt",
            mime="text/plain",
            use_container_width=True,
        )

    st.markdown("---")

    # 5 Structured Deliverable Tabs
    tab_reels, tab_linkedin, tab_proof, tab_agents, tab_arch = st.tabs([
        "📱 Instagram Reels Studio",
        "💼 LinkedIn Virality Engine",
        "🔍 Human-Readable Proof & Sources",
        "🤖 Individual Agent Outputs",
        "🏗️ Architecture & Flow",
    ])

    with tab_reels:
        st.markdown(f"### 📱 Shoot-Ready Instagram Reel Scripts for **{result.get('game_name', 'Target Game')}**")
        st.caption("Engineered for 0-3s pattern interrupts, 2-4s beat pacing, and seamless loop phrasing back to the hook.")
        scripts_text = ""
        if len(result.get("task_outputs", [])) >= 3:
            scripts_text = result["task_outputs"][2]["output"]
        else:
            scripts_text = result.get("final_output", "")
        st.markdown(scripts_text)

    with tab_linkedin:
        st.markdown(f"### 💼 LinkedIn Algorithmic Companion Posts for **{result.get('game_name', 'Target Game')}**")
        st.caption("Professional storytelling engineered for high dwell time, technical engineering takeaways, and comment debates.")
        st.markdown(result.get("final_output", ""))

    with tab_proof:
        st.markdown("### 🔍 Human-Readable Proof of Content & Verification Audit")
        st.info("Plain English source attribution, confidence matrix, and visual reference guide for video editors.")
        prod_output = ""
        if len(result.get("task_outputs", [])) >= 4:
            prod_output = result["task_outputs"][3]["output"]
        else:
            prod_output = result.get("final_output", "")
        st.markdown(prod_output)

        urls_found = re.findall(r"https?://[^\s\)\"\'>]+", str(result))
        if urls_found:
            st.markdown("#### 🔗 Extracted Clickable Citations:")
            seen = set()
            for u in urls_found:
                clean_u = u.rstrip(".,;)")
                if clean_u not in seen and len(clean_u) > 10:
                    seen.add(clean_u)
                    st.markdown(f"- [{clean_u}]({clean_u})")

    with tab_agents:
        st.markdown("### 🤖 Proof of 4 Sequential Agents")
        st.caption("Verify each agent's individual deliverable saved to `./outputs/`.")
        emojis = ["🔍", "🐛", "✍️", "🎬"]
        for i, t in enumerate(result.get("task_outputs", []), 1):
            with st.expander(f"{emojis[i-1]} Agent {i}: {t['agent']}  |  📄 `{t['file']}`  |  📊 {t['word_count']} words", expanded=(i == 1)):
                st.caption(f"Output path: `outputs/{t['file']}`  |  Characters: {t['char_count']:,}")
                st.markdown(t["output"])

    with tab_arch:
        st.markdown("### 🏗️ ReelLore AI Multi-Agent Architecture")
        st.caption("Sequential 4-agent pipeline with Groq LPU auto-fallback, Serper, Reddit & Steam tools.")
        graph = """
        digraph ReelLoreAI {
            rankdir=TB;
            bgcolor="#0D0F14";
            node [
                shape=box,
                style="filled,rounded",
                fontname="Inter",
                fontsize=11,
                fontcolor="#F1F5F9",
                color="#242838",
                penwidth=1.5
            ];
            edge [
                color="#6366F1",
                fontcolor="#94A3B8",
                fontname="Inter",
                fontsize=9,
                penwidth=1.5
            ];

            User [label="🎮 User Input\\n(Game & Sub-Topic)", fillcolor="#161922"];
            GroqLPU [label="⚡ Groq LPU Engine\\n(True Llama + Auto-Fallback)", fillcolor="#1E1B4B", color="#6366F1"];
            CrewManager [label="🎯 CrewAI Orchestrator\\n(Sequential Process)", fillcolor="#1E1B4B", color="#6366F1"];

            Agent1 [label="🔍 Agent 1\\nLore & Trivia Scout", fillcolor="#064E3B", color="#10B981"];
            Agent2 [label="🐛 Agent 2\\nDevLog & Bug Archaeologist", fillcolor="#450A0A", color="#EF4444"];
            Agent3 [label="✍️ Agent 3\\nDual-Platform Scriptwriter", fillcolor="#172554", color="#3B82F6"];
            Agent4 [label="🎬 Agent 4\\nProduction & Proof Director", fillcolor="#422006", color="#F59E0B"];

            Serper [label="🌐 Serper API (Google)", fillcolor="#161922", shape=ellipse];
            Reddit [label="📱 Reddit JSON Miner", fillcolor="#161922", shape=ellipse];
            Steam [label="🎮 Steam Patch Notes API", fillcolor="#161922", shape=ellipse];

            Deliverables [label="📦 Complete Package\\n• 3 IG Reel Scripts\\n• 3 LinkedIn Viral Posts\\n• Human Proof of Content\\n• Shoot-Ready PDF Packet", fillcolor="#1E1B4B", color="#6366F1"];

            User -> CrewManager [label="game + topic"];
            GroqLPU -> CrewManager [label="LPU Tokens"];
            CrewManager -> Agent1 [label="Task 1"];
            Agent1 -> Agent2 [label="lore context (Task 2)", style=dashed];
            Agent2 -> Agent3 [label="dev context (Task 3)", style=dashed];
            Agent3 -> Agent4 [label="scripts context (Task 4)", style=dashed];
            Agent4 -> Deliverables [label="production deliverable"];

            Agent1 -> Serper [label="search", style=dotted];
            Agent2 -> Reddit [label="mine", style=dotted];
            Agent2 -> Steam [label="fetch", style=dotted];
        }
        """
        st.graphviz_chart(graph)


# ═════════════════════════════════════════════════════════════════════
# PAGE 2: RUN HISTORY
# ═════════════════════════════════════════════════════════════════════
def render_history_page():
    st.markdown("""
    <div class="studio-header">
        <div>
            <div class="studio-title">📜 Run History Store</div>
            <div class="studio-subtitle">Persistent local archive of completed multi-agent deliverables, Markdown packets, and Shoot-Ready PDFs.</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Back to Latest Run link / button
    nav_col1, nav_col2 = st.columns([2, 1])
    with nav_col1:
        if st.session_state.latest_run:
            st.caption(f"Latest completed run: **{st.session_state.latest_run.get('game_name')}** ({st.session_state.latest_run.get('elapsed_seconds', '--')}s)")
        else:
            st.caption("No completed run in this session yet.")
    with nav_col2:
        if st.button("⬅️ Back to Latest Studio Run", type="primary", use_container_width=True):
            st.session_state.viewing_historical_run = None
            st.switch_page(page_studio)

    st.markdown("---")

    history_items = list_runs()
    if not history_items:
        st.info("No saved runs in history yet. Launch a generation run in the Studio to see it appear here!")
        return

    st.markdown(f"**Found {len(history_items)} saved generation runs:**")

    for item in history_items:
        rid = item["run_id"]
        with st.container():
            st.markdown(
                f"""
                <div class="history-card">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <div class="history-title">🎮 {item['game_name']} — <span style="color:#818CF8;">{item['topic']}</span></div>
                        <span class="status-badge badge-green">⏱️ {item['elapsed_seconds']}s</span>
                    </div>
                    <div class="history-body">
                        📅 {item['display_date']}  |  🧠 Model: <code>{item['model_name']}</code>  |  📊 {item['total_words']:,} words  |  Focus: {item['content_focus']}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            h_col1, h_col2, h_col3 = st.columns([2, 2, 1])
            with h_col1:
                if st.button(f"👁️ View / Load Run", key=f"view_{rid}", use_container_width=True):
                    loaded_data = load_run(rid)
                    if loaded_data:
                        # Set viewing_historical_run WITHOUT clobbering latest_run!
                        st.session_state.viewing_historical_run = loaded_data
                        st.session_state.game_name = loaded_data.get("game_name", st.session_state.game_name)
                        st.session_state.specific_topic = loaded_data.get("topic", "")
                        st.success(f"Loaded `{rid}` into Studio view!")
                        st.switch_page(page_studio)

            with h_col2:
                loaded_entry = load_run(rid)
                if loaded_entry and loaded_entry.get("pdf_bytes"):
                    st.download_button(
                        "📄 Download PDF",
                        data=loaded_entry["pdf_bytes"],
                        file_name=f"ReelLore_{item['game_name'].replace(' ', '_')}_{rid}.pdf",
                        mime="application/pdf",
                        key=f"dl_pdf_{rid}",
                        use_container_width=True,
                    )
                else:
                    st.caption("No cached PDF")

            with h_col3:
                if st.button("🗑️ Delete", key=f"del_{rid}", use_container_width=True):
                    delete_run(rid)
                    st.rerun()


# ── Multipage Navigation Setup ──────────────────────────────────────
page_studio = st.Page(render_studio_page, title="Studio (Latest Run)", icon="🎮", default=True)
page_history = st.Page(render_history_page, title="Run History", icon="📜")

nav = st.navigation([page_studio, page_history])
nav.run()
