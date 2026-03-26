# Twitter Bot Backend

FastAPI backend server for the Twitter Bot application.

## Structure

```
backend/
├── main.py              # FastAPI application entry point
├── config.py            # Configuration settings
├── requirements.txt     # Python dependencies
│
├── ai/                  # AI & Content Generation
│   ├── behavior_planner.py
│   ├── content_generator.py
│   ├── profile_analyzer.py
│   └── selector_finder.py
│
├── api/                 # API Layer
│   ├── dependencies.py
│   └── routes/          # Endpoint handlers
│       ├── actions.py
│       ├── bot.py
│       ├── dashboard.py
│       ├── file_import.py
│       ├── logs.py
│       ├── profiles.py
│       ├── sessions.py
│       ├── settings.py
│       ├── stats.py
│       ├── tasks.py
│       └── websocket.py
│
├── core/                # Core Bot Functionality
│   ├── playwright_manager.py
│   ├── selectors.py
│   └── twitter_actions.py
│
├── db/                  # Database Layer
│   ├── database.py
│   ├── models.py
│   └── repositories/
│
├── services/            # Business Logic
│   ├── action_service.py
│   ├── profile_service.py
│   └── task_service.py
│
├── utils/               # Utilities
│   └── logger.py
│
└── logs/                # Application logs
```

## Setup

1. **Create virtual environment**
   ```bash
   python -m venv venv
   ```

2. **Activate virtual environment**
   ```bash
   # Windows
   ./venv/Scripts/activate

   # Linux/Mac
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   ./venv/Scripts/pip install -r requirements.txt
   ```

## Running

```bash
./venv/Scripts/python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

Or with auto-reload for development:
```bash
./venv/Scripts/python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## API Documentation

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
- **API Endpoints List:** [../API_ENDPOINTS.md](../API_ENDPOINTS.md)

## Key Components

### API Routes

| Route | Description |
|-------|-------------|
| `/api/v1/profiles` | Profile management (sync, open browser, etc.) |
| `/api/v1/tasks` | Task queue operations |
| `/api/v1/actions` | Twitter actions (follow, like, retweet, etc.) |
| `/api/v1/dashboard` | Dashboard statistics |
| `/api/v1/settings` | Application settings |
| `/api/v1/logs` | Log retrieval |
| `/api/v1/stats` | Statistics and analytics |
| `/api/v1/sessions` | Session management |

### Core Modules

- **playwright_manager.py** - Browser automation via AdsPower + Playwright
- **twitter_actions.py** - Twitter-specific automation actions
- **selectors.py** - CSS selectors for Twitter/X elements

### AI Modules

- **content_generator.py** - Gemini-powered content generation
- **profile_analyzer.py** - AI-based profile analysis
- **behavior_planner.py** - Action planning and scheduling

## Database

SQLite database (`twitter_bot.db`) with tables for:
- Profiles
- Actions
- Tasks
- Sessions
- Logs
- Statistics

## Environment Variables

Configured via `.env` file in the project root:

| Variable | Description |
|----------|-------------|
| `ADSPOWER_API_URL` | AdsPower local API URL |
| `GEMINI_API_KEY` | Google Gemini API key |
| `LOG_LEVEL` | Logging level (INFO, DEBUG, etc.) |
