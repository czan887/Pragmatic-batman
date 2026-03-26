"""
Task queue API routes
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Optional

from db.models import Task, TaskCreate, TaskStatus
from services.task_service import TaskService
from api.dependencies import get_task_service

router = APIRouter()


@router.get("/", response_model=list[Task])
async def list_tasks(
    limit: int = 100,
    status_filter: Optional[TaskStatus] = None,
    service: TaskService = Depends(get_task_service)
):
    """
    List all tasks

    Returns tasks ordered by priority and creation time.
    Optionally filter by status.
    """
    if status_filter:
        return await service.get_by_status(status_filter, limit)
    return await service.get_all(limit)


@router.get("/pending", response_model=list[Task])
async def list_pending_tasks(
    limit: int = 50,
    service: TaskService = Depends(get_task_service)
):
    """
    List pending tasks

    Returns tasks that are waiting to be processed.
    """
    return await service.get_pending(limit)


@router.get("/statistics")
async def get_task_statistics(
    service: TaskService = Depends(get_task_service)
):
    """
    Get task queue statistics

    Returns counts of tasks in each status.
    """
    return await service.get_statistics()


@router.get("/{task_id}", response_model=Task)
async def get_task(
    task_id: int,
    service: TaskService = Depends(get_task_service)
):
    """
    Get task details

    Returns detailed information about a specific task.
    """
    task = await service.get_by_id(task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task {task_id} not found"
        )
    return task


@router.get("/{task_id}/position")
async def get_task_position(
    task_id: int,
    service: TaskService = Depends(get_task_service)
):
    """
    Get task position in queue

    Returns the position of a pending task in the processing queue.
    """
    position = await service.get_queue_position(task_id)
    if position is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task {task_id} not found or not pending"
        )
    return {"task_id": task_id, "position": position}


@router.post("/", response_model=Task)
async def create_task(
    task: TaskCreate,
    service: TaskService = Depends(get_task_service)
):
    """
    Create a new task

    Adds a task to the processing queue.
    """
    return await service.create(task)


@router.post("/{task_id}/cancel")
async def cancel_task(
    task_id: int,
    service: TaskService = Depends(get_task_service)
):
    """
    Cancel a pending task

    Only pending tasks can be cancelled.
    """
    success = await service.cancel(task_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Task {task_id} cannot be cancelled (may not exist or not be pending)"
        )
    return {"status": "success", "message": f"Task {task_id} cancelled"}


@router.post("/batch/{batch_id}/cancel")
async def cancel_batch(
    batch_id: str,
    service: TaskService = Depends(get_task_service)
):
    """
    Cancel all pending tasks in a batch

    Cancels all pending tasks that share the given batch ID.
    """
    cancelled = await service.cancel_batch(batch_id)
    return {"status": "success", "cancelled": cancelled}


@router.delete("/{task_id}")
async def delete_task(
    task_id: int,
    service: TaskService = Depends(get_task_service)
):
    """
    Delete a task

    Removes a task from the queue. Task must be completed, failed, or cancelled.
    """
    success = await service.delete(task_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Task {task_id} cannot be deleted (may be in progress)"
        )
    return {"status": "success", "message": f"Task {task_id} deleted"}


@router.post("/clear-completed")
async def clear_completed_tasks(
    older_than_days: int = 7,
    service: TaskService = Depends(get_task_service)
):
    """
    Clear old completed tasks

    Removes completed, failed, and cancelled tasks older than the specified days.
    """
    cleared = await service.clear_completed(older_than_days)
    return {"status": "success", "cleared": cleared}


@router.post("/process-next")
async def process_next_task(
    service: TaskService = Depends(get_task_service)
):
    """
    Process the next pending task

    Claims and starts processing the next task in the queue.
    Returns the task being processed or None if queue is empty.
    """
    task = await service.process_next()
    if not task:
        return {"status": "empty", "message": "No pending tasks"}
    return {"status": "processing", "task": task}


@router.get("/batch/{batch_id}", response_model=list[Task])
async def get_batch_tasks(
    batch_id: str,
    service: TaskService = Depends(get_task_service)
):
    """
    Get all tasks in a batch

    Returns all tasks that share the given batch ID.
    """
    return await service.get_by_batch(batch_id)


@router.get("/batch/{batch_id}/status")
async def get_batch_status(
    batch_id: str,
    service: TaskService = Depends(get_task_service)
):
    """
    Get batch status summary

    Returns aggregated status of all tasks in a batch.
    """
    return await service.get_batch_status(batch_id)
