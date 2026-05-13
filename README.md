# AutoNews AI — Complete Project

## 📁 Structure

```
news_room/
├── src/                    # Frontend (React Admin Portal)
│   ├── components/         # Sidebar, TopBar, StatCard, etc.
│   ├── pages/              # Dashboard, AI Agents, Analytics, etc.
│   ├── data/               # Mock data for UI
│   └── index.css           # Design system
│
├── backend/                # Backend (Python Automation)
│   ├── config.py           # Settings & API keys
│   ├── news_scraper.py     # Trending news detection
│   ├── fact_checker.py     # Fake news filter
│   ├── script_writer.py    # AI script generation (Gemini)
│   ├── video_maker.py      # Video creation (Edge TTS + FFmpeg)
│   ├── youtube_upload.py   # YouTube API upload
│   ├── insta_upload.py     # Instagram API upload
│   ├── pipeline.py         # Main orchestrator
│   ├── scheduler.py        # Cron scheduler (6AM/12PM/5PM/7PM)
│   ├── requirements.txt    # Python dependencies
│   └── .env.example        # API key template
│
├── index.html
├── package.json
└── README.md
```

## 🚀 Quick Start

### Frontend (Admin Portal)
```bash
cd news_room
npm install
npm run dev
# Open http://localhost:5173
```

### Backend (Automation Pipeline)
```bash
cd news_room/backend
pip install -r requirements.txt

# Copy and fill API keys
copy .env.example .env

# Run pipeline once (manual approval mode)
python pipeline.py

# Run pipeline with auto-upload
python pipeline.py --auto

# Start scheduler (runs at 6AM, 12PM, 5PM, 7PM)
python scheduler.py
```

## 🔑 API Keys Setup

| Service | Get From | Free Limit |
|---------|----------|------------|
| NewsAPI | newsapi.org | 100 req/day |
| Gemini | aistudio.google.com | 1500 req/day |
| YouTube API | console.cloud.google.com | Free |
| Instagram API | developers.facebook.com | Free |

## 📊 Pipeline Flow

```
Google Trends + NewsAPI + Reddit
        ↓
   News Scout (scrape)
        ↓
   Fact Checker (verify)
        ↓
   Script Writer (Gemini AI)
        ↓
   Video Maker (Edge TTS + FFmpeg)
        ↓
   Human Approval (admin portal)
        ↓
   YouTube + Instagram Upload
        ↓
   Analytics Tracking
```
