# Twitter Bot API Endpoints

This document lists all backend API endpoints available in the FastAPI application.

**Base URL:** `http://localhost:8000`

---

## Health Check

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Health check endpoint (returns status and version) |

---

## Profiles (`/api/v1/profiles`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | List all profiles |
| POST | `/sync` | Sync profiles from AdsPower |
| GET | `/{profile_id}` | Get profile details with action summary |
| PATCH | `/{profile_id}` | Update profile information |
| POST | `/{profile_id}/open` | Open browser for profile |
| POST | `/{profile_id}/close` | Close browser for profile |
| GET | `/{profile_id}/status` | Get profile browser status |
| POST | `/{profile_id}/refresh-stats` | Refresh profile statistics |
| DELETE | `/{profile_id}` | Delete a profile |

---

## Tasks (`/api/v1/tasks`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | List all tasks (with optional status filter) |
| GET | `/pending` | List pending tasks |
| GET | `/statistics` | Get task queue statistics |
| GET | `/{task_id}` | Get task details |
| GET | `/{task_id}/position` | Get task position in queue |
| POST | `/` | Create a new task |
| POST | `/{task_id}/cancel` | Cancel a pending task |
| POST | `/batch/{batch_id}/cancel` | Cancel all pending tasks in a batch |
| DELETE | `/{task_id}` | Delete a task |
| POST | `/clear-completed` | Clear old completed tasks |
| POST | `/process-next` | Process the next pending task |
| GET | `/batch/{batch_id}` | Get all tasks in a batch |
| GET | `/batch/{batch_id}/status` | Get batch status summary |

---

## Actions (`/api/v1/actions`)

### Single Actions

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/follow` | Follow a user |
| POST | `/unfollow` | Unfollow a user |
| POST | `/follow-followers` | Queue batch follow of target's followers |
| POST | `/post-tweet` | Post a tweet |
| POST | `/comment` | Comment on a tweet |
| POST | `/like` | Like a tweet |
| POST | `/retweet` | Retweet a tweet |
| POST | `/refactor-post` | Refactor/modify a post |

### Bulk Actions

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/bulk/follow` | Bulk follow multiple users |
| POST | `/bulk/unfollow` | Bulk unfollow multiple users |
| POST | `/bulk/like` | Bulk like tweets |
| POST | `/bulk/retweet` | Bulk retweet tweets |
| POST | `/bulk/comment` | Bulk comment on tweets |
| GET | `/bulk/status/{batch_id}` | Get bulk action batch status |

### Processing Actions

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/process-timeline` | Process a user's timeline (like, retweet, comment) |
| POST | `/process-hashtag` | Process tweets with specific hashtag |
| POST | `/process-post-urls` | Process tweets from specific URLs |
| POST | `/process-users` | Process tweets from specific users |
| POST | `/unfollow-non-followers` | Unfollow users who don't follow back |
| POST | `/multi-profile` | Execute action across multiple profiles |

### History & Statistics

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/history/{profile_id}` | Get action history for a profile |
| GET | `/statistics` | Get action statistics |
| POST | `/stop/{profile_id}` | Stop actions for a profile |

---

## Dashboard (`/api/v1/dashboard`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/stats` | Get dashboard statistics (aggregated overview) |
| GET | `/profiles` | Get all profiles with action summaries |
| GET | `/action-breakdown` | Get action breakdown by type |
| GET | `/task-queue-status` | Get task queue status |
| GET | `/recent-activity` | Get recent task activity |

---

## Settings (`/api/v1/settings`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Get current application settings |
| PATCH | `/` | Update application settings |
| POST | `/test-gemini` | Test Gemini API connection |
| POST | `/test-adspower` | Test AdsPower API connection |

---

## Bot/AI (`/api/v1/bot`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/chat` | Send chat message to AI bot |
| POST | `/execute` | Execute planned actions from AI bot |
| GET | `/status` | Get bot status |

---

## Logs (`/api/v1/logs`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Get logs with optional filtering |
| GET | `/stats` | Get log statistics |
| GET | `/errors` | Get error logs |
| GET | `/profile/{profile_id}` | Get logs for a specific profile |
| GET | `/search` | Search logs |
| POST | `/cleanup` | Clean up old logs |

---

## File Import (`/api/v1/import`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/` | Import data from file (TXT, CSV, XLSX) |
| POST | `/validate` | Validate file format before import |

---

## Statistics (`/api/v1/stats`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/daily` | Get daily statistics |
| GET | `/range` | Get statistics for a date range |
| GET | `/trends` | Get trend comparisons |
| GET | `/summary` | Get summary statistics (today, week, month, year, all-time) |
| GET | `/weekly` | Get weekly aggregated statistics |
| GET | `/monthly` | Get monthly aggregated statistics |
| GET | `/yearly` | Get yearly aggregated statistics |

---

## Sessions (`/api/v1/sessions`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/start` | Start a new session |
| POST | `/{session_id}/end` | End a session |
| GET | `/active` | Get active sessions |
| GET | `/history` | Get session history |
| GET | `/{session_id}` | Get session details |
| POST | `/cleanup` | Cleanup stale sessions |

---

## WebSocket (`/ws`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/status` | Get WebSocket connection status |
| POST | `/test-log` | Test WebSocket log broadcasting |

---

## Summary

- **Total Endpoints:** 87
- **GET Requests:** ~50
- **POST Requests:** ~30
- **PATCH Requests:** 2
- **DELETE Requests:** 2

---

## Interactive API Documentation

FastAPI provides interactive API documentation at:
- **Swagger UI:** `http://localhost:8000/docs`
- **ReDoc:** `http://localhost:8000/redoc`
