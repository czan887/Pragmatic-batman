// API Error Response Types
export interface ApiError {
  code: string;
  message: string;
  title?: string;
  suggestion?: string;
}

export interface ApiErrorResponse {
  success: false;
  error: ApiError;
}

// Profile types
export interface Profile {
  user_id: string;
  serial_number: string;
  name: string;
  domain_name: string | null;
  group_id: string | null;
  group_name: string | null;
  created_time: string | null;
  last_open_time: string | null;
  ip: string | null;
  ip_country: string | null;
  followers_count: number;
  following_count: number;
  bio: string | null;
  location: string | null;
  last_updated: string | null;
}

export interface ProfileWithActions extends Profile {
  actions: Record<string, ActionSummary>;
  total_assigned: number;
  total_completed: number;
  total_failed: number;
  success_rate: number;
}

export interface ActionSummary {
  assigned: number;
  completed: number;
  failed: number;
}

// Task types
export type TaskStatus = 'pending' | 'in_progress' | 'completed' | 'failed' | 'cancelled';
export type TaskType = 'follow' | 'unfollow' | 'like' | 'retweet' | 'comment' | 'post_tweet' | 'follow_followers' | 'process_timeline';

export interface Task {
  id: number;
  profile_id: string;
  task_type: TaskType;
  task_data: Record<string, unknown> | null;
  status: TaskStatus;
  priority: number;
  batch_id: string | null;
  created_at: string | null;
  started_at: string | null;
  completed_at: string | null;
  error_message: string | null;
}

// Dashboard types
export interface DashboardStats {
  total_profiles: number;
  active_profiles: number;
  total_tasks_today: number;
  completed_tasks_today: number;
  failed_tasks_today: number;
  total_follows: number;
  total_likes: number;
  total_comments: number;
  success_rate: number;
}

export interface TaskStatistics {
  pending: number;
  in_progress: number;
  completed: number;
  failed: number;
  cancelled: number;
  total: number;
}

// Log types
export type LogLevel = 'INFO' | 'SUCCESS' | 'WARNING' | 'ERROR' | 'DEBUG';

export interface LogEntry {
  type: string;
  timestamp: string;
  level: LogLevel;
  message: string;
  profile_id: string | null;
}

// Request types
export interface FollowRequest {
  profile_id: string;
  username: string;
  use_ai_analysis: boolean;
}

export interface FollowFollowersRequest {
  profile_id: string;
  target_username: string;
  batch_size: number;
  batch_delay_minutes: number;
  use_ai_analysis: boolean;
}

export interface TimelineRequest {
  profile_id: string;
  username: string;
  should_like: boolean;
  should_retweet: boolean;
  should_comment: boolean;
  use_ai_comment: boolean;
  comment_template: string | null;
  max_tweets: number;
}

export interface PostTweetRequest {
  profile_id: string;
  text: string | null;
  use_ai_generation: boolean;
  topic: string | null;
  style: string;
}

// Bulk Action Request Types
export interface BulkFollowRequest {
  profile_id: string;
  usernames: string[];
  use_ai_analysis: boolean;
  delay_between_follows: number;
}

export interface BulkUnfollowRequest {
  profile_id: string;
  usernames: string[];
  delay_between_unfollows: number;
}

export interface BulkLikeRequest {
  profile_id: string;
  tweet_urls: string[];
  delay_between_likes: number;
}

export interface BulkRetweetRequest {
  profile_id: string;
  tweet_urls: string[];
  delay_between_retweets: number;
}

export interface BulkCommentRequest {
  profile_id: string;
  tweet_urls: string[];
  use_ai_generation: boolean;
  comment_template: string | null;
  delay_between_comments: number;
}

export interface MultiProfileActionRequest {
  profile_ids: string[];
  action_type: 'follow' | 'unfollow' | 'like' | 'retweet' | 'comment';
  target: string;
  use_ai: boolean;
  delay_between_profiles: number;
}

export interface BulkActionResponse {
  status: string;
  batch_id: string;
  total_items: number;
  message: string;
}

export interface BatchStatus {
  batch_id: string;
  found: boolean;
  total?: number;
  pending?: number;
  in_progress?: number;
  completed?: number;
  failed?: number;
  cancelled?: number;
  progress?: number;
  status?: string;
  message?: string;
}

