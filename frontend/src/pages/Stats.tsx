import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  BarChart3,
  UserPlus,
  UserMinus,
  Heart,
  Repeat,
  MessageCircle,
  Send,
  CheckCircle,
  XCircle,
  Activity,
  Calendar,
  RefreshCw,
} from 'lucide-react';
import StatsTrendCard from '../components/StatsTrendCard';
import SessionSummaryCard from '../components/SessionSummaryCard';
import { statsApi, sessionsApi, profilesApi } from '../api/client';
import type { StatsTrend } from '../types';

type Period = 'today' | 'week' | 'month' | 'year' | 'all';
type TrendPeriod = 'daily' | 'weekly' | 'monthly';

const periodLabels: Record<Period, string> = {
  today: 'Today',
  week: 'This Week',
  month: 'This Month',
  year: 'This Year',
  all: 'All Time',
};

const trendPeriodLabels: Record<TrendPeriod, string> = {
  daily: 'vs Yesterday',
  weekly: 'vs Last Week',
  monthly: 'vs Last Month',
};

export default function Stats() {
  const [period, setPeriod] = useState<Period>('today');
  const [trendPeriod, setTrendPeriod] = useState<TrendPeriod>('daily');
  const [profileFilter, setProfileFilter] = useState<string>('');

  const { data: profiles } = useQuery({
    queryKey: ['profiles'],
    queryFn: profilesApi.list,
  });

  const { data: summary, isLoading: summaryLoading, refetch: refetchSummary } = useQuery({
    queryKey: ['stats', 'summary'],
    queryFn: statsApi.getSummary,
    refetchInterval: 30000,
  });

  const { data: trends } = useQuery({
    queryKey: ['stats', 'trends', trendPeriod],
    queryFn: () => statsApi.getTrends(trendPeriod),
    refetchInterval: 30000,
  });

  const { data: sessionHistory, isLoading: sessionsLoading } = useQuery({
    queryKey: ['sessions', 'history'],
    queryFn: () => sessionsApi.getHistory(10),
    refetchInterval: 30000,
  });

  const getCurrentStats = () => {
    if (!summary) return null;
    switch (period) {
      case 'today': return summary.today;
      case 'week': return summary.this_week;
      case 'month': return summary.this_month;
      case 'year': return summary.this_year;
      case 'all': return summary.all_time;
      default: return summary.today;
    }
  };

  const getTrend = (key: string): StatsTrend['changes'][string] | undefined => {
    return trends?.changes?.[key];
  };

  const currentStats = getCurrentStats();

  if (summaryLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-gray-400">Loading statistics...</div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <BarChart3 className="w-7 h-7 text-twitter-blue" />
            Statistics
          </h1>
          <p className="text-gray-400">Track your automation performance</p>
        </div>
        <button
          onClick={() => refetchSummary()}
          className="flex items-center gap-2 px-4 py-2 bg-[#192734] border border-[#38444d] rounded-lg text-gray-300 hover:bg-[#1e2732] transition-colors"
        >
          <RefreshCw className="w-4 h-4" />
          Refresh
        </button>
      </div>

      {/* Period Selector & Filters */}
      <div className="flex flex-wrap items-center gap-4">
        <div className="flex items-center gap-2">
          <Calendar className="w-4 h-4 text-gray-400" />
          <div className="flex bg-[#192734] rounded-lg border border-[#38444d] p-1">
            {(Object.keys(periodLabels) as Period[]).map((p) => (
              <button
                key={p}
                onClick={() => setPeriod(p)}
                className={`px-3 py-1.5 text-sm rounded-md transition-colors ${
                  period === p
                    ? 'bg-twitter-blue text-white'
                    : 'text-gray-400 hover:text-white'
                }`}
              >
                {periodLabels[p]}
              </button>
            ))}
          </div>
        </div>

        {profiles && profiles.length > 0 && (
          <select
            value={profileFilter}
            onChange={(e) => setProfileFilter(e.target.value)}
            className="bg-[#192734] border border-[#38444d] rounded-lg px-3 py-2 text-gray-300 text-sm focus:outline-none focus:border-twitter-blue"
          >
            <option value="">All Profiles</option>
            {profiles.map((p) => (
              <option key={p.user_id} value={p.user_id}>
                {p.name || p.serial_number}
              </option>
            ))}
          </select>
        )}
      </div>

      {/* Stats Overview */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatsTrendCard
          title="Total Actions"
          value={currentStats?.total_actions || 0}
          icon={Activity}
          color="blue"
          trend={period === 'today' ? getTrend('total_actions') : undefined}
        />
        <StatsTrendCard
          title="Successful"
          value={currentStats?.successful_actions || 0}
          icon={CheckCircle}
          color="green"
          trend={period === 'today' ? getTrend('successful_actions') : undefined}
        />
        <StatsTrendCard
          title="Failed"
          value={currentStats?.failed_actions || 0}
          icon={XCircle}
          color="red"
          trend={period === 'today' ? getTrend('failed_actions') : undefined}
        />
        <StatsTrendCard
          title="Success Rate"
          value={currentStats ? Math.round((currentStats.successful_actions / Math.max(currentStats.total_actions, 1)) * 100) : 0}
          icon={BarChart3}
          color="purple"
          subtitle="%"
        />
      </div>

      {/* Action Breakdown */}
      <div>
        <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
          Action Breakdown
          {period === 'today' && (
            <div className="flex bg-[#192734] rounded-lg border border-[#38444d] p-0.5 ml-4">
              {(Object.keys(trendPeriodLabels) as TrendPeriod[]).map((tp) => (
                <button
                  key={tp}
                  onClick={() => setTrendPeriod(tp)}
                  className={`px-2 py-1 text-xs rounded transition-colors ${
                    trendPeriod === tp
                      ? 'bg-twitter-blue/20 text-twitter-blue'
                      : 'text-gray-500 hover:text-gray-300'
                  }`}
                >
                  {trendPeriodLabels[tp]}
                </button>
              ))}
            </div>
          )}
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <StatsTrendCard
            title="Follows"
            value={currentStats?.follows_count || 0}
            icon={UserPlus}
            color="blue"
            trend={period === 'today' ? getTrend('follows_count') : undefined}
          />
          <StatsTrendCard
            title="Unfollows"
            value={currentStats?.unfollows_count || 0}
            icon={UserMinus}
            color="yellow"
            trend={period === 'today' ? getTrend('unfollows_count') : undefined}
          />
          <StatsTrendCard
            title="Likes"
            value={currentStats?.likes_count || 0}
            icon={Heart}
            color="red"
            trend={period === 'today' ? getTrend('likes_count') : undefined}
          />
          <StatsTrendCard
            title="Retweets"
            value={currentStats?.retweets_count || 0}
            icon={Repeat}
            color="green"
            trend={period === 'today' ? getTrend('retweets_count') : undefined}
          />
          <StatsTrendCard
            title="Comments"
            value={currentStats?.comments_count || 0}
            icon={MessageCircle}
            color="purple"
            trend={period === 'today' ? getTrend('comments_count') : undefined}
          />
          <StatsTrendCard
            title="Tweets Posted"
            value={currentStats?.tweets_posted_count || 0}
            icon={Send}
            color="blue"
            trend={period === 'today' ? getTrend('tweets_posted_count') : undefined}
          />
        </div>
      </div>

      {/* Session History */}
      <div>
        <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
          <Activity className="w-5 h-5 text-twitter-blue" />
          Recent Sessions
        </h2>
        {sessionsLoading ? (
          <div className="text-gray-400">Loading sessions...</div>
        ) : sessionHistory?.sessions && sessionHistory.sessions.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {sessionHistory.sessions.map((session) => (
              <SessionSummaryCard key={session.session_id} session={session} />
            ))}
          </div>
        ) : (
          <div className="bg-[#192734] rounded-xl p-8 border border-[#38444d] text-center">
            <Activity className="w-12 h-12 text-gray-600 mx-auto mb-3" />
            <p className="text-gray-400">No sessions recorded yet</p>
            <p className="text-gray-500 text-sm mt-1">
              Sessions will appear here as you perform bot actions
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
