"""
Action repository for database operations
"""
from datetime import datetime
from typing import Optional
from loguru import logger

from db.database import execute_and_commit, fetch_one, fetch_all
from db.models import Action, ActionCreate, ActionUpdate, ActionBreakdown
from db.repositories.stats_repo import StatsRepository
from db.repositories.session_repo import SessionRepository


class ActionRepository:
    """Repository for action database operations"""

    async def get_by_id(self, action_id: int) -> Optional[Action]:
        """Get action by ID"""
        query = '''
            SELECT id, profile_id, action_type, action_name,
                   assigned_count, completed_count, failed_count,
                   date_created, last_updated
            FROM actions
            WHERE id = ?
        '''
        row = await fetch_one(query, (action_id,))
        if row:
            return Action(**dict(row))
        return None

    async def get_by_profile(self, profile_id: str) -> list[Action]:
        """Get all actions for a profile"""
        query = '''
            SELECT id, profile_id, action_type, action_name,
                   assigned_count, completed_count, failed_count,
                   date_created, last_updated
            FROM actions
            WHERE profile_id = ?
            ORDER BY last_updated DESC
        '''
        rows = await fetch_all(query, (profile_id,))
        return [Action(**dict(row)) for row in rows]

    async def find_or_create(
        self,
        profile_id: str,
        action_type: str,
        action_name: str
    ) -> Action:
        """Find existing action or create new one"""
        query = '''
            SELECT id, profile_id, action_type, action_name,
                   assigned_count, completed_count, failed_count,
                   date_created, last_updated
            FROM actions
            WHERE profile_id = ? AND action_type = ? AND action_name = ?
        '''
        row = await fetch_one(query, (profile_id, action_type, action_name))

        if row:
            return Action(**dict(row))

        # Create new action
        insert_query = '''
            INSERT INTO actions (profile_id, action_type, action_name,
                                 assigned_count, date_created, last_updated)
            VALUES (?, ?, ?, 0, ?, ?)
        '''
        now = datetime.now()
        action_id = await execute_and_commit(insert_query, (
            profile_id, action_type, action_name, now, now
        ))
        return await self.get_by_id(action_id)

    async def log_assigned(
        self,
        profile_id: str,
        action_type: str,
        action_name: str,
        count: int = 1
    ) -> Action:
        """Log actions assigned to a profile"""
        action = await self.find_or_create(profile_id, action_type, action_name)

        query = '''
            UPDATE actions
            SET assigned_count = assigned_count + ?, last_updated = ?
            WHERE id = ?
        '''
        await execute_and_commit(query, (count, datetime.now(), action.id))
        return await self.get_by_id(action.id)

    async def log_completed(
        self,
        profile_id: str,
        action_type: str,
        action_name: str,
        success: bool = True,
        error_message: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> Action:
        """Log action completion (success or failure)"""
        action = await self.find_or_create(profile_id, action_type, action_name)

        if success:
            query = '''
                UPDATE actions
                SET completed_count = completed_count + 1, last_updated = ?
                WHERE id = ?
            '''
        else:
            query = '''
                UPDATE actions
                SET failed_count = failed_count + 1, last_updated = ?
                WHERE id = ?
            '''

        await execute_and_commit(query, (datetime.now(), action.id))

        # Update daily stats
        try:
            stats_repo = StatsRepository()
            today = datetime.now().strftime("%Y-%m-%d")
            await stats_repo.increment_stat(today, action_type, profile_id, success)
        except Exception as e:
            logger.warning(f"Failed to update daily stats for {action_type}: {e}")

        # Update session tracking if a session is active
        if session_id:
            try:
                session_repo = SessionRepository()
                await session_repo.log_session_action(
                    session_id, action_type, success,
                    error_message if not success else None
                )
            except Exception as e:
                logger.warning(f"Failed to update session {session_id}: {e}")

        return await self.get_by_id(action.id)

    async def get_statistics(self) -> dict:
        """Get overall action statistics"""
        # Total statistics
        total_query = '''
            SELECT
                COUNT(DISTINCT profile_id) as total_profiles,
                SUM(assigned_count) as total_assigned,
                SUM(completed_count) as total_completed,
                SUM(failed_count) as total_failed
            FROM actions
        '''
        total_row = await fetch_one(total_query)

        # Action breakdown
        breakdown_query = '''
            SELECT
                action_type,
                action_name,
                SUM(assigned_count) as assigned,
                SUM(completed_count) as completed,
                SUM(failed_count) as failed
            FROM actions
            GROUP BY action_type, action_name
            ORDER BY assigned DESC
        '''
        breakdown_rows = await fetch_all(breakdown_query)

        total_assigned = total_row['total_assigned'] or 0
        total_completed = total_row['total_completed'] or 0
        total_failed = total_row['total_failed'] or 0

        return {
            'total_stats': {
                'total_profiles': total_row['total_profiles'] or 0,
                'total_assigned': total_assigned,
                'total_completed': total_completed,
                'total_failed': total_failed,
                'success_rate': (total_completed / total_assigned * 100) if total_assigned > 0 else 0
            },
            'action_breakdown': [
                ActionBreakdown(
                    action_type=row['action_type'],
                    action_name=row['action_name'],
                    assigned=row['assigned'] or 0,
                    completed=row['completed'] or 0,
                    failed=row['failed'] or 0,
                    success_rate=(row['completed'] / row['assigned'] * 100) if row['assigned'] else 0
                ).model_dump()
                for row in breakdown_rows
            ]
        }

    async def get_today_statistics(self) -> dict:
        """Get today's action statistics"""
        query = '''
            SELECT
                SUM(assigned_count) as assigned,
                SUM(completed_count) as completed,
                SUM(failed_count) as failed
            FROM actions
            WHERE DATE(last_updated) = DATE('now')
        '''
        row = await fetch_one(query)

        return {
            'assigned': row['assigned'] or 0,
            'completed': row['completed'] or 0,
            'failed': row['failed'] or 0
        }

    async def clear_for_profile(self, profile_id: str) -> bool:
        """Clear all actions for a profile"""
        query = "DELETE FROM actions WHERE profile_id = ?"
        await execute_and_commit(query, (profile_id,))
        return True
