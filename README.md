# Twitter Bot

A sophisticated Twitter/X automation bot with a modern web interface (React + FastAPI). Manages multiple Twitter accounts through AdsPower browser profiles.

## Features

- **Multi-Account Management** - Integrate with AdsPower API for browser profile management
- **Task Queue System** - Persistent queue with batch processing and rate limiting
- **Following Automation** - Follow/unfollow users, collect followers, bulk operations
- **Content Interaction** - Like, retweet, comment on tweets and hashtags
- **AI-Powered Features** - Google Gemini integration for auto-generated comments
- **Real-Time Dashboard** - Monitor actions, statistics, and logs

## Project Structure

```
twitterbot/
├── backend/          # FastAPI backend (API server)
├── frontend/         # React + TypeScript frontend (Vite)
└── scripts/          # Helper scripts
```

## Quick Start

### Prerequisites

- Python 3.12+
- Node.js 18+
- AdsPower browser (for multi-profile management)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd twitterbot
   ```

2. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

3. **Install dependencies**

   Backend:
   ```bash
   cd backend
   python -m venv venv
   ./venv/Scripts/pip install -r requirements.txt
   ```

   Frontend:
   ```bash
   cd frontend
   npm install
   ```

### Running the Application

```bash
# Terminal 1 - Backend
cd backend
./venv/Scripts/python -m uvicorn main:app --host 0.0.0.0 --port 8000

# Terminal 2 - Frontend
cd frontend
npm run dev
```

Access the web interface at `http://localhost:3000`

## Documentation

- [API Endpoints](./API_ENDPOINTS.md) - Complete list of backend API endpoints
- [Architecture](./ARCHITECTURE.md) - System architecture and diagrams
- [Backend README](./backend/README.md) - Backend-specific documentation
- [Frontend README](./frontend/README.md) - Frontend-specific documentation

## Tech Stack

| Component | Technology |
|-----------|------------|
| Backend | FastAPI, Playwright, SQLite |
| Frontend | React, TypeScript, Vite, Tailwind CSS |
| AI | Google Gemini |
| Browser Automation | AdsPower + Playwright |

## Environment Variables

| Variable | Description |
|----------|-------------|
| `ADSPOWER_API_URL` | AdsPower local API URL |
| `GEMINI_API_KEY` | Google Gemini API key |

## License

Private project - All rights reserved.
