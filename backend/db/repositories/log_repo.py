"""
Log repository for database operations
"""
from datetime import datetime, timedelta
from typing import Optional
import aiosqlite

from db.database import get_db, execute_and_commit, fetch_all, fetch_one


class LogRepository:
    """Repository for managing logs in database"""

    async def save_log(
        self,
        level: str,
        message: str,
        profile_id: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> int:
        """
        Save a log entry to the database

        Args:
            level: Log level (INFO, WARNING, ERROR, SUCCESS, DEBUG)
            message: Log message
            profile_id: Optional profile ID
            session_id: Optional session ID

        Returns:
            ID of the inserted log entry
        """
        query = """
            INSERT INTO session_logs (profile_id, session_id, level, message, timestamp)
            VALUES (?, ?, ?, ?, ?)
        """
        log_id = await execute_and_commit(
            query,
            (profile_id, session_id, level.upper(), message, datetime.now().isoformat())
        )
        return log_id

    async def get_logs(
        self,
        limit: int = 100,
        offset: int = 0,
        level: Optional[str] = None,
        profile_id: Optional[str] = None,
        since: Optional[datetime] = None
    ) -> list[dict]:
        """
        Get logs with optional filtering

        Args:
            limit: Maximum number of logs to return
            offset: Number of logs to skip
            level: Filter by log level
            profile_id: Filter by profile ID
            since: Filter logs since this timestamp

        Returns:
            List of log entries
        """
        conditions = []
        params = []

        if level:
            conditions.append("level = ?")
            params.append(level.upper())

        if profile_id:
            conditions.append("profile_id = ?")
            params.append(profile_id)

        if since:
            conditions.append("timestamp >= ?")
            params.append(since.isoformat())

        where_clause = " AND ".join(conditions) if conditions else "1=1"

        query = f"""
            SELECT id, profile_id, session_id, level, message, timestamp
            FROM session_logs
            WHERE {where_clause}
            ORDER BY timestamp DESC
            LIMIT ? OFFSET ?
        """
        params.extend([limit, offset])

        rows = await fetch_all(query, tuple(params))
        return [dict(row) for row in rows]

    async def get_logs_by_profile(self, profile_id: str, limit: int = 50) -> list[dict]:
        """Get logs for a specific profile"""
        return await self.get_logs(limit=limit, profile_id=profile_id)

    async def get_recent_errors(self, limit: int = 20) -> list[dict]:
        """Get recent error logs"""
        return await self.get_logs(limit=limit, level="ERROR")

    async def get_log_stats(self, since: Optional[datetime] = None) -> dict:
        """
        Get log statistics

        Args:
            since: Get stats since this timestamp (default: last 24 hours)

        Returns:
            Dictionary with log counts by level
        """
        if since is None:
            since = datetime.now() - timedelta(hours=24)

        query = """
            SELECT level, COUNT(*) as count
            FROM session_logs
            WHERE timestamp >= ?
            GROUP BY level
        """
        rows = await fetch_all(query, (since.isoformat(),))

        stats = {
            "total": 0,
            "INFO": 0,
            "WARNING": 0,
            "ERROR": 0,
            "SUCCESS": 0,
            "DEBUG": 0
        }

        for row in rows:
            level = row["level"]
            count = row["count"]
            stats[level] = count
            stats["total"] += count

        return stats

    async def cleanup_old_logs(self, days: int = 30) -> int:
        """
        Delete logs older than specified days

        Args:
            days: Delete logs older than this many days

        Returns:
            Number of deleted logs
        """
        cutoff = datetime.now() - timedelta(days=days)

        # Get count first
        count_query = "SELECT COUNT(*) as count FROM session_logs WHERE timestamp < ?"
        result = await fetch_one(count_query, (cutoff.isoformat(),))
        count = result["count"] if result else 0

        # Delete old logs
        delete_query = "DELETE FROM session_logs WHERE timestamp < ?"
        await execute_and_commit(delete_query, (cutoff.isoformat(),))

        return count

    async def search_logs(self, search_term: str, limit: int = 50) -> list[dict]:
        """
        Search logs by message content

        Args:
            search_term: Term to search for in log messages
            limit: Maximum number of results

        Returns:
            List of matching log entries
        """
        query = """
            SELECT id, profile_id, session_id, level, message, timestamp
            FROM session_logs
            WHERE message LIKE ?
            ORDER BY timestamp DESC
            LIMIT ?
        """
        rows = await fetch_all(query, (f"%{search_term}%", limit))
        return [dict(row) for row in rows]
