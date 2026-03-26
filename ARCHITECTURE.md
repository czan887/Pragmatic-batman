# Twitter Bot Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              TWITTER BOT SYSTEM                                  │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│       ┌──────────────────┐          ┌──────────────────┐                        │
│       │     Frontend     │          │     Backend      │                        │
│       │  (React + TS)    │          │    (FastAPI)     │                        │
│       │   Port: 3000     │          │    Port: 8000    │                        │
│       └────────┬─────────┘          └────────┬─────────┘                        │
│                │                             │                                   │
│                │      HTTP/REST              │                                   │
│                │      WebSocket              │                                   │
│                └─────────────────────────────┘                                   │
│                                      │                                           │
│                                      ▼                                           │
│                    ┌─────────────────────────────┐                              │
│                    │       Services Layer        │                              │
│                    │  ProfileService             │                              │
│                    │  ActionService              │                              │
│                    │  TaskService                │                              │
│                    └─────────────┬───────────────┘                              │
│                                  │                                               │
│              ┌───────────────────┼───────────────────┐                          │
│              ▼                   ▼                   ▼                          │
│      ┌──────────────┐    ┌──────────────┐    ┌──────────────┐                  │
│      │  Playwright  │    │    SQLite    │    │  Gemini AI   │                  │
│      │   Manager    │    │   Database   │    │     API      │                  │
│      └──────┬───────┘    └──────────────┘    └──────────────┘                  │
│             │                                                                    │
│             ▼                                                                    │
│      ┌──────────────┐                                                           │
│      │   AdsPower   │                                                           │
│      │  Local API   │                                                           │
│      │  Port: 50325 │                                                           │
│      └──────┬───────┘                                                           │
│             │ CDP (Chrome DevTools Protocol)                                     │
│             ▼                                                                    │
│      ┌──────────────┐                                                           │
│      │   Browser    │                                                           │
│      │  Instances   │                                                           │
│      └──────┬───────┘                                                           │
│             │                                                                    │
│             ▼                                                                    │
│      ┌──────────────┐                                                           │
│      │  Twitter/X   │                                                           │
│      └──────────────┘                                                           │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Backend Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                FASTAPI BACKEND                                   │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │                            API LAYER (Routes)                            │    │
│  ├─────────┬─────────┬─────────┬─────────┬─────────┬─────────┬────────────┤    │
│  │profiles │  tasks  │ actions │dashboard│settings │  logs   │  sessions  │    │
│  │   .py   │   .py   │   .py   │   .py   │   .py   │   .py   │    .py     │    │
│  ├─────────┴─────────┴─────────┴─────────┴─────────┴─────────┴────────────┤    │
│  │  bot.py  │  stats.py  │  file_import.py  │  websocket.py               │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
│                                      │                                           │
│                                      ▼                                           │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │                          SERVICES LAYER                                  │    │
│  ├───────────────────┬───────────────────┬─────────────────────────────────┤    │
│  │  profile_service  │  action_service   │       task_service              │    │
│  │       .py         │       .py         │           .py                   │    │
│  └───────────────────┴───────────────────┴─────────────────────────────────┘    │
│                                      │                                           │
│                 ┌────────────────────┼────────────────────┐                     │
│                 ▼                    ▼                    ▼                     │
│  ┌─────────────────────┐  ┌─────────────────┐  ┌─────────────────────┐         │
│  │     CORE LAYER      │  │   DATABASE      │  │     AI LAYER        │         │
│  ├─────────────────────┤  │     LAYER       │  ├─────────────────────┤         │
│  │ playwright_manager  │  ├─────────────────┤  │ content_generator   │         │
│  │ twitter_actions     │  │   database.py   │  │ profile_analyzer    │         │
│  │ selectors           │  │   models.py     │  │ behavior_planner    │         │
│  └─────────────────────┘  │                 │  │ selector_finder     │         │
│           │               │  Repositories:  │  └─────────────────────┘         │
│           │               │  ├─action_repo  │            │                     │
│           │               │  ├─log_repo     │            │                     │
│           │               │  ├─profile_repo │            │                     │
│           │               │  ├─session_repo │            │                     │
│           │               │  ├─stats_repo   │            │                     │
│           │               │  └─task_repo    │            │                     │
│           │               └─────────────────┘            │                     │
│           ▼                        │                     ▼                     │
│  ┌─────────────────┐      ┌──────────────┐      ┌──────────────┐              │
│  │    AdsPower     │      │    SQLite    │      │   Google     │              │
│  │      API        │      │   Database   │      │   Gemini     │              │
│  └─────────────────┘      └──────────────┘      └──────────────┘              │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Frontend Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              REACT FRONTEND                                      │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │                              App.tsx                                     │    │
│  │                         (React Router)                                   │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
│                                      │                                           │
│                                      ▼                                           │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │                           Layout Component                               │    │
│  │  ┌──────────────┐    ┌──────────────────────────────────────────────┐   │    │
│  │  │              │    │                                              │   │    │
│  │  │   Sidebar    │    │              Page Content                    │   │    │
│  │  │              │    │                                              │   │    │
│  │  │  - Dashboard │    │  ┌────────────────────────────────────────┐  │   │    │
│  │  │  - Profiles  │    │  │              PAGES                     │  │   │    │
│  │  │  - Actions   │    │  ├────────────────────────────────────────┤  │   │    │
│  │  │  - Tasks     │    │  │  Dashboard.tsx    │  Profiles.tsx      │  │   │    │
│  │  │  - Stats     │    │  │  UserActions.tsx  │  PostActions.tsx   │  │   │    │
│  │  │  - Logs      │    │  │  HashtagActions   │  AccountActions    │  │   │    │
│  │  │  - Settings  │    │  │  Tasks.tsx        │  Stats.tsx         │  │   │    │
│  │  │  - Bot       │    │  │  Logs.tsx         │  Settings.tsx      │  │   │    │
│  │  │              │    │  │  Bot.tsx          │                    │  │   │    │
│  │  └──────────────┘    │  └────────────────────────────────────────┘  │   │    │
│  │                      └──────────────────────────────────────────────┘   │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
│                                      │                                           │
│                                      ▼                                           │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │                         SHARED COMPONENTS                                │    │
│  ├─────────────┬─────────────┬─────────────┬─────────────┬─────────────────┤    │
│  │ ProfileCard │ProfileSelect│  StatsCard  │ TaskQueue   │   LogViewer     │    │
│  │ FileImport  │StatsTrend   │SessionCard  │ Layout      │   Sidebar       │    │
│  └─────────────┴─────────────┴─────────────┴─────────────┴─────────────────┘    │
│                                      │                                           │
│                 ┌────────────────────┴────────────────────┐                     │
│                 ▼                                         ▼                     │
│  ┌─────────────────────────────┐          ┌─────────────────────────────┐       │
│  │        API Client           │          │         Hooks               │       │
│  │      (api/client.ts)        │          │   (hooks/useWebSocket.ts)   │       │
│  │                             │          │                             │       │
│  │  - 70+ typed endpoints      │          │  - Real-time updates        │       │
│  │  - React Query integration  │          │  - Auto-reconnect           │       │
│  │  - Axios instance           │          │  - Live log streaming       │       │
│  └─────────────────────────────┘          └─────────────────────────────┘       │
│                 │                                         │                     │
│                 └────────────────────┬────────────────────┘                     │
│                                      ▼                                           │
│                          ┌─────────────────────┐                                │
│                          │   Backend API       │                                │
│                          │   localhost:8000    │                                │
│                          └─────────────────────┘                                │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## AdsPower Connection Flow

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         ADSPOWER CONNECTION FLOW                                 │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  FRONTEND                                                                        │
│  ┌────────────────────────────────────────┐                                     │
│  │ 1. User clicks "Open Browser" button   │                                     │
│  │    Profiles.tsx → profilesApi.open()   │                                     │
│  └──────────────────┬─────────────────────┘                                     │
│                     │ POST /api/v1/profiles/{id}/open                           │
│                     ▼                                                            │
│  BACKEND API                                                                     │
│  ┌────────────────────────────────────────┐                                     │
│  │ 2. Route handler receives request      │                                     │
│  │    profiles.py → service.open_browser()│                                     │
│  └──────────────────┬─────────────────────┘                                     │
│                     ▼                                                            │
│  SERVICE LAYER                                                                   │
│  ┌────────────────────────────────────────┐                                     │
│  │ 3. ProfileService.open_browser()       │                                     │
│  │    → playwright.connect_to_adspower()  │                                     │
│  └──────────────────┬─────────────────────┘                                     │
│                     ▼                                                            │
│  PLAYWRIGHT MANAGER                                                              │
│  ┌────────────────────────────────────────┐                                     │
│  │ 4. Check if already connected          │                                     │
│  │    if yes → return existing page       │                                     │
│  │    if no  → continue to step 5         │                                     │
│  └──────────────────┬─────────────────────┘                                     │
│                     ▼                                                            │
│  ┌────────────────────────────────────────┐                                     │
│  │ 5. Call AdsPower API                   │                                     │
│  │    GET /api/v1/browser/start           │                                     │
│  │    params: {user_id: profile_id}       │                                     │
│  └──────────────────┬─────────────────────┘                                     │
│                     ▼                                                            │
│  ADSPOWER LOCAL API (Port 50325)                                                │
│  ┌────────────────────────────────────────┐                                     │
│  │ 6. AdsPower launches browser profile   │                                     │
│  │    Returns: WebSocket endpoint (CDP)   │                                     │
│  │    {"data":{"ws":{"puppeteer":"ws://"}}}│                                    │
│  └──────────────────┬─────────────────────┘                                     │
│                     ▼                                                            │
│  PLAYWRIGHT MANAGER (continued)                                                  │
│  ┌────────────────────────────────────────┐                                     │
│  │ 7. Connect via Chrome DevTools Protocol│                                     │
│  │    playwright.chromium.connect_over_cdp│                                     │
│  │    (ws_endpoint)                       │                                     │
│  └──────────────────┬─────────────────────┘                                     │
│                     ▼                                                            │
│  ┌────────────────────────────────────────┐                                     │
│  │ 8. Store references & navigate         │                                     │
│  │    self.browsers[profile_id] = browser │                                     │
│  │    self.pages[profile_id] = page       │                                     │
│  │    page.goto("https://x.com/home")     │                                     │
│  └──────────────────┬─────────────────────┘                                     │
│                     ▼                                                            │
│  ┌────────────────────────────────────────┐                                     │
│  │ 9. Broadcast status via WebSocket      │                                     │
│  │    "Browser opened for profile X"      │                                     │
│  └──────────────────┬─────────────────────┘                                     │
│                     ▼                                                            │
│  FRONTEND (WebSocket)                                                            │
│  ┌────────────────────────────────────────┐                                     │
│  │ 10. UI updates in real-time            │                                     │
│  │     useWebSocket() receives update     │                                     │
│  │     Profile card shows "Connected"     │                                     │
│  └────────────────────────────────────────┘                                     │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Database Schema

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              SQLite DATABASE                                     │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  ┌─────────────────────┐          ┌─────────────────────┐                       │
│  │      profiles       │          │       actions       │                       │
│  ├─────────────────────┤          ├─────────────────────┤                       │
│  │ id (PK)             │──────────│ id (PK)             │                       │
│  │ user_id (AdsPower)  │     ┌───▶│ profile_id (FK)     │                       │
│  │ serial_number       │     │    │ action_type         │                       │
│  │ name                │     │    │ target              │                       │
│  │ group_name          │     │    │ status              │                       │
│  │ domain_name         │     │    │ created_at          │                       │
│  │ followers_count     │     │    │ completed_at        │                       │
│  │ following_count     │     │    │ error_message       │                       │
│  │ created_at          │     │    └─────────────────────┘                       │
│  │ updated_at          │     │                                                  │
│  └─────────────────────┘     │    ┌─────────────────────┐                       │
│            │                 │    │        tasks        │                       │
│            │                 │    ├─────────────────────┤                       │
│            │                 │    │ id (PK)             │                       │
│            └─────────────────┼───▶│ profile_id (FK)     │                       │
│                              │    │ batch_id            │                       │
│                              │    │ action_type         │                       │
│                              │    │ task_data (JSON)    │                       │
│                              │    │ status              │                       │
│                              │    │ priority            │                       │
│                              │    │ created_at          │                       │
│                              │    │ started_at          │                       │
│                              │    │ completed_at        │                       │
│                              │    │ error_message       │                       │
│                              │    └─────────────────────┘                       │
│                              │                                                  │
│                              │    ┌─────────────────────┐                       │
│                              │    │      sessions       │                       │
│                              │    ├─────────────────────┤                       │
│                              │    │ id (PK)             │                       │
│                              └───▶│ profile_id (FK)     │                       │
│                                   │ started_at          │                       │
│                                   │ ended_at            │                       │
│                                   │ actions_count       │                       │
│                                   │ status              │                       │
│                                   └─────────────────────┘                       │
│                                                                                  │
│  ┌─────────────────────┐          ┌─────────────────────┐                       │
│  │        logs         │          │    daily_stats      │                       │
│  ├─────────────────────┤          ├─────────────────────┤                       │
│  │ id (PK)             │          │ id (PK)             │                       │
│  │ profile_id (FK)     │          │ profile_id (FK)     │                       │
│  │ level               │          │ date                │                       │
│  │ message             │          │ follows             │                       │
│  │ timestamp           │          │ unfollows           │                       │
│  │ module              │          │ likes               │                       │
│  └─────────────────────┘          │ retweets            │                       │
│                                   │ comments            │                       │
│                                   │ tweets              │                       │
│                                   └─────────────────────┘                       │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Task Queue Flow

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                           TASK QUEUE SYSTEM                                   │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│   ┌─────────┐                                                                 │
│   │  User   │                                                                 │
│   │ Request │                                                                 │
│   └────┬────┘                                                                 │
│        │                                                                      │
│        ▼                                                                      │
│   ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐        │
│   │  Bulk Follow    │     │  Process        │     │  Follow         │        │
│   │  (100 users)    │────▶│  Hashtag        │────▶│  Followers      │        │
│   └─────────────────┘     └─────────────────┘     └─────────────────┘        │
│        │                         │                       │                    │
│        └─────────────────────────┼───────────────────────┘                    │
│                                  ▼                                            │
│                    ┌───────────────────────────┐                              │
│                    │      TASK QUEUE           │                              │
│                    │  ┌───┬───┬───┬───┬───┐   │                              │
│                    │  │ T │ T │ T │ T │...│   │                              │
│                    │  │ 1 │ 2 │ 3 │ 4 │   │   │                              │
│                    │  └───┴───┴───┴───┴───┘   │                              │
│                    │    status: pending        │                              │
│                    └─────────────┬─────────────┘                              │
│                                  │                                            │
│                                  ▼                                            │
│                    ┌───────────────────────────┐                              │
│                    │    ROUND-ROBIN            │                              │
│                    │    SCHEDULER              │                              │
│                    │                           │                              │
│                    │  Profile 1 ──▶ Task 1     │                              │
│                    │  Profile 2 ──▶ Task 2     │                              │
│                    │  Profile 3 ──▶ Task 3     │                              │
│                    │  Profile 1 ──▶ Task 4     │                              │
│                    │      ...                  │                              │
│                    └─────────────┬─────────────┘                              │
│                                  │                                            │
│         ┌────────────────────────┼────────────────────────┐                   │
│         ▼                        ▼                        ▼                   │
│   ┌──────────┐            ┌──────────┐            ┌──────────┐               │
│   │ Profile  │            │ Profile  │            │ Profile  │               │
│   │    1     │            │    2     │            │    3     │               │
│   │ Browser  │            │ Browser  │            │ Browser  │               │
│   └────┬─────┘            └────┬─────┘            └────┬─────┘               │
│        │                       │                       │                      │
│        ▼                       ▼                       ▼                      │
│   ┌──────────┐            ┌──────────┐            ┌──────────┐               │
│   │ Execute  │            │ Execute  │            │ Execute  │               │
│   │  Action  │            │  Action  │            │  Action  │               │
│   └────┬─────┘            └────┬─────┘            └────┬─────┘               │
│        │                       │                       │                      │
│        └───────────────────────┼───────────────────────┘                      │
│                                ▼                                              │
│                    ┌───────────────────────────┐                              │
│                    │   UPDATE STATUS           │                              │
│                    │   - completed / failed    │                              │
│                    │   - Broadcast via WS      │                              │
│                    │   - Save to Database      │                              │
│                    └───────────────────────────┘                              │
│                                                                               │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## External Integrations

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                          EXTERNAL INTEGRATIONS                                   │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │                           AdsPower Integration                           │    │
│  │                                                                          │    │
│  │   Backend                    AdsPower Local API (Port 50325)             │    │
│  │  ┌────────────┐             ┌────────────────────────────────┐          │    │
│  │  │            │  GET /start │                                │          │    │
│  │  │ Playwright │────────────▶│  Start Browser Profile         │          │    │
│  │  │  Manager   │             │  Returns: WebSocket endpoint   │          │    │
│  │  │            │◀────────────│  {"ws":{"puppeteer":"ws://..."}}│          │    │
│  │  │            │             │                                │          │    │
│  │  │            │  GET /stop  │                                │          │    │
│  │  │            │────────────▶│  Close Browser Profile         │          │    │
│  │  │            │             │                                │          │    │
│  │  │            │  GET /list  │                                │          │    │
│  │  │            │────────────▶│  List All Profiles             │          │    │
│  │  └────────────┘             └────────────────────────────────┘          │    │
│  │        │                                                                 │    │
│  │        │ CDP (Chrome DevTools Protocol)                                  │    │
│  │        ▼                                                                 │    │
│  │  ┌────────────┐                                                         │    │
│  │  │  Browser   │  Isolated browser with unique fingerprint                │    │
│  │  │  Instance  │  Controlled via Playwright                              │    │
│  │  └────────────┘                                                         │    │
│  │                                                                          │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │                        Google Gemini Integration                         │    │
│  │                                                                          │    │
│  │   Backend                    Gemini API                                  │    │
│  │  ┌────────────┐             ┌────────────────┐                          │    │
│  │  │ Content    │  Generate   │                │                          │    │
│  │  │ Generator  │────────────▶│  gemini-flash  │                          │    │
│  │  │            │◀────────────│                │                          │    │
│  │  │ Profile    │  Analyze    │  Response      │                          │    │
│  │  │ Analyzer   │────────────▶│                │                          │    │
│  │  │            │◀────────────│  Analysis      │                          │    │
│  │  └────────────┘             └────────────────┘                          │    │
│  │                                                                          │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │                         Twitter/X Interaction                            │    │
│  │                                                                          │    │
│  │   Playwright Page           Twitter/X Website                            │    │
│  │  ┌────────────┐             ┌────────────────┐                          │    │
│  │  │            │  Navigate   │                │                          │    │
│  │  │ Twitter    │────────────▶│  User Profile  │                          │    │
│  │  │ Actions    │             │  Tweet Page    │                          │    │
│  │  │            │  Click/Type │  Timeline      │                          │    │
│  │  │            │────────────▶│  Search        │                          │    │
│  │  │            │             │                │                          │    │
│  │  │            │  Extract    │                │                          │    │
│  │  │            │◀────────────│  DOM Elements  │                          │    │
│  │  └────────────┘             └────────────────┘                          │    │
│  │                                                                          │    │
│  │  Actions: Follow, Unfollow, Like, Retweet, Comment, Post Tweet          │    │
│  │                                                                          │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Directory Structure

