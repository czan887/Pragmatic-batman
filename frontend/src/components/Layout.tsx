import { Outlet } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Square, CheckCircle2 } from 'lucide-react';
import Sidebar from './Sidebar';
import { tasksApi, actionsApi, profilesApi } from '../api/client';

export default function Layout() {
  const queryClient = useQueryClient();

  // Get task statistics
  const { data: taskStats } = useQuery({
    queryKey: ['taskStats'],
    queryFn: tasksApi.getStatistics,
    refetchInterval: 5000,
  });

  // Get profiles for stop functionality
  const { data: profiles } = useQuery({
    queryKey: ['profiles'],
    queryFn: profilesApi.list,
  });

  // Stop mutation
  const stopMutation = useMutation({
    mutationFn: (profileId: string) => actionsApi.stop(profileId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['taskStats'] });
    },
  });

  const isRunning = (taskStats?.in_progress ?? 0) > 0;
  const pendingCount = taskStats?.pending ?? 0;
  const inProgressCount = taskStats?.in_progress ?? 0;

  const handleStopAll = () => {
    // Stop all profiles with active tasks
    profiles?.forEach((profile) => {
      stopMutation.mutate(profile.user_id);
    });
  };

  return (
    <div className="flex h-screen bg-[#15202b]">
      <Sidebar />
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Global Header with Bot Controls */}
        <header className="bg-[#192734] border-b border-[#38444d] px-6 py-3 flex items-center justify-between">
          <div className="flex items-center gap-4">
            {/* Bot Status */}
            <div className="flex items-center gap-2">
              {isRunning ? (
                <>
                  <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
                  <span className="text-green-500 text-sm font-medium">Bot Running</span>
                </>
              ) : pendingCount > 0 ? (
                <>
                  <div className="w-2 h-2 bg-yellow-500 rounded-full" />
                  <span className="text-yellow-500 text-sm font-medium">Tasks Pending</span>
                </>
              ) : (
                <>
                  <div className="w-2 h-2 bg-gray-500 rounded-full" />
                  <span className="text-gray-400 text-sm font-medium">Bot Idle</span>
                </>
              )}
            </div>

            {/* Task Counts */}
            {(pendingCount > 0 || inProgressCount > 0) && (
              <div className="flex items-center gap-3 text-sm">
                {inProgressCount > 0 && (
                  <span className="px-2 py-1 bg-green-500/10 text-green-500 rounded">
                    {inProgressCount} in progress
                  </span>
                )}
                {pendingCount > 0 && (
                  <span className="px-2 py-1 bg-yellow-500/10 text-yellow-500 rounded">
                    {pendingCount} pending
                  </span>
                )}
              </div>
            )}
          </div>

          {/* Bot Controls */}
          <div className="flex items-center gap-2">
            {isRunning && (
              <button
                onClick={handleStopAll}
                disabled={stopMutation.isPending}
                className="flex items-center gap-2 px-4 py-2 bg-red-600 text-white rounded-lg font-medium hover:bg-red-700 disabled:opacity-50 transition-colors"
              >
                <Square className="w-4 h-4" />
                {stopMutation.isPending ? 'Stopping...' : 'Stop All'}
              </button>
            )}

            {/* Connection Status */}
            <div className="flex items-center gap-1 text-xs text-gray-400">
              <CheckCircle2 className="w-3 h-3 text-green-500" />
              Connected
            </div>
          </div>
        </header>

        {/* Main Content */}
        <main className="flex-1 overflow-auto p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
