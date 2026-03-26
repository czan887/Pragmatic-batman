"""
AI-powered profile analyzer for smart follow decisions
"""
from typing import Optional
import json
from datetime import datetime

from anthropic import AsyncAnthropic
from pydantic import BaseModel

from config import get_settings
from utils.logger import setup_logger

logger = setup_logger(__name__)


class ProfileScore(BaseModel):
    """Result of profile analysis"""
    should_follow: bool
    score: float  # 0.0 to 1.0
    reason: str
    flags: list[str] = []  # e.g., ["bot", "spam", "inactive", "quality", "engaged"]


class ProfileAnalyzer:
    """
    AI-powered profile analyzer using Claude

    Analyzes Twitter profiles to determine if they're worth following,
    detecting bots, spam accounts, and inactive users.
    """

    def __init__(self, api_key: Optional[str] = None):
        settings = get_settings()
        self.api_key = api_key or settings.anthropic_api_key

        if not self.api_key:
            logger.warning("No Anthropic API key configured, profile analysis disabled")
            self.client = None
        else:
            self.client = AsyncAnthropic(api_key=self.api_key)

    async def analyze(
        self,
        profile_data: dict,
        criteria: Optional[dict] = None
    ) -> ProfileScore:
        """
        Analyze a Twitter profile using AI

        Args:
            profile_data: Dictionary containing profile information
                - username: str
                - bio: str (optional)
                - followers_count: int
                - following_count: int
                - recent_tweets: list[str] (optional)
                - account_age: str (optional)
            criteria: Optional custom criteria for scoring

        Returns:
            ProfileScore with decision and reasoning
        """
        if not self.client:
            # Return default "yes" if no API configured
            return ProfileScore(
                should_follow=True,
                score=0.5,
                reason="AI analysis unavailable - defaulting to follow",
                flags=["no_analysis"]
            )

        # Build analysis prompt
        prompt = self._build_prompt(profile_data, criteria)

        try:
            response = await self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=300,
                messages=[{"role": "user", "content": prompt}]
            )

            # Parse JSON response
            result_text = response.content[0].text
            result = self._parse_response(result_text)

            logger.info(
                f"Profile analysis for {profile_data.get('username')}: "
                f"score={result.score}, should_follow={result.should_follow}"
            )

            return result

        except Exception as e:
            logger.error(f"Profile analysis failed: {e}")
            return ProfileScore(
                should_follow=True,
                score=0.5,
                reason=f"Analysis error: {str(e)}",
                flags=["error"]
            )

    def _build_prompt(self, profile_data: dict, criteria: Optional[dict]) -> str:
        """Build the analysis prompt"""
        username = profile_data.get('username', 'unknown')
        bio = profile_data.get('bio', 'No bio')
        followers = profile_data.get('followers_count', 0)
        following = profile_data.get('following_count', 0)
        tweets = profile_data.get('recent_tweets', [])
        account_age = profile_data.get('account_age', 'Unknown')

        tweets_text = "\n".join([f"- {t}" for t in tweets[:5]]) if tweets else "No recent tweets"

        # Calculate basic ratio
        ratio = followers / following if following > 0 else 0

        criteria_text = ""
        if criteria:
            criteria_text = f"""
Additional criteria to consider:
- Minimum followers: {criteria.get('min_followers', 0)}
- Maximum following: {criteria.get('max_following', 'no limit')}
- Required keywords in bio: {criteria.get('bio_keywords', 'none')}
- Avoid keywords: {criteria.get('avoid_keywords', 'none')}
"""

        return f"""Analyze this Twitter profile and decide if it's worth following.

**Profile Data:**
- Username: @{username}
- Bio: {bio}
- Followers: {followers:,}
- Following: {following:,}
- Follower/Following Ratio: {ratio:.2f}
- Account Age: {account_age}

**Recent Tweets:**
{tweets_text}
{criteria_text}
**Evaluation Criteria:**
1. Is this a real person or likely a bot/spam account?
2. Is the account active (based on tweet content)?
3. Is the content quality reasonable?
4. Is the follower/following ratio healthy?
5. Does the bio suggest genuine engagement?

**Red Flags to Watch For:**
- Excessive emoji or hashtag spam
- Generic/promotional bio
- Very high following with low followers
- No recent activity
- Suspiciously new account with many followers

**Return ONLY valid JSON in this exact format:**
{{"should_follow": true/false, "score": 0.0-1.0, "reason": "brief reason", "flags": ["list", "of", "flags"]}}

Flags should be from: ["real", "bot", "spam", "inactive", "quality", "engaged", "promotional", "new_account"]"""

    def _parse_response(self, text: str) -> ProfileScore:
        """Parse the AI response into ProfileScore"""
        try:
            # Try to extract JSON from response
            text = text.strip()

            # Handle markdown code blocks
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0]
            elif "```" in text:
                text = text.split("```")[1].split("```")[0]

            # Find JSON object in text
            start = text.find("{")
            end = text.rfind("}") + 1
            if start != -1 and end > start:
                json_str = text[start:end]
                data = json.loads(json_str)
                return ProfileScore(**data)

        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse AI response as JSON: {e}")
        except Exception as e:
            logger.warning(f"Error parsing response: {e}")

        # Default response on parse failure
        return ProfileScore(
            should_follow=True,
            score=0.5,
            reason="Could not parse AI response",
            flags=["parse_error"]
        )

    async def batch_analyze(
        self,
        profiles: list[dict],
        criteria: Optional[dict] = None
    ) -> list[ProfileScore]:
        """
        Analyze multiple profiles

        Args:
            profiles: List of profile data dictionaries
            criteria: Optional custom criteria

        Returns:
            List of ProfileScore results
        """
        results = []
        for profile in profiles:
            result = await self.analyze(profile, criteria)
            results.append(result)
        return results

    async def quick_filter(self, profile_data: dict) -> bool:
        """
        Quick filter based on basic metrics without AI

        Args:
            profile_data: Profile data dictionary

        Returns:
            True if profile passes basic filters
        """
        followers = profile_data.get('followers_count', 0)
        following = profile_data.get('following_count', 0)

        # Basic heuristic filters
        if following > 0 and followers / following < 0.01:
            return False  # Very low ratio, likely spam

        if followers == 0 and following > 1000:
            return False  # No followers but following many

        if following > 5000 and followers < 100:
            return False  # Mass following with no real followers

        return True
