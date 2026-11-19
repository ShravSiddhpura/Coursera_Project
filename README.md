# 🎮 ReelLore AI — Editorial Media Studio & Multi-Agent Content Engine

> **A high-throughput, production-grade Short-Form Video & LinkedIn Virality Engine** designed for employer review and free cloud deployment on **Streamlit Community Cloud** — powered by **CrewAI × Groq LPU × Streamlit**.

![Python](https://img.shields.io/badge/Python-3.11%20%7C%203.12-blue?logo=python)
![CrewAI](https://img.shields.io/badge/CrewAI-Multi--Agent%20Pipeline-blueviolet)
![Groq](https://img.shields.io/badge/LLM-Groq%20LPU%20Auto--Fallback-orange)
![UI](https://img.shields.io/badge/UI-Editorial%20Media%20Studio-emerald)
![PDF](https://img.shields.io/badge/Export-Shoot--Ready%20PDF-rose)
![Streamlit](https://img.shields.io/badge/Deploy-Streamlit%20Community%20Cloud-red?logo=streamlit)

---

## ✨ Upgraded Features & Core Architecture

### 🕹️ 1. PS5-Style Game Cover Selector & Dedicated GTA 6 Command Hub
- **PS5-Inspired Cover Shelf**: Curated shelf with authentic CDN artwork (Steam CDN + IGDB) and zero broken image icons:
  - **Grand Theft Auto VI (`GTA 6`)** is the **Hero Featured Title** (highlighted by default with custom telemetry, Leonida/Vice City research, and next-gen RAGE 9 engine tags).
  - Selectable covers for *Red Dead Redemption 2*, *Cyberpunk 2077*, *Kingdom Come: Deliverance 2*, *Elden Ring*, *GTA V*, and *The Witcher 3*.
  - **Custom Game Search**: Enter any video game in history with dynamic cover generation.
- **Dedicated GTA 6 Command Hub**:
  - Specific topic search bar (e.g., *"Vice City map & Leonida ecosystem details"*, *"Trailer 1 & 2 frame breakdowns & dev leaks"*, *"AI NPC & physics rumors vs confirmed facts"*).
  - 5 Quick Presets for instant high-relevance deep research.

### 🧠 2. Dynamic Model Discovery, True Meta Llama Priority & Auto-Fallback Chaining
- **Proper Model Filtering**:
  - `allam-2-7b` is an actual model ID on Groq (ALLaM-2-7B, an Arabic LLM), NOT a typo for Llama.
  - Automatically filters out `allam`, `whisper`, `guard`, `orpheus`, `playai`, and `distil-whisper`.
  - Dynamically queries `https://api.groq.com/openai/v1/models` and sorts **true Meta Llama models to the top** (`llama-3.3-70b-versatile`, `llama-3.1-8b-instant`, `meta-llama/llama-4-scout-17b-16e-instruct`).
- **Seamless Auto-Fallback Chaining**:
  - Configures LiteLLM fallback chains so if a model encounters a `429` rate limit or transient error, the multi-agent crew automatically pivots to active high-throughput fallbacks (`qwen/qwen3.8-27b`, `openai/gpt-oss-20b`) without stalling.

### 🚀 3. Dual-Algorithm Virality Engine (Instagram Reels + LinkedIn)
- **Instagram Reels Optimization**:
  - 0–3s pattern-interrupt hook (visual cue + spoken audio hook).
  - 2–4s rapid beat pacing with retention spikes and curiosity gaps.
  - Seamless loop phrasing where the final line connects back to the opening hook.
  - Saves/shares triggers + targeted SEO captions and 15–20 hashtags.
- **LinkedIn Algorithmic Optimization**:
  - Professional storytelling angle focusing on game engineering, world simulation, production craft, and studio leadership.
  - Strong opening 2-line "see more" hook that forces readers to expand the post.
  - High-dwell narrative structure with bullet takeaways.
  - Open-ended discussion-driving question prompting comments to trigger the LinkedIn engagement algorithm.

### 📄 4. Production-Grade Shoot-Ready PDF Packet (`fpdf2`)
- Pure Python PDF engine (`fpdf2`) with zero system font dependencies — guaranteed to compile on Linux/Streamlit Cloud.
- **Complete Director's Production Packet**:
  1. Executive Summary & Strategy Overview
  2. Shoot-Ready Time-Coded Scripts (Visual B-roll, on-screen text overlays, voiceover pacing tags)
  3. Companion LinkedIn High-Dwell Posts
  4. **Human-Readable Proof of Content & Citation Matrix**:
     - Named sources (Wikis, Reddit, Steam, Dev interviews) with **clickable links**.
     - Fact-check confidence matrix (🟢 Confirmed, 🟡 Community Discussion, 🔴 Speculation/Leak).
     - Video & Visual Reference Guide (exact trailer timestamps and B-roll scenes for the editor).

### 💾 5. Persistent Run History Store (`./history/`)
- Automatically saves every generation to `./history/` (JSON metadata, Markdown package, and Shoot-Ready PDF).
- Browse past runs, one-click **Reload into Studio**, and one-click **Download PDF** across browser refreshes and server restarts.

### 🎓 6. Academic Report Generator Intact (`generate_report.py`)
- Generates the complete 20+ page college report (`OJT_Coursera_Project_Report.docx`) with formal academic tables, architecture diagrams, and verification records.

---

## 🏗️ Multi-Agent Architecture

```
User Input (Game + Topic)
          │
          ▼
┌────────────────────────────────────────────────────────┐
│             CrewAI Sequential Orchestrator             │
│        (Groq LPU Engine + Automatic Fallbacks)         │
└────────────────────────────────────────────────────────┘
     │
     ├─► Agent 1: Lore & Trivia Scout ──────────► [Google Serper API]
     │            (Discovers lore & verified source links)
     │
     ├─► Agent 2: DevLog & Bug Archaeologist ───► [Reddit & Steam APIs]
     │            (Mines engine post-mortems & glitches)
     │
     ├─► Agent 3: Dual-Platform Scriptwriter ───► [Context from 1 & 2]
     │            (3 IG Reels + 3 LinkedIn Companion Posts)
     │
     └─► Agent 4: Production & Proof Director ──► [Context from 3]
                  (B-Roll cues, SEO captions, Proof of Content & PDF)
          │
          ▼
   Deliverables:
   ├── 📱 Instagram Reels Studio (Shoot Sheets)
   ├── 💼 LinkedIn Virality Engine (High-Dwell Narrative)
   ├── 🔍 Human-Readable Proof of Content & Clickable Links
   ├── 📄 Shoot-Ready PDF Packet (.pdf)
   └── 💾 Persistent History Store (./history/)
```

---

## 🚀 Local Installation & Run

### 1. Clone & Setup
```bash
git clone <your-repo-url>
cd Corsera_Project
```

### 2. Create Virtual Environment
```bash
python3 -m venv .venv
source .venv/bin/activate   # macOS / Linux
# .venv\Scripts\activate    # Windows
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure API Keys
Create a `.env` file in the workspace root:
```env
GROQ_API_KEY=gsk_your_groq_key_here
SERPER_API_KEY=your_serper_key_here
```

### 5. Launch the Studio
```bash
streamlit run app.py
```
Open [http://localhost:8501](http://localhost:8501) in your browser.

### 6. Academic Report Generation (Optional)
```bash
python generate_report.py
```
Outputs `OJT_Coursera_Project_Report.docx` in the workspace root.

---

## ☁️ Free Cloud Deployment: Streamlit Community Cloud

You can deploy **ReelLore AI** for free on [Streamlit Community Cloud](https://share.streamlit.io):

1. **Push your code to GitHub**:
   ```bash
   git add .
   git commit -m "Upgrade ReelLore AI to v2.0 Production Deck"
   git push origin main
   ```
2. **Go to Streamlit Community Cloud**:
   - Sign in with your GitHub account at [share.streamlit.io](https://share.streamlit.io).
   - Click **New app**.
   - Select your repository, branch (`main`), and main file path (`app.py`).
3. **Configure Secrets**:
   - In **Advanced settings** → **Secrets**, paste your API keys in TOML format:
     ```toml
     GROQ_API_KEY = "gsk_your_groq_key_here"
     SERPER_API_KEY = "your_serper_key_here"
     ```
   - Click **Deploy!**
4. **Employer Demo & Cold-Start Note**:
   - Streamlit Community Cloud puts idle free apps to sleep after a period of inactivity.
   - When an employer opens the link, the app will wake up in ~15–30 seconds.
   - Once awake, Groq LPU inference runs at **sub-second speeds (400+ tokens/sec)**!

---

## 📁 Repository Structure

```
./
├── .streamlit/
│   └── config.toml            # Studio dark theme & server settings
├── src/
│   ├── __init__.py            # Telemetry opt-outs & schema patches
│   ├── models.py              # Groq model discovery, Llama sorting & fallback chaining
│   ├── ps5_shelf.py           # PS5 game shelf catalog, cover CDN URLs & topic presets
│   ├── tools.py               # Custom Serper, Reddit & Steam research tools
│   ├── agents.py              # 4 specialized CrewAI agents
│   ├── tasks.py               # 4 sequential tasks (Dual-platform + Proof of Content)
│   ├── pdf_generator.py       # Shoot-Ready PDF script packet generator (fpdf2)
│   ├── history.py             # Persistent run history manager (JSON, MD, PDF)
│   └── crew.py                # Sequential crew assembly & live telemetry hooks
├── history/                   # Local persistent run store (.gitkeep tracked)
├── outputs/                   # Agent deliverables & generated PDF packets
├── app.py                     # Editorial Media Studio Streamlit application
├── generate_report.py         # Academic OJT report generator (python-docx)
├── requirements.txt           # Python dependencies (fpdf2, crewai, streamlit, etc.)
├── .env.example               # Secret template
├── .gitignore                 # Protected secrets & build artifacts
└── README.md                  # System documentation
```

---

## 🔑 Required API Keys

| Key | Provider | Purpose | Free Tier |
|---|---|---|---|
| `GROQ_API_KEY` | [console.groq.com](https://console.groq.com/keys) | Groq LPU inference (Meta Llama 3.3, Qwen, GPT-OSS) | Free fast tier |
| `SERPER_API_KEY` | [serper.dev](https://serper.dev/api-key) | Real-time Google Search organic data & URLs | 2,500 free queries |

---

## 🎓 Academic Project Information

- **Student:** Shrav Jitendra Siddhpura
- **SAP ID:** 60004230236 | **Roll:** C143
- **Programme:** B.Tech Computer Engineering (Honors in Data Science)
- **Institution:** Department of Computer Engineering, SVKM's DJSCE
- **Academic Year:** 2024–2025
- **Course:** On-Job Training (OJT) / Coursera Project
