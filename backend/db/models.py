"""
Pydantic models for Twitter Bot v2.0
"""
from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime
from enum import Enum


# Enums
class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskType(str, Enum):
    FOLLOW = "follow"
    UNFOLLOW = "unfollow"
    LIKE = "like"
    RETWEET = "retweet"
    COMMENT = "comment"
    POST_TWEET = "post_tweet"
    FOLLOW_FOLLOWERS = "follow_followers"
    PROCESS_TIMELINE = "process_timeline"
    PROCESS_HASHTAG = "process_hashtag"
    PROCESS_POST_URLS = "process_post_urls"
    UNFOLLOW_NON_FOLLOWERS = "unfollow_non_followers"
    REFACTOR_POST = "refactor_post"


class LogLevel(str, Enum):
    INFO = "INFO"
    SUCCESS = "SUCCESS"
    WARNING = "WARNING"
    ERROR = "ERROR"
    DEBUG = "DEBUG"


# Profile Models
class ProfileBase(BaseModel):
    """Base profile model"""
    user_id: str
    serial_number: str
    name: str
    domain_name: Optional[str] = None
    group_id: Optional[str] = None
    group_name: Optional[str] = None


class ProfileCreate(ProfileBase):
    """Profile creation model"""
    pass


class ProfileUpdate(BaseModel):
    """Profile update model"""
    name: Optional[str] = None
    followers_count: Optional[int] = None
    following_count: Optional[int] = None
    ip: Optional[str] = None
    ip_country: Optional[str] = None


class Profile(ProfileBase):
    """Full profile model"""
    created_time: Optional[str] = None
    last_open_time: Optional[str] = None
    ip: Optional[str] = None
    ip_country: Optional[str] = None
    followers_count: int = 0
    following_count: int = 0
    bio: Optional[str] = None
    location: Optional[str] = None
    last_updated: Optional[datetime] = None

    class Config:
        from_attributes = True


class ProfileWithActions(Profile):
    """Profile with action summary"""
    actions: dict = Field(default_factory=dict)
    total_assigned: int = 0
    total_completed: int = 0
    total_failed: int = 0
    success_rate: float = 0.0


# Action Models
class ActionBase(BaseModel):
    """Base action model"""
    profile_id: str
    action_type: str
    action_name: str


class ActionCreate(ActionBase):
    """Action creation model"""
    assigned_count: int = 1


class ActionUpdate(BaseModel):
    """Action update model"""
    completed_count: Optional[int] = None
    failed_count: Optional[int] = None


class Action(ActionBase):
    """Full action model"""
    id: int
    assigned_count: int = 0
    completed_count: int = 0
    failed_count: int = 0
    date_created: Optional[datetime] = None
    last_updated: Optional[datetime] = None

    @property
    def success_rate(self) -> float:
        if self.assigned_count == 0:
            return 0.0
        return (self.completed_count / self.assigned_count) * 100

    class Config:
        from_attributes = True


# Task Models
class TaskBase(BaseModel):
    """Base task model"""
    profile_id: str
    task_type: TaskType
    task_data: Optional[dict] = None
    priority: int = 0


class TaskCreate(TaskBase):
    """Task creation model"""
    batch_id: Optional[str] = None


class TaskUpdate(BaseModel):
    """Task update model"""
    status: Optional[TaskStatus] = None
    error_message: Optional[str] = None


class Task(TaskBase):
    """Full task model"""
    id: int
    status: TaskStatus = TaskStatus.PENDING
    batch_id: Optional[str] = None
    created_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None

    class Config:
        from_attributes = True


# Request/Response Models
class FollowRequest(BaseModel):
    """Follow user request"""
    profile_id: str
    username: str
    use_ai_analysis: bool = True


class FollowFollowersRequest(BaseModel):
    """Follow followers batch request"""
    profile_id: str
    target_username: str
    batch_size: int = Field(default=15, ge=1, le=50)
    batch_delay_minutes: int = Field(default=60, ge=1)
    use_ai_analysis: bool = True


class TimelineRequest(BaseModel):
    """Process timeline request"""
    profile_id: str
    username: str
    should_like: bool = False
    should_retweet: bool = False
    should_comment: bool = False
    use_ai_comment: bool = False
    comment_template: Optional[str] = None
    max_tweets: int = Field(default=10, ge=1, le=50)


class PostTweetRequest(BaseModel):
    """Post tweet request"""
    profile_id: str
    text: Optional[str] = None
    use_ai_generation: bool = False
    topic: Optional[str] = None
    style: str = "informative"


