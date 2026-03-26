import { Clock, CheckCircle, XCircle, Activity } from 'lucide-react';
import type { SessionSummary } from '../types';

interface SessionSummaryCardProps {
  session: SessionSummary;
}

const formatDuration = (seconds: number | null): string => {
  if (!seconds) return '-';
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const secs = seconds % 60;

  if (hours > 0) {
    return `${hours}h ${minutes}m`;
  }
  if (minutes > 0) {
    return `${minutes}m ${secs}s`;
  }
  return `${secs}s`;
};

const formatDate = (dateStr: string): string => {
  const date = new Date(dateStr);
  return date.toLocaleString();
};

const statusColors = {
  active: 'bg-green-500/20 text-green-400 border-green-500/30',
  completed: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
  interrupted: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30',
};

export default function SessionSummaryCard({ session }: SessionSummaryCardProps) {
  return (
    <div className="bg-[#192734] rounded-xl p-4 border border-[#38444d]">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <Activity className="w-4 h-4 text-twitter-blue" />
          <span className="text-sm text-gray-400">
            {formatDate(session.started_at)}
          </span>
        </div>
        <span className={`px-2 py-0.5 text-xs font-medium rounded border ${statusColors[session.status]}`}>
          {session.status}
        </span>
      </div>

      <div className="grid grid-cols-3 gap-4 mb-3">
        <div className="text-center">
          <p className="text-2xl font-bold text-white">{session.total_actions}</p>
          <p className="text-xs text-gray-500">Total Actions</p>
        </div>
        <div className="text-center">
          <div className="flex items-center justify-center gap-1">
            <CheckCircle className="w-4 h-4 text-green-500" />
            <span className="text-xl font-bold text-green-500">{session.successful_count}</span>
          </div>
          <p className="text-xs text-gray-500">Success</p>
        </div>
        <div className="text-center">
          <div className="flex items-center justify-center gap-1">
            <XCircle className="w-4 h-4 text-red-500" />
            <span className="text-xl font-bold text-red-500">{session.failed_count}</span>
          </div>
          <p className="text-xs text-gray-500">Failed</p>
        </div>
      </div>

      <div className="flex items-center justify-between text-sm border-t border-[#38444d] pt-3">
        <div className="flex items-center gap-1 text-gray-400">
          <Clock className="w-4 h-4" />
          <span>{formatDuration(session.duration_seconds)}</span>
        </div>
        <div className={`font-medium ${session.success_rate >= 80 ? 'text-green-500' : session.success_rate >= 50 ? 'text-yellow-500' : 'text-red-500'}`}>
          {session.success_rate.toFixed(1)}% Success Rate
        </div>
      </div>

      {session.error_count > 0 && (
        <div className="mt-2 text-xs text-red-400 bg-red-500/10 rounded px-2 py-1">
          {session.error_count} error(s) encountered
        </div>
      )}
    </div>
  );
}
