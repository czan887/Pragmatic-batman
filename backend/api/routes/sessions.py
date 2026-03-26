"""
Sessions API routes for tracking bot sessions
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query

from db.models import SessionSummary, SessionCreate, SessionHistoryResponse
from db.repositories.session_repo import SessionRepository
from api.dependencies import get_session_repo

router = APIRouter()


@router.post("/start", response_model=dict)
async def start_session(
    request: SessionCreate,
    session_repo: SessionRepository = Depends(get_session_repo)
):
    """
    Start a new session

    Creates a new bot session and returns the session ID.
    """
    session_id = await session_repo.start_session(request.profile_id)
    return {
        "status": "success",
        "session_id": session_id,
        "message": "Session started"
    }


@router.post("/{session_id}/end", response_model=SessionSummary)
async def end_session(
    session_id: str,
    session_repo: SessionRepository = Depends(get_session_repo)
):
    """
    End a session

    Marks the session as complete and returns the session summary.
    """
    session = await session_repo.end_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.get("/active", response_model=list[SessionSummary])
async def get_active_sessions(
    session_repo: SessionRepository = Depends(get_session_repo)
):
    """
    Get active sessions

    Returns all currently active sessions.
    """
    return await session_repo.get_all_active_sessions()


@router.get("/history", response_model=SessionHistoryResponse)
async def get_session_history(
    limit: int = Query(20, ge=1, le=100, description="Maximum number of sessions to return"),
    days: Optional[int] = Query(None, ge=1, le=365, description="Filter to sessions within N days"),
    profile_id: Optional[str] = Query(None, description="Filter by profile ID"),
    session_repo: SessionRepository = Depends(get_session_repo)
):
    """
    Get session history

    Returns a list of recent sessions.
    """
    sessions = await session_repo.get_session_history(limit, days, profile_id)
    return SessionHistoryResponse(
        sessions=sessions,
        total_count=len(sessions)
    )


@router.get("/{session_id}", response_model=SessionSummary)
async def get_session(
    session_id: str,
    session_repo: SessionRepository = Depends(get_session_repo)
):
    """
    Get session details

    Returns full details for a specific session.
    """
    session = await session_repo.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.post("/cleanup", response_model=dict)
async def cleanup_stale_sessions(
    timeout_minutes: int = Query(30, ge=5, le=1440, description="Session inactivity timeout in minutes"),
    session_repo: SessionRepository = Depends(get_session_repo)
):
    """
    Cleanup stale sessions

    Ends sessions that have been inactive beyond the timeout threshold.
    """
    count = await session_repo.end_stale_sessions(timeout_minutes)
    return {
        "status": "success",
        "ended_sessions": count,
        "message": f"Ended {count} stale session(s)"
    }
