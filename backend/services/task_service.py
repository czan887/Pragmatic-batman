"""
Task service - business logic for task queue management
"""
from typing import Optional
import uuid

from db.repositories.task_repo import TaskRepository
from db.repositories.action_repo import ActionRepository
from db.models import Task, TaskCreate, TaskStatus, TaskType
from utils.logger import setup_logger
from api.routes.websocket import broadcast_log

logger = setup_logger(__name__)


class TaskService:
    """
    Service for managing the task queue

    Handles:
    - Task creation and scheduling
    - Task status management
    - Batch operations
    - Queue processing
    """

    def __init__(
        self,
        task_repo: TaskRepository,
        action_repo: ActionRepository
    ):
        self.task_repo = task_repo
        self.action_repo = action_repo

    async def get_all(self, limit: int = 100) -> list[Task]:
        """Get all tasks"""
        return await self.task_repo.get_all(limit)

    async def get_by_id(self, task_id: int) -> Optional[Task]:
        """Get task by ID"""
        return await self.task_repo.get_by_id(task_id)

    async def get_by_status(self, status: TaskStatus, limit: int = 100) -> list[Task]:
        """Get tasks by status"""
        tasks = await self.task_repo.get_all(limit * 2)  # Get more to filter
        return [t for t in tasks if t.status == status][:limit]

    async def get_pending(self, limit: int = 50) -> list[Task]:
        """Get pending tasks"""
        return await self.task_repo.get_pending(limit)

    async def get_by_batch(self, batch_id: str) -> list[Task]:
        """Get all tasks in a batch"""
        return await self.task_repo.get_by_batch(batch_id)

    async def get_statistics(self) -> dict:
        """Get task queue statistics"""
        return await self.task_repo.get_statistics()

    async def get_queue_position(self, task_id: int) -> Optional[int]:
        """Get task position in queue"""
        return await self.task_repo.get_queue_position(task_id)

    async def create(self, task: TaskCreate) -> Task:
        """Create a new task"""
        created = await self.task_repo.create(task)

        logger.info(f"Created task {created.id}: {created.task_type} for profile {created.profile_id}")
        await broadcast_log(
            "INFO",
            f"Task created: {created.task_type}",
            created.profile_id
        )

        return created

    async def create_batch(
        self,
        tasks: list[TaskCreate],
        batch_id: Optional[str] = None
    ) -> list[Task]:
        """Create multiple tasks in a batch"""
        if not batch_id:
            batch_id = str(uuid.uuid4())

        # Add batch_id to all tasks
        for task in tasks:
            task.batch_id = batch_id

        created = await self.task_repo.create_batch(tasks)

        logger.info(f"Created batch {batch_id} with {len(created)} tasks")
        await broadcast_log("INFO", f"Created batch with {len(created)} tasks")

        return created

    async def update_status(
        self,
        task_id: int,
        status: TaskStatus,
        error_message: Optional[str] = None
    ) -> Optional[Task]:
        """Update task status"""
        task = await self.task_repo.update_status(task_id, status, error_message)

        if task:
            from api.routes.websocket import manager
            await manager.broadcast_task_update(task_id, status.value, {
                "profile_id": task.profile_id,
                "task_type": task.task_type
            })

        return task

    async def cancel(self, task_id: int) -> bool:
        """Cancel a pending task"""
        task = await self.task_repo.get_by_id(task_id)
        if not task or task.status != TaskStatus.PENDING:
            return False

        await self.task_repo.update_status(task_id, TaskStatus.CANCELLED)
        logger.info(f"Cancelled task {task_id}")
        await broadcast_log("INFO", f"Task {task_id} cancelled", task.profile_id)

        return True

    async def cancel_batch(self, batch_id: str) -> int:
        """Cancel all pending tasks in a batch"""
        count = await self.task_repo.cancel_batch(batch_id)
        logger.info(f"Cancelled {count} tasks in batch {batch_id}")
        await broadcast_log("INFO", f"Cancelled {count} tasks in batch {batch_id}")
        return count

    async def delete(self, task_id: int) -> bool:
        """Delete a task"""
        task = await self.task_repo.get_by_id(task_id)
        if not task:
            return False

        # Can't delete in-progress tasks
        if task.status == TaskStatus.IN_PROGRESS:
            return False

        await self.task_repo.delete(task_id)
        return True

    async def clear_completed(self, older_than_days: int = 7) -> int:
        """Clear old completed tasks"""
        count = await self.task_repo.clear_completed(older_than_days)
        logger.info(f"Cleared {count} old completed tasks")
        return count

    async def process_next(self) -> Optional[Task]:
        """
        Claim and start processing the next pending task

        This is called by the task processor to get the next task.
        """
        task = await self.task_repo.claim_next()

        if task:
            logger.info(f"Processing task {task.id}: {task.task_type}")
            await broadcast_log(
                "INFO",
                f"Processing task: {task.task_type}",
                task.profile_id
            )

        return task

    async def complete_task(self, task_id: int, success: bool, error_message: Optional[str] = None):
        """Mark a task as completed or failed"""
        status = TaskStatus.COMPLETED if success else TaskStatus.FAILED
        task = await self.update_status(task_id, status, error_message)

        if task:
            # Log action completion
            await self.action_repo.log_completed(
                task.profile_id,
                task.task_type,
                task.task_data.get("target", "unknown") if task.task_data else "unknown",
                success
            )

            level = "SUCCESS" if success else "ERROR"
            message = f"Task completed: {task.task_type}" if success else f"Task failed: {error_message}"
            await broadcast_log(level, message, task.profile_id)

    async def get_batch_status(self, batch_id: str) -> dict:
        """Get aggregated status of a batch"""
        tasks = await self.task_repo.get_by_batch(batch_id)

        status_counts = {
            "pending": 0,
            "in_progress": 0,
            "completed": 0,
            "failed": 0,
            "cancelled": 0
        }

        for task in tasks:
            status_counts[task.status.value] = status_counts.get(task.status.value, 0) + 1

        total = len(tasks)
        completed = status_counts["completed"]
        failed = status_counts["failed"]

        return {
            "batch_id": batch_id,
            "total": total,
            "status_counts": status_counts,
            "progress": (completed + failed) / total * 100 if total > 0 else 0,
            "success_rate": completed / (completed + failed) * 100 if (completed + failed) > 0 else 0
        }

    async def schedule_follow_batch(
        self,
        profile_id: str,
        usernames: list[str],
        use_ai_analysis: bool = True
    ) -> str:
        """
        Schedule a batch of follow tasks

        Returns:
            Batch ID
        """
        batch_id = str(uuid.uuid4())

        tasks = []
        for username in usernames:
            tasks.append(TaskCreate(
                profile_id=profile_id,
                task_type=TaskType.FOLLOW,
                task_data={
                    "target": username,
                    "use_ai_analysis": use_ai_analysis
                },
                batch_id=batch_id
            ))

        # Log assigned actions
        await self.action_repo.log_assigned(
            profile_id,
            "follow",
            "batch",
            len(usernames)
        )

        await self.create_batch(tasks, batch_id)
        return batch_id
