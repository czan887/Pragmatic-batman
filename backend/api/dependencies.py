"""
Shared dependencies for API routes
"""
from typing import Optional
from fastapi import Depends, Request
from loguru import logger

from db.repositories.profile_repo import ProfileRepository
from db.repositories.action_repo import ActionRepository
from db.repositories.task_repo import TaskRepository
from db.repositories.stats_repo import StatsRepository
from db.repositories.session_repo import SessionRepository
from services.profile_service import ProfileService
from services.task_service import TaskService
from services.action_service import ActionService
from core.playwright_manager import PlaywrightManager


async def get_playwright(request: Request) -> Optional[PlaywrightManager]:
    """Get Playwright manager from app state (may be None if initialization failed)"""
    playwright = request.app.state.playwright

    # Lazy initialization if not already done
    if playwright is None:
        try:
            playwright = await PlaywrightManager.create()
            request.app.state.playwright = playwright
        except Exception as e:
            logger.warning(f"Playwright lazy initialization failed: {e}")
            # Return None - browser operations will fail gracefully

    return playwright


def get_profile_repo() -> ProfileRepository:
    """Get profile repository"""
    return ProfileRepository()


def get_action_repo() -> ActionRepository:
    """Get action repository"""
    return ActionRepository()


def get_task_repo() -> TaskRepository:
    """Get task repository"""
    return TaskRepository()


def get_stats_repo() -> StatsRepository:
    """Get stats repository"""
    return StatsRepository()


def get_session_repo() -> SessionRepository:
    """Get session repository"""
    return SessionRepository()


def get_profile_service(
    profile_repo: ProfileRepository = Depends(get_profile_repo),
    playwright: PlaywrightManager = Depends(get_playwright)
) -> ProfileService:
    """Get profile service"""
    return ProfileService(profile_repo, playwright)


def get_task_service(
    task_repo: TaskRepository = Depends(get_task_repo),
    action_repo: ActionRepository = Depends(get_action_repo)
) -> TaskService:
    """Get task service"""
    return TaskService(task_repo, action_repo)


def get_action_service(
    profile_repo: ProfileRepository = Depends(get_profile_repo),
    action_repo: ActionRepository = Depends(get_action_repo),
    task_repo: TaskRepository = Depends(get_task_repo),
    playwright: PlaywrightManager = Depends(get_playwright)
) -> ActionService:
    """Get action service"""
    return ActionService(profile_repo, action_repo, task_repo, playwright)
