"""
AI-powered content generation for tweets and comments
"""
from typing import Optional
import random

import google.generativeai as genai

from config import get_settings
from utils.logger import setup_logger

logger = setup_logger(__name__)


class ContentGenerator:
    """
    AI-powered content generation using Google Gemini

    Generates human-like tweets, comments, and replies
    """

    def __init__(self, api_key: Optional[str] = None):
        settings = get_settings()
        self.api_key = api_key or settings.gemini_api_key

        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel(settings.ai_model)
        else:
            logger.warning("No Gemini API key configured, content generation disabled")
            self.model = None

    async def generate_comment(
        self,
        tweet_text: str,
        style: str = "engaging",
        context: Optional[dict] = None
    ) -> Optional[str]:
        """
        Generate a contextual comment/reply for a tweet

        Args:
            tweet_text: The tweet to reply to
            style: Comment style (engaging, supportive, thoughtful, humorous)
            context: Optional context (user info, previous interactions)

        Returns:
            Generated comment text
        """
        if not self.model:
            return self._get_fallback_comment(style)

        context_info = ""
        if context:
            context_info = f"""
Additional context:
- Your persona: {context.get('persona', 'helpful and engaged')}
- Relationship: {context.get('relationship', 'follower')}
- Topic focus: {context.get('topic', 'general')}
"""

        prompt = f"""Generate a natural, {style} reply to this tweet.

Tweet: "{tweet_text}"
{context_info}
Requirements:
- Sound human, not AI-generated
- Be relevant to the tweet content
- Keep under 200 characters
- No hashtags unless contextually appropriate
- Match the tweet's tone (casual, professional, humorous, etc.)
- Don't be generic like "Great post!" or "I agree!"
- Add value or continue the conversation

Reply (just the text, no quotes):"""

        try:
            response = await self.model.generate_content_async(
                prompt,
                generation_config={
                    'temperature': 0.9,
                    'top_p': 0.95,
                    'max_output_tokens': 200,
                }
            )

            comment = response.text.strip()
            # Remove quotes if present
            comment = comment.strip('"\'')
            return comment[:200]  # Ensure length limit

        except Exception as e:
            logger.error(f"Comment generation failed: {e}")
            return self._get_fallback_comment(style)

    async def generate_tweet(
        self,
        topic: str,
        style: str = "informative",
        include_cta: bool = False,
        max_length: int = 280
    ) -> Optional[str]:
        """
        Generate an original tweet

        Args:
            topic: Topic to tweet about
            style: Tweet style (informative, casual, professional, humorous)
            include_cta: Whether to include a call-to-action
            max_length: Maximum tweet length

        Returns:
            Generated tweet text
        """
        if not self.model:
            return None

        cta_instruction = "Include a subtle call-to-action (question, poll hint, etc.)" if include_cta else "No call-to-action needed"

        prompt = f"""Write a tweet about: {topic}

Style: {style}
{cta_instruction}

Requirements:
- Maximum {max_length} characters
- Sound authentic and human
- No excessive hashtags (max 2, only if natural)
- Engaging and shareable
- No emojis unless they fit naturally

Tweet (just the text, no quotes):"""

        try:
            response = await self.model.generate_content_async(
                prompt,
                generation_config={
                    'temperature': 1.0,
                    'top_p': 0.95,
                    'max_output_tokens': max_length,
                }
            )

            tweet = response.text.strip()
            tweet = tweet.strip('"\'')
            return tweet[:max_length]

        except Exception as e:
            logger.error(f"Tweet generation failed: {e}")
            return None

    async def refactor_tweet(
        self,
        original_tweet: str,
        style: Optional[str] = None
    ) -> Optional[str]:
        """
        Refactor/rewrite a tweet with different wording

        Args:
            original_tweet: The original tweet to refactor
            style: Optional style modifier

        Returns:
            Refactored tweet text
        """
        if not self.model:
            return None

        style_instruction = f"Use a {style} tone." if style else "Keep the same tone."

        prompt = f"""Create a new tweet that conveys a similar message but with different wording.

Original tweet: "{original_tweet}"

Requirements:
- Keep the same main message
- Use different vocabulary and structure
- Sound natural and authentic
- Maximum 280 characters
- No hashtags or emojis
- {style_instruction}

New tweet (just the text, no quotes):"""

        try:
            response = await self.model.generate_content_async(
                prompt,
                generation_config={
                    'temperature': 1.0,
                    'top_p': 0.95,
                    'max_output_tokens': 280,
                }
            )

            tweet = response.text.strip()
            tweet = tweet.strip('"\'')
            return tweet[:280]

        except Exception as e:
            logger.error(f"Tweet refactoring failed: {e}")
            return None

    async def generate_thread(
        self,
        topic: str,
        num_tweets: int = 5,
        style: str = "informative"
    ) -> list[str]:
        """
        Generate a Twitter thread

        Args:
            topic: Topic for the thread
            num_tweets: Number of tweets in thread
            style: Thread style

        Returns:
            List of tweet texts
        """
        if not self.model:
            return []

        prompt = f"""Write a Twitter thread about: {topic}

Number of tweets: {num_tweets}
Style: {style}

Requirements:
- Each tweet maximum 270 characters (to leave room for numbering)
- First tweet should hook the reader
- Each tweet should flow naturally to the next
- Last tweet should conclude with a summary or CTA
- Sound human and authentic
- Separate each tweet with ---

Thread:"""

        try:
            response = await self.model.generate_content_async(
                prompt,
                generation_config={
                    'temperature': 0.9,
                    'top_p': 0.95,
                    'max_output_tokens': 1500,
                }
            )

            # Split by separator
            tweets = response.text.strip().split("---")
            tweets = [t.strip().strip('"\'') for t in tweets if t.strip()]

            # Add numbering
            numbered = []
            for i, tweet in enumerate(tweets[:num_tweets], 1):
                numbered.append(f"{i}/{num_tweets} {tweet}"[:280])

            return numbered

        except Exception as e:
            logger.error(f"Thread generation failed: {e}")
            return []

    def _get_fallback_comment(self, style: str) -> str:
        """Get a fallback comment when AI is unavailable"""
        fallbacks = {
            "engaging": [
                "This is really interesting, thanks for sharing!",
                "Great point, hadn't thought about it that way.",
                "Appreciate you sharing this perspective.",
            ],
            "supportive": [
                "Couldn't agree more with this.",
                "This resonates with me.",
                "Well said!",
            ],
            "thoughtful": [
                "This raises some good points worth considering.",
                "Interesting take on this topic.",
                "Worth thinking about this more deeply.",
            ],
            "humorous": [
                "Ha! Too true.",
                "This made my day.",
                "Needed this laugh today.",
            ],
        }

        comments = fallbacks.get(style, fallbacks["engaging"])
        return random.choice(comments)
