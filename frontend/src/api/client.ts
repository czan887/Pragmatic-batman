import axios, { AxiosError } from 'axios';
import { showErrorNotification } from '../services/notificationService';
import type { ApiErrorResponse } from '../types';
import type {
  Profile,
  ProfileWithActions,
  Task,
  DashboardStats,
  TaskStatistics,
  FollowRequest,
  FollowFollowersRequest,
  TimelineRequest,
  PostTweetRequest,
  BulkFollowRequest,
  BulkUnfollowRequest,
  BulkLikeRequest,
  BulkRetweetRequest,
  BulkCommentRequest,
  MultiProfileActionRequest,
  BulkActionResponse,
  BatchStatus,
  HashtagRequest,
  PostUrlsRequest,
  UserActionsRequest,
  UnfollowNonFollowersRequest,
  RefactorPostRequest,
  SettingsResponse,
  SettingsUpdateRequest,
  ImportResult,
  ChatMessageRequest,
  ChatMessageResponse,
  ExecuteActionsRequest,
  ExecuteActionsResponse,
  DailyStats,
  StatsTrend,
  StatsRangeResponse,
  StatsSummaryResponse,
  SessionSummary,
  SessionHistoryResponse,
  SessionCreateRequest,
} from '../types';

const api = axios.create({
  baseURL: '/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Global error interceptor for showing toast notifications
api.interceptors.response.use(
  (response) => response,
  (error: AxiosError<ApiErrorResponse>) => {
    // Check if this is a structured error response from our backend
    if (error.response?.data?.error) {
      const { code, message, title, suggestion } = error.response.data.error;
      showErrorNotification(message, title || code, suggestion);
    } else if (error.response) {
      // Generic HTTP error
      const status = error.response.status;
      const statusText = error.response.statusText;
      showErrorNotification(
        `Request failed with status ${status}`,
        statusText || 'Request Failed'
      );
    } else if (error.request) {
      // Network error - no response received
      showErrorNotification(
        'Unable to connect to the server. Please check your connection.',
        'Connection Error'
      );
    } else {
      // Something else went wrong
      showErrorNotification(error.message || 'An unexpected error occurred', 'Error');
    }

    return Promise.reject(error);
  }
);

// Profiles API
export const profilesApi = {
  list: async (): Promise<Profile[]> => {
    const { data } = await api.get<Profile[]>('/profiles/');
    return data;
  },

  get: async (profileId: string): Promise<ProfileWithActions> => {
    const { data } = await api.get<ProfileWithActions>(`/profiles/${profileId}`);
    return data;
  },

  sync: async (): Promise<{ status: string; synced: number }> => {
    const { data } = await api.post('/profiles/sync');
    return data;
  },

  open: async (profileId: string): Promise<{ status: string; message: string }> => {
    const { data } = await api.post(`/profiles/${profileId}/open`);
    return data;
  },

  close: async (profileId: string): Promise<{ status: string; message: string }> => {
    const { data } = await api.post(`/profiles/${profileId}/close`);
    return data;
  },

  getStatus: async (profileId: string): Promise<{ profile_id: string; browser_open: boolean }> => {
    const { data } = await api.get(`/profiles/${profileId}/status`);
    return data;
  },

  refreshStats: async (profileId: string): Promise<{ status: string; stats: Record<string, number> }> => {
    const { data } = await api.post(`/profiles/${profileId}/refresh-stats`);
    return data;
  },
};

// Tasks API
export const tasksApi = {
  list: async (limit = 100): Promise<Task[]> => {
    const { data } = await api.get<Task[]>('/tasks/', { params: { limit } });
    return data;
  },

  getPending: async (limit = 50): Promise<Task[]> => {
    const { data } = await api.get<Task[]>('/tasks/pending', { params: { limit } });
    return data;
  },

  getStatistics: async (): Promise<TaskStatistics> => {
    const { data } = await api.get<TaskStatistics>('/tasks/statistics');
    return data;
  },

  cancel: async (taskId: number): Promise<{ status: string; message: string }> => {
    const { data } = await api.post(`/tasks/${taskId}/cancel`);
    return data;
  },

  cancelBatch: async (batchId: string): Promise<{ status: string; cancelled: number }> => {
    const { data } = await api.post(`/tasks/batch/${batchId}/cancel`);
    return data;
  },

  clearCompleted: async (olderThanDays = 7): Promise<{ status: string; cleared: number }> => {
    const { data } = await api.post('/tasks/clear-completed', null, {
      params: { older_than_days: olderThanDays },
    });
    return data;
  },
};

// Actions API
export const actionsApi = {
  follow: async (request: FollowRequest): Promise<{ status: string; message: string }> => {
    const { data } = await api.post('/actions/follow', request);
    return data;
  },

  unfollow: async (profileId: string, username: string): Promise<{ status: string; message: string }> => {
    const { data } = await api.post('/actions/unfollow', null, {
      params: { profile_id: profileId, username },
    });
    return data;
  },

  followFollowers: async (request: FollowFollowersRequest): Promise<{ status: string; batch_id: string; message: string }> => {
    const { data } = await api.post('/actions/follow-followers', request);
    return data;
  },

  processTimeline: async (request: TimelineRequest): Promise<{ status: string; message: string }> => {
    const { data } = await api.post('/actions/process-timeline', request);
    return data;
  },

  postTweet: async (request: PostTweetRequest): Promise<{ status: string; message: string }> => {
    const { data } = await api.post('/actions/post-tweet', request);
    return data;
  },

  like: async (profileId: string, tweetUrl: string): Promise<{ status: string; message: string }> => {
    const { data } = await api.post('/actions/like', null, {
      params: { profile_id: profileId, tweet_url: tweetUrl },
    });
    return data;
  },

  retweet: async (profileId: string, tweetUrl: string): Promise<{ status: string; message: string }> => {
    const { data } = await api.post('/actions/retweet', null, {
      params: { profile_id: profileId, tweet_url: tweetUrl },
    });
    return data;
  },

  getStatistics: async (): Promise<Record<string, unknown>> => {
    const { data } = await api.get('/actions/statistics');
    return data;
  },

  stop: async (profileId: string): Promise<{ status: string; message: string }> => {
    const { data } = await api.post(`/actions/stop/${profileId}`);
    return data;
  },

  // Bulk Actions
  bulkFollow: async (request: BulkFollowRequest): Promise<BulkActionResponse> => {
    const { data } = await api.post('/actions/bulk/follow', request);
    return data;
  },

  bulkUnfollow: async (request: BulkUnfollowRequest): Promise<BulkActionResponse> => {
    const { data } = await api.post('/actions/bulk/unfollow', request);
    return data;
  },

  bulkLike: async (request: BulkLikeRequest): Promise<BulkActionResponse> => {
    const { data } = await api.post('/actions/bulk/like', request);
    return data;
  },

  bulkRetweet: async (request: BulkRetweetRequest): Promise<BulkActionResponse> => {
    const { data } = await api.post('/actions/bulk/retweet', request);
    return data;
  },

  bulkComment: async (request: BulkCommentRequest): Promise<BulkActionResponse> => {
    const { data } = await api.post('/actions/bulk/comment', request);
    return data;
  },

  multiProfile: async (request: MultiProfileActionRequest): Promise<BulkActionResponse> => {
    const { data } = await api.post('/actions/multi-profile', request);
    return data;
  },

  getBatchStatus: async (batchId: string): Promise<BatchStatus> => {
    const { data } = await api.get(`/actions/bulk/status/${batchId}`);
    return data;
  },

  // New Tkinter Feature Parity Endpoints
  processHashtag: async (request: HashtagRequest): Promise<{ status: string; message: string }> => {
    const { data } = await api.post('/actions/process-hashtag', request);
    return data;
  },

  processPostUrls: async (request: PostUrlsRequest): Promise<{ status: string; message: string }> => {
    const { data } = await api.post('/actions/process-post-urls', request);
    return data;
  },

  processUsers: async (request: UserActionsRequest): Promise<{ status: string; message: string }> => {
    const { data } = await api.post('/actions/process-users', request);
    return data;
  },

  unfollowNonFollowers: async (request: UnfollowNonFollowersRequest): Promise<{ status: string; message: string }> => {
    const { data } = await api.post('/actions/unfollow-non-followers', request);
    return data;
  },

  refactorPost: async (request: RefactorPostRequest): Promise<{ status: string; message: string }> => {
    const { data } = await api.post('/actions/refactor-post', request);
    return data;
  },
};

// Dashboard API
export const dashboardApi = {
  getStats: async (): Promise<DashboardStats> => {
    const { data } = await api.get<DashboardStats>('/dashboard/stats');
    return data;
  },

  getProfiles: async (): Promise<ProfileWithActions[]> => {
    const { data } = await api.get<ProfileWithActions[]>('/dashboard/profiles');
    return data;
  },

  getActionBreakdown: async (): Promise<Record<string, unknown>[]> => {
    const { data } = await api.get('/dashboard/action-breakdown');
    return data;
  },

  getTaskQueueStatus: async (): Promise<TaskStatistics> => {
    const { data } = await api.get<TaskStatistics>('/dashboard/task-queue-status');
    return data;
  },

  getRecentActivity: async (limit = 20): Promise<Task[]> => {
    const { data } = await api.get<Task[]>('/dashboard/recent-activity', {
      params: { limit },
    });
    return data;
  },
};

// Settings API
export const settingsApi = {
  get: async (): Promise<SettingsResponse> => {
    const { data } = await api.get<SettingsResponse>('/settings');
    return data;
  },

  update: async (request: SettingsUpdateRequest): Promise<{ status: string; message: string; updates: Record<string, unknown> }> => {
    const { data } = await api.patch('/settings', request);
    return data;
  },

  testGemini: async (): Promise<{ status: string; message: string; model: string }> => {
    const { data } = await api.post('/settings/test-gemini');
    return data;
  },

  testAdspower: async (): Promise<{ status: string; message: string; url: string }> => {
    const { data } = await api.post('/settings/test-adspower');
    return data;
  },
};

// File Import API
export const importApi = {
  importFile: async (file: File): Promise<ImportResult> => {
    const formData = new FormData();
    formData.append('file', file);
    const { data } = await api.post<ImportResult>('/import', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return data;
  },

  validateFile: async (file: File): Promise<{ valid: boolean; filename: string; error?: string }> => {
    const formData = new FormData();
    formData.append('file', file);
    const { data } = await api.post('/import/validate', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return data;
  },
};

// Bot/Chat API
export const botApi = {
  sendMessage: async (request: ChatMessageRequest): Promise<ChatMessageResponse> => {
    const { data } = await api.post<ChatMessageResponse>('/bot/chat', request);
    return data;
  },

  executeActions: async (request: ExecuteActionsRequest): Promise<ExecuteActionsResponse> => {
    const { data } = await api.post<ExecuteActionsResponse>('/bot/execute', request);
    return data;
  },

  getStatus: async (): Promise<{ status: string; active_agents: number }> => {
    const { data } = await api.get('/bot/status');
    return data;
  },
};

// Logs API
export const logsApi = {
  getLogs: async (params?: {
    limit?: number;
    offset?: number;
    level?: string;
    profile_id?: string;
    hours?: number;
  }): Promise<{ logs: Array<{ id: number; profile_id: string | null; session_id: string | null; level: string; message: string; timestamp: string }>; count: number }> => {
    const { data } = await api.get('/logs/', { params });
    return data;
  },

  getStats: async (hours = 24): Promise<{ stats: Record<string, number>; period_hours: number }> => {
    const { data } = await api.get('/logs/stats/', { params: { hours } });
    return data;
  },

  getErrors: async (limit = 20): Promise<{ errors: Array<{ id: number; level: string; message: string; timestamp: string }>; count: number }> => {
    const { data } = await api.get('/logs/errors/', { params: { limit } });
    return data;
  },

  search: async (q: string, limit = 50): Promise<{ query: string; logs: Array<{ id: number; level: string; message: string; timestamp: string }>; count: number }> => {
    const { data } = await api.get('/logs/search/', { params: { q, limit } });
    return data;
  },

  cleanup: async (days = 30): Promise<{ status: string; deleted: number }> => {
    const { data } = await api.post('/logs/cleanup/', null, { params: { days } });
    return data;
  },
};

// Stats API
export const statsApi = {
  getDaily: async (date?: string, profile_id?: string): Promise<DailyStats> => {
    const { data } = await api.get<DailyStats>('/stats/daily', {
      params: { date, profile_id },
    });
    return data;
  },

  getRange: async (
    start_date: string,
    end_date: string,
    granularity: string = 'daily',
    profile_id?: string
  ): Promise<StatsRangeResponse> => {
    const { data } = await api.get<StatsRangeResponse>('/stats/range', {
      params: { start_date, end_date, granularity, profile_id },
    });
    return data;
  },

  getTrends: async (period: string = 'daily'): Promise<StatsTrend> => {
    const { data } = await api.get<StatsTrend>('/stats/trends', {
      params: { period },
    });
    return data;
  },

  getSummary: async (): Promise<StatsSummaryResponse> => {
    const { data } = await api.get<StatsSummaryResponse>('/stats/summary');
    return data;
  },

  getWeekly: async (weeks_back: number = 4): Promise<DailyStats[]> => {
    const { data } = await api.get<DailyStats[]>('/stats/weekly', {
      params: { weeks_back },
    });
    return data;
  },

  getMonthly: async (months_back: number = 12): Promise<DailyStats[]> => {
    const { data } = await api.get<DailyStats[]>('/stats/monthly', {
      params: { months_back },
    });
    return data;
  },

  getYearly: async (): Promise<DailyStats[]> => {
    const { data } = await api.get<DailyStats[]>('/stats/yearly');
    return data;
  },
};

// Sessions API
export const sessionsApi = {
  start: async (request: SessionCreateRequest = {}): Promise<{ status: string; session_id: string; message: string }> => {
    const { data } = await api.post('/sessions/start', request);
    return data;
  },

  end: async (session_id: string): Promise<SessionSummary> => {
    const { data } = await api.post<SessionSummary>(`/sessions/${session_id}/end`);
    return data;
  },

  getActive: async (): Promise<SessionSummary[]> => {
    const { data } = await api.get<SessionSummary[]>('/sessions/active');
    return data;
  },

  getHistory: async (limit: number = 20, days?: number, profile_id?: string): Promise<SessionHistoryResponse> => {
    const { data } = await api.get<SessionHistoryResponse>('/sessions/history', {
      params: { limit, days, profile_id },
    });
    return data;
  },

  get: async (session_id: string): Promise<SessionSummary> => {
    const { data } = await api.get<SessionSummary>(`/sessions/${session_id}`);
    return data;
  },

  cleanup: async (timeout_minutes: number = 30): Promise<{ status: string; ended_sessions: number; message: string }> => {
    const { data } = await api.post('/sessions/cleanup', null, {
      params: { timeout_minutes },
    });
    return data;
  },
};

export default api;
