"""
ReelLore AI — Streamlit Application
=====================================
Multi-Agent Game Lore & Dev-Log Instagram Reel Generator
with live execution trace, individual agent proof tabs,
and architecture diagram.
"""

import os
import sys
import time
import html
import re
import threading
import streamlit as st
from dotenv import load_dotenv
from src.agents import get_available_groq_models, get_fastest_working_model

# ── Load environment variables ──────────────────────────────────────
load_dotenv()


class StreamlitOutputCapture:
    """Tees sys.stdout and sys.stderr into a live-updating Streamlit monospace terminal."""

    def __init__(self, placeholder, max_lines=150):
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
                    for k in [
                        "error", "exception", "failed", "429", "400", "404",
                        "ratelimit", "badrequest", "notfound", "traceback"
                    ]
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
                rendered.append(f'<div style="color:#FF4B4B; font-weight:700;">🚨 {escaped}</div>')
            elif line.startswith("🤖") or line.startswith("✅") or line.startswith("🚀") or line.startswith("⏳"):
                rendered.append(f'<div style="color:#B06CFF; font-weight:600;">{escaped}</div>')
            elif "tool" in line.lower() or "search" in line.lower() or "step" in line.lower():
                rendered.append(f'<div style="color:#00FF88;">{escaped}</div>')
            else:
                rendered.append(f'<div style="color:#A0A0C0;">{escaped}</div>')
        body = "".join(rendered) if rendered else '<div style="color:#666;">Waiting for agent stream...</div>'
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


def _get_key(name: str) -> str:
    """Get API key from env vars with st.secrets fallback."""
    val = os.getenv(name)
    if not val:
        try:
            val = st.secrets.get(name)
        except Exception:
            pass
    return val or ""