```
twitterbot/
│
├── backend/                          # FastAPI Backend Server
│   ├── main.py                       # Application entry point
│   ├── config.py                     # Configuration management
│   ├── requirements.txt              # Python dependencies
│   │
│   ├── api/                          # API Layer
│   │   ├── dependencies.py           # Dependency injection
│   │   └── routes/                   # Endpoint handlers
│   │       ├── actions.py            # Twitter action endpoints
│   │       ├── bot.py                # AI chat endpoints
│   │       ├── dashboard.py          # Dashboard data endpoints
│   │       ├── file_import.py        # File upload endpoints
│   │       ├── logs.py               # Log retrieval endpoints
│   │       ├── profiles.py           # Profile management endpoints
│   │       ├── sessions.py           # Session management endpoints
│   │       ├── settings.py           # Settings endpoints
│   │       ├── stats.py              # Statistics endpoints
│   │       ├── tasks.py              # Task queue endpoints
│   │       └── websocket.py          # WebSocket endpoints
│   │
│   ├── ai/                           # AI/ML Layer
│   │   ├── behavior_planner.py       # Action planning
│   │   ├── content_generator.py      # Gemini content generation
│   │   ├── profile_analyzer.py       # Profile analysis
│   │   └── selector_finder.py        # Dynamic selector finding
│   │
│   ├── core/                         # Core Business Logic
│   │   ├── playwright_manager.py     # Browser management (AdsPower)
│   │   ├── selectors.py              # CSS/XPath selectors
│   │   └── twitter_actions.py        # Twitter automation logic
│   │
│   ├── db/                           # Database Layer
│   │   ├── database.py               # Database connection
│   │   ├── models.py                 # Pydantic models (50+)
│   │   └── repositories/             # Data access layer
│   │       ├── action_repo.py
│   │       ├── log_repo.py
│   │       ├── profile_repo.py
│   │       ├── session_repo.py
│   │       ├── stats_repo.py
│   │       └── task_repo.py
│   │
│   ├── services/                     # Service Layer
│   │   ├── action_service.py         # Action orchestration
│   │   ├── profile_service.py        # Profile operations
│   │   └── task_service.py           # Task management
│   │
│   ├── utils/                        # Utilities
│   │   └── logger.py                 # Logging (loguru + DB)
│   │
│   └── tests/                        # Unit tests
│
├── frontend/                         # React Frontend
│   ├── src/
│   │   ├── main.tsx                  # Entry point
│   │   ├── App.tsx                   # Root component + routing
│   │   ├── index.css                 # Global styles
│   │   │
│   │   ├── api/                      # API Client
│   │   │   └── client.ts             # Axios + 70+ endpoints
│   │   │
│   │   ├── components/               # Reusable Components
│   │   │   ├── FileImport.tsx
│   │   │   ├── Layout.tsx
│   │   │   ├── LogViewer.tsx
│   │   │   ├── ProfileCard.tsx
│   │   │   ├── ProfileSelector.tsx
│   │   │   ├── SessionSummaryCard.tsx
│   │   │   ├── Sidebar.tsx
│   │   │   ├── StatsCard.tsx
│   │   │   ├── StatsTrendCard.tsx
│   │   │   └── TaskQueue.tsx
│   │   │
│   │   ├── pages/                    # Page Components
│   │   │   ├── AccountActions.tsx
│   │   │   ├── Bot.tsx
│   │   │   ├── Dashboard.tsx
│   │   │   ├── HashtagActions.tsx
│   │   │   ├── Logs.tsx
│   │   │   ├── PostActions.tsx
│   │   │   ├── Profiles.tsx
│   │   │   ├── Settings.tsx
│   │   │   ├── Stats.tsx
│   │   │   ├── Tasks.tsx
│   │   │   └── UserActions.tsx
│   │   │
│   │   ├── hooks/                    # Custom Hooks
│   │   │   └── useWebSocket.ts       # Real-time updates
│   │   │
│   │   └── types/                    # TypeScript Types
│   │       └── index.ts              # 381 lines of types
│   │
│   ├── package.json
│   ├── vite.config.ts
│   ├── tsconfig.json
│   └── tailwind.config.js
│
├── scripts/                          # Helper scripts
│
├── .env                              # Environment variables
├── .gitignore                        # Git ignore rules
├── README.md                         # Project documentation
├── API_ENDPOINTS.md                  # API documentation
├── ARCHITECTURE.md                   # This file
└── CLAUDE.md                         # Claude AI instructions
```

