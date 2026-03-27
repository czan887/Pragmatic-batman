"""
Global Exception Handler Middleware

Catches all TwitterBotError exceptions and returns standardized JSON responses.
Also broadcasts system errors via WebSocket for real-time notifications.
"""
import traceback
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from loguru import logger

from core.exceptions import TwitterBotError


async def broadcast_error_notification(error: TwitterBotError):
    """Broadcast system error notification via WebSocket"""
    try:
        from api.routes.websocket import broadcast_notification
        await broadcast_notification(
            notification_type="error",
            title=error.title,
            message=error.message,
            error_code=error.error_code
        )
    except Exception as e:
        logger.debug(f"Failed to broadcast error notification: {e}")


async def twitter_bot_exception_handler(request: Request, exc: TwitterBotError) -> JSONResponse:
    """Handle TwitterBotError exceptions"""
    logger.error(f"TwitterBotError: {exc.error_code} - {exc.message}")

    # Broadcast to WebSocket for real-time notification
    await broadcast_error_notification(exc)

    return JSONResponse(
        status_code=exc.status_code,
        content=exc.to_dict()
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions"""
    logger.error(f"Unhandled exception: {exc}")
    logger.debug(traceback.format_exc())

    # Create a generic TwitterBotError for unexpected exceptions
    error = TwitterBotError(
        message="An unexpected error occurred",
        error_code="UNEXPECTED_ERROR",
        status_code=500,
        title="Unexpected Error",
        suggestion="Please try again. If the problem persists, check the server logs."
    )

    # Broadcast to WebSocket for real-time notification
    await broadcast_error_notification(error)

    return JSONResponse(
        status_code=500,
        content=error.to_dict()
    )


def register_exception_handlers(app: FastAPI):
    """Register all exception handlers with the FastAPI app"""
    app.add_exception_handler(TwitterBotError, twitter_bot_exception_handler)
    # Optionally catch all exceptions (can be noisy in development)
    # app.add_exception_handler(Exception, generic_exception_handler)
