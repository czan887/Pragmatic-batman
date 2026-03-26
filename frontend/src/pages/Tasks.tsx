import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Clock, CheckCircle, XCircle, AlertCircle, Loader2, Trash2, X } from 'lucide-react';
import { tasksApi } from '../api/client';
import { getStatusColor, formatDateTime } from '../utils/formatters';
import type { TaskStatus } from '../types';

const getStatusIcon = (status: TaskStatus) => {
  switch (status) {
    case 'pending':
      return <Clock className="w-5 h-5 text-yellow-500" />;
    case 'in_progress':
      return <Loader2 className="w-5 h-5 text-twitter-blue animate-spin" />;
    case 'completed':
      return <CheckCircle className="w-5 h-5 text-green-500" />;
    case 'failed':
      return <XCircle className="w-5 h-5 text-red-500" />;
    case 'cancelled':
      return <AlertCircle className="w-5 h-5 text-gray-500" />;
    default:
      return null;
  }
};

export default function Tasks() {
  const queryClient = useQueryClient();

  const { data: tasks, isLoading } = useQuery({
    queryKey: ['tasks'],
    queryFn: () => tasksApi.list(100),
    refetchInterval: 5000,
  });

  const { data: stats } = useQuery({
    queryKey: ['tasks', 'statistics'],
    queryFn: tasksApi.getStatistics,
    refetchInterval: 5000,
  });

  const cancelMutation = useMutation({
    mutationFn: (taskId: number) => tasksApi.cancel(taskId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['tasks'] }),
  });

  const clearMutation = useMutation({
    mutationFn: () => tasksApi.clearCompleted(7),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['tasks'] }),
  });

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Tasks</h1>
          <p className="text-gray-400">Manage your task queue</p>
        </div>

        <button
          onClick={() => clearMutation.mutate()}
          disabled={clearMutation.isPending}
          className="flex items-center gap-2 px-4 py-2 bg-[#192734] border border-[#38444d] text-gray-300 rounded-full hover:bg-[#1e2732] disabled:opacity-50"
        >
          <Trash2 className="w-4 h-4" />
          Clear Completed
        </button>
      </div>

      {/* Stats */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          <StatBox label="Pending" value={stats.pending} color="yellow" />
          <StatBox label="In Progress" value={stats.in_progress} color="blue" />
          <StatBox label="Completed" value={stats.completed} color="green" />
          <StatBox label="Failed" value={stats.failed} color="red" />
          <StatBox label="Cancelled" value={stats.cancelled} color="gray" />
        </div>
      )}

      {/* Task List */}
      <div className="bg-[#192734] rounded-xl border border-[#38444d] overflow-hidden">
        {isLoading ? (
          <div className="p-8 text-center text-gray-400">Loading tasks...</div>
        ) : !tasks || tasks.length === 0 ? (
          <div className="p-8 text-center text-gray-400">No tasks found</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-[#38444d]">
                  <th className="text-left p-4 text-gray-400 font-medium">ID</th>
                  <th className="text-left p-4 text-gray-400 font-medium">Type</th>
                  <th className="text-left p-4 text-gray-400 font-medium">Target</th>
                  <th className="text-left p-4 text-gray-400 font-medium">Status</th>
                  <th className="text-left p-4 text-gray-400 font-medium">Created</th>
                  <th className="text-left p-4 text-gray-400 font-medium">Actions</th>
                </tr>
              </thead>
              <tbody>
                {tasks.map((task) => (
                  <tr key={task.id} className="border-b border-[#38444d] hover:bg-[#1e2732]">
                    <td className="p-4 text-gray-300">#{task.id}</td>
                    <td className="p-4 text-white font-medium capitalize">
                      {task.task_type.replace('_', ' ')}
                    </td>
                    <td className="p-4 text-gray-400">
                      {(task.task_data?.target as string) || '-'}
                    </td>
                    <td className="p-4">
                      <span
                        className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(task.status)}`}
                      >
                        {getStatusIcon(task.status)}
                        {task.status}
                      </span>
                    </td>
                    <td className="p-4 text-gray-400 text-sm">{formatDateTime(task.created_at)}</td>
                    <td className="p-4">
                      {task.status === 'pending' && (
                        <button
                          onClick={() => cancelMutation.mutate(task.id)}
                          className="p-2 text-gray-400 hover:text-red-500 hover:bg-red-500/10 rounded-lg"
                          title="Cancel task"
                        >
                          <X className="w-4 h-4" />
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

function StatBox({
  label,
  value,
  color,
}: {
  label: string;
  value: number;
  color: 'yellow' | 'blue' | 'green' | 'red' | 'gray';
}) {
  const colorClasses = {
    yellow: 'border-yellow-500/30 bg-yellow-500/5',
    blue: 'border-twitter-blue/30 bg-twitter-blue/5',
    green: 'border-green-500/30 bg-green-500/5',
    red: 'border-red-500/30 bg-red-500/5',
    gray: 'border-gray-500/30 bg-gray-500/5',
  };

  return (
    <div className={`p-4 rounded-xl border ${colorClasses[color]}`}>
      <p className="text-sm text-gray-400">{label}</p>
      <p className="text-2xl font-bold text-white">{value}</p>
    </div>
  );
}
