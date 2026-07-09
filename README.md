<div align="center">

# ⚽ MatchSense : Agentic World Cup 2026 Intelligence System

**Tagline:** *Beyond Scores. Understand the World Cup.*

An agentic AI system that autonomously gathers World Cup match intelligence, runs ensemble predictions with explainability, simulates the remaining knockout bracket via Monte Carlo, and serves it all through a proper web app with accessible audio briefings for low-vision fans.

An advanced, Multi-Agent World Cup Intelligence and Live Analytics platform built for the FIFA World Cup 2026 knockout stage. It integrates Large Language Models (LLMs), Ensemble Machine Learning (XGBoost + Poisson + ELO), SHAP explainability, and text-to-speech to deliver deep match analysis alongside accessibility-first audio briefings.

Instead of displaying basic stats, MatchSense utilizes specialized data gathering agents to compile match profiles, runs a weighted ensemble model to predict outcomes, explains each prediction using SHAP force values, and narrates the tactical preview aloud in multiple languages for low-vision football fans.

Designed with a premium, high-contrast dark theme (featuring glassmorphism layouts and sharp borders), the platform offers an interactive Knockout Bracket, SHAP contribution panels, live xG predictions, rolling championship probabilities, and accessibility controllers.

*Autonomous data gathering · Ensemble ML predictions · Explainability · Accessible audio briefings*

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-19-61DAFB?style=flat-square&logo=react&logoColor=black)](https://react.dev)
[![XGBoost](https://img.shields.io/badge/XGBoost-2.1-FF6600?style=flat-square)](https://xgboost.readthedocs.io)
[![MongoDB](https://img.shields.io/badge/MongoDB-Motor-47A248?style=flat-square&logo=mongodb&logoColor=white)](https://motor.readthedocs.io)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)](LICENSE)

</div>

---

🌐 **Deployed Link :** https://match-sense-frontend.onrender.com

--- 

## Problem framing ❓

MatchSense is a **multi-layer AI system** for the FIFA World Cup 2026 knockout stage that goes far beyond a basic win/loss predictor:

| What most projects do | What MatchSense does |
|---|---|
| Single model, one output | Weighted ensemble (ELO + Poisson + XGBoost) |
| Black-box predictions | SHAP feature explanations on every prediction |
| Static data | Live data agent with 3-provider fallback chain |
| Win/loss only | Full Monte Carlo bracket simulation (10k runs) |
| English only | TTS audio briefings in EN · ES · PT · FR |
| No accessibility | ARIA labels, keyboard nav, large-text toggle |
| Local script | Deployed web app with REST API |

Most "World Cup ML projects" are single-model win/loss predictors with no explainability, no live data refresh, and no accessibility consideration. MatchSense aims to be a multi-layer system: an autonomous data-gathering agent, a probabilistic ensemble model with explainability, and an accessibility-first output layer — combining three distinct technical skills into one coherent product rather than three disconnected demos, delivered as a real deployed website rather than a local script.

---

## Project Objective ✨
Design and develop a web-based World Cup intelligence console capable of providing event-based insights, predictions, and audio briefings using an ensemble ML pipeline and LangChain agent tools.

Unlike standard sports applications, this system shows:
*   **Explainable Predictions**: Explains every prediction using SHAP force values and football reasoning instead of black-box AI.
*   **Accessible briefings**: Converts structured match briefs into voice-narration previews (OpenAI TTS) in English, Spanish, Portuguese, and French.
*   **Monte Carlo Simulation**: Runs 10,000 runs across the tournament tree to calculate live championship odds.
*   **Automated Background Cron**: Live syncs, caching, and daily model retraining.

---

## 📸 Screenshots

### 1. Interactive Tournament Bracket
![Bracket Interface](https://raw.githubusercontent.com/Alvira-Parveen/Match-Sense/main/screenshots/bracket.png)

### 2. SHAP Explainability & Player Metrics
![SHAP Panel](https://raw.githubusercontent.com/Alvira-Parveen/Match-Sense/main/screenshots/shap.png)

### 3. Accessible Audio Match Brief
![Audio Player](https://raw.githubusercontent.com/Alvira-Parveen/Match-Sense/main/screenshots/audio.png)

---

## 🏛️ System Architecture Workflow

```
┌─────────────────────────────────────────────────────────────────┐
│                        MatchSense                               │
│                                                                 │
│  ┌──────────────┐   ┌──────────────────┐   ┌────────────────┐  │
│  │  DATA AGENT  │   │ PREDICTION ENGINE│   │ ACCESSIBILITY  │  │
│  │              │   │                  │   │     LAYER      │  │
│  │ LangChain    │──▶│ ELO Rating       │──▶│                │  │
│  │ tool-calling │   │ Poisson Model    │   │ LLM Summary    │  │
│  │              │   │ XGBoost (757 rows│   │ OpenAI TTS     │  │
│  │ • Fixtures   │   │ SHAP Explainer   │   │ EN/ES/PT/FR    │  │
│  │ • Form/H2H   │   │ Monte Carlo 10k  │   │ ARIA + a11y    │  │
│  │ • Injuries   │   │                  │   │                │  │
│  └──────┬───────┘   └──────────────────┘   └────────────────┘  │
│         │                                                       │
│  ┌──────▼───────────────────────────────────────────────────┐  │
│  │                    DATA SOURCES                           │  │
│  │  football-data.org → API-Football → TheSportsDB → Static │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  FastAPI Backend (:8001)  ←→  React Frontend (:3000)     │  │
│  │  MongoDB (Motor async)  ·  APScheduler background jobs   │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

```mermaid
graph TD
    subgraph Client [React 19 Frontend]
        UI[Knockout Bracket UI]
        TTS[Audio Match Brief Player]
        A11y[Large Text Alt Toggle]
        SHAP_UI[SHAP Graph Component]
    end

    subgraph Server [FastAPI Backend]
        API[FastAPI Router]
        Agent[LangChain Agent Engine]
        XGB[XGBoost Predictor]
        SHAP[SHAP Explainer]
        MC[Monte Carlo Simulator]
        Jobs[APScheduler Cron Tasks]
    end

    subgraph Data [Data & API Layer]
        CSV[(257 Real Matches CSV)]
        Mongo[(MongoDB Logs & Cache)]
        Apis[API-Football & football-data.org]
    end

    UI -->|Query Match| API
    API -->|Fetch Brief| Agent
    Agent -->|Scrape| Apis
    Agent -->|Log Activity| Mongo
    API -->|Predict| XGB
    XGB -->|Train| CSV
    API -->|Explain| SHAP
    API -->|Simulate| MC
    Jobs -->|Daily Sync / Retrain| API
    API -->|Generate MP3| TTS
```

### Layer 1 — Data Agent (agentic tool-calling)

- LangChain-style agent with tool access:
    - Tool: fetch live fixtures/scores
    - Tool: scrape team form + head-to-head history
    - Tool: pull injury/lineup news
- Runs daily as the tournament progresses (Round of 16 → QF → SF → Final)
- Output: structured JSON match briefs per fixture

### Layer 2 — Prediction Engine (ML core)

- Ensemble: ELO ratings + Poisson goal model + XGBoost on team features
- SHAP for explainability — surfaces why the model favors a team (form, squad depth, head-to-head)
- Monte Carlo simulation (10k+ runs) across the remaining bracket → live championship probability per team
- Re-runs and updates after every result

### Layer 3 — Accessibility Output

- Converts the agent's structured match brief into plain-language event summaries + TTS audio narration
- Positioned as an accessible match-briefing layer for visually impaired fans
- Differentiates the project from generic prediction tools and ties to my broader interest in assistive tech

### Web App  

- Backend : FastAPI serving REST endpoints — /predict, /bracket-simulation, /match-brief, /audio-summary — wrapping the agent + ensemble + Monte Carlo + accessibility layers
- Frontend : React (or plain HTML/CSS/JS) single-page site — bracket visualization, live win-probability bars, SHAP explanation panel, audio player for accessible briefings
- Reasoning for the switch: Streamlit is fine for an internal demo but reads as a "notebook with buttons" rather than a shipped product; a real frontend + API separation is what a portfolio/hackathon judge expects from something pitched as "agentic system," and it's also directly deployable (Vercel/Netlify for frontend, Render/Railway for backend) instead of requiring a local Python environment to run at all — which was the actual point of failure during my build (venv/dependency issues, OpenMP errors, etc. that a static deployed site sidesteps entirely for the end viewer)

---

## 🌟 Features

### 🤖 Layer 1 — Agentic Data Gathering
- **LangChain tool-calling** agent with 3 real tools: `fetch_fixture`, `form_and_h2h`, `injury_report`
- **4-provider fallback chain**: football-data.org → API-Football → TheSportsDB → static data
- **In-memory TTL cache** (1hr) to stay within free-tier API rate limits
- **LLM-routed mode** (optional): ReAct agent decides tool order autonomously

### 📊 Layer 2 — Ensemble Prediction + Explainability
- **ELO ratings** — 2000 FIFA ELO scores per team, updated with real results
- **Bivariate Poisson** — models goals scored/conceded independently, derives scoreline distribution
- **XGBoost classifier** — trained on 757 matches (257 real WC/Euro/Copa/AFCON knockouts + 500 synthetic)
- **Weighted ensemble** — ELO 25% · Poisson 35% · XGBoost 40%
- **SHAP explanations** — per-prediction feature contribution breakdown
- **Monte Carlo simulation** — 10,000 bracket runs, championship probability per team

### 🎙️ Layer 3 — Accessibility-First Output
- **Plain-language match previews** — LLM-generated, TTS-optimised narration
- **Audio briefings** — direct OpenAI TTS API (`tts-1`) in 4 voices/languages
- **Multi-language**: English (nova) · Spanish (jorge) · Portuguese (marco) · French (denise)
- **Large-text toggle** — UI font scales for low-vision users
- **ARIA labels** — full keyboard navigation support

### 🕐 Background Intelligence
- **APScheduler** — 4 jobs running in the FastAPI event loop
  - Fixture refresh every 6 hours
  - Monte Carlo re-run every 6 hours (offset 30 min)
  - XGBoost retrain daily at 03:00 UTC
  - Scraper cache clear every 2 hours

---

## 🧠 How It Works

```text
User Selects Match File
            ↓
    FastAPI Router
            ↓
  LangChain Data Agent
            ↓
┌───────────────────────┼────────────────────────┐
↓                       ↓                        ↓
Scrape Form & H2H     Fetch Fixtures       Squad Injury Feed
(football-data.org)   (API-Football)       (TheSportsDB)
└───────────────────────┬────────────────────────┘
                        ↓
            Ensemble Prediction Engine
      (ELO 25% · Poisson 35% · XGBoost 40%)
                        ↓
            ┌───────────┴───────────┐
            ↓                       ↓
    SHAP Explainability    Monte Carlo Bracket
    (Feature Attribution)    (10,000 Simulator Runs)
            └───────────┬───────────┘
                        ↓
             Accessibility TTS Output
          (Voice Briefings in 4 Languages)
```

---

## 📂 Project Structure

```
Match-Sense/
├── backend/
│   ├── server.py              # FastAPI app + all route handlers
│   ├── agent.py               # Match-brief orchestration + LLM summariser
│   ├── lc_agent.py            # LangChain agent + tool wrappers
│   ├── ml_engine.py           # ELO + Poisson + ensemble + Monte Carlo
│   ├── xgb_model.py           # XGBoost train / predict / SHAP
│   ├── scraper.py             # Live HTTP scraping (4-provider fallback)
│   ├── scheduler.py           # APScheduler background jobs
│   ├── tts_service.py         # TTS synthesis via OpenAI /v1/audio/speech
│   ├── data.py                # WC 2026 team + bracket static data
│   ├── data_provider.py       # Live/mock data abstraction layer
│   ├── cache.py               # MongoDB-backed API response cache
│   ├── historical_matches.csv # 257 real knockout matches (XGB training set)
│   ├── requirements.txt       # Python dependencies
│   └── .env.example           # Environment variable template (safe to commit)
│
├── frontend/
│   ├── src/
│   │   ├── App.js             # Root app + routing
│   │   ├── pages/
│   │   │   ├── TeamPage.jsx           # Team profile + MC probability
│   │   │   ├── AdminPage.jsx          # Admin result marking
│   │   │   └── ResultsArchivePage.jsx # Historical results
│   │   └── components/
│   │       ├── Bracket.jsx            # Interactive bracket UI
│   │       ├── SHAPPanel.jsx          # SHAP explanation visualisation
│   │       ├── AudioBriefingPlayer.jsx # TTS audio player
│   │       ├── MonteCarloChart.jsx    # MC championship probability chart
│   │       └── ...
│   ├── package.json
│   └── .env.example
│
├── tests/                     # pytest test suite
├── .gitignore
└── README.md
```

---

## 📦 Major Modules

### 1. Interactive Match Dashboard
*   Displays the Round of 16 through to the Final, updating predicted paths dynamically based on model outputs.
*   Highlights user-selected favorite teams across their projected tournament paths.

### 2. Explainable Prediction Panel
*   Displays win/draw/loss probabilities alongside predicted expected goal (xG) scorelines.
*   Draws interactive horizontal bar charts showing positive (blue) and negative (red) feature impacts on the outcome.

### 3. Accessible Audio Narrator
*   Streams base64-encoded MP3 audio previews.
*   Features a quick language dropdown to swap between English, Spanish, Portuguese, and French voice profiles.

### 4. Monte Carlo Bracket Simulator
*   Simulates the remaining tournament brackets 10,000 times.
*   Calculates and visualizes each team's probability of reaching the Quarterfinals, Semifinals, Final, and winning the Championship.

### 5. Automated Background Scheduler
*   **Fixture Sync**: Refreshes live matches every 6 hours.
*   **Simulation Sync**: Re-runs the Monte Carlo pipeline every 6.5 hours.
*   **Model Retraining**: Automatically retrains the XGBoost classifier on the updated historical match database daily at 03:00 UTC.

---

## 🛠️ Tech Stack

| Layer | Technology | Version |
|-------|-----------|---------|
| **API Framework** | FastAPI + Uvicorn | 0.110 / 0.25 |
| **Database** | MongoDB via Motor (async) | 4.6 / 3.3 |
| **ML** | XGBoost | 2.1.1 |
| **Explainability** | SHAP | 0.46 |
| **Data** | pandas · NumPy · scikit-learn | latest |
| **Agent** | LangChain + LangChain-Core | 0.3.x |
| **HTTP Client** | httpx (async) | 0.27+ |
| **Scheduler** | APScheduler | 3.10+ |
| **LLM / TTS** | OpenAI-compatible API (Gemini or OpenAI) | — |
| **Frontend** | React 19 + Tailwind CSS | 19 / 3.x |
| **UI Components** | shadcn/ui · Phosphor icons | — |
| **Validation** | Pydantic v2 | 2.6+ |
| **Auth** | JWT (python-jose) + bcrypt | — |

- Agent/orchestration: LangChain-style tool-calling
- ML: XGBoost, SHAP, custom ELO + Poisson goal model
- Simulation: Monte Carlo (NumPy)
- Backend: FastAPI (Python), serving the ML/agent layers as REST endpoints
- Frontend: React + Tailwind (or HTML/CSS/JS if time-constrained), deployed static/serverless
- Accessibility: TTS (e.g. gTTS) + summarization, audio served via the API
Data: live fixture/score APIs (API-Football), historical data for model training

---

## 🧠 Prerequisites

Make sure you have these installed before starting:

```bash
python3 --version    # 3.11 or higher
node --version       # 18 or higher
npm --version        # 9 or higher
```

You will also need accounts for (all have free tiers):

| Service | Purpose | Sign up |
|---------|---------|---------|
| **MongoDB Atlas** | Database | [mongodb.com/cloud/atlas/register](https://www.mongodb.com/cloud/atlas/register) |
| **API-Football** | Live fixture data | [dashboard.api-football.com](https://dashboard.api-football.com) |
| **football-data.org** | Team form scraping | [football-data.org/client/register](https://www.football-data.org/client/register) |
| **Google AI Studio** *(optional)* | LLM summaries + translations | [aistudio.google.com](https://aistudio.google.com) |
| **OpenAI** *(optional, for TTS audio)* | Audio briefings | [platform.openai.com](https://platform.openai.com) |

> **The app runs without LLM/TTS keys** — match summaries fall back to template text and audio is disabled gracefully.

---

## 🚀 Step-by-Step Installation Guide

### Step 1: Clone the Repository
```bash
git clone <your-repository-url>
cd Match-Sense
```

### Step 2: Set Up Backend Environment
```bash
# Activate your Python virtual environment
python3 -m venv venv
source venv/bin/activate

# Install backend dependencies
pip install -r backend/requirements.txt
```

### Step 3: Configure Environment Variables
Create a `.env` file in the `backend/` directory:
```env
MONGO_URL="your_mongodb_atlas_connection_string"
DB_NAME="matchsense"
LLM_API_KEY="your_google_gemini_or_openai_api_key"
API_FOOTBALL_KEY="your_api_football_key"
FOOTBALL_DATA_KEY="your_football_data_org_key"
ADMIN_KEY="your_admin_secret_key"
DATA_PROVIDER="api_football"
CORS_ORIGINS="http://localhost:3000"
LANGCHAIN_LLM_ROUTED="false"
```
*(Leave `LLM_API_KEY` blank to bypass AI features and use clean, template-based match summaries instead)*.

### Step 4: Run the Backend
```bash
cd backend
uvicorn server:app --reload --port 8001
```

### Step 5: Run the Frontend
Open a new terminal tab, navigate to the frontend directory, configure the backend connection, and launch:
```bash
cd frontend

# Set backend link
echo "REACT_APP_BACKEND_URL=http://localhost:8001" > .env

# Install and launch React
npm install
npm start
```
Open **[http://localhost:3000](http://localhost:3000)** in your browser!


---

## Environment Variables

Copy `backend/.env.example` to `backend/.env` and fill in your values.
**Never commit `.env`** — it is covered by `.gitignore`.

```ini
# ── Database (required) ───────────────────────────────────────────────────────
MONGO_URL=mongodb+srv://user:password@cluster0.xxxxx.mongodb.net/matchsense
DB_NAME=matchsense

# ── LLM + TTS (optional — app works without these) ───────────────────────────
# Accepts: OpenAI key (sk-...) for full LLM+TTS
#          Google Gemini key (AIza...) for LLM only (TTS requires OpenAI)
LLM_API_KEY=your_key_here

# ── Football data APIs (recommended) ─────────────────────────────────────────
API_FOOTBALL_KEY=your_api_football_key      # from dashboard.api-football.com
FOOTBALL_DATA_KEY=your_football_data_key   # from football-data.org

# ── App config ────────────────────────────────────────────────────────────────
DATA_PROVIDER=api_football          # api_football | mock
CORS_ORIGINS=http://localhost:3000  # comma-separated allowed origins
ADMIN_KEY=change_me_strong_secret   # protects /admin/results endpoint

# ── Optional ──────────────────────────────────────────────────────────────────
LANGCHAIN_LLM_ROUTED=false   # true = ReAct agent routes tool calls via LLM
```

| Variable | Required | Description |
|----------|:--------:|-------------|
| `MONGO_URL` | ✅ | MongoDB Atlas connection string |
| `DB_NAME` | ✅ | Database name (e.g. `matchsense`) |
| `LLM_API_KEY` | ⚡ | LLM provider key — enables AI summaries + TTS |
| `API_FOOTBALL_KEY` | ⚡ | Live fixture + standings data (free tier) |
| `FOOTBALL_DATA_KEY` | ⚡ | Team form scraping (free tier) |
| `DATA_PROVIDER` | ✅ | `api_football` (default) or `mock` |
| `CORS_ORIGINS` | ✅ | Allowed frontend origins |
| `ADMIN_KEY` | ✅ | Secret for admin result endpoints |
| `LANGCHAIN_LLM_ROUTED` | — | Enable autonomous LLM-routed agent (costs credits) |

---

## API Reference

All endpoints are prefixed with `/api`.

### Core

| Method | Endpoint | Description |
|--------|---------|-------------|
| `GET` | `/` | Health check + model readiness |
| `GET` | `/teams` | All 16 Round of 16 teams with ELO + stats |
| `GET` | `/bracket` | Full bracket structure with predictions |

### Predictions

| Method | Endpoint | Description |
|--------|---------|-------------|
| `GET` | `/predict/{match_id}` | Ensemble prediction + SHAP values for one match |
| `GET` | `/simulate?runs=10000` | Monte Carlo bracket simulation |
| `GET` | `/replay` | Model accuracy replay on historical data |

### Agent & Intelligence

| Method | Endpoint | Description |
|--------|---------|-------------|
| `GET` | `/match-brief/{match_id}` | Full agent-gathered match intelligence brief |
| `GET` | `/audio-summary/{match_id}?lang=en` | TTS audio briefing (lang: `en` `es` `pt` `fr`) |
| `GET` | `/agent-logs` | Recent agent activity log (last 60 events) |

### Teams & Live Data

| Method | Endpoint | Description |
|--------|---------|-------------|
| `GET` | `/team/{code}` | Team profile + Monte Carlo championship probability |
| `GET` | `/live/fixtures` | Live R16 fixtures (cached 12h) |
| `GET` | `/scheduler/status` | Background job next-run times + history |

### User Features

| Method | Endpoint | Description |
|--------|---------|-------------|
| `POST` | `/favorites` | Save a favourite team (session-based) |
| `GET` | `/favorites` | Get saved favourites |
| `POST` | `/admin/results` | Mark a real match result (`ADMIN_KEY` required) |

---

## How the ML Works

### Training Data
- **257 real matches** — World Cup knockout rounds (1986–2022), Euro knockouts (2000–2024), Copa América (2015–2024), AFCON (2021–2023), UEFA Nations League Finals
- **500 synthetic matches** — generated from the same feature distribution to balance class labels
- **Features**: home ELO, away ELO, home form (0–1), away form (0–1), attack differential, defense differential, injury delta, result (0=away win, 1=draw, 2=home win)

### Ensemble Weights
```
Final probability = 0.25 × ELO + 0.35 × Poisson + 0.40 × XGBoost
```

### SHAP Explanations
Every `/predict/{match_id}` response includes a `shap_values` object showing how much each feature pushed the prediction toward home win, draw, or away win.

### Monte Carlo Simulation
Runs the full 16-team bracket 10,000 times sampling from each match's probability distribution. Returns championship probability per team and most likely bracket path.

---

## Running Tests

```bash
cd backend
pytest tests/ -v
```

---

## Deployment

### Backend (Render / Railway)

1. Connect your GitHub repo
2. Set **Root Directory** → `backend`
3. Set **Start Command** → `uvicorn server:app --host 0.0.0.0 --port $PORT`
4. Add all environment variables from `.env` in the dashboard
5. Set `CORS_ORIGINS=https://your-frontend.vercel.app`

### Frontend (Vercel / Netlify)

1. Connect your GitHub repo
2. Set **Root Directory** → `frontend`
3. Set **Build Command** → `npm run build`
4. Set **Output Directory** → `build`
5. Add `REACT_APP_API_URL=https://your-backend.render.com` as env var

---

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Commit your changes: `git commit -m "feat: add my feature"`
4. Push to the branch: `git push origin feature/my-feature`
5. Open a Pull Request

---

## 👤 Author

**Name**: ALVIRA PARVEEN  
🔗 [LinkedIn](https://www.linkedin.com/in/alvira-parveen-78022536b)  
🌐 [GitHub](https://github.com/Alvira-Parveen)

---

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.


---

<div align="center">
Built with ⚽ for the FIFA World Cup 2026
</div>
