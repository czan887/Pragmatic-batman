"""
Stats repository for tracking daily statistics
"""
from datetime import datetime, timedelta
from typing import Optional

from db.database import execute_and_commit, fetch_one, fetch_all
from db.models import DailyStats, TrendChange, StatsTrend


class StatsRepository:
    """Repository for daily stats database operations"""

    ACTION_TYPE_MAP = {
        "follow": "follows_count",
        "unfollow": "unfollows_count",
        "like": "likes_count",
        "retweet": "retweets_count",
        "comment": "comments_count",
        "post_tweet": "tweets_posted_count",
    }

    async def get_daily_stats(
        self, date: str, profile_id: Optional[str] = None
    ) -> Optional[DailyStats]:
        """Get stats for a specific day"""
        if profile_id:
            query = '''
                SELECT * FROM daily_stats
                WHERE date = ? AND profile_id = ?
            '''
            row = await fetch_one(query, (date, profile_id))
        else:
            # Aggregate all profiles for the date
            query = '''
                SELECT
                    NULL as id,
                    ? as date,
                    NULL as profile_id,
                    COALESCE(SUM(follows_count), 0) as follows_count,
                    COALESCE(SUM(unfollows_count), 0) as unfollows_count,
                    COALESCE(SUM(likes_count), 0) as likes_count,
                    COALESCE(SUM(retweets_count), 0) as retweets_count,
                    COALESCE(SUM(comments_count), 0) as comments_count,
                    COALESCE(SUM(tweets_posted_count), 0) as tweets_posted_count,
                    COALESCE(SUM(total_actions), 0) as total_actions,
                    COALESCE(SUM(successful_actions), 0) as successful_actions,
                    COALESCE(SUM(failed_actions), 0) as failed_actions,
                    MIN(created_at) as created_at,
                    MAX(updated_at) as updated_at
                FROM daily_stats
                WHERE date = ?
            '''
            row = await fetch_one(query, (date, date))

        if row and (row['total_actions'] or row['id']):
            return DailyStats(**dict(row))
        # Return empty stats for the date
        return DailyStats(date=date, profile_id=profile_id)

    async def get_stats_range(
        self,
        start_date: str,
        end_date: str,
        profile_id: Optional[str] = None,
        granularity: str = "daily"
    ) -> list[DailyStats]:
        """Get stats for a date range with optional granularity"""
        if granularity == "daily":
            date_format = "date"
        elif granularity == "weekly":
            date_format = "strftime('%Y-W%W', date)"
        elif granularity == "monthly":
            date_format = "strftime('%Y-%m', date)"
        else:
            date_format = "date"

        if profile_id:
            query = f'''
                SELECT
                    NULL as id,
                    {date_format} as date,
                    profile_id,
                    SUM(follows_count) as follows_count,
                    SUM(unfollows_count) as unfollows_count,
                    SUM(likes_count) as likes_count,
                    SUM(retweets_count) as retweets_count,
                    SUM(comments_count) as comments_count,
                    SUM(tweets_posted_count) as tweets_posted_count,
                    SUM(total_actions) as total_actions,
                    SUM(successful_actions) as successful_actions,
                    SUM(failed_actions) as failed_actions,
                    MIN(created_at) as created_at,
                    MAX(updated_at) as updated_at
                FROM daily_stats
                WHERE date >= ? AND date <= ? AND profile_id = ?
                GROUP BY {date_format}, profile_id
                ORDER BY date ASC
            '''
            rows = await fetch_all(query, (start_date, end_date, profile_id))
        else:
            query = f'''
                SELECT
                    NULL as id,
                    {date_format} as date,
                    NULL as profile_id,
                    SUM(follows_count) as follows_count,
                    SUM(unfollows_count) as unfollows_count,
                    SUM(likes_count) as likes_count,
                    SUM(retweets_count) as retweets_count,
                    SUM(comments_count) as comments_count,
                    SUM(tweets_posted_count) as tweets_posted_count,
                    SUM(total_actions) as total_actions,
                    SUM(successful_actions) as successful_actions,
                    SUM(failed_actions) as failed_actions,
                    MIN(created_at) as created_at,
                    MAX(updated_at) as updated_at
                FROM daily_stats
                WHERE date >= ? AND date <= ?
                GROUP BY {date_format}
                ORDER BY date ASC
            '''
            rows = await fetch_all(query, (start_date, end_date))

        return [DailyStats(**dict(row)) for row in rows]

    async def get_weekly_stats(self, weeks_back: int = 4) -> list[DailyStats]:
        """Get aggregated weekly stats"""
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(weeks=weeks_back)).strftime("%Y-%m-%d")
        return await self.get_stats_range(start_date, end_date, granularity="weekly")

    async def get_monthly_stats(self, months_back: int = 12) -> list[DailyStats]:
        """Get aggregated monthly stats"""
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=months_back * 30)).strftime("%Y-%m-%d")
        return await self.get_stats_range(start_date, end_date, granularity="monthly")

    async def get_yearly_stats(self) -> list[DailyStats]:
        """Get aggregated yearly stats"""
        query = '''
            SELECT
                NULL as id,
                strftime('%Y', date) as date,
                NULL as profile_id,
                SUM(follows_count) as follows_count,
                SUM(unfollows_count) as unfollows_count,
                SUM(likes_count) as likes_count,
                SUM(retweets_count) as retweets_count,
                SUM(comments_count) as comments_count,
                SUM(tweets_posted_count) as tweets_posted_count,
                SUM(total_actions) as total_actions,
                SUM(successful_actions) as successful_actions,
                SUM(failed_actions) as failed_actions,
                MIN(created_at) as created_at,
                MAX(updated_at) as updated_at
            FROM daily_stats
            GROUP BY strftime('%Y', date)
            ORDER BY date ASC
        '''
        rows = await fetch_all(query)
        return [DailyStats(**dict(row)) for row in rows]

    async def increment_stat(
        self,
        date: str,
        action_type: str,
        profile_id: Optional[str] = None,
        success: bool = True
    ) -> DailyStats:
        """Update stats on action completion"""
        # Get the column name for this action type
        action_column = self.ACTION_TYPE_MAP.get(action_type.lower())

        # Check if record exists
        if profile_id:
            check_query = '''
                SELECT id FROM daily_stats WHERE date = ? AND profile_id = ?
            '''
            existing = await fetch_one(check_query, (date, profile_id))
        else:
            check_query = '''
                SELECT id FROM daily_stats WHERE date = ? AND profile_id IS NULL
            '''
            existing = await fetch_one(check_query, (date,))

        now = datetime.now()

        if existing:
            # Update existing record
            if action_column:
                if success:
                    query = f'''
                        UPDATE daily_stats
                        SET {action_column} = {action_column} + 1,
                            total_actions = total_actions + 1,
                            successful_actions = successful_actions + 1,
                            updated_at = ?
                        WHERE id = ?
                    '''
                else:
                    query = f'''
                        UPDATE daily_stats
                        SET {action_column} = {action_column} + 1,
                            total_actions = total_actions + 1,
                            failed_actions = failed_actions + 1,
                            updated_at = ?
                        WHERE id = ?
                    '''
            else:
                # Unknown action type - just update totals
                if success:
                    query = '''
                        UPDATE daily_stats
                        SET total_actions = total_actions + 1,
                            successful_actions = successful_actions + 1,
                            updated_at = ?
                        WHERE id = ?
                    '''
                else:
                    query = '''
                        UPDATE daily_stats
                        SET total_actions = total_actions + 1,
                            failed_actions = failed_actions + 1,
                            updated_at = ?
                        WHERE id = ?
                    '''
            await execute_and_commit(query, (now, existing['id']))
        else:
            # Insert new record
            success_count = 1 if success else 0
            fail_count = 0 if success else 1

            columns = ['date', 'profile_id', 'total_actions', 'successful_actions', 'failed_actions', 'created_at', 'updated_at']
            values = [date, profile_id, 1, success_count, fail_count, now, now]
            placeholders = ['?'] * len(values)

            if action_column:
                columns.append(action_column)
                values.append(1)
                placeholders.append('?')

            query = f'''
                INSERT INTO daily_stats ({', '.join(columns)})
                VALUES ({', '.join(placeholders)})
            '''
            await execute_and_commit(query, tuple(values))

        return await self.get_daily_stats(date, profile_id)

    async def get_trends(self, period: str = "daily") -> StatsTrend:
        """Compare current vs previous period"""
        today = datetime.now()

        if period == "daily":
            current_start = today.strftime("%Y-%m-%d")
            current_end = current_start
            previous_start = (today - timedelta(days=1)).strftime("%Y-%m-%d")
            previous_end = previous_start
        elif period == "weekly":
            # Current week (Monday to today)
            current_start = (today - timedelta(days=today.weekday())).strftime("%Y-%m-%d")
            current_end = today.strftime("%Y-%m-%d")
            # Previous week
            previous_start = (today - timedelta(days=today.weekday() + 7)).strftime("%Y-%m-%d")
            previous_end = (today - timedelta(days=today.weekday() + 1)).strftime("%Y-%m-%d")
        elif period == "monthly":
            # Current month
            current_start = today.replace(day=1).strftime("%Y-%m-%d")
            current_end = today.strftime("%Y-%m-%d")
            # Previous month
            first_of_month = today.replace(day=1)
            last_month_end = first_of_month - timedelta(days=1)
            previous_start = last_month_end.replace(day=1).strftime("%Y-%m-%d")
            previous_end = last_month_end.strftime("%Y-%m-%d")
        else:
            # Default to daily
            current_start = today.strftime("%Y-%m-%d")
            current_end = current_start
            previous_start = (today - timedelta(days=1)).strftime("%Y-%m-%d")
            previous_end = previous_start

        current_stats = await self._aggregate_range(current_start, current_end)
        previous_stats = await self._aggregate_range(previous_start, previous_end)

        # Calculate changes
        changes = {}
        metrics = [
            'follows_count', 'unfollows_count', 'likes_count',
            'retweets_count', 'comments_count', 'tweets_posted_count',
            'total_actions', 'successful_actions', 'failed_actions'
        ]

        for metric in metrics:
            current_val = getattr(current_stats, metric, 0) or 0
            previous_val = getattr(previous_stats, metric, 0) or 0

            diff = current_val - previous_val
            if previous_val > 0:
                percentage = (diff / previous_val) * 100
            elif current_val > 0:
                percentage = 100.0
            else:
                percentage = 0.0

            if diff > 0:
                direction = "up"
            elif diff < 0:
                direction = "down"
            else:
                direction = "same"

            changes[metric] = TrendChange(
                value=float(diff),
                percentage=round(percentage, 1),
                direction=direction
            )

        return StatsTrend(
            current=current_stats,
            previous=previous_stats,
            changes=changes
        )

    async def _aggregate_range(self, start_date: str, end_date: str) -> DailyStats:
        """Aggregate stats for a date range"""
        query = '''
            SELECT
                NULL as id,
                ? as date,
                NULL as profile_id,
                COALESCE(SUM(follows_count), 0) as follows_count,
                COALESCE(SUM(unfollows_count), 0) as unfollows_count,
                COALESCE(SUM(likes_count), 0) as likes_count,
                COALESCE(SUM(retweets_count), 0) as retweets_count,
                COALESCE(SUM(comments_count), 0) as comments_count,
                COALESCE(SUM(tweets_posted_count), 0) as tweets_posted_count,
                COALESCE(SUM(total_actions), 0) as total_actions,
                COALESCE(SUM(successful_actions), 0) as successful_actions,
                COALESCE(SUM(failed_actions), 0) as failed_actions,
                MIN(created_at) as created_at,
                MAX(updated_at) as updated_at
            FROM daily_stats
            WHERE date >= ? AND date <= ?
        '''
        row = await fetch_one(query, (start_date, start_date, end_date))

        if row:
            return DailyStats(**dict(row))
        return DailyStats(date=start_date)

    async def get_summary(self) -> dict:
        """Get summary stats for today, week, month, year, and all time"""
        today = datetime.now()

        # Today
        today_stats = await self.get_daily_stats(today.strftime("%Y-%m-%d"))

        # This week
        week_start = (today - timedelta(days=today.weekday())).strftime("%Y-%m-%d")
        week_stats = await self._aggregate_range(week_start, today.strftime("%Y-%m-%d"))

        # This month
        month_start = today.replace(day=1).strftime("%Y-%m-%d")
        month_stats = await self._aggregate_range(month_start, today.strftime("%Y-%m-%d"))

        # This year
        year_start = today.replace(month=1, day=1).strftime("%Y-%m-%d")
        year_stats = await self._aggregate_range(year_start, today.strftime("%Y-%m-%d"))

        # All time
        all_time_stats = await self._aggregate_range("1970-01-01", today.strftime("%Y-%m-%d"))

        return {
            "today": today_stats,
            "this_week": week_stats,
            "this_month": month_stats,
            "this_year": year_stats,
            "all_time": all_time_stats
        }