# ── Page configuration ──────────────────────────────────────────────
st.set_page_config(
    page_title="ReelLore AI — Multi-Agent Reel Generator",
    page_icon="🎮",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS for premium look ─────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

    /* Global font */
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* Main title gradient */
    .main-title {
        font-size: 2.8rem;
        font-weight: 900;
        background: linear-gradient(135deg, #8032FC 0%, #B06CFF 40%, #FF6AC1 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 0.2rem;
        letter-spacing: -0.02em;
    }
    .sub-title {
        font-size: 1.05rem;
        color: #9898B0;
        margin-bottom: 2rem;
        font-weight: 400;
    }

    /* Status badges */
    .status-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.78rem;
        font-weight: 600;
        margin-bottom: 6px;
    }
    .badge-green {
        background: rgba(34, 197, 94, 0.15);
        color: #22c55e;
        border: 1px solid rgba(34, 197, 94, 0.3);
    }
    .badge-red {
        background: rgba(239, 68, 68, 0.15);
        color: #ef4444;
        border: 1px solid rgba(239, 68, 68, 0.3);
    }

    /* Agent cards */
    .agent-card {
        background: linear-gradient(135deg, #1a1a2e 0%, #16162a 100%);
        border: 1px solid #2a2a4a;
        border-radius: 12px;
        padding: 14px 16px;
        margin-bottom: 10px;
        transition: border-color 0.3s ease;
    }
    .agent-card:hover {
        border-color: #8032FC;
    }
    .agent-card .agent-name {
        font-weight: 700;
        font-size: 0.85rem;
        color: #B06CFF;
    }
    .agent-card .agent-desc {
        font-size: 0.75rem;
        color: #8888A8;
        margin-top: 4px;
    }

    /* Quick pill buttons */
    .pill-container {
        display: flex;
        gap: 8px;
        flex-wrap: wrap;
        margin-bottom: 16px;
    }

    /* Log terminal */
    .log-terminal {
        background: #0a0a12;
        border: 1px solid #1f1f3a;
        border-radius: 10px;
        padding: 16px;
        font-family: 'JetBrains Mono', 'Fira Code', monospace;
        font-size: 0.78rem;
        color: #c0c0d8;
        max-height: 500px;
        overflow-y: auto;
        line-height: 1.6;
    }

    /* Pulsing Active Agent Banner */
    @keyframes pulseGlow {
        0% { box-shadow: 0 0 12px rgba(128, 50, 252, 0.25), inset 0 0 12px rgba(128, 50, 252, 0.1); border-color: rgba(128, 50, 252, 0.4); }
        50% { box-shadow: 0 0 24px rgba(255, 106, 193, 0.45), inset 0 0 16px rgba(128, 50, 252, 0.25); border-color: rgba(255, 106, 193, 0.65); }
        100% { box-shadow: 0 0 12px rgba(128, 50, 252, 0.25), inset 0 0 12px rgba(128, 50, 252, 0.1); border-color: rgba(128, 50, 252, 0.4); }
    }
    .pulse-banner {
        background: linear-gradient(135deg, #15152a 0%, #1a1636 100%);
        border: 1.5px solid #8032FC;
        border-radius: 12px;
        padding: 16px 20px;
        margin: 14px 0 18px 0;
        animation: pulseGlow 2.4s infinite ease-in-out;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .pulse-title {
        font-weight: 700;
        font-size: 0.96rem;
        color: #FFFFFF;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    .pulse-dot {
        width: 10px;
        height: 10px;
        border-radius: 50%;
        background-color: #00FF88;
        display: inline-block;
        box-shadow: 0 0 10px #00FF88;
        animation: blink 1.2s infinite ease-in-out;
    }
    @keyframes blink {
        0%, 100% { opacity: 1; transform: scale(1); }
        50% { opacity: 0.35; transform: scale(0.8); }
    }
    .pulse-sub {
        font-size: 0.82rem;
        color: #A8A8CC;
        margin-top: 5px;
    }
    .pulse-timer {
        font-family: 'JetBrains Mono', 'Fira Code', monospace;
        font-size: 1.15rem;
        font-weight: 800;
        color: #FF6AC1;
        background: rgba(255, 106, 193, 0.12);
        padding: 6px 14px;
        border-radius: 8px;
        border: 1px solid rgba(255, 106, 193, 0.3);
    }
    .live-terminal-stream {
        background: #08080f;
        border: 1px solid #1e1e35;
        border-radius: 10px;
        padding: 14px 16px;
        font-family: 'JetBrains Mono', 'Fira Code', monospace;
        font-size: 0.77rem;
        color: #C5C5E0;
        max-height: 320px;
        overflow-y: auto;
        line-height: 1.55;
        white-space: pre-wrap;
        word-break: break-all;
    }

    /* Metric cards */
    .metric-row {
        display: flex;
        gap: 12px;
        margin-bottom: 16px;
    }
    .metric-card {
        background: linear-gradient(135deg, #1a1a2e, #181830);
        border: 1px solid #2a2a4a;
        border-radius: 12px;
        padding: 16px 20px;
        flex: 1;
        text-align: center;
    }
    .metric-card .metric-value {
        font-size: 1.8rem;
        font-weight: 800;
        background: linear-gradient(135deg, #8032FC, #FF6AC1);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .metric-card .metric-label {
        font-size: 0.75rem;
        color: #7878a0;
        margin-top: 4px;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    /* Tabs styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 4px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px 8px 0 0;
        padding: 8px 20px;
        font-weight: 600;
    }

    /* Download button */
    .stDownloadButton > button {
        background: linear-gradient(135deg, #8032FC, #6020C0) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        padding: 10px 24px !important;
        transition: transform 0.2s ease, box-shadow 0.2s ease !important;
    }
    .stDownloadButton > button:hover {
        transform: translateY(-1px) !important;
        box-shadow: 0 6px 20px rgba(128, 50, 252, 0.4) !important;
    }

    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)


# ── Sidebar ─────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ Configuration")

    # API Status
    groq_key = _get_key("GROQ_API_KEY")
    serper_key = _get_key("SERPER_API_KEY")
    if groq_key:
        st.markdown('<div class="status-badge badge-green">🟢 GROQ_API_KEY: Connected</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="status-badge badge-red">🔴 GROQ_API_KEY: Missing</div>', unsafe_allow_html=True)
    if serper_key:
        st.markdown('<div class="status-badge badge-green">🟢 SERPER_API_KEY: Connected</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="status-badge badge-red">🔴 SERPER_API_KEY: Missing</div>', unsafe_allow_html=True)

    st.divider()

    # Model selector with dynamic Groq discovery & Llama priority
    available_models = get_available_groq_models(groq_key)
    fastest_model = get_fastest_working_model(groq_key)
    default_idx = available_models.index(fastest_model) if fastest_model in available_models else 0

    model_choice = st.selectbox(
        "🧠 Groq Model",
        options=available_models,
        index=default_idx,
        help="Fast Llama models are sorted to the top. Select an active Groq LLM.",
    )

    # Content focus
    content_focus = st.radio(
        "🎯 Content Focus",
        options=["All-Rounder", "Lore & Easter Eggs", "Famous Bugs & Patch Notes", "Dev Stories"],
        index=0,
    )

    st.divider()

    # Active agents card
    st.markdown("### 🤖 Active Multi-Agent Crew")
    agents_info = [
        ("🔍 Lore & Trivia Scout", "Searches wikis & dev interviews for hidden lore"),
        ("🐛 DevLog & Bug Archaeologist", "Mines Reddit & Steam for bugs & patch notes"),
        ("✍️ Viral Reel Scriptwriter", "Crafts 3 scroll-stopping Reel scripts"),
        ("🎬 Production & SEO Director", "Builds B-roll cues, captions & hashtags"),
    ]
    for name, desc in agents_info:
        st.markdown(
            f'<div class="agent-card">'
            f'<div class="agent-name">{name}</div>'
            f'<div class="agent-desc">{desc}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )


# ── Main Content ────────────────────────────────────────────────────
st.markdown('<h1 class="main-title">🎮 ReelLore AI</h1>', unsafe_allow_html=True)
st.markdown(
    '<p class="sub-title">Multi-Agent Game Lore & Dev-Log Instagram Reel Generator — '
    'Powered by CrewAI × Groq</p>',
    unsafe_allow_html=True,
)

# Initialize session state for game_name
if "game_name" not in st.session_state:
    st.session_state.game_name = "Red Dead Redemption 2"


def set_game(name: str):
    st.session_state.game_name = name


# Game input bound directly to session state
st.text_input(
    "🎮 Enter Game Name",
    key="game_name",
    placeholder="Type a game title…",
    label_visibility="visible",
)
game_name = st.session_state.game_name

# Quick-select pills with on_click callback
st.markdown("**Quick Select:**")
pill_cols = st.columns(5)
quick_games = ["Cyberpunk 2077", "Kingdom Come: Deliverance 2", "GTA V", "Elden Ring", "The Witcher 3"]
for i, qg in enumerate(quick_games):
    pill_cols[i].button(
        qg,
        key=f"pill_{i}",
        on_click=set_game,
        args=(qg,),
        use_container_width=True,
    )

st.markdown("---")

# Launch and Load buttons
launch_disabled = not groq_key or not serper_key
if launch_disabled:
    st.warning("⚠️ Both `GROQ_API_KEY` and `SERPER_API_KEY` must be configured to launch the crew.")

btn_col1, btn_col2 = st.columns([3, 2])
with btn_col1:
    launch = st.button(
        "🚀 Launch Multi-Agent Crew",
        disabled=launch_disabled,
        use_container_width=True,
        type="primary",
    )
with btn_col2:
    load_saved = st.button(
        "📂 Load Last Saved Run from `outputs/`",
        use_container_width=True,
    )

# ── Load Saved Run Logic ───────────────────────────────────────────
if load_saved:
    outputs_dir = os.path.join(os.path.dirname(__file__), "outputs")
    task_specs = [
        ("01_lore_findings.md", "Lore & Trivia Scout"),
        ("02_dev_and_bugs.md", "DevLog & Bug Archaeologist"),
        ("03_reel_scripts.md", "Viral Reel Scriptwriter"),
        ("04_production_package.md", "Production & SEO Director"),
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
            f"[{time.strftime('%H:%M:%S')}] 📂 Loaded previous run from local outputs/ directory.",
            f"[{time.strftime('%H:%M:%S')}] ✅ Restored 01_lore_findings.md ({task_outputs[0]['word_count']} words)",
            f"[{time.strftime('%H:%M:%S')}] ✅ Restored 02_dev_and_bugs.md ({task_outputs[1]['word_count']} words)",
            f"[{time.strftime('%H:%M:%S')}] ✅ Restored 03_reel_scripts.md ({task_outputs[2]['word_count']} words)",
            f"[{time.strftime('%H:%M:%S')}] ✅ Restored 04_production_package.md ({task_outputs[3]['word_count']} words)",
        ]
        st.session_state.crew_result = {
            "final_output": final_out,
            "task_outputs": task_outputs,
            "logs": saved_logs,
            "elapsed_seconds": "Saved",
        }
        st.session_state.agent_logs = saved_logs
        st.success(f"✅ Loaded {found_files} saved agent outputs from `outputs/`!")
    else:
        st.warning("⚠️ No completed runs found in `outputs/` directory yet. Click **Launch Multi-Agent Crew** to run the agents!")

# ── Crew Execution ──────────────────────────────────────────────────
if launch:
    if "agent_logs" not in st.session_state:
        st.session_state.agent_logs = []

    # Visual Placeholders for live telemetry
    banner_placeholder = st.empty()
    progress_placeholder = st.empty()
    live_progress = progress_placeholder.progress(
        0.10, text="⏳ Agent 1/4: Lore & Trivia Scout is searching wikis & lore..."
    )

    terminal_expander = st.expander("📡 Live Crew Terminal & API Stream", expanded=True)
    with terminal_expander:
        terminal_stream_placeholder = st.empty()
        terminal_stream_placeholder.markdown(
            f'<div class="live-terminal-stream">🚀 Connecting to model `{model_choice}` on Groq LPU engine & initializing 4 agents...</div>',
            unsafe_allow_html=True,
        )

    # Initialize stdout/stderr capture
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

    def ui_log_callback(msg: str):
        st.session_state.agent_logs.append(msg)
        output_capture.write(f"{msg}\n")

    update_banner("Agent 1/4: Lore & Trivia Scout", "Initializing agent pipeline and search tools...")

    with st.status(f"🚀 Running 4-agent crew for **{game_name}**…", expanded=True) as status_box:
        status_box.write(f"Connected to model `{model_choice}` on Groq LPU engine…")
        st.session_state.agent_logs = []

        try:
            from src.crew import run_crew

            result = run_crew(
                game_name=game_name,
                model_name=model_choice,
                content_focus=content_focus,
                log_callback=ui_log_callback,
                status_box=status_box,
                progress_callback=update_progress,
                banner_callback=update_banner,
            )
            st.session_state.crew_result = result
            status_box.update(label=f"✅ Crew completed in {result['elapsed_seconds']}s!", state="complete")
            banner_placeholder.markdown(
                f"""
                <div class="pulse-banner" style="border-color:#22c55e;">
                    <div>
                        <div class="pulse-title"><span class="pulse-dot" style="background:#22c55e; box-shadow:0 0 10px #22c55e;"></span> All 4 Agents Completed!</div>
                        <div class="pulse-sub">✅ Reel production package generated successfully</div>
                    </div>
                    <div class="pulse-timer" style="color:#22c55e; border-color:#22c55e;">⏱️ {result['elapsed_seconds']}s</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        except Exception as exc:
            status_box.update(label="❌ Crew execution failed", state="error")
            st.error(f"❌ Execution Failed: {type(exc).__name__}: {str(exc)}")
            st.exception(exc)

            banner_placeholder.markdown(
                f"""
                <div class="pulse-banner" style="border-color:#ef4444;">
                    <div>
                        <div class="pulse-title"><span class="pulse-dot" style="background:#ef4444; box-shadow:0 0 10px #ef4444;"></span> Execution Interrupted</div>
                        <div class="pulse-sub">❌ Error: {html.escape(str(exc)[:120])}</div>
                    </div>
                    <div class="pulse-timer" style="color:#ef4444; border-color:#ef4444;">FAIL</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            # Check if any partial outputs were saved before failure
            outputs_dir = os.path.join(os.path.dirname(__file__), "outputs")
            task_specs = [
                ("01_lore_findings.md", "Lore & Trivia Scout"),
                ("02_dev_and_bugs.md", "DevLog & Bug Archaeologist"),
                ("03_reel_scripts.md", "Viral Reel Scriptwriter"),
                ("04_production_package.md", "Production & SEO Director"),
            ]
            partial_outputs = []
            found_any = False
            for fname, label in task_specs:
                fpath = os.path.join(outputs_dir, fname)
                if os.path.exists(fpath):
                    with open(fpath, "r", encoding="utf-8") as f:
                        c = f.read()
                    if c.strip():
                        found_any = True
                else:
                    c = f"*(Agent interrupted before completing `{fname}`)*"
                partial_outputs.append({
                    "agent": label,
                    "file": fname,
                    "output": c,
                    "word_count": len(c.split()),
                    "char_count": len(c),
                })
            if found_any:
                st.info("ℹ️ Partial agent outputs saved prior to interruption are available below.")
                st.session_state.crew_result = {
                    "final_output": partial_outputs[0]["output"],
                    "task_outputs": partial_outputs,
                    "logs": st.session_state.agent_logs,
                    "elapsed_seconds": "Partial",
                }

        finally:
            output_capture.stop()


# ── Results Display ─────────────────────────────────────────────────
if "crew_result" in st.session_state:
    result = st.session_state.crew_result

    elapsed_display = (
        f"{result['elapsed_seconds']}s"
        if isinstance(result.get("elapsed_seconds"), (int, float))
        else str(result.get("elapsed_seconds", "Saved"))
    )

    # Metrics row
    st.markdown(
        f"""
        <div class="metric-row">
            <div class="metric-card">
                <div class="metric-value">4</div>
                <div class="metric-label">Agents Executed</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{elapsed_display}</div>
                <div class="metric-label">Total Execution Time</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{sum(t['word_count'] for t in result['task_outputs'])}</div>
                <div class="metric-label">Total Words Generated</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{len(result['logs'])}</div>
                <div class="metric-label">Trace Log Entries</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # 4 Tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "📦 Final Reel Package",
        "🤖 Individual Agent Outputs (Proof of 4 Agents)",
        "📡 Live Agent Execution Trace (Logs)",
        "🏗️ Multi-Agent Architecture Diagram",
    ])

    # ── Tab 1: Final Package ────────────────────────────────────────
    with tab1:
        st.markdown("### 🎬 Complete Reel Production Package")
        st.markdown(result["final_output"])
        st.divider()

        # Download button
        full_package = ""
        for t in result["task_outputs"]:
            full_package += f"# {t['agent']}\n\n{t['output']}\n\n{'='*60}\n\n"

        st.download_button(
            label="⬇️ Download Full Package (.md)",
            data=full_package,
            file_name=f"ReelLore_{game_name.replace(' ', '_')}_Package.md",
            mime="text/markdown",
        )

    # ── Tab 2: Individual Agent Outputs ─────────────────────────────
    with tab2:
        st.markdown("### 🔍 Proof of Multi-Agent Execution")
        st.info("Each expander below shows the **exact output** produced by one of the 4 agents.")

        for i, t in enumerate(result["task_outputs"], 1):
            emoji = ["🔍", "🐛", "✍️", "🎬"][i - 1]
            with st.expander(f"{emoji} Agent {i}: {t['agent']}  |  📄 {t['file']}  |  📊 {t['word_count']} words", expanded=(i == 1)):
                st.caption(f"Output file: `outputs/{t['file']}`  |  Characters: {t['char_count']:,}")
                st.markdown(t["output"])

    # ── Tab 3: Execution Trace ──────────────────────────────────────
    with tab3:
        st.markdown("### 📡 Agent Execution Trace Log")
        st.caption("Real-time log of agent steps, tool calls, and task handoffs captured via CrewAI callbacks.")

        log_text = "\n".join(result["logs"])
        st.markdown(f'<div class="log-terminal">{log_text}</div>', unsafe_allow_html=True)

        st.download_button(
            label="⬇️ Download Trace Log (.txt)",
            data=log_text,
            file_name="execution_trace_log.txt",
            mime="text/plain",
        )

    # ── Tab 4: Architecture Diagram ─────────────────────────────────
    with tab4:
        st.markdown("### 🏗️ Multi-Agent Architecture Diagram")
        st.caption("Visual representation of the ReelLore AI sequential agent pipeline.")

        graph = """
        digraph ReelLoreAI {
            rankdir=TB;
            bgcolor="#0E0E12";
            node [
                shape=box,
                style="filled,rounded",
                fontname="Inter",
                fontsize=11,
                fontcolor="#F0F0F5",
                color="#3a3a5a",
                penwidth=1.5
            ];
            edge [
                color="#8032FC",
                fontcolor="#9898B0",
                fontname="Inter",
                fontsize=9,
                penwidth=1.5
            ];

            // Nodes
            User [label="👤 User\\n(Game Name Input)", fillcolor="#1a1a2e"];
            CrewManager [label="🎯 Crew Manager\\n(Sequential Process)", fillcolor="#2d1b5e", color="#8032FC"];

            Agent1 [label="🔍 Agent 1\\nLore & Trivia Scout", fillcolor="#1e2a1e", color="#22c55e"];
            Agent2 [label="🐛 Agent 2\\nDevLog & Bug Archaeologist", fillcolor="#2a1e1e", color="#ef4444"];
            Agent3 [label="✍️ Agent 3\\nViral Reel Scriptwriter", fillcolor="#1e1e2a", color="#3b82f6"];
            Agent4 [label="🎬 Agent 4\\nProduction & SEO Director", fillcolor="#2a2a1e", color="#eab308"];

            Serper [label="🌐 Serper API\\n(Google Search)", fillcolor="#1a1a2e", shape=ellipse];
            Reddit [label="📱 Reddit JSON\\n(Community Mining)", fillcolor="#1a1a2e", shape=ellipse];
            Steam [label="🎮 Steam API\\n(Patch Notes)", fillcolor="#1a1a2e", shape=ellipse];

            Output [label="📦 Final Output\\n(3 Reel Scripts +\\nProduction Package)", fillcolor="#2d1b5e", color="#8032FC"];

            // Edges
            User -> CrewManager [label="game name"];
            CrewManager -> Agent1 [label="Task 1"];
            CrewManager -> Agent2 [label="Task 2"];
            Agent1 -> Agent3 [label="lore context", style=dashed];
            Agent2 -> Agent3 [label="devlog context", style=dashed];
            CrewManager -> Agent3 [label="Task 3"];
            Agent3 -> Agent4 [label="scripts context", style=dashed];
            CrewManager -> Agent4 [label="Task 4"];
            Agent4 -> Output [label="final package"];

            Agent1 -> Serper [label="search", style=dotted];
            Agent2 -> Reddit [label="mine", style=dotted];
            Agent2 -> Steam [label="fetch", style=dotted];
        }
        """
        st.graphviz_chart(graph)

        st.markdown("""
        **Pipeline Flow:**
        1. **User** enters a game name → **Crew Manager** orchestrates 4 sequential tasks
        2. **Agent 1** (Lore Scout) searches game wikis via **Serper API**
        3. **Agent 2** (Bug Archaeologist) mines **Reddit** and **Steam** for dev stories
        4. **Agent 3** (Scriptwriter) receives context from Agents 1 & 2 → writes 3 Reel scripts
        5. **Agent 4** (Production Director) receives scripts → produces full production package
        6. All outputs saved individually to `outputs/` as multi-agent execution proof
        """)

# ── Footer ──────────────────────────────────────────────────────────
st.markdown("---")
st.markdown(
    "<div style='text-align:center; color:#5a5a7a; font-size:0.8rem;'>"
    "ReelLore AI — Built with CrewAI × Groq × Streamlit | "
    "Shrav Jitendra Siddhpura (SAP: 60004230236)"
    "</div>",
    unsafe_allow_html=True,
)
