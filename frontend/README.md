# Twitter Bot Frontend

React + TypeScript frontend dashboard for the Twitter Bot application.

## Tech Stack

- **React 18** - UI framework
- **TypeScript** - Type safety
- **Vite** - Build tool and dev server
- **Tailwind CSS** - Styling
- **React Router** - Routing

## Structure

```
frontend/
├── src/
│   ├── main.tsx           # Entry point
│   ├── App.tsx            # Root component with routing
│   ├── index.css          # Global styles
│   │
│   ├── api/               # API Client
│   │   └── client.ts
│   │
│   ├── components/        # Reusable UI Components
│   │   ├── AccountActions.tsx
│   │   ├── FileImport.tsx
│   │   ├── Layout.tsx
│   │   ├── LogViewer.tsx
│   │   ├── ProfileCard.tsx
│   │   ├── ProfileSelector.tsx
│   │   ├── SessionSummaryCard.tsx
│   │   ├── Sidebar.tsx
│   │   ├── StatsCard.tsx
│   │   ├── StatsTrendCard.tsx
│   │   └── TaskQueue.tsx
│   │
│   ├── pages/             # Page Components
│   │   ├── Actions.tsx
│   │   ├── Bot.tsx
│   │   ├── Dashboard.tsx
│   │   ├── HashtagActions.tsx
│   │   ├── Logs.tsx
│   │   ├── PostActions.tsx
│   │   ├── Profiles.tsx
│   │   ├── Settings.tsx
│   │   ├── Stats.tsx
│   │   ├── Tasks.tsx
│   │   └── UserActions.tsx
│   │
│   ├── hooks/             # Custom React Hooks
│   │   └── useWebSocket.ts
│   │
│   └── types/             # TypeScript Definitions
│
├── dist/                  # Production build output
├── package.json
├── vite.config.ts
├── tsconfig.json
└── tailwind.config.js
```

## Setup

1. **Install dependencies**
   ```bash
   npm install
   ```

2. **Configure API URL** (if needed)

   Edit `src/api/client.ts` to set the backend URL.

## Development

```bash
npm run dev
```

Access the app at http://localhost:3000

## Build

```bash
npm run build
```

Production files will be in `dist/`.

## Pages

| Page | Route | Description |
|------|-------|-------------|
| Dashboard | `/` | Overview with stats and activity |
| Profiles | `/profiles` | Manage AdsPower profiles |
| Actions | `/actions` | Execute Twitter actions |
| User Actions | `/actions/users` | User-specific actions |
| Post Actions | `/actions/posts` | Post-specific actions |
| Hashtag Actions | `/actions/hashtags` | Hashtag-based actions |
| Tasks | `/tasks` | View and manage task queue |
| Stats | `/stats` | Detailed statistics |
| Logs | `/logs` | Application logs |
| Settings | `/settings` | Configure API keys and settings |
| Bot | `/bot` | AI chat interface |

## Components

- **Layout** - Main app layout with sidebar
- **ProfileSelector** - Dropdown to select active profile
- **TaskQueue** - Real-time task queue display
- **LogViewer** - Scrollable log output
- **StatsCard** - Statistic display cards
- **FileImport** - Drag-and-drop file upload

## API Integration

The frontend communicates with the backend via:
- REST API calls (`src/api/client.ts`)
- WebSocket for real-time updates (`src/hooks/useWebSocket.ts`)

Backend URL default: `http://localhost:8000`
