# AutoNews AI — Complete Project (v2.0)

AutoNews AI is a fully automated, agent-driven content creation engine. It hunts for trending news, verifies facts, writes scripts using AI, generates narrated videos, and queues them for YouTube/Instagram upload—all overseen by a Multi-Agent "Team Leader" and monitored via a live React Dashboard.

## 🚀 Key Features
- **Multi-Agent Architecture**: A "Team Leader" (`supervisor.py`) orchestrates subordinate agents with built-in retry loops and error recovery.
- **Trend Hunter Agent v2**: Uses Circuit Breakers, semantic deduplication, and an 8-signal virality scorer across Google Trends, Reddit, NewsAPI, and curated RSS feeds.
- **Fact Checker Agent v2**: Evaluates clickbait probability, matches against a domain trust registry, and flags misinformation.
- **Live React Dashboard**: View real-time Server-Sent Event (SSE) logs, track agent health, and watch generated `.mp4` videos directly in your browser.
- **Local Database**: All scraped news and agent actions are persisted in an SQLite database.

---

## 📁 Structure

```text
news_room/
├── src/                    # Frontend (React Admin Portal)
│   ├── components/         # Live AgentHealth, LogTerminal, PipelineTracker
│   ├── pages/              # Dashboard, ContentQueue (Video Playback)
│   └── index.css           # Design system
│
├── backend/                # Backend (Python Multi-Agent System)
│   ├── api.py              # FastAPI server (SSE logs & Media serving)
│   ├── supervisor.py       # Team Leader Agent (Orchestrator)
│   ├── database.py         # SQLite DB Setup (autonews.db)
│   ├── config.py           # Settings & API keys
│   ├── news_scraper.py     # Trend Hunter Agent v2.0
│   ├── fact_checker.py     # Fact Checker Agent v2.0
│   ├── script_writer.py    # AI script generation (Gemini)
│   ├── video_maker.py      # Video creation (Edge TTS + FFmpeg)
│   ├── youtube_upload.py   # YouTube API upload
│   ├── insta_upload.py     # Instagram API upload
│   ├── pipeline.py         # Legacy/manual orchestrator
│   └── scheduler.py        # Cron scheduler (6AM/12PM/5PM/7PM)
```

---

## 🚀 Quick Start

### 1. Backend (FastAPI + AI Agents)
Open a terminal and navigate to the backend folder:
```bash
cd news_room/backend

# Install dependencies (requires FastAPI, Uvicorn, etc.)
pip install -r requirements.txt
pip install fastapi uvicorn sse-starlette

# Set up API keys (Gemini, NewsAPI, YouTube)
copy .env.example .env

# Start the Backend API & Team Leader Server
python -m uvicorn api:app --reload
```
*(The server runs on `http://localhost:8000`)*

### 2. Frontend (React Live Dashboard)
Open a second terminal:
```bash
cd news_room
npm install
npm run dev
```
*(Open `http://localhost:5173` in your browser)*

Click **"Run Pipeline Now"** on the dashboard to watch the Team Leader dispatch agents and generate videos in real-time!

---

## 🔑 API Keys Setup

| Service | Get From | Free Limit |
|---------|----------|------------|
| NewsAPI | newsapi.org | 100 req/day |
| GNews | gnews.io | 100 req/day |
| Gemini | aistudio.google.com | 1500 req/day |
| YouTube API | console.cloud.google.com | Free |
| Instagram API | developers.facebook.com | Free |

---

## 📊 Multi-Agent Flow

```text
Google Trends / RSS / Reddit / NewsAPI
               ↓
    [Agent 1] Trend Hunter
               ↓
          SQLite Database
               ↓
    [Agent 2] Fact Checker
               ↓
    [Agent 3] Script Writer (Gemini AI)
               ↓
    [Agent 4] Video Maker (TTS + FFmpeg)
               ↓
    [Supervisor] Team Leader (Handles Retries & Errors)
               ↓
    React Dashboard (Live Logs & Video Playback)
               ↓
    [Agent 5] YouTube/Instagram Uploader
```
