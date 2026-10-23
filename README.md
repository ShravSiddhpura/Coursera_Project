# 🎮 ReelLore AI — Multi-Agent Game Lore & Dev-Log Instagram Reel Generator

> An autonomous multi-agent system that researches game lore, mines developer stories, and generates production-ready Instagram Reel scripts — powered by **CrewAI × Groq × Streamlit**.

![Python](https://img.shields.io/badge/Python-3.11+-blue?logo=python)
![CrewAI](https://img.shields.io/badge/CrewAI-Multi--Agent-blueviolet)
![Groq](https://img.shields.io/badge/LLM-Groq%20LLaMA%203.3-orange)
![Streamlit](https://img.shields.io/badge/UI-Streamlit-red?logo=streamlit)

---

## ✨ Features

- **4 Specialized AI Agents** working in a sequential pipeline
- **Real-time web research** via Google Serper API, Reddit JSON, and Steam API
- **3 Instagram Reel scripts** with Hook → Body → Climax/CTA structure
- **Complete production package** with B-roll cues, voiceover tags, and SEO captions
- **Live execution telemetry** — inspect each agent's work independently
- **Architecture diagram** rendered in-app via Graphviz
- **Dark-themed premium UI** built with Streamlit

## 🏗️ Multi-Agent Architecture

```
User → Crew Manager → Agent 1 (Lore Scout)        → [Serper API]
                    → Agent 2 (Bug Archaeologist)  → [Reddit + Steam API]
                    → Agent 3 (Scriptwriter)       ← context from 1 & 2
                    → Agent 4 (Production Director) ← context from 3
                    → Final Output Package
```

## 🚀 Quick Start

### 1. Clone & Setup
```bash
git clone <your-repo-url>
cd Corsera_Project
```

### 2. Create Virtual Environment
```bash
python -m venv .venv
source .venv/bin/activate   # macOS/Linux
# .venv\Scripts\activate    # Windows
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure API Keys
Create a `.env` file (or copy `.env.example`):
```bash
cp .env.example .env
# Edit .env with your actual API keys
```

### 5. Run the App
```bash
streamlit run app.py
```

### 6. Generate Academic Report (Optional)
```bash
python generate_report.py
```

## 📁 Project Structure

```
./
├── .streamlit/config.toml     # Dark theme configuration
├── src/
│   ├── __init__.py
│   ├── tools.py               # Serper, Reddit, Steam custom tools
│   ├── agents.py              # 4 CrewAI agents
│   ├── tasks.py               # 4 sequential tasks
│   └── crew.py                # Crew orchestration with callbacks
├── outputs/                   # Auto-saved agent outputs (proof)
├── app.py                     # Streamlit UI
├── generate_report.py         # Academic report generator
├── requirements.txt           # Dependencies
├── .env.example               # API key template
└── README.md                  # This file
```

## 🔑 API Keys Required

| Key | Source | Purpose |
|-----|--------|---------|
| `GROQ_API_KEY` | [console.groq.com](https://console.groq.com/keys) | LLM inference (LLaMA 3.3 70B) |
| `SERPER_API_KEY` | [serper.dev](https://serper.dev/api-key) | Google web search |

## 🎓 Academic Project

**Student:** Shrav Jitendra Siddhpura (SAP: 60004230236 | Roll: C143)  
**Programme:** B.Tech Computer Engineering (Honors in Data Science)  
**Institute:** DJSCE, Mumbai  
**Course:** OJT / Coursera Project  

---

*Built with ❤️ using CrewAI, Groq, and Streamlit*
