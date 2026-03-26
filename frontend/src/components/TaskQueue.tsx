import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { X, Clock, CheckCircle, XCircle, AlertCircle, Loader2 } from 'lucide-react';
import { tasksApi } from '../api/client';
import { formatTaskType } from '../utils/formatters';
import type { Task, TaskStatus } from '../types';

interface TaskQueueProps {
  limit?: number;
}

const getStatusIcon = (status: TaskStatus) => {
  switch (status) {
    case 'pending':
      return <Clock className="w-4 h-4 text-yellow-500" />;
    case 'in_progress':
      return <Loader2 className="w-4 h-4 text-twitter-blue animate-spin" />;
    case 'completed':
      return <CheckCircle className="w-4 h-4 text-green-500" />;
    case 'failed':
      return <XCircle className="w-4 h-4 text-red-500" />;
    case 'cancelled':
      return <AlertCircle className="w-4 h-4 text-gray-500" />;
    default:
      return null;
  }
};

export default function TaskQueue({ limit = 20 }: TaskQueueProps) {
  const queryClient = useQueryClient();

  const { data: tasks, isLoading } = useQuery({
    queryKey: ['tasks', 'pending'],
    queryFn: () => tasksApi.getPending(limit),
    refetchInterval: 5000,
  });

  const cancelMutation = useMutation({
    mutationFn: (taskId: number) => tasksApi.cancel(taskId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tasks'] });
    },
  });

  if (isLoading) {
    return (
      <div className="bg-[#192734] rounded-xl border border-[#38444d] p-8 text-center">
        <Loader2 className="w-8 h-8 text-twitter-blue animate-spin mx-auto" />
        <p className="text-gray-400 mt-2">Loading tasks...</p>
      </div>
    );
  }

  return (
    <div className="bg-[#192734] rounded-xl border border-[#38444d] overflow-hidden">
      <div className="px-4 py-3 border-b border-[#38444d]">
        <h3 className="font-semibold text-white">Task Queue</h3>
        <p className="text-xs text-gray-500">
          {tasks?.length || 0} pending task{tasks?.length !== 1 ? 's' : ''}
        </p>
      </div>

      {!tasks || tasks.length === 0 ? (
        <div className="p-8 text-center text-gray-500">No pending tasks</div>
      ) : (
        <div className="divide-y divide-[#38444d] max-h-96 overflow-auto">
          {tasks.map((task) => (
            <TaskItem
              key={task.id}
              task={task}
              onCancel={() => cancelMutation.mutate(task.id)}
              getStatusIcon={getStatusIcon}
              formatTaskType={formatTaskType}
            />
          ))}
        </div>
      )}
    </div>
  );
}

function TaskItem({
  task,
  onCancel,
  getStatusIcon,
  formatTaskType,
}: {
  task: Task;
  onCancel: () => void;
  getStatusIcon: (status: TaskStatus) => React.ReactNode;
  formatTaskType: (type: string) => string;
}) {
  const target = task.task_data?.target as string | undefined;

  return (
    <div className="flex items-center justify-between p-4 hover:bg-[#1e2732]">
      <div className="flex items-center gap-3">
        {getStatusIcon(task.status)}
        <div>
          <p className="text-sm font-medium text-white">{formatTaskType(task.task_type)}</p>
          {target && <p className="text-xs text-gray-500">@{target}</p>}
        </div>
      </div>

      <div className="flex items-center gap-2">
        <span className="text-xs text-gray-500">#{task.id}</span>
        {task.status === 'pending' && (
          <button
            onClick={onCancel}
            className="p-1 text-gray-400 hover:text-red-500 hover:bg-red-500/10 rounded"
            title="Cancel task"
          >
            <X className="w-4 h-4" />
          </button>
        )}
      </div>
    </div>
  );
}