---

## Technology Stack Summary

| Layer | Technology | Purpose |
|-------|------------|---------|
| **Frontend** | React 18 | UI Framework |
| | TypeScript 5.3 | Type Safety |
| | Vite 5.0 | Build Tool |
| | Tailwind CSS 3.4 | Styling |
| | React Router 6.21 | Navigation |
| | React Query 5.17 | Server State |
| | Axios 1.6 | HTTP Client |
| **Backend** | FastAPI | REST API |
| | Uvicorn | ASGI Server |
| | Playwright | Browser Automation |
| | SQLite + aiosqlite | Database |
| | Pydantic 2.x | Data Validation |
| | httpx | Async HTTP Client |
| | loguru | Logging |
| **AI** | Google Gemini | Content Generation |
| **External** | AdsPower | Browser Profiles |
| | Twitter/X | Target Platform |

---

## Communication Protocols

| Protocol | Use Case | Endpoint |
|----------|----------|----------|
| HTTP REST | CRUD operations | `/api/v1/*` |
| WebSocket | Real-time logs, status | `/ws/*` |
| CDP | Browser control | AdsPower → Playwright |

---

## Code Quality Assessment

### Backend (8.1/10)
- ✅ Excellent project structure
- ✅ Clean code separation (routes/services/repos)
- ✅ Comprehensive type hints
- ✅ Centralized configuration
- ✅ Good logging with loguru
- ⚠️ Some silent exception handlers
- ⚠️ No authentication layer

### Frontend (8.8/10)
- ✅ Clean component architecture
- ✅ Strong TypeScript usage
- ✅ React Query for server state
- ✅ WebSocket for real-time updates
- ✅ Consistent Tailwind styling
- ⚠️ Some formatter duplication
- ⚠️ No global error boundary

### Isolation (10/10)
- ✅ Complete FE/BE separation
- ✅ All AdsPower calls through backend
- ✅ No direct external API calls from frontend
- ✅ Proper dependency injection

---

*Document updated: March 2026*
