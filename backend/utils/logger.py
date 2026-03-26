"""
Logging configuration for Twitter Bot v2.0
Supports console, file, and database logging
"""
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, Callable
import asyncio

from loguru import logger


# Global flag to track if logger has been configured
_logger_configured = False

# Global reference to log repository (set during initialization)
_log_repo = None


class InterceptHandler(logging.Handler):
    """Handler to intercept standard logging and redirect to loguru"""

    def emit(self, record: logging.LogRecord) -> None:
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())


def setup_logger(
    name: str = "twitter_bot",
    log_level: Optional[str] = None,
    log_file: Optional[str] = None,
    log_rotation: Optional[str] = None,
    log_retention: Optional[str] = None,
    use_settings: bool = True
) -> logging.Logger:
    """
    Setup and configure logger with console and optional file output

    Args:
        name: Logger name
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR). If None, uses settings.
        log_file: Log file path. If None and use_settings=True, uses settings.
        log_rotation: Log file rotation size. If None, uses settings.
        log_retention: Log retention period. If None, uses settings.
        use_settings: Whether to load defaults from application settings.

    Returns:
        Configured logger instance
    """
    global _logger_configured

    # Only configure once
    if _logger_configured:
        return logging.getLogger(name)

    # Load from settings if parameters not provided
    if use_settings:
        try:
            from config import get_settings
            settings = get_settings()
            log_level = log_level or settings.log_level
            log_file = log_file or settings.log_file_path
            log_rotation = log_rotation or settings.log_rotation
            log_retention = log_retention or settings.log_retention
        except Exception:
            # Fallback defaults if settings not available
            log_level = log_level or "INFO"
            log_rotation = log_rotation or "10 MB"
            log_retention = log_retention or "7 days"
    else:
        log_level = log_level or "INFO"
        log_rotation = log_rotation or "10 MB"
        log_retention = log_retention or "7 days"

    # Remove default handler
    logger.remove()

    # Add custom SUCCESS level (if not already exists)
    try:
        logger.level("SUCCESS")
    except ValueError:
        # Level doesn't exist, create it
        logger.level("SUCCESS", no=25, color="<green>", icon="✓")

    # Add console handler with colored output
    logger.add(
        sys.stdout,
        colorize=True,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=log_level,
    )

    # Add file handler if specified
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        logger.add(
            log_file,
            rotation=log_rotation,
            retention=log_retention,
            compression="gz",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
            level=log_level,
            enqueue=True,  # Thread-safe file writing
        )
        logger.info(f"File logging enabled: {log_file}")

    # Intercept standard logging
    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)

    # Get standard logger for compatibility
    std_logger = logging.getLogger(name)
    std_logger.setLevel(getattr(logging, log_level.upper()))

    _logger_configured = True
    logger.info(f"Logger initialized with level: {log_level}")

    return std_logger


def init_logger_from_settings():
    """Initialize logger using application settings"""
    from config import get_settings
    settings = get_settings()

    return setup_logger(
        name="twitter_bot",
        log_level=settings.log_level,
        log_file=settings.log_file_path,
        log_rotation=settings.log_rotation,
        log_retention=settings.log_retention
    )


def set_log_repository(repo):
    """Set the log repository for database logging"""
    global _log_repo
    _log_repo = repo


def get_log_repository():
    """Get the log repository"""
    return _log_repo


class BotLogger:
    """Logger specifically for bot operations with WebSocket broadcasting and DB logging"""

    def __init__(
        self,
        profile_id: str,
        broadcast_callback: Optional[Callable] = None,
        session_id: Optional[str] = None,
        save_to_db: bool = True
    ):
        """
        Initialize BotLogger

        Args:
            profile_id: Profile ID for log context
            broadcast_callback: Optional callback for WebSocket broadcasting
            session_id: Optional session ID for grouping logs
            save_to_db: Whether to save logs to database
        """
        self.profile_id = profile_id
        self.broadcast_callback = broadcast_callback
        self.session_id = session_id
        self.save_to_db = save_to_db
        self._logger = logger.bind(profile_id=profile_id)

    def _log(self, level: str, message: str) -> dict:
        """Internal logging method"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "level": level,
            "profile_id": self.profile_id,
            "message": message
        }

        # Map SUCCESS to INFO for loguru (if SUCCESS level not available)
        loguru_level = level.lower() if level != "SUCCESS" else "success"
        try:
            getattr(self._logger, loguru_level)(message)
        except AttributeError:
            self._logger.info(f"[{level}] {message}")

        # Save to database asynchronously
        if self.save_to_db and _log_repo is not None:
            self._save_to_db_async(level, message)

        # Broadcast to WebSocket if callback provided
        if self.broadcast_callback:
            self._broadcast_async(log_entry)

        return log_entry

    def _save_to_db_async(self, level: str, message: str):
        """Save log to database asynchronously"""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.create_task(
                    _log_repo.save_log(
                        level=level,
                        message=message,
                        profile_id=self.profile_id,
                        session_id=self.session_id
                    )
                )
        except RuntimeError:
            pass  # No event loop available

    def _broadcast_async(self, log_entry: dict):
        """Broadcast log entry via WebSocket asynchronously"""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.create_task(self.broadcast_callback(log_entry))
        except RuntimeError:
            pass  # No event loop available

    def info(self, message: str) -> dict:
        """Log info message"""
        return self._log("INFO", message)

    def success(self, message: str) -> dict:
        """Log success message"""
        return self._log("SUCCESS", message)

    def warning(self, message: str) -> dict:
        """Log warning message"""
        return self._log("WARNING", message)

    def error(self, message: str) -> dict:
        """Log error message"""
        return self._log("ERROR", message)

    def debug(self, message: str) -> dict:
        """Log debug message"""
        return self._log("DEBUG", message)


async def save_log_to_db(
    level: str,
    message: str,
    profile_id: Optional[str] = None,
    session_id: Optional[str] = None
):
    """
    Standalone function to save a log entry to database

    Args:
        level: Log level
        message: Log message
        profile_id: Optional profile ID
        session_id: Optional session ID
    """
    if _log_repo is not None:
        await _log_repo.save_log(
            level=level,
            message=message,
            profile_id=profile_id,
            session_id=session_id
        )
