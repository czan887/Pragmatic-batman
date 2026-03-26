"""
Stats API routes for tracking daily/weekly/monthly/yearly statistics
"""
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, Query

from db.models import DailyStats, StatsTrend, StatsRangeResponse, StatsSummaryResponse
from db.repositories.stats_repo import StatsRepository
from api.dependencies import get_stats_repo

router = APIRouter()


@router.get("/daily", response_model=DailyStats)
async def get_daily_stats(
    date: Optional[str] = Query(None, description="Date in YYYY-MM-DD format, defaults to today"),
    profile_id: Optional[str] = Query(None, description="Filter by profile ID"),
    stats_repo: StatsRepository = Depends(get_stats_repo)
):
    """
    Get daily statistics

    Returns action statistics for a specific day.
    If no date is provided, returns today's stats.
    """
    if not date:
        date = datetime.now().strftime("%Y-%m-%d")

    return await stats_repo.get_daily_stats(date, profile_id)


@router.get("/range", response_model=StatsRangeResponse)
async def get_stats_range(
    start_date: str = Query(..., description="Start date in YYYY-MM-DD format"),
    end_date: str = Query(..., description="End date in YYYY-MM-DD format"),
    granularity: str = Query("daily", description="Granularity: daily, weekly, or monthly"),
    profile_id: Optional[str] = Query(None, description="Filter by profile ID"),
    stats_repo: StatsRepository = Depends(get_stats_repo)
):
    """
    Get statistics for a date range

    Returns aggregated statistics for a date range with specified granularity.
    """
    stats = await stats_repo.get_stats_range(start_date, end_date, profile_id, granularity)

    # Calculate totals
    total = DailyStats(
        date=f"{start_date} to {end_date}",
        profile_id=profile_id,
        follows_count=sum(s.follows_count for s in stats),
        unfollows_count=sum(s.unfollows_count for s in stats),
        likes_count=sum(s.likes_count for s in stats),
        retweets_count=sum(s.retweets_count for s in stats),
        comments_count=sum(s.comments_count for s in stats),
        tweets_posted_count=sum(s.tweets_posted_count for s in stats),
        total_actions=sum(s.total_actions for s in stats),
        successful_actions=sum(s.successful_actions for s in stats),
        failed_actions=sum(s.failed_actions for s in stats),
    )

    return StatsRangeResponse(
        stats=stats,
        start_date=start_date,
        end_date=end_date,
        granularity=granularity,
        total=total
    )


@router.get("/trends", response_model=StatsTrend)
async def get_trends(
    period: str = Query("daily", description="Period to compare: daily, weekly, or monthly"),
    stats_repo: StatsRepository = Depends(get_stats_repo)
):
    """
    Get trend comparisons

    Compares current period statistics with the previous period.
    """
    return await stats_repo.get_trends(period)


@router.get("/summary", response_model=StatsSummaryResponse)
async def get_summary(
    stats_repo: StatsRepository = Depends(get_stats_repo)
):
    """
    Get summary statistics

    Returns aggregated stats for today, this week, this month, this year, and all time.
    """
    summary = await stats_repo.get_summary()
    return StatsSummaryResponse(**summary)


@router.get("/weekly")
async def get_weekly_stats(
    weeks_back: int = Query(4, ge=1, le=52, description="Number of weeks to look back"),
    stats_repo: StatsRepository = Depends(get_stats_repo)
):
    """
    Get weekly aggregated statistics

    Returns statistics aggregated by week.
    """
    return await stats_repo.get_weekly_stats(weeks_back)


@router.get("/monthly")
async def get_monthly_stats(
    months_back: int = Query(12, ge=1, le=24, description="Number of months to look back"),
    stats_repo: StatsRepository = Depends(get_stats_repo)
):
    """
    Get monthly aggregated statistics

    Returns statistics aggregated by month.
    """
    return await stats_repo.get_monthly_stats(months_back)


@router.get("/yearly")
async def get_yearly_stats(
    stats_repo: StatsRepository = Depends(get_stats_repo)
):
    """
    Get yearly aggregated statistics

    Returns statistics aggregated by year.
    """
    return await stats_repo.get_yearly_stats()
