"""
Centralized CSS selector management for Twitter
Supports self-healing through selector cache persistence
"""
import json
from pathlib import Path
from typing import Optional
from datetime import datetime

from db.database import fetch_one, execute_and_commit


class Selectors:
    """
    Centralized selector management with persistence and self-healing support

    Selectors are stored in memory with fallback to database cache.
    When AI-based recovery finds new selectors, they're persisted for future use.
    """

    # Default Twitter selectors (updated as of 2024)
    _default_selectors = {
        # Follow/Unfollow buttons
        "FOLLOW_BUTTON": "[data-testid='placementTracking'] button:has-text('Follow')",
        "FOLLOW_BUTTON_XPATH": "//div[@data-testid='placementTracking']/div/button",
        "UNFOLLOW_BUTTON": "[data-testid$='-unfollow']",
        "CONFIRM_UNFOLLOW": "[data-testid='confirmationSheetConfirm']",

        # Tweet actions
        "LIKE_BUTTON": "[data-testid='like']",
        "UNLIKE_BUTTON": "[data-testid='unlike']",
        "RETWEET_BUTTON": "[data-testid='retweet']",
        "UNRETWEET_BUTTON": "[data-testid='unretweet']",
        "RETWEET_CONFIRM": "[data-testid='retweetConfirm']",
        "REPLY_BUTTON": "[data-testid='reply']",

        # Tweet composition
        "TWEET_TEXTAREA": "[data-testid='tweetTextarea_0']",
        "REPLY_TEXTAREA": "[data-testid='tweetTextarea_0']",
        "POST_TWEET_BUTTON": "[data-testid='tweetButtonInline']",
        "POST_REPLY_BUTTON": "[data-testid='tweetButtonInline']",

        # Tweet elements
        "TWEET": "[data-testid='tweet']",
        "TWEET_TEXT": "[data-testid='tweetText']",
        "TWEET_TIME": "time",
        "TWEET_LINK": "a[href*='/status/']",

        # User elements
        "USER_CELL": "[data-testid='UserCell']",
        "USER_NAME": "[data-testid='User-Name']",
        "USER_AVATAR": "[data-testid='UserAvatar-Container']",

        # Profile page
        "PROFILE_HEADER": "[data-testid='UserProfileHeader_Items']",
        "FOLLOWERS_LINK": "a[href*='followers']",
        "FOLLOWING_LINK": "a[href$='/following']",
        "FOLLOWERS_COUNT": "a[href*='followers'] > span:first-child span",
        "FOLLOWING_COUNT": "a[href$='/following'] > span:first-child span",
        "BIO": "[data-testid='UserDescription']",
        "LOCATION": "[data-testid='UserProfileHeader_Items'] span[data-testid='UserLocation']",

        # Navigation
        "HOME_TAB": "[data-testid='AppTabBar_Home_Link']",
        "PROFILE_TAB": "[data-testid='AppTabBar_Profile_Link']",
        "SEARCH_TAB": "[data-testid='AppTabBar_Search_Link']",
        "NOTIFICATIONS_TAB": "[data-testid='AppTabBar_Notifications_Link']",
        "MESSAGES_TAB": "[data-testid='AppTabBar_DirectMessage_Link']",

        # Compose tweet
        "COMPOSE_TWEET_BUTTON": "[data-testid='SideNav_NewTweet_Button']",

        # Timeline
        "TIMELINE": "[data-testid='primaryColumn']",
        "TIMELINE_TWEETS": "[data-testid='cellInnerDiv']",

        # Media
        "MEDIA_UPLOAD": "input[data-testid='fileInput']",
        "MEDIA_PREVIEW": "[data-testid='attachments']",

        # Login (for verification)
        "LOGIN_BUTTON": "[data-testid='loginButton']",
        "LOGGED_IN_INDICATOR": "[data-testid='SideNav_AccountSwitcher_Button']",

        # Errors and dialogs
        "ERROR_DETAIL": "[data-testid='error-detail']",
        "MODAL_CLOSE": "[data-testid='app-bar-close']",
        "CONFIRM_DIALOG": "[data-testid='confirmationSheetDialog']",
    }

    _cache: dict[str, str] = {}
    _loaded: bool = False

    @classmethod
    def get(cls, name: str) -> str:
        """
        Get a selector by name

        Args:
            name: Selector name (e.g., 'FOLLOW_BUTTON')

        Returns:
            CSS selector string
        """
        # Try cache first
        if name in cls._cache:
            return cls._cache[name]

        # Fall back to defaults
        return cls._default_selectors.get(name, "")

    @classmethod
    def get_all(cls) -> dict[str, str]:
        """Get all selectors (merged defaults and cache)"""
        merged = cls._default_selectors.copy()
        merged.update(cls._cache)
        return merged

    @classmethod
    async def load_cache(cls):
        """Load cached selectors from database"""
        if cls._loaded:
            return

        try:
            query = "SELECT name, selector FROM selector_cache"
            from db.database import fetch_all
            rows = await fetch_all(query)

            for row in rows:
                cls._cache[row['name']] = row['selector']

            cls._loaded = True
        except Exception:
            # Database might not be initialized yet
            pass

    @classmethod
    async def update(cls, name: str, selector: str):
        """
        Update a selector and persist to database

        Args:
            name: Selector name
            selector: New CSS selector
        """
        cls._cache[name] = selector

        # Persist to database
        try:
            query = '''
                INSERT INTO selector_cache (name, selector, last_verified)
                VALUES (?, ?, ?)
                ON CONFLICT(name) DO UPDATE SET
                    selector = excluded.selector,
                    last_verified = excluded.last_verified,
                    success_count = selector_cache.success_count + 1
            '''
            await execute_and_commit(query, (name, selector, datetime.now()))
        except Exception:
            pass

    @classmethod
    async def record_success(cls, name: str):
        """Record successful use of a selector"""
        try:
            query = '''
                UPDATE selector_cache
                SET success_count = success_count + 1, last_verified = ?
                WHERE name = ?
            '''
            await execute_and_commit(query, (datetime.now(), name))
        except Exception:
            pass

    @classmethod
    async def record_failure(cls, name: str):
        """Record failed use of a selector"""
        try:
            query = '''
                UPDATE selector_cache
                SET failure_count = failure_count + 1
                WHERE name = ?
            '''
            await execute_and_commit(query, (name,))
        except Exception:
            pass

    @classmethod
    def reset_to_defaults(cls):
        """Reset cache to default selectors"""
        cls._cache.clear()
        cls._loaded = False


