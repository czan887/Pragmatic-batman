"""
Custom exception hierarchy for Twitter Bot

Provides structured error handling with standardized error codes,
HTTP status codes, and user-friendly messages.
"""
from typing import Optional


class TwitterBotError(Exception):
    """Base exception for all Twitter Bot errors"""

    error_code: str = "INTERNAL_ERROR"
    status_code: int = 500
    title: str = "Internal Error"
    suggestion: str = "Please try again later or contact support."

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        status_code: Optional[int] = None,
        title: Optional[str] = None,
        suggestion: Optional[str] = None,
    ):
        super().__init__(message)
        self.message = message
        if error_code:
            self.error_code = error_code
        if status_code:
            self.status_code = status_code
        if title:
            self.title = title
        if suggestion:
            self.suggestion = suggestion

    def to_dict(self) -> dict:
        """Convert exception to API response format"""
        return {
            "success": False,
            "error": {
                "code": self.error_code,
                "message": self.message,
                "title": self.title,
                "suggestion": self.suggestion,
            }
        }


# External Service Errors
class ExternalServiceError(TwitterBotError):
    """Base error for external service failures"""
    error_code = "EXTERNAL_SERVICE_ERROR"
    status_code = 502
    title = "External Service Error"
    suggestion = "The external service may be temporarily unavailable. Please try again."


class AdsPowerError(ExternalServiceError):
    """AdsPower API or connection errors"""
    error_code = "ADSPOWER_ERROR"
    title = "AdsPower Error"
    suggestion = "Check that AdsPower is running and the API URL is correct."


class PlaywrightError(ExternalServiceError):
    """Playwright browser automation errors"""
    error_code = "PLAYWRIGHT_ERROR"
    title = "Browser Automation Error"
    suggestion = "The browser may have crashed or become unresponsive. Try closing and reopening the profile."


class AIServiceError(ExternalServiceError):
    """AI service errors (Gemini, Anthropic)"""
    error_code = "AI_SERVICE_ERROR"
    title = "AI Service Error"
    suggestion = "Check your API key configuration and try again."


# Browser/Profile Errors
class BrowserNotConnectedError(TwitterBotError):
    """Browser is not connected or opened"""
    error_code = "BROWSER_NOT_CONNECTED"
    status_code = 400
    title = "Browser Not Connected"
    suggestion = "Please open the browser profile before performing actions."


class ProfileNotFoundError(TwitterBotError):
    """Profile not found in database or AdsPower"""
    error_code = "PROFILE_NOT_FOUND"
    status_code = 404
    title = "Profile Not Found"
    suggestion = "Sync profiles from AdsPower to refresh the profile list."


# Validation Errors
class ValidationError(TwitterBotError):
    """Request validation errors"""
    error_code = "VALIDATION_ERROR"
    status_code = 400
    title = "Invalid Request"
    suggestion = "Please check your input and try again."


# Rate Limiting
class RateLimitError(TwitterBotError):
    """Rate limit exceeded"""
    error_code = "RATE_LIMIT_ERROR"
    status_code = 429
    title = "Rate Limit Exceeded"
    suggestion = "Please wait before performing more actions. Twitter has rate limits."


# Twitter-specific Errors
class TwitterActionError(TwitterBotError):
    """Error performing Twitter action"""
    error_code = "TWITTER_ACTION_ERROR"
    status_code = 400
    title = "Twitter Action Failed"
    suggestion = "The action may have failed due to Twitter limitations. Check the logs for details."


class TwitterAuthError(TwitterBotError):
    """Twitter authentication or session error"""
    error_code = "TWITTER_AUTH_ERROR"
    status_code = 401
    title = "Twitter Authentication Error"
    suggestion = "The Twitter session may have expired. Please re-login to Twitter in the browser."


# Task Errors
class TaskError(TwitterBotError):
    """Task execution error"""
    error_code = "TASK_ERROR"
    status_code = 500
    title = "Task Execution Error"
    suggestion = "The task failed to execute. Check the logs for more details."


class TaskNotFoundError(TwitterBotError):
    """Task not found"""
    error_code = "TASK_NOT_FOUND"
    status_code = 404
    title = "Task Not Found"
    suggestion = "The requested task does not exist."