# Dashboard Models
class DashboardStats(BaseModel):
    """Dashboard statistics"""
    total_profiles: int = 0
    active_profiles: int = 0
    total_tasks_today: int = 0
    completed_tasks_today: int = 0
    failed_tasks_today: int = 0
    total_follows: int = 0
    total_likes: int = 0
    total_comments: int = 0
    success_rate: float = 0.0


class ActionBreakdown(BaseModel):
    """Action type breakdown"""
    action_type: str
    action_name: str
    assigned: int
    completed: int
    failed: int
    success_rate: float


# Log Models
class LogEntry(BaseModel):
    """Log entry model"""
    timestamp: datetime
    level: LogLevel
    profile_id: Optional[str] = None
    message: str


# AI Models
class ProfileScore(BaseModel):
    """AI profile analysis result"""
    should_follow: bool
    score: float = Field(ge=0.0, le=1.0)
    reason: str
    flags: list[str] = Field(default_factory=list)


class BehaviorPlan(BaseModel):
    """AI behavior plan"""
    start_time: datetime
    end_time: datetime
    actions: list[dict]
    breaks: list[dict] = Field(default_factory=list)
    estimated_actions: int


# Bulk Action Models
class BulkFollowRequest(BaseModel):
    """Bulk follow multiple users request"""
    profile_id: str
    usernames: list[str] = Field(..., min_length=1, max_length=100)
    use_ai_analysis: bool = True
    delay_between_follows: int = Field(default=30, ge=5, le=300, description="Seconds between follows")


class BulkUnfollowRequest(BaseModel):
    """Bulk unfollow multiple users request"""
    profile_id: str
    usernames: list[str] = Field(..., min_length=1, max_length=100)
    delay_between_unfollows: int = Field(default=20, ge=5, le=300, description="Seconds between unfollows")


class BulkLikeRequest(BaseModel):
    """Bulk like multiple tweets request"""
    profile_id: str
    tweet_urls: list[str] = Field(..., min_length=1, max_length=100)
    delay_between_likes: int = Field(default=10, ge=3, le=120, description="Seconds between likes")


class BulkRetweetRequest(BaseModel):
    """Bulk retweet multiple tweets request"""
    profile_id: str
    tweet_urls: list[str] = Field(..., min_length=1, max_length=50)
    delay_between_retweets: int = Field(default=30, ge=10, le=300, description="Seconds between retweets")


class BulkCommentRequest(BaseModel):
    """Bulk comment on multiple tweets request"""
    profile_id: str
    tweet_urls: list[str] = Field(..., min_length=1, max_length=50)
    use_ai_generation: bool = True
    comment_template: Optional[str] = None
    delay_between_comments: int = Field(default=60, ge=30, le=600, description="Seconds between comments")


class MultiProfileActionRequest(BaseModel):
    """Execute action across multiple profiles"""
    profile_ids: list[str] = Field(..., min_length=1, max_length=20)
    action_type: Literal["follow", "unfollow", "like", "retweet", "comment"]
    target: str = Field(..., description="Username or tweet URL depending on action")
    use_ai: bool = False
    delay_between_profiles: int = Field(default=60, ge=10, le=600, description="Seconds between profile actions")


class BulkActionResponse(BaseModel):
    """Response for bulk action requests"""
    status: str
    batch_id: str
    total_items: int
    message: str


# ==================== NEW MODELS FOR TKINTER FEATURE PARITY ====================

class HashtagRequest(BaseModel):
    """Process hashtag posts request"""
    profile_id: str
    hashtags: list[str] = Field(..., min_length=1, max_length=20, description="List of hashtags without # symbol")
    should_like: bool = False
    should_retweet: bool = False
    should_comment: bool = False
    use_ai_comment: bool = False
    should_refactor: bool = False
    comment_template: Optional[str] = None
    max_posts_per_hashtag: int = Field(default=10, ge=1, le=50)


class PostUrlsRequest(BaseModel):
    """Process post URLs request"""
    profile_id: str
    post_urls: list[str] = Field(..., min_length=1, max_length=100, description="List of tweet/post URLs")
    should_like: bool = False
    should_retweet: bool = False
    should_comment: bool = False
    use_ai_comment: bool = False
    should_refactor: bool = False
    comment_template: Optional[str] = None