# Selector name constants for type safety
class S:
    """Selector name constants"""
    FOLLOW_BUTTON = "FOLLOW_BUTTON"
    FOLLOW_BUTTON_XPATH = "FOLLOW_BUTTON_XPATH"
    UNFOLLOW_BUTTON = "UNFOLLOW_BUTTON"
    CONFIRM_UNFOLLOW = "CONFIRM_UNFOLLOW"
    LIKE_BUTTON = "LIKE_BUTTON"
    UNLIKE_BUTTON = "UNLIKE_BUTTON"
    RETWEET_BUTTON = "RETWEET_BUTTON"
    UNRETWEET_BUTTON = "UNRETWEET_BUTTON"
    RETWEET_CONFIRM = "RETWEET_CONFIRM"
    REPLY_BUTTON = "REPLY_BUTTON"
    TWEET_TEXTAREA = "TWEET_TEXTAREA"
    REPLY_TEXTAREA = "REPLY_TEXTAREA"
    POST_TWEET_BUTTON = "POST_TWEET_BUTTON"
    POST_REPLY_BUTTON = "POST_REPLY_BUTTON"
    TWEET = "TWEET"
    TWEET_TEXT = "TWEET_TEXT"
    TWEET_TIME = "TWEET_TIME"
    TWEET_LINK = "TWEET_LINK"
    USER_CELL = "USER_CELL"
    USER_NAME = "USER_NAME"
    USER_AVATAR = "USER_AVATAR"
    PROFILE_HEADER = "PROFILE_HEADER"
    FOLLOWERS_LINK = "FOLLOWERS_LINK"
    FOLLOWING_LINK = "FOLLOWING_LINK"
    FOLLOWERS_COUNT = "FOLLOWERS_COUNT"
    FOLLOWING_COUNT = "FOLLOWING_COUNT"
    BIO = "BIO"
    LOCATION = "LOCATION"
    TIMELINE = "TIMELINE"
    TIMELINE_TWEETS = "TIMELINE_TWEETS"
    LOGGED_IN_INDICATOR = "LOGGED_IN_INDICATOR"
    PROFILE_TAB = "PROFILE_TAB"
