"""
Dashboard API routes
"""
from fastapi import APIRouter, Depends

from db.models import DashboardStats
from db.repositories.profile_repo import ProfileRepository
from db.repositories.action_repo import ActionRepository
from db.repositories.task_repo import TaskRepository
from api.dependencies import get_profile_repo, get_action_repo, get_task_repo

router = APIRouter()


@router.get("/stats", response_model=DashboardStats)
async def get_dashboard_stats(
    profile_repo: ProfileRepository = Depends(get_profile_repo),
    action_repo: ActionRepository = Depends(get_action_repo),
    task_repo: TaskRepository = Depends(get_task_repo)
):
    """
    Get dashboard statistics

    Returns aggregated statistics for the dashboard overview.
    """
    # Get profile count
    total_profiles = await profile_repo.get_count()

    # Get action statistics
    action_stats = await action_repo.get_statistics()
    today_stats = await action_repo.get_today_statistics()

    # Get task statistics
    task_stats = await task_repo.get_statistics()

    # Calculate active profiles (those with actions today)
    # This is approximate - a more accurate count would require additional queries

    return DashboardStats(
        total_profiles=total_profiles,
        active_profiles=action_stats['total_stats']['total_profiles'],
        total_tasks_today=today_stats['assigned'],
        completed_tasks_today=today_stats['completed'],
        failed_tasks_today=today_stats['failed'],
        total_follows=_count_action_type(action_stats, 'follow'),
        total_likes=_count_action_type(action_stats, 'like'),
        total_comments=_count_action_type(action_stats, 'comment'),
        success_rate=action_stats['total_stats']['success_rate']
    )


@router.get("/profiles")
async def get_dashboard_profiles(
    profile_repo: ProfileRepository = Depends(get_profile_repo)
):
    """
    Get all profiles with action summaries for dashboard

    Returns profiles with their action statistics.
    """
    profiles = await profile_repo.get_all()

    # Get action summary for each profile
    result = []
    for profile in profiles:
        profile_with_actions = await profile_repo.get_with_actions(profile.user_id)
        if profile_with_actions:
            result.append(profile_with_actions)
        else:
            result.append(profile)

    return result


@router.get("/action-breakdown")
async def get_action_breakdown(
    action_repo: ActionRepository = Depends(get_action_repo)
):
    """
    Get action breakdown by type

    Returns statistics grouped by action type.
    """
    stats = await action_repo.get_statistics()
    return stats['action_breakdown']


@router.get("/task-queue-status")
async def get_task_queue_status(
    task_repo: TaskRepository = Depends(get_task_repo)
):
    """
    Get task queue status

    Returns counts of tasks in each status.
    """
    return await task_repo.get_statistics()


@router.get("/recent-activity")
async def get_recent_activity(
    limit: int = 20,
    task_repo: TaskRepository = Depends(get_task_repo)
):
    """
    Get recent task activity

    Returns recently completed tasks.
    """
    # Get recent tasks
    tasks = await task_repo.get_all(limit=limit)

    return [
        {
            "id": task.id,
            "profile_id": task.profile_id,
            "task_type": task.task_type,
            "status": task.status,
            "created_at": task.created_at,
            "completed_at": task.completed_at,
            "error_message": task.error_message
        }
        for task in tasks
    ]


def _count_action_type(stats: dict, action_type: str) -> int:
    """Helper to count actions of a specific type"""
    total = 0
    for breakdown in stats.get('action_breakdown', []):
        if breakdown.get('action_type') == action_type:
            total += breakdown.get('completed', 0)
    return total
