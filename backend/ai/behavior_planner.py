"""
Human-like behavior planning for Twitter automation
"""
import random
from datetime import datetime, timedelta
from typing import Optional

from pydantic import BaseModel

from config import get_settings
from utils.logger import setup_logger

logger = setup_logger(__name__)


class PlannedAction(BaseModel):
    """A planned action in the session"""
    task_type: str
    target: Optional[str] = None
    scheduled_at: float  # Seconds from session start
    delay_before: float  # Delay in seconds before this action


class PlannedBreak(BaseModel):
    """A planned break in the session"""
    at_action: int  # After which action number
    duration: float  # Break duration in seconds


class SessionPlan(BaseModel):
    """Complete session plan"""
    start_time: datetime
    end_time: datetime
    actions: list[PlannedAction]
    breaks: list[PlannedBreak]
    estimated_duration_minutes: float


class BehaviorPlanner:
    """
    Plans human-like behavior patterns for Twitter automation

    Creates session plans with:
    - Natural timing variations
    - Random breaks (like a human checking phone, getting coffee, etc.)
    - Varied action sequences
    - Realistic pacing
    """

    def __init__(self):
        self.settings = get_settings()
        self.session_history: list[dict] = []

    def plan_session(
        self,
        tasks: list[dict],
        duration_minutes: int = 120,
        intensity: str = "normal"
    ) -> SessionPlan:
        """
        Plan a session with human-like behavior patterns

        Args:
            tasks: List of task dictionaries with 'type', 'target', 'count'
            duration_minutes: Total session duration
            intensity: Activity intensity ('light', 'normal', 'heavy')

        Returns:
            SessionPlan with scheduled actions and breaks
        """
        start_time = datetime.now()
        end_time = start_time + timedelta(minutes=duration_minutes)

        # Calculate total actions
        total_actions = sum(t.get("count", 1) for t in tasks)

        if total_actions == 0:
            return SessionPlan(
                start_time=start_time,
                end_time=end_time,
                actions=[],
                breaks=[],
                estimated_duration_minutes=0
            )

        # Adjust timing based on intensity
        intensity_multipliers = {
            "light": 1.5,   # More time between actions
            "normal": 1.0,
            "heavy": 0.7    # Less time between actions
        }
        multiplier = intensity_multipliers.get(intensity, 1.0)

        # Calculate base delay between actions
        total_seconds = duration_minutes * 60
        avg_delay = (total_seconds / total_actions) * multiplier

        # Plan actions
        actions = []
        breaks = []
        current_time = 0.0
        action_count = 0

        # Break parameters
        min_actions_before_break = 10
        max_actions_before_break = 25
        next_break_at = random.randint(min_actions_before_break, max_actions_before_break)

        for task in tasks:
            task_type = task.get("type", "unknown")
            target = task.get("target")
            count = task.get("count", 1)

            for i in range(count):
                # Calculate delay with natural variation
                delay = self._calculate_delay(avg_delay)

                actions.append(PlannedAction(
                    task_type=task_type,
                    target=target,
                    scheduled_at=current_time,
                    delay_before=delay
                ))

                current_time += delay
                action_count += 1

                # Add break if needed
                if action_count >= next_break_at:
                    break_duration = self._calculate_break_duration()
                    breaks.append(PlannedBreak(
                        at_action=action_count,
                        duration=break_duration
                    ))
                    current_time += break_duration
                    next_break_at = action_count + random.randint(
                        min_actions_before_break,
                        max_actions_before_break
                    )

        # Calculate actual duration
        estimated_duration = current_time / 60

        logger.info(
            f"Session planned: {len(actions)} actions, {len(breaks)} breaks, "
            f"~{estimated_duration:.1f} minutes"
        )

        return SessionPlan(
            start_time=start_time,
            end_time=start_time + timedelta(seconds=current_time),
            actions=actions,
            breaks=breaks,
            estimated_duration_minutes=estimated_duration
        )

    def _calculate_delay(self, base_delay: float) -> float:
        """
        Calculate delay with natural human-like variation

        Uses a log-normal distribution to simulate human timing,
        where most actions are near the base delay but occasionally
        there are longer pauses.
        """
        # Base random variation (gaussian)
        variation = random.gauss(1.0, 0.3)
        delay = base_delay * variation

        # Clamp to reasonable bounds
        min_delay = self.settings.min_action_delay
        max_delay = base_delay * 3

        delay = max(min_delay, min(delay, max_delay))

        # Occasional longer pause (simulating distraction)
        if random.random() < 0.1:  # 10% chance
            delay += random.uniform(5, 15)

        # Rare very long pause (phone call, bathroom, etc.)
        if random.random() < 0.02:  # 2% chance
            delay += random.uniform(30, 120)

        return delay

    def _calculate_break_duration(self) -> float:
        """Calculate a natural break duration"""
        # Most breaks are short (checking phone, etc.)
        base_duration = random.gauss(60, 30)  # 60 seconds average

        # Sometimes longer breaks
        if random.random() < 0.2:  # 20% chance
            base_duration = random.uniform(120, 300)  # 2-5 minutes

        return max(30, base_duration)  # Minimum 30 seconds

    def get_next_delay(
        self,
        last_action_type: Optional[str] = None,
        next_action_type: Optional[str] = None
    ) -> float:
        """
        Get randomized delay for next action

        Args:
            last_action_type: Type of last action performed
            next_action_type: Type of next action to perform

        Returns:
            Delay in seconds
        """
        settings = self.settings
        base = random.uniform(settings.min_action_delay, settings.max_action_delay)

        # Adjust based on action type transitions
        if last_action_type and next_action_type:
            if last_action_type == next_action_type:
                # Same action type - slightly faster
                base *= 0.8
            elif last_action_type in ["follow", "unfollow"] and next_action_type in ["follow", "unfollow"]:
                # Follow actions in sequence
                base *= 0.9
            elif next_action_type == "comment":
                # Comments take longer (thinking time)
                base *= 1.5

        # Add occasional longer pauses
        if random.random() < 0.1:
            base += random.uniform(5, 15)

        return max(settings.min_action_delay, base)

    def should_take_break(self, actions_since_break: int) -> tuple[bool, float]:
        """
        Decide if a break should be taken

        Args:
            actions_since_break: Number of actions since last break

        Returns:
            Tuple of (should_break, break_duration)
        """
        # Probability increases with more actions
        base_probability = min(0.3, actions_since_break / 50)

        # Add randomness
        if random.random() < base_probability:
            duration = self._calculate_break_duration()
            return True, duration

        return False, 0

    def get_session_schedule(self, timezone_offset: int = 0) -> dict:
        """
        Get optimal session schedule based on typical Twitter activity patterns

        Args:
            timezone_offset: Hours offset from UTC

        Returns:
            Dictionary with recommended session windows
        """
        # Peak Twitter engagement times (in local time)
        weekday_peaks = [
            (8, 10),    # Morning commute
            (12, 14),   # Lunch break
            (17, 19),   # Evening commute
            (20, 23),   # Evening leisure
        ]

        weekend_peaks = [
            (10, 12),   # Late morning
            (14, 17),   # Afternoon
            (19, 23),   # Evening
        ]

        current_hour = (datetime.now().hour + timezone_offset) % 24
        is_weekend = datetime.now().weekday() >= 5

        peaks = weekend_peaks if is_weekend else weekday_peaks

        # Find current or next peak
        current_peak = None
        next_peak = None

        for start, end in peaks:
            if start <= current_hour < end:
                current_peak = (start, end)
                break
            elif current_hour < start:
                next_peak = (start, end)
                break

        if not next_peak and peaks:
            next_peak = peaks[0]  # Tomorrow's first peak

        return {
            "is_peak_time": current_peak is not None,
            "current_peak": current_peak,
            "next_peak": next_peak,
            "recommended_intensity": "heavy" if current_peak else "normal",
            "is_weekend": is_weekend
        }

    def randomize_action_order(self, actions: list[dict]) -> list[dict]:
        """
        Randomize action order while keeping related actions grouped

        Args:
            actions: List of action dictionaries

        Returns:
            Shuffled list maintaining some grouping
        """
        if len(actions) <= 2:
            return actions

        # Group by type
        groups = {}
        for action in actions:
            action_type = action.get("type", "other")
            if action_type not in groups:
                groups[action_type] = []
            groups[action_type].append(action)

        # Shuffle within groups
        for group in groups.values():
            random.shuffle(group)

        # Interleave groups
        result = []
        group_lists = list(groups.values())
        random.shuffle(group_lists)

        while any(group_lists):
            for group in group_lists[:]:
                if group:
                    result.append(group.pop(0))
                if not group:
                    group_lists.remove(group)

        return result
