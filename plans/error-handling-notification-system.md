# Plan: Comprehensive Error Handling & Notification System

## Overview

Implement a transparent error handling and notification system that distinguishes between:
1. **System-level errors** → Toast notifications (API failures, connection issues, exceptions)
2. **Bot activity logs** → Log tab only (follows, likes, retweets, etc.) - **Already persisted in database**

---

## Backend Changes

### 1. Create Custom Exception Hierarchy
**File:** `backend/core/exceptions.py` (NEW)

```python
class TwitterBotError(Exception):
    error_code: str = "INTERNAL_ERROR"
    status_code: int = 500

class ExternalServiceError(TwitterBotError): ...  # AdsPower, AI, Playwright
class ProfileNotFoundError(TwitterBotError): ...  # 404 errors
class ValidationError(TwitterBotError): ...       # 400 errors
class RateLimitError(TwitterBotError): ...        # 429 errors
class BrowserNotConnectedError(TwitterBotError): ...
```

### 2. Create Global Exception Handler Middleware
**File:** `backend/api/middleware/error_handler.py` (NEW)

- Catches all TwitterBotError exceptions
- Returns standardized JSON response: `{ success: false, error: { code, message, title, suggestion } }`
- Broadcasts system errors via WebSocket with `type: "notification"`

### 3. Update main.py
**File:** `backend/main.py`

- Register error handler middleware

### 4. Add Notification Broadcast Method
**File:** `backend/api/routes/websocket.py`

Add `broadcast_notification()` method for system-level alerts (separate from `broadcast_log()`):
```python
async def broadcast_notification(type: str, title: str, message: str, error_code: str = None):
    # type: "error" | "success" | "warning" | "info"
    # This triggers toast on frontend
```

### 5. Update Services to Use New Exceptions
**Files:** `backend/services/*.py`

Replace generic `Exception` with specific exceptions:
- `AdsPowerError` for AdsPower failures
- `PlaywrightError` for browser automation failures
- `AIServiceError` for Gemini/Anthropic failures

---

## Frontend Changes

### 1. Install Toast Library
```bash
cd frontend && npm install sonner
```

### 2. Create Notification Context
**File:** `frontend/src/contexts/NotificationContext.tsx` (NEW)

- Provides `showSuccess`, `showError`, `showWarning`, `showInfo` functions
- Wraps Sonner's `<Toaster>` component with dark theme styling
- Positioned bottom-right

### 3. Create Notification Service Bridge
**File:** `frontend/src/services/notificationService.ts` (NEW)

- Allows axios interceptor to access notification context

### 4. Add Axios Error Interceptor
**File:** `frontend/src/api/client.ts`

- Intercept API errors globally
- Parse standardized error response
- Show toast for system errors automatically

### 5. Create WebSocket Notification Hook
**File:** `frontend/src/hooks/useWebSocketNotifications.ts` (NEW)

Smart filtering logic:
```typescript
// SHOW as toast (system-level):
- type === "notification"
- level === "ERROR" && isSystemError(message)

// System error patterns:
- "connection failed", "error connecting"
- "API error", "service unavailable"
- "rate limit", "authentication"
- "browser", "playwright", "adspower"

// DO NOT show as toast (bot activity):
- "Following @", "Followed @"
- "Liked", "Retweeted", "Commented"
- "Posted tweet", "Processing user"
```

### 6. Update main.tsx
**File:** `frontend/src/main.tsx`

- Wrap app with `<NotificationProvider>`

### 7. Update App.tsx
**File:** `frontend/src/App.tsx`

- Initialize notification service
- Add `useWebSocketNotifications()` hook

### 8. Add Error Types
**File:** `frontend/src/types/index.ts`

```typescript
interface ApiErrorResponse {
  success: false;
  error: { code: string; message: string; title?: string; suggestion?: string; }
}
```

### 9. Add Period Selector to LogViewer
**File:** `frontend/src/components/LogViewer.tsx`

Add time period selector for bot activity logs:
```typescript
type LogPeriod = 'today' | 'week' | 'month' | 'all';

const periodHours: Record<LogPeriod, number | undefined> = {
  today: 24,
  week: 168,    // 7 days
  month: 720,   // 30 days
  all: undefined
};

// Add period selector dropdown next to level filter
<select value={period} onChange={(e) => setPeriod(e.target.value)}>
  <option value="today">Today</option>
  <option value="week">This Week</option>
  <option value="month">This Month</option>
  <option value="all">All Time</option>
</select>
```

**Note:** Bot activity logs are already persisted in the database (`session_logs` table) via `LogRepository.save_log()`. The API already supports `hours` parameter for filtering.

---

## What Shows Where

| Event Type | Toast | Log Tab |
|------------|-------|---------|
| API connection error | Yes | Yes |
| AdsPower failure | Yes | Yes |
| Browser open/close error | Yes | Yes |
| Rate limit warning | Yes | Yes |
| Profile sync complete | Yes | No |
| Following @user | No | Yes |
| Liked tweet | No | Yes |
| Retweeted post | No | Yes |
| Posted comment | No | Yes |
| Task started/completed | No | Yes |

---

## Files to Create/Modify

### New Files:
1. `backend/core/exceptions.py`
2. `backend/api/middleware/error_handler.py`
3. `frontend/src/contexts/NotificationContext.tsx`
4. `frontend/src/services/notificationService.ts`
5. `frontend/src/hooks/useWebSocketNotifications.ts`

### Modified Files:
1. `backend/main.py` - Register middleware
2. `backend/api/routes/websocket.py` - Add broadcast_notification
3. `frontend/src/main.tsx` - Add NotificationProvider
4. `frontend/src/App.tsx` - Initialize services, add hook
5. `frontend/src/api/client.ts` - Add axios interceptor
6. `frontend/src/types/index.ts` - Add error types
7. `frontend/src/components/LogViewer.tsx` - Add period selector (Today/Week/Month/All)

---

## Verification

1. **Test API errors**: Stop backend, try an action → should see toast
2. **Test WebSocket errors**: Simulate AdsPower failure → should see toast
3. **Test bot activity**: Run follow action → should appear in Log tab only, no toast
4. **Test success notifications**: Sync profiles → should see success toast
5. **Test period selector**: Switch between Today/Week/Month/All in Log tab → logs should filter correctly
6. **Build frontend**: `npm run build` should pass
