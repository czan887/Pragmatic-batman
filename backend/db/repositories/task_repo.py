"""
Task repository for database operations
"""
from datetime import datetime
from typing import Optional
import json

from db.database import execute_and_commit, fetch_one, fetch_all
from db.models import Task, TaskCreate, TaskUpdate, TaskStatus


class TaskRepository:
    """Repository for task database operations"""

    async def get_by_id(self, task_id: int) -> Optional[Task]:
        """Get task by ID"""
        query = '''
            SELECT id, profile_id, task_type, task_data, status, priority,
                   batch_id, created_at, started_at, completed_at, error_message
            FROM tasks
            WHERE id = ?
        '''
        row = await fetch_one(query, (task_id,))
        if row:
            data = dict(row)
            if data['task_data']:
                data['task_data'] = json.loads(data['task_data'])
            return Task(**data)
        return None

    async def get_all(self, limit: int = 100) -> list[Task]:
        """Get all tasks"""
        query = '''
            SELECT id, profile_id, task_type, task_data, status, priority,
                   batch_id, created_at, started_at, completed_at, error_message
            FROM tasks
            ORDER BY priority DESC, created_at ASC
            LIMIT ?
        '''
        rows = await fetch_all(query, (limit,))
        tasks = []
        for row in rows:
            data = dict(row)
            if data['task_data']:
                data['task_data'] = json.loads(data['task_data'])
            tasks.append(Task(**data))
        return tasks

    async def get_by_profile(self, profile_id: str) -> list[Task]:
        """Get all tasks for a profile"""
        query = '''
            SELECT id, profile_id, task_type, task_data, status, priority,
                   batch_id, created_at, started_at, completed_at, error_message
            FROM tasks
            WHERE profile_id = ?
            ORDER BY created_at DESC
        '''
        rows = await fetch_all(query, (profile_id,))
        tasks = []
        for row in rows:
            data = dict(row)
            if data['task_data']:
                data['task_data'] = json.loads(data['task_data'])
            tasks.append(Task(**data))
        return tasks

    async def get_pending(self, limit: int = 50) -> list[Task]:
        """Get pending tasks ordered by priority"""
        query = '''
            SELECT id, profile_id, task_type, task_data, status, priority,
                   batch_id, created_at, started_at, completed_at, error_message
            FROM tasks
            WHERE status = 'pending'
            ORDER BY priority DESC, created_at ASC
            LIMIT ?
        '''
        rows = await fetch_all(query, (limit,))
        tasks = []
        for row in rows:
            data = dict(row)
            if data['task_data']:
                data['task_data'] = json.loads(data['task_data'])
            tasks.append(Task(**data))
        return tasks

    async def get_by_batch(self, batch_id: str) -> list[Task]:
        """Get all tasks in a batch"""
        query = '''
            SELECT id, profile_id, task_type, task_data, status, priority,
                   batch_id, created_at, started_at, completed_at, error_message
            FROM tasks
            WHERE batch_id = ?
            ORDER BY created_at ASC
        '''
        rows = await fetch_all(query, (batch_id,))
        tasks = []
        for row in rows:
            data = dict(row)
            if data['task_data']:
                data['task_data'] = json.loads(data['task_data'])
            tasks.append(Task(**data))
        return tasks

    async def create(self, task: TaskCreate) -> Task:
        """Create a new task"""
        query = '''
            INSERT INTO tasks (profile_id, task_type, task_data, status,
                              priority, batch_id, created_at)
            VALUES (?, ?, ?, 'pending', ?, ?, ?)
        '''
        task_data = json.dumps(task.task_data) if task.task_data else None
        task_id = await execute_and_commit(query, (
            task.profile_id,
            task.task_type.value,
            task_data,
            task.priority,
            task.batch_id,
            datetime.now()
        ))
        return await self.get_by_id(task_id)

    async def create_batch(self, tasks: list[TaskCreate]) -> list[Task]:
        """Create multiple tasks in a batch"""
        created_tasks = []
        for task in tasks:
            created = await self.create(task)
            created_tasks.append(created)
        return created_tasks

    async def update_status(
        self,
        task_id: int,
        status: TaskStatus,
        error_message: Optional[str] = None
    ) -> Optional[Task]:
        """Update task status"""
        now = datetime.now()

        if status == TaskStatus.IN_PROGRESS:
            query = '''
                UPDATE tasks
                SET status = ?, started_at = ?
                WHERE id = ?
            '''
            await execute_and_commit(query, (status.value, now, task_id))
        elif status in [TaskStatus.COMPLETED, TaskStatus.FAILED]:
            query = '''
                UPDATE tasks
                SET status = ?, completed_at = ?, error_message = ?
                WHERE id = ?
            '''
            await execute_and_commit(query, (status.value, now, error_message, task_id))
        else:
            query = '''
                UPDATE tasks
                SET status = ?
                WHERE id = ?
            '''
            await execute_and_commit(query, (status.value, task_id))

        return await self.get_by_id(task_id)

    async def claim_next(self) -> Optional[Task]:
        """Claim the next pending task for processing"""
        # Get next pending task
        query = '''
            SELECT id FROM tasks
            WHERE status = 'pending'
            ORDER BY priority DESC, created_at ASC
            LIMIT 1
        '''
        row = await fetch_one(query)

        if not row:
            return None

        task_id = row['id']
        return await self.update_status(task_id, TaskStatus.IN_PROGRESS)

    async def cancel_batch(self, batch_id: str) -> int:
        """Cancel all pending tasks in a batch"""
        query = '''
            UPDATE tasks
            SET status = 'cancelled'
            WHERE batch_id = ? AND status = 'pending'
        '''
        await execute_and_commit(query, (batch_id,))

        # Get count of cancelled
        count_query = '''
            SELECT COUNT(*) as count FROM tasks
            WHERE batch_id = ? AND status = 'cancelled'
        '''
        row = await fetch_one(count_query)
        return row['count'] if row else 0

    async def delete(self, task_id: int) -> bool:
        """Delete a task"""
        query = "DELETE FROM tasks WHERE id = ?"
        await execute_and_commit(query, (task_id,))
        return True

    async def clear_completed(self, older_than_days: int = 7) -> int:
        """Clear old completed tasks"""
        query = '''
            DELETE FROM tasks
            WHERE status IN ('completed', 'cancelled', 'failed')
            AND completed_at < datetime('now', '-' || ? || ' days')
        '''
        await execute_and_commit(query, (older_than_days,))

        # This is approximate since SQLite doesn't return affected rows easily
        return 0

    async def get_statistics(self) -> dict:
        """Get task statistics"""
        query = '''
            SELECT
                status,
                COUNT(*) as count
            FROM tasks
            GROUP BY status
        '''
        rows = await fetch_all(query)

        stats = {
            'pending': 0,
            'in_progress': 0,
            'completed': 0,
            'failed': 0,
            'cancelled': 0
        }

        for row in rows:
            stats[row['status']] = row['count']

        stats['total'] = sum(stats.values())
        return stats

    async def get_queue_position(self, task_id: int) -> Optional[int]:
        """Get position of task in the queue"""
        task = await self.get_by_id(task_id)
        if not task or task.status != TaskStatus.PENDING:
            return None

        query = '''
            SELECT COUNT(*) as position
            FROM tasks
            WHERE status = 'pending'
            AND (priority > ? OR (priority = ? AND created_at < ?))
        '''
        row = await fetch_one(query, (task.priority, task.priority, task.created_at))
        return row['position'] + 1 if row else None
