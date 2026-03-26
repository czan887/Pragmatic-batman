import { useEffect, useRef, useState, useCallback } from 'react';
import type { LogEntry } from '../types';

interface UseWebSocketOptions {
  channel?: 'logs' | 'tasks' | 'profiles' | 'all';
  maxLogs?: number;
  onMessage?: (data: unknown) => void;
}

interface UseWebSocketReturn {
  logs: LogEntry[];
  connected: boolean;
  clearLogs: () => void;
  reconnect: () => void;
}

export function useWebSocket(options: UseWebSocketOptions = {}): UseWebSocketReturn {
  const { channel = 'logs', maxLogs = 500, onMessage } = options;

  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [connected, setConnected] = useState(false);
  const ws = useRef<WebSocket | null>(null);
  const reconnectTimeout = useRef<ReturnType<typeof setTimeout>>();
  const reconnectAttempts = useRef(0);

  const connect = useCallback(() => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      return;
    }

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/${channel}`;

    try {
      ws.current = new WebSocket(wsUrl);

      ws.current.onopen = () => {
        setConnected(true);
        reconnectAttempts.current = 0;
        console.log(`WebSocket connected to ${channel}`);
      };

      ws.current.onclose = () => {
        setConnected(false);
        console.log(`WebSocket disconnected from ${channel}`);

        // Auto-reconnect with exponential backoff
        const delay = Math.min(1000 * Math.pow(2, reconnectAttempts.current), 30000);
        reconnectAttempts.current++;

        reconnectTimeout.current = setTimeout(() => {
          console.log(`Attempting to reconnect to ${channel}...`);
          connect();
        }, delay);
      };

      ws.current.onerror = (error) => {
        console.error('WebSocket error:', error);
      };

      ws.current.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);

          // Handle log messages
          if (data.type === 'log' || data.level) {
            const logEntry: LogEntry = {
              type: data.type || 'log',
              timestamp: data.timestamp,
              level: data.level,
              message: data.message,
              profile_id: data.profile_id,
            };

            setLogs((prev) => {
              const newLogs = [...prev, logEntry];
              return newLogs.slice(-maxLogs);
            });
          }

          // Call custom message handler
          if (onMessage) {
            onMessage(data);
          }
        } catch (e) {
          console.error('Failed to parse WebSocket message:', e);
        }
      };
    } catch (error) {
      console.error('Failed to create WebSocket:', error);
    }
  }, [channel, maxLogs, onMessage]);

  const disconnect = useCallback(() => {
    if (reconnectTimeout.current) {
      clearTimeout(reconnectTimeout.current);
    }

    if (ws.current) {
      ws.current.close();
      ws.current = null;
    }
  }, []);

  const clearLogs = useCallback(() => {
    setLogs([]);
  }, []);

  const reconnect = useCallback(() => {
    disconnect();
    reconnectAttempts.current = 0;
    connect();
  }, [connect, disconnect]);

  useEffect(() => {
    connect();

    // Send ping every 30 seconds to keep connection alive
    const pingInterval = setInterval(() => {
      if (ws.current?.readyState === WebSocket.OPEN) {
        ws.current.send('ping');
      }
    }, 30000);

    return () => {
      clearInterval(pingInterval);
      disconnect();
    };
  }, [connect, disconnect]);

  return { logs, connected, clearLogs, reconnect };
}

// Hook for task updates
export function useTaskUpdates(onUpdate?: (taskId: number, status: string) => void) {
  const handleMessage = useCallback((data: unknown) => {
    const typedData = data as { type?: string; task_id?: number; status?: string };
    if (typedData.type === 'task_update' && onUpdate && typedData.task_id && typedData.status) {
      onUpdate(typedData.task_id, typedData.status);
    }
  }, [onUpdate]);

  return useWebSocket({ channel: 'tasks', onMessage: handleMessage });
}

// Hook for profile updates
export function useProfileUpdates(onUpdate?: (profileId: string, status: string) => void) {
  const handleMessage = useCallback((data: unknown) => {
    const typedData = data as { type?: string; profile_id?: string; status?: string };
    if (typedData.type === 'profile_update' && onUpdate && typedData.profile_id && typedData.status) {
      onUpdate(typedData.profile_id, typedData.status);
    }
  }, [onUpdate]);

  return useWebSocket({ channel: 'profiles', onMessage: handleMessage });
}
