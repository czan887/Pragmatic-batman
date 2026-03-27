import { useEffect, useRef } from 'react';
import { useNotifications } from '../contexts/NotificationContext';

interface WebSocketMessage {
  type: string;
  timestamp: string;
  level?: string;
  message?: string;
  notification_type?: 'error' | 'success' | 'warning' | 'info';
  title?: string;
  error_code?: string;
}

/**
 * System error patterns that should trigger toast notifications
 */
const SYSTEM_ERROR_PATTERNS = [
  /connection failed/i,
  /error connecting/i,
  /api error/i,
  /service unavailable/i,
  /rate limit/i,
  /authentication/i,
  /browser.*error/i,
  /playwright/i,
  /adspower/i,
  /failed to open/i,
  /failed to close/i,
  /failed to connect/i,
  /timeout/i,
  /network error/i,
];

/**
 * Bot activity patterns that should NOT trigger toast notifications
 * These are informational logs that only appear in the Log tab
 */
const BOT_ACTIVITY_PATTERNS = [
  /following @/i,
  /followed @/i,
  /unfollowed @/i,
  /liked/i,
  /retweeted/i,
  /commented/i,
  /posted tweet/i,
  /processing user/i,
  /processing timeline/i,
  /processing hashtag/i,
  /task.*started/i,
  /task.*completed/i,
  /task.*queued/i,
  /navigating to/i,
  /scrolling/i,
  /waiting/i,
  /analyzing/i,
];

/**
 * Check if a message is a system error that should show as toast
 */
function isSystemError(message: string): boolean {
  // Check if it matches any system error pattern
  const matchesSystemError = SYSTEM_ERROR_PATTERNS.some((pattern) => pattern.test(message));
  if (matchesSystemError) return true;

  // Check if it matches bot activity (should NOT show as toast)
  const matchesBotActivity = BOT_ACTIVITY_PATTERNS.some((pattern) => pattern.test(message));
  if (matchesBotActivity) return false;

  // Default: don't show as toast for ambiguous messages
  return false;
}

/**
 * Hook that listens for WebSocket notifications and shows toasts
 * for system-level errors and notifications
 */
export function useWebSocketNotifications() {
  const { showSuccess, showError, showWarning, showInfo } = useNotifications();
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<number | null>(null);

  useEffect(() => {
    const connect = () => {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const wsUrl = `${protocol}//${window.location.host}/ws/logs`;

      try {
        wsRef.current = new WebSocket(wsUrl);

        wsRef.current.onmessage = (event) => {
          try {
            const data: WebSocketMessage = JSON.parse(event.data);

            // Handle explicit notification type messages
            if (data.type === 'notification') {
              const title = data.title || '';
              const message = data.message || '';

              switch (data.notification_type) {
                case 'error':
                  showError(message, title);
                  break;
                case 'success':
                  showSuccess(message, title);
                  break;
                case 'warning':
                  showWarning(message, title);
                  break;
                case 'info':
                  showInfo(message, title);
                  break;
              }
              return;
            }

            // Handle log messages - only show toast for system errors
            if (data.type === 'log' && data.level === 'ERROR' && data.message) {
              if (isSystemError(data.message)) {
                showError(data.message, 'System Error');
              }
              // Bot activity errors only go to log tab, no toast
            }
          } catch (e) {
            // Ignore parse errors for non-JSON messages (like pong)
          }
        };

        wsRef.current.onclose = () => {
          // Attempt to reconnect after 5 seconds
          reconnectTimeoutRef.current = window.setTimeout(connect, 5000);
        };

        wsRef.current.onerror = () => {
          wsRef.current?.close();
        };
      } catch (e) {
        // WebSocket connection failed, will retry
        reconnectTimeoutRef.current = window.setTimeout(connect, 5000);
      }
    };

    connect();

    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [showSuccess, showError, showWarning, showInfo]);
}
