"""
AI-powered selector recovery for self-healing automation
Uses Claude to find new selectors when Twitter UI changes
"""
from typing import Optional
import re

from anthropic import AsyncAnthropic

from config import get_settings
from utils.logger import setup_logger

logger = setup_logger(__name__)


class SelectorFinder:
    """
    AI-powered CSS selector finder for self-healing automation

    When a selector fails, this class uses Claude to analyze the
    page HTML and find alternative selectors that accomplish the
    same goal.
    """

    def __init__(self, api_key: Optional[str] = None):
        settings = get_settings()
        self.api_key = api_key or settings.anthropic_api_key

        if self.api_key:
            self.client = AsyncAnthropic(api_key=self.api_key)
        else:
            logger.warning("No Anthropic API key, selector recovery disabled")
            self.client = None

    async def find_selector(
        self,
        selector_name: str,
        page_html: str,
        context: Optional[str] = None
    ) -> Optional[str]:
        """
        Find a selector for a given element type

        Args:
            selector_name: Name describing what we're looking for
                          (e.g., "FOLLOW_BUTTON", "LIKE_BUTTON")
            page_html: Current page HTML content
            context: Optional additional context

        Returns:
            CSS selector string if found, None otherwise
        """
        if not self.client:
            return None

        # Get selector description
        descriptions = self._get_selector_descriptions()
        description = descriptions.get(
            selector_name,
            f"the {selector_name.replace('_', ' ').lower()}"
        )

        # Extract relevant HTML portion
        html_snippet = self._extract_relevant_html(page_html, selector_name)

        prompt = self._build_prompt(selector_name, description, html_snippet, context)

        try:
            response = await self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=150,
                messages=[{"role": "user", "content": prompt}]
            )

            selector = response.content[0].text.strip()
            selector = self._clean_selector(selector)

            if self._is_valid_selector(selector):
                logger.info(f"Found new selector for {selector_name}: {selector}")
                return selector
            else:
                logger.warning(f"Invalid selector returned: {selector}")
                return None

        except Exception as e:
            logger.error(f"Selector finding failed: {e}")
            return None

    async def find_follow_button(self, page_html: str) -> Optional[str]:
        """Find the follow button selector"""
        return await self.find_selector("FOLLOW_BUTTON", page_html)

    async def find_like_button(self, page_html: str) -> Optional[str]:
        """Find the like button selector"""
        return await self.find_selector("LIKE_BUTTON", page_html)

    async def find_retweet_button(self, page_html: str) -> Optional[str]:
        """Find the retweet button selector"""
        return await self.find_selector("RETWEET_BUTTON", page_html)

    async def find_reply_textarea(self, page_html: str) -> Optional[str]:
        """Find the reply textarea selector"""
        return await self.find_selector("REPLY_TEXTAREA", page_html)

    def _get_selector_descriptions(self) -> dict[str, str]:
        """Get human-readable descriptions for selector types"""
        return {
            "FOLLOW_BUTTON": "the Follow button on a Twitter profile page (not Following or Pending)",
            "UNFOLLOW_BUTTON": "the Following/Unfollow button on a profile page for someone you follow",
            "LIKE_BUTTON": "the Like/Heart button on a tweet that hasn't been liked yet",
            "UNLIKE_BUTTON": "the Unlike/Heart button on a tweet that has been liked (filled heart)",
            "RETWEET_BUTTON": "the Retweet button on a tweet that hasn't been retweeted",
            "REPLY_BUTTON": "the Reply button on a tweet",
            "REPLY_TEXTAREA": "the text input area for composing a reply to a tweet",
            "TWEET_TEXTAREA": "the main tweet composition textarea",
            "POST_REPLY_BUTTON": "the button to submit/post a reply",
            "POST_TWEET_BUTTON": "the button to submit/post a new tweet",
            "USER_CELL": "a user cell/card in a list of users (followers, following, etc.)",
            "TWEET": "a tweet container element in a timeline",
            "TWEET_TEXT": "the text content element within a tweet",
        }

    def _extract_relevant_html(self, html: str, selector_name: str) -> str:
        """
        Extract relevant portion of HTML based on selector type

        This reduces token usage by focusing on the relevant part of the page
        """
        # Keywords to search for based on selector type
        keywords_map = {
            "FOLLOW_BUTTON": ["follow", "Follow", "following"],
            "UNFOLLOW_BUTTON": ["following", "Following", "unfollow"],
            "LIKE_BUTTON": ["like", "Like", "heart", "favorite"],
            "UNLIKE_BUTTON": ["unlike", "Unlike", "heart", "favorite"],
            "RETWEET_BUTTON": ["retweet", "Retweet", "repost"],
            "REPLY_BUTTON": ["reply", "Reply"],
            "REPLY_TEXTAREA": ["reply", "Reply", "textarea", "contenteditable"],
            "TWEET_TEXTAREA": ["tweet", "Tweet", "textarea", "compose"],
            "POST_REPLY_BUTTON": ["reply", "Reply", "post", "Post"],
            "POST_TWEET_BUTTON": ["tweet", "Tweet", "post", "Post"],
            "USER_CELL": ["UserCell", "user-cell", "user_cell"],
            "TWEET": ["tweet", "Tweet", "article"],
            "TWEET_TEXT": ["tweetText", "tweet-text", "tweet_text"],
        }

        keywords = keywords_map.get(selector_name, [selector_name.lower()])

        # Find best matching area
        best_idx = -1
        best_keyword = ""

        for keyword in keywords:
            idx = html.lower().find(keyword.lower())
            if idx != -1 and (best_idx == -1 or idx < best_idx):
                best_idx = idx
                best_keyword = keyword

        if best_idx == -1:
            # Return first portion of HTML
            return html[:5000]

        # Extract surrounding context
        start = max(0, best_idx - 2500)
        end = min(len(html), best_idx + 2500)

        snippet = html[start:end]

        # Try to find complete tags
        if start > 0:
            tag_start = snippet.find("<")
            if tag_start != -1:
                snippet = snippet[tag_start:]

        return snippet

    def _build_prompt(
        self,
        selector_name: str,
        description: str,
        html_snippet: str,
        context: Optional[str]
    ) -> str:
        """Build the prompt for selector finding"""
        context_info = f"\nAdditional context: {context}" if context else ""

        return f"""Analyze this HTML and find a robust CSS selector for {description}.

HTML snippet:
```html
{html_snippet}
```
{context_info}
Requirements for the selector:
1. Be specific enough to uniquely identify the target element
2. Prefer data-testid attributes if available (e.g., [data-testid='something'])
3. Avoid classes that look auto-generated or dynamic (e.g., css-1abc2de)
4. Be resilient to minor HTML structure changes
5. Use standard CSS selector syntax

Return ONLY the CSS selector, nothing else. No explanation, no quotes, just the selector.

Selector:"""

    def _clean_selector(self, selector: str) -> str:
        """Clean up the selector from AI response"""
        # Remove markdown code blocks if present
        selector = selector.strip()
        selector = selector.strip("`")
        selector = selector.strip('"\'')

        # Remove any explanation text
        if "\n" in selector:
            selector = selector.split("\n")[0]

        # Remove "Selector:" prefix if present
        if selector.lower().startswith("selector:"):
            selector = selector[9:].strip()

        return selector.strip()

    def _is_valid_selector(self, selector: str) -> bool:
        """
        Validate that a string is a reasonable CSS selector

        Args:
            selector: The selector to validate

        Returns:
            True if selector appears valid
        """
        if not selector or len(selector) < 2:
            return False

        if len(selector) > 500:
            return False

        # Must start with a valid selector character
        valid_starts = ["[", ".", "#", "*", "a", "b", "d", "f", "i", "l", "p", "s", "t", "u"]
        if not any(selector.lower().startswith(s) for s in valid_starts):
            return False

        # Check for balanced brackets
        if selector.count("[") != selector.count("]"):
            return False

        if selector.count("(") != selector.count(")"):
            return False

        # Check for common invalid patterns
        invalid_patterns = [
            r"^\s*$",           # Empty or whitespace only
            r"^https?://",      # URLs
            r"<[^>]+>",         # HTML tags
            r"^[\d]+$",         # Just numbers
        ]

        for pattern in invalid_patterns:
            if re.match(pattern, selector):
                return False

        return True

    async def verify_selector(
        self,
        selector: str,
        page_html: str
    ) -> bool:
        """
        Verify that a selector would match something in the HTML

        This is a simple heuristic check, not a full DOM query
        """
        # Check for data-testid matches
        if "[data-testid=" in selector:
            testid_match = re.search(r"\[data-testid=['\"]([^'\"]+)['\"]\]", selector)
            if testid_match:
                testid = testid_match.group(1)
                return f'data-testid="{testid}"' in page_html or f"data-testid='{testid}'" in page_html

        # Check for class matches
        if "." in selector:
            classes = re.findall(r"\.([a-zA-Z_-][a-zA-Z0-9_-]*)", selector)
            for cls in classes:
                if f'class="' in page_html and cls in page_html:
                    return True
                if f"class='" in page_html and cls in page_html:
                    return True

        # Check for ID matches
        if "#" in selector:
            ids = re.findall(r"#([a-zA-Z_-][a-zA-Z0-9_-]*)", selector)
            for id_val in ids:
                if f'id="{id_val}"' in page_html or f"id='{id_val}'" in page_html:
                    return True

        # Can't verify - assume it might work
        return True
