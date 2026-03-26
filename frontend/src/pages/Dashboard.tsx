import { useQuery } from '@tanstack/react-query';
import { Users, CheckCircle, XCircle, TrendingUp, Heart, MessageCircle, UserPlus } from 'lucide-react';
import StatsCard from '../components/StatsCard';
import LogViewer from '../components/LogViewer';
import TaskQueue from '../components/TaskQueue';
import { dashboardApi } from '../api/client';

export default function Dashboard() {
  const { data: stats, isLoading } = useQuery({
    queryKey: ['dashboard', 'stats'],
    queryFn: dashboardApi.getStats,
    refetchInterval: 10000,
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-gray-400">Loading dashboard...</div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">Dashboard</h1>
        <p className="text-gray-400">Overview of your Twitter automation</p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatsCard
          title="Total Profiles"
          value={stats?.total_profiles || 0}
          icon={Users}
          color="blue"
        />
        <StatsCard
          title="Completed Today"
          value={stats?.completed_tasks_today || 0}
          icon={CheckCircle}
          color="green"
        />
        <StatsCard
          title="Failed Today"
          value={stats?.failed_tasks_today || 0}
          icon={XCircle}
          color="red"
        />
        <StatsCard
          title="Success Rate"
          value={`${(stats?.success_rate || 0).toFixed(1)}%`}
          icon={TrendingUp}
          color="purple"
        />
      </div>

      {/* Action Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <StatsCard
          title="Total Follows"
          value={stats?.total_follows || 0}
          icon={UserPlus}
          color="blue"
        />
        <StatsCard
          title="Total Likes"
          value={stats?.total_likes || 0}
          icon={Heart}
          color="red"
        />
        <StatsCard
          title="Total Comments"
          value={stats?.total_comments || 0}
          icon={MessageCircle}
          color="green"
        />
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <TaskQueue limit={10} />
        <LogViewer maxHeight="400px" />
      </div>
    </div>
  );
}