// New Request Types for Tkinter Feature Parity
export interface HashtagRequest {
  profile_id: string;
  hashtags: string[];
  should_like: boolean;
  should_retweet: boolean;
  should_comment: boolean;
  use_ai_comment: boolean;
  should_refactor: boolean;
  comment_template: string | null;
  max_posts_per_hashtag: number;
}

export interface PostUrlsRequest {
  profile_id: string;
  post_urls: string[];
  should_like: boolean;
  should_retweet: boolean;
  should_comment: boolean;
  use_ai_comment: boolean;
  should_refactor: boolean;
  comment_template: string | null;
}

export interface UserActionsRequest {
  profile_id: string;
  usernames: string[];
  should_follow: boolean;
  should_unfollow: boolean;
  should_like: boolean;
  should_retweet: boolean;
  should_comment: boolean;
  use_ai_comment: boolean;
  should_refactor: boolean;
  comment_template: string | null;
  max_tweets_per_user: number;
}

export interface UnfollowNonFollowersRequest {
  profile_id: string;
  max_unfollow: number;
  delay_between_unfollows: number;
}

export interface RefactorPostRequest {
  profile_id: string;
  original_tweet_url: string;
  style: string;
}

export interface SettingsResponse {
  adspower_url: string;
  adspower_api_key: string;
  gemini_api_key: string;
  anthropic_api_key: string;
  default_batch_size: number;
  default_batch_delay_minutes: number;
  min_action_delay: number;
  max_action_delay: number;
  enable_profile_analysis: boolean;
  enable_behavior_planning: boolean;
  enable_mcp_recovery: boolean;
  ai_model: string;
}

export interface SettingsUpdateRequest {
  gemini_api_key?: string;
  anthropic_api_key?: string;
  adspower_api_key?: string;
  default_batch_size?: number;
  default_batch_delay_minutes?: number;
  min_action_delay?: number;
  max_action_delay?: number;
  enable_profile_analysis?: boolean;
  enable_behavior_planning?: boolean;
  enable_mcp_recovery?: boolean;
}

export interface ImportResult {
  status: string;
  items: string[];
  count: number;
  filename: string;
  format: string;
}

// Bot/Chat Types
export interface BotAction {
  type: string;
  target?: string;
  params?: Record<string, unknown>;
  status: 'pending' | 'executing' | 'completed' | 'error';
  result?: string;
}

export interface ChatMessageRequest {
  message: string;
  profile_id?: string;
  conversation_history?: Array<{
    role: 'user' | 'assistant' | 'system';
    content: string;
  }>;
}

export interface ChatMessageResponse {
  message: string;
  actions?: BotAction[];
  profile_used?: string;
}

export interface ExecuteActionsRequest {
  actions: BotAction[];
  profile_id?: string;
}

export interface ExecuteActionsResponse {
  status: string;
  results: string[];
}

// Stats types
export interface DailyStats {
  id?: number | null;
  date: string;
  profile_id: string | null;
  follows_count: number;
  unfollows_count: number;
  likes_count: number;
  retweets_count: number;
  comments_count: number;
  tweets_posted_count: number;
  total_actions: number;
  successful_actions: number;
  failed_actions: number;
  created_at?: string | null;
  updated_at?: string | null;
}

export interface TrendChange {
  value: number;
  percentage: number;
  direction: 'up' | 'down' | 'same';
}

export interface StatsTrend {
  current: DailyStats;
  previous: DailyStats;
  changes: Record<string, TrendChange>;
}

export interface StatsRangeResponse {
  stats: DailyStats[];
  start_date: string;
  end_date: string;
  granularity: string;
  total: DailyStats;
}

export interface StatsSummaryResponse {
  today: DailyStats;
  this_week: DailyStats;
  this_month: DailyStats;
  this_year: DailyStats;
  all_time: DailyStats;
}

// Session types
export type SessionStatus = 'active' | 'completed' | 'interrupted';

export interface SessionSummary {
  id?: number | null;
  session_id: string;
  profile_id: string | null;
  started_at: string;
  ended_at: string | null;
  duration_seconds: number | null;
  total_actions: number;
  follows_count: number;
  unfollows_count: number;
  likes_count: number;
  retweets_count: number;
  comments_count: number;
  tweets_posted_count: number;
  successful_count: number;
  failed_count: number;
  success_rate: number;
  errors_json: string | null;
  error_count: number;
  status: SessionStatus;
}

export interface SessionHistoryResponse {
  sessions: SessionSummary[];
  total_count: number;
}

export interface SessionCreateRequest {
  profile_id?: string | null;
}
