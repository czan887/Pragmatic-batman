"""
Logs API routes for retrieving and managing logs
"""
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Query, HTTPException

from db.repositories.log_repo import LogRepository
from utils.logger import get_log_repository

router = APIRouter()


def get_repo() -> LogRepository:
    """Get log repository, create if not set"""
    repo = get_log_repository()
    if repo is None:
        return LogRepository()
    return repo


@router.get("/")
async def get_logs(
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    level: Optional[str] = Query(default=None, description="Filter by log level"),
    profile_id: Optional[str] = Query(default=None, description="Filter by profile ID"),
    hours: Optional[int] = Query(default=None, description="Get logs from last N hours")
):
    """
    Get logs with optional filtering

    - **limit**: Maximum number of logs to return (1-1000)
    - **offset**: Number of logs to skip for pagination
    - **level**: Filter by log level (INFO, WARNING, ERROR, SUCCESS, DEBUG)
    - **profile_id**: Filter by profile ID
    - **hours**: Get logs from the last N hours
    """
    repo = get_repo()

    since = None
    if hours:
        since = datetime.now() - timedelta(hours=hours)

    logs = await repo.get_logs(
        limit=limit,
        offset=offset,
        level=level,
        profile_id=profile_id,
        since=since
    )

    return {
        "logs": logs,
        "count": len(logs),
        "limit": limit,
        "offset": offset
    }


@router.get("/stats")
async def get_log_stats(
    hours: int = Query(default=24, ge=1, le=168, description="Get stats for last N hours")
):
    """
    Get log statistics

    Returns counts of logs by level for the specified time period.
    """
    repo = get_repo()
    since = datetime.now() - timedelta(hours=hours)
    stats = await repo.get_log_stats(since=since)

    return {
        "stats": stats,
        "period_hours": hours,
        "since": since.isoformat()
    }


@router.get("/errors")
async def get_recent_errors(
    limit: int = Query(default=20, ge=1, le=100)
):
    """
    Get recent error logs

    Returns the most recent error logs.
    """
    repo = get_repo()
    errors = await repo.get_recent_errors(limit=limit)

    return {
        "errors": errors,
        "count": len(errors)
    }


@router.get("/profile/{profile_id}")
async def get_logs_by_profile(
    profile_id: str,
    limit: int = Query(default=50, ge=1, le=500)
):
    """
    Get logs for a specific profile

    Returns logs associated with the specified profile.
    """
    repo = get_repo()
    logs = await repo.get_logs_by_profile(profile_id=profile_id, limit=limit)

    return {
        "profile_id": profile_id,
        "logs": logs,
        "count": len(logs)
    }


@router.get("/search")
async def search_logs(
    q: str = Query(..., min_length=2, description="Search term"),
    limit: int = Query(default=50, ge=1, le=200)
):
    """
    Search logs by message content

    Searches for logs containing the specified term in their message.
    """
    repo = get_repo()
    logs = await repo.search_logs(search_term=q, limit=limit)

    return {
        "query": q,
        "logs": logs,
        "count": len(logs)
    }


@router.post("/cleanup")
async def cleanup_old_logs(
    days: int = Query(default=30, ge=1, le=365, description="Delete logs older than N days")
):
    """
    Clean up old logs

    Deletes logs older than the specified number of days.
    """
    repo = get_repo()
    deleted = await repo.cleanup_old_logs(days=days)

    return {
        "status": "success",
        "deleted": deleted,
        "older_than_days": days
    }
