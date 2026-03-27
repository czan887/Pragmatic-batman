import { useRef, useEffect, useState, useCallback } from 'react';
import { Trash2, Wifi, WifiOff, Copy, Download, Check, Search, X, RefreshCw } from 'lucide-react';
import { useWebSocket } from '../hooks/useWebSocket';
import { logsApi } from '../api/client';
import { formatTime, formatDateTime, getLevelColor } from '../utils/formatters';
import type { LogEntry } from '../types';

interface LogViewerProps {
  maxHeight?: string;
  showControls?: boolean;
}

type LogPeriod = 'today' | 'week' | 'month' | 'all';

const periodHours: Record<LogPeriod, number | undefined> = {
  today: 24,
  week: 168,    // 7 days
  month: 720,   // 30 days
  all: undefined
};

export default function LogViewer({ maxHeight = '400px', showControls = true }: LogViewerProps) {
  const { logs: wsLogs, connected, clearLogs: clearWsLogs } = useWebSocket({ channel: 'logs' });
  const containerRef = useRef<HTMLDivElement>(null);
  const [copied, setCopied] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [showSearch, setShowSearch] = useState(false);
  const [levelFilter, setLevelFilter] = useState<string>('all');
  const [period, setPeriod] = useState<LogPeriod>('today');
  const [persistedLogs, setPersistedLogs] = useState<LogEntry[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  // Fetch persisted logs from database based on period
  const fetchPersistedLogs = useCallback(async () => {
    try {
      setIsLoading(true);
      const hours = periodHours[period];
      const response = await logsApi.getLogs({ limit: 1000, hours });
      const logs = response.logs.map((log) => ({
        type: 'log',
        timestamp: log.timestamp,
        level: log.level as LogEntry['level'],
        message: log.message,
        profile_id: log.profile_id,
      }));
      // Sort by timestamp ascending (oldest first)
      logs.sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime());
      setPersistedLogs(logs);
    } catch (error) {
      console.error('Failed to fetch persisted logs:', error);
    } finally {
      setIsLoading(false);
    }
  }, [period]);

  useEffect(() => {
    fetchPersistedLogs();
  }, [fetchPersistedLogs]);

  // Combine persisted logs with real-time WebSocket logs
  // Remove duplicates based on timestamp + message
  const logs = [...persistedLogs, ...wsLogs].reduce((acc, log) => {
    const key = `${log.timestamp}-${log.message}`;
    if (!acc.some(l => `${l.timestamp}-${l.message}` === key)) {
      acc.push(log);
    }
    return acc;
  }, [] as LogEntry[]);

  const clearLogs = () => {
    clearWsLogs();
    setPersistedLogs([]);
  };

  // Auto-scroll to bottom
  useEffect(() => {
    if (containerRef.current) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight;
    }
  }, [logs]);


  // Filter logs based on search and level
  const filteredLogs = logs.filter((log) => {
    const matchesSearch = searchTerm === '' ||
      log.message.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (log.profile_id && log.profile_id.toLowerCase().includes(searchTerm.toLowerCase()));

    const matchesLevel = levelFilter === 'all' || log.level === levelFilter;

    return matchesSearch && matchesLevel;
  });

  // Copy all logs to clipboard
  const copyLogs = async () => {
    const logText = filteredLogs
      .map((log) => {
        const time = formatDateTime(log.timestamp);
        const profile = log.profile_id ? `[${log.profile_id}]` : '';
        return `${time} [${log.level}] ${profile} ${log.message}`;
      })
      .join('\n');

    try {
      await navigator.clipboard.writeText(logText);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy logs:', err);
    }
  };

  // Save logs to file
  const saveLogs = () => {
    const logText = filteredLogs
      .map((log) => {
        const time = formatDateTime(log.timestamp);
        const profile = log.profile_id ? `[${log.profile_id}]` : '';
        return `${time} [${log.level}] ${profile} ${log.message}`;
      })
      .join('\n');

    const blob = new Blob([logText], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `twitter-bot-logs-${new Date().toISOString().split('T')[0]}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const levelCounts = {
    INFO: logs.filter((l) => l.level === 'INFO').length,
    SUCCESS: logs.filter((l) => l.level === 'SUCCESS').length,
    WARNING: logs.filter((l) => l.level === 'WARNING').length,
    ERROR: logs.filter((l) => l.level === 'ERROR').length,
  };

  return (
    <div className="bg-[#192734] rounded-xl border border-[#38444d] overflow-hidden">
      {showControls && (
        <div className="border-b border-[#38444d]">
          {/* Header */}
          <div className="flex items-center justify-between px-4 py-3">
            <div className="flex items-center gap-2">
              <h3 className="font-semibold text-white">Activity Logs</h3>
              {connected ? (
                <span className="flex items-center gap-1 text-xs text-green-500">
                  <Wifi className="w-3 h-3" />
                  Live
                </span>
              ) : (
                <span className="flex items-center gap-1 text-xs text-red-500">
                  <WifiOff className="w-3 h-3" />
                  Offline
                </span>
              )}
              <span className="text-xs text-gray-500">({filteredLogs.length} entries)</span>
            </div>
            <div className="flex items-center gap-1">
              <button
                onClick={fetchPersistedLogs}
                disabled={isLoading}
                className="p-2 text-gray-400 hover:text-white hover:bg-[#1e2732] rounded-lg transition-colors disabled:opacity-50"
                title="Refresh logs from database"
              >
                <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
              </button>
              <button
                onClick={() => setShowSearch(!showSearch)}
                className={`p-2 rounded-lg transition-colors ${
                  showSearch
                    ? 'bg-twitter-blue/20 text-twitter-blue'
                    : 'text-gray-400 hover:text-white hover:bg-[#1e2732]'
                }`}
                title="Search logs"
              >
                <Search className="w-4 h-4" />
              </button>
              <button
                onClick={copyLogs}
                className="p-2 text-gray-400 hover:text-white hover:bg-[#1e2732] rounded-lg transition-colors"
                title="Copy all logs"
              >
                {copied ? <Check className="w-4 h-4 text-green-500" /> : <Copy className="w-4 h-4" />}
              </button>
              <button
                onClick={saveLogs}
                className="p-2 text-gray-400 hover:text-white hover:bg-[#1e2732] rounded-lg transition-colors"
                title="Save logs to file"
              >
                <Download className="w-4 h-4" />
              </button>
              <button
                onClick={clearLogs}
                className="p-2 text-gray-400 hover:text-white hover:bg-[#1e2732] rounded-lg transition-colors"
                title="Clear view (logs remain in database)"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* Search & Filter Bar */}
          {showSearch && (
            <div className="px-4 pb-3 flex gap-2">
              <div className="relative flex-1">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
                <input
                  type="text"
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  placeholder="Search logs..."
                  className="w-full pl-10 pr-8 py-2 bg-[#1e2732] border border-[#38444d] rounded-lg text-white placeholder:text-gray-500 focus:outline-none focus:border-twitter-blue text-sm"
                />
                {searchTerm && (
                  <button
                    onClick={() => setSearchTerm('')}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-white"
                  >
                    <X className="w-4 h-4" />
                  </button>
                )}
              </div>
              <select
                value={period}
                onChange={(e) => setPeriod(e.target.value as LogPeriod)}
                className="px-3 py-2 bg-[#1e2732] border border-[#38444d] rounded-lg text-white text-sm focus:outline-none focus:border-twitter-blue"
              >
                <option value="today">Today</option>
                <option value="week">This Week</option>
                <option value="month">This Month</option>
                <option value="all">All Time</option>
              </select>
              <select
                value={levelFilter}
                onChange={(e) => setLevelFilter(e.target.value)}
                className="px-3 py-2 bg-[#1e2732] border border-[#38444d] rounded-lg text-white text-sm focus:outline-none focus:border-twitter-blue"
              >
                <option value="all">All Levels</option>
                <option value="INFO">INFO ({levelCounts.INFO})</option>
                <option value="SUCCESS">SUCCESS ({levelCounts.SUCCESS})</option>
                <option value="WARNING">WARNING ({levelCounts.WARNING})</option>
                <option value="ERROR">ERROR ({levelCounts.ERROR})</option>
              </select>
            </div>
          )}

          {/* Level Stats */}
          <div className="px-4 pb-3 flex gap-2">
            <LevelBadge level="INFO" count={levelCounts.INFO} color="text-twitter-blue bg-twitter-blue/10" />
            <LevelBadge level="SUCCESS" count={levelCounts.SUCCESS} color="text-green-500 bg-green-500/10" />
            <LevelBadge level="WARNING" count={levelCounts.WARNING} color="text-yellow-500 bg-yellow-500/10" />
            <LevelBadge level="ERROR" count={levelCounts.ERROR} color="text-red-500 bg-red-500/10" />
          </div>
        </div>
      )}

      <div
        ref={containerRef}
        className="overflow-auto font-mono text-sm p-4 space-y-1"
        style={{ maxHeight }}
      >
        {isLoading ? (
          <div className="text-gray-500 text-center py-8">
            Loading logs...
          </div>
        ) : filteredLogs.length === 0 ? (
          <div className="text-gray-500 text-center py-8">
            {logs.length === 0 ? 'No logs yet. Activity will appear here.' : 'No logs match your search.'}
          </div>
        ) : (
          filteredLogs.map((log, index) => (
            <LogLine
              key={index}
              log={log}
              getLevelColor={getLevelColor}
              formatTime={formatTime}
              searchTerm={searchTerm}
            />
          ))
        )}
      </div>
    </div>
  );
}

function LevelBadge({ level, count, color }: { level: string; count: number; color: string }) {
  return (
    <span className={`px-2 py-1 rounded text-xs font-medium ${color}`}>
      {level}: {count}
    </span>
  );
}

function LogLine({
  log,
  getLevelColor,
  formatTime,
  searchTerm,
}: {
  log: LogEntry;
  getLevelColor: (level: string) => string;
  formatTime: (timestamp: string) => string;
  searchTerm: string;
}) {
  // Highlight search term in message
  const highlightText = (text: string) => {
    if (!searchTerm) return text;

    const parts = text.split(new RegExp(`(${searchTerm})`, 'gi'));
    return parts.map((part, i) =>
      part.toLowerCase() === searchTerm.toLowerCase() ? (
        <span key={i} className="bg-yellow-500/30 text-yellow-200">
          {part}
        </span>
      ) : (
        part
      )
    );
  };

  return (
    <div className="flex gap-2 hover:bg-[#1e2732] px-2 py-1 rounded group">
      <span className="text-gray-500 flex-shrink-0">{formatTime(log.timestamp)}</span>
      <span className={`flex-shrink-0 font-semibold ${getLevelColor(log.level)}`}>
        [{log.level}]
      </span>
      {log.profile_id && (
        <span className="text-purple-400 flex-shrink-0">[{log.profile_id.slice(0, 8)}...]</span>
      )}
      <span className="text-gray-300">{highlightText(log.message)}</span>
    </div>
  );
}
