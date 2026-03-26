"""
Session repository for tracking bot sessions
"""
import json
import uuid
from datetime import datetime, timedelta
from typing import Optional

from db.database import execute_and_commit, fetch_one, fetch_all
from db.models import SessionSummary, SessionStatus


class SessionRepository:
    """Repository for session database operations"""

    ACTION_TYPE_MAP = {
        "follow": "follows_count",
        "unfollow": "unfollows_count",
        "like": "likes_count",
        "retweet": "retweets_count",
        "comment": "comments_count",
        "post_tweet": "tweets_posted_count",
    }

    async def start_session(self, profile_id: Optional[str] = None) -> str:
        """Create a new session, return session_id"""
        session_id = str(uuid.uuid4())
        now = datetime.now()

        query = '''
            INSERT INTO session_summaries (session_id, profile_id, started_at, status)
            VALUES (?, ?, ?, ?)
        '''
        await execute_and_commit(query, (session_id, profile_id, now, SessionStatus.ACTIVE.value))
        return session_id

    async def end_session(self, session_id: str) -> Optional[SessionSummary]:
        """Mark session complete, compute summary"""
        session = await self.get_session(session_id)
        if not session:
            return None

        now = datetime.now()
        duration = int((now - session.started_at).total_seconds()) if session.started_at else 0

        # Calculate success rate
        total = session.successful_count + session.failed_count
        success_rate = (session.successful_count / total * 100) if total > 0 else 0.0

        query = '''
            UPDATE session_summaries
            SET ended_at = ?, duration_seconds = ?, success_rate = ?, status = ?
            WHERE session_id = ?
        '''
        await execute_and_commit(query, (now, duration, success_rate, SessionStatus.COMPLETED.value, session_id))
        return await self.get_session(session_id)

    async def get_active_session(self, profile_id: Optional[str] = None) -> Optional[SessionSummary]:
        """Get current active session for a profile"""
        if profile_id:
            query = '''
                SELECT * FROM session_summaries
                WHERE profile_id = ? AND status = ?
                ORDER BY started_at DESC
                LIMIT 1
            '''
            row = await fetch_one(query, (profile_id, SessionStatus.ACTIVE.value))
        else:
            query = '''
                SELECT * FROM session_summaries
                WHERE status = ?
                ORDER BY started_at DESC
                LIMIT 1
            '''
            row = await fetch_one(query, (SessionStatus.ACTIVE.value,))

        if row:
            return self._row_to_session(row)
        return None

    async def get_all_active_sessions(self) -> list[SessionSummary]:
        """Get all active sessions"""
        query = '''
            SELECT * FROM session_summaries
            WHERE status = ?
            ORDER BY started_at DESC
        '''
        rows = await fetch_all(query, (SessionStatus.ACTIVE.value,))
        return [self._row_to_session(row) for row in rows]

    async def get_session(self, session_id: str) -> Optional[SessionSummary]:
        """Get session by ID"""
        query = '''
            SELECT * FROM session_summaries WHERE session_id = ?
        '''
        row = await fetch_one(query, (session_id,))
        if row:
            return self._row_to_session(row)
        return None

    async def log_session_action(
        self,
        session_id: str,
        action_type: str,
        success: bool = True,
        error: Optional[str] = None
    ) -> bool:
        """Track action in session"""
        session = await self.get_session(session_id)
        if not session:
            return False

        action_column = self.ACTION_TYPE_MAP.get(action_type.lower())

        # Build update query
        updates = ["total_actions = total_actions + 1"]

        if success:
            updates.append("successful_count = successful_count + 1")
        else:
            updates.append("failed_count = failed_count + 1")

        if action_column:
            updates.append(f"{action_column} = {action_column} + 1")

        # Handle error logging
        if error:
            # Get current errors and append
            current_errors = session.errors or []
            current_errors.append(error)
            new_errors_json = json.dumps(current_errors[-50:])  # Keep last 50 errors
            updates.append("errors_json = ?")
            updates.append("error_count = error_count + 1")

            query = f'''
                UPDATE session_summaries
                SET {', '.join(updates)}
                WHERE session_id = ?
            '''
            await execute_and_commit(query, (new_errors_json, session_id))
        else:
            query = f'''
                UPDATE session_summaries
                SET {', '.join(updates)}
                WHERE session_id = ?
            '''
            await execute_and_commit(query, (session_id,))

        return True

    async def get_session_summary(self, session_id: str) -> Optional[SessionSummary]:
        """Get full summary for a session"""
        return await self.get_session(session_id)

    async def get_session_history(
        self,
        limit: int = 20,
        days: Optional[int] = None,
        profile_id: Optional[str] = None
    ) -> list[SessionSummary]:
        """List recent sessions"""
        conditions = []
        params = []

        if days:
            cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")
            conditions.append("started_at >= ?")
            params.append(cutoff)

        if profile_id:
            conditions.append("profile_id = ?")
            params.append(profile_id)

        where_clause = " AND ".join(conditions) if conditions else "1=1"

        query = f'''
            SELECT * FROM session_summaries
            WHERE {where_clause}
            ORDER BY started_at DESC
            LIMIT ?
        '''
        params.append(limit)

        rows = await fetch_all(query, tuple(params))
        return [self._row_to_session(row) for row in rows]

    async def get_or_create_active_session(self, profile_id: Optional[str] = None) -> str:
        """Get active session or create a new one"""
        active = await self.get_active_session(profile_id)
        if active:
            return active.session_id
        return await self.start_session(profile_id)

    async def end_stale_sessions(self, timeout_minutes: int = 30) -> int:
        """End sessions that have been inactive for too long"""
        cutoff = datetime.now() - timedelta(minutes=timeout_minutes)

        # Find stale active sessions
        query = '''
            SELECT session_id FROM session_summaries
            WHERE status = ? AND started_at < ?
        '''
        rows = await fetch_all(query, (SessionStatus.ACTIVE.value, cutoff))

        count = 0
        for row in rows:
            session = await self.get_session(row['session_id'])
            if session:
                # Calculate duration
                duration = int((cutoff - session.started_at).total_seconds())
                total = session.successful_count + session.failed_count
                success_rate = (session.successful_count / total * 100) if total > 0 else 0.0

                update_query = '''
                    UPDATE session_summaries
                    SET ended_at = ?, duration_seconds = ?, success_rate = ?, status = ?
                    WHERE session_id = ?
                '''
                await execute_and_commit(update_query, (
                    cutoff, duration, success_rate,
                    SessionStatus.INTERRUPTED.value, row['session_id']
                ))
                count += 1

        return count

    def _row_to_session(self, row) -> SessionSummary:
        """Convert database row to SessionSummary"""
        data = dict(row)

        # Parse datetime fields
        if data.get('started_at') and isinstance(data['started_at'], str):
            data['started_at'] = datetime.fromisoformat(data['started_at'])
        if data.get('ended_at') and isinstance(data['ended_at'], str):
            data['ended_at'] = datetime.fromisoformat(data['ended_at'])

        # Parse status enum
        if data.get('status'):
            data['status'] = SessionStatus(data['status'])

        return SessionSummary(**data)