class UserActionsRequest(BaseModel):
    """Process user actions request (combined follow/unfollow/timeline)"""
    profile_id: str
    usernames: list[str] = Field(..., min_length=1, max_length=100, description="List of usernames")
    should_follow: bool = False
    should_unfollow: bool = False
    should_like: bool = False
    should_retweet: bool = False
    should_comment: bool = False
    use_ai_comment: bool = False
    should_refactor: bool = False
    comment_template: Optional[str] = None
    max_tweets_per_user: int = Field(default=10, ge=1, le=50)


class UnfollowNonFollowersRequest(BaseModel):
    """Unfollow non-followers request"""
    profile_id: str
    max_unfollow: int = Field(default=50, ge=1, le=200, description="Maximum number to unfollow")
    delay_between_unfollows: int = Field(default=30, ge=5, le=300, description="Seconds between unfollows")


class RefactorPostRequest(BaseModel):
    """Refactor/rewrite post request"""
    profile_id: str
    original_tweet_url: str
    style: str = Field(default="similar", description="Style: similar, casual, professional, humorous")


class SettingsUpdateRequest(BaseModel):
    """Settings update request"""
    gemini_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    adspower_api_key: Optional[str] = None
    default_batch_size: Optional[int] = Field(default=None, ge=1, le=100)
    default_batch_delay_minutes: Optional[int] = Field(default=None, ge=1, le=240)
    min_action_delay: Optional[float] = Field(default=None, ge=1.0, le=30.0)
    max_action_delay: Optional[float] = Field(default=None, ge=2.0, le=60.0)
    enable_profile_analysis: Optional[bool] = None
    enable_behavior_planning: Optional[bool] = None
    enable_mcp_recovery: Optional[bool] = None


class SettingsResponse(BaseModel):
    """Settings response"""
    adspower_url: str
    adspower_api_key: str  # masked
    gemini_api_key: str  # masked
    anthropic_api_key: str  # masked
    default_batch_size: int
    default_batch_delay_minutes: int
    min_action_delay: float
    max_action_delay: float
    enable_profile_analysis: bool
    enable_behavior_planning: bool
    enable_mcp_recovery: bool
    ai_model: str


# ==================== STATS AND SESSION MODELS ====================

class SessionStatus(str, Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    INTERRUPTED = "interrupted"


class DailyStats(BaseModel):
    """Daily statistics model"""
    id: Optional[int] = None
    date: str
    profile_id: Optional[str] = None
    follows_count: int = 0
    unfollows_count: int = 0
    likes_count: int = 0
    retweets_count: int = 0
    comments_count: int = 0
    tweets_posted_count: int = 0
    total_actions: int = 0
    successful_actions: int = 0
    failed_actions: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class DailyStatsCreate(BaseModel):
    """Daily stats creation model"""
    date: str
    profile_id: Optional[str] = None


class SessionSummary(BaseModel):
    """Session summary model"""
    id: Optional[int] = None
    session_id: str
    profile_id: Optional[str] = None
    started_at: datetime
    ended_at: Optional[datetime] = None
    duration_seconds: Optional[int] = None
    total_actions: int = 0
    follows_count: int = 0
    unfollows_count: int = 0
    likes_count: int = 0
    retweets_count: int = 0
    comments_count: int = 0
    tweets_posted_count: int = 0
    successful_count: int = 0
    failed_count: int = 0
    success_rate: float = 0.0
    errors_json: Optional[str] = None
    error_count: int = 0
    status: SessionStatus = SessionStatus.ACTIVE

    class Config:
        from_attributes = True

    @property
    def errors(self) -> list[str]:
        """Parse errors from JSON string"""
        import json
        if self.errors_json:
            try:
                return json.loads(self.errors_json)
            except json.JSONDecodeError:
                return []
        return []


class SessionCreate(BaseModel):
    """Session creation model"""
    profile_id: Optional[str] = None


class TrendChange(BaseModel):
    """Change indicator for trend comparison"""
    value: float
    percentage: float
    direction: Literal["up", "down", "same"]


class StatsTrend(BaseModel):
    """Trend comparison between current and previous period"""
    current: DailyStats
    previous: DailyStats
    changes: dict[str, TrendChange]


class StatsRangeResponse(BaseModel):
    """Response for stats range query"""
    stats: list[DailyStats]
    start_date: str
    end_date: str
    granularity: str
    total: DailyStats


class StatsSummaryResponse(BaseModel):
    """Summary stats response"""
    today: DailyStats
    this_week: DailyStats
    this_month: DailyStats
    this_year: DailyStats
    all_time: DailyStats


class SessionHistoryResponse(BaseModel):
    """Response for session history"""
    sessions: list[SessionSummary]
    total_count: int
