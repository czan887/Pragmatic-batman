"""
Twitter automation actions using Playwright
"""
from playwright.async_api import Page, TimeoutError as PlaywrightTimeout, ElementHandle
from typing import Optional, Callable, Any
import random
import asyncio

from .selectors import Selectors, S
from config import get_settings
from utils.logger import BotLogger

# Type for log callback
LogCallback = Callable[[str, str], None]


class TwitterActions:
    """
    Twitter automation actions using Playwright

    All methods are designed to be human-like with natural delays
    and include self-healing selector recovery via AI
    """

    def __init__(
        self,
        page: Page,
        profile_id: str,
        log_callback: Optional[LogCallback] = None,
        selector_finder: Optional[Any] = None
    ):
        self.page = page
        self.profile_id = profile_id
        self.selector_finder = selector_finder
        self._logger = BotLogger(profile_id)

        # Use provided callback or default logger
        self.log = log_callback or self._default_log

    def _default_log(self, message: str, level: str = "INFO"):
        """Default logging method"""
        getattr(self._logger, level.lower(), self._logger.info)(message)

    async def _random_delay(self, min_sec: float = None, max_sec: float = None):
        """Add human-like random delay"""
        settings = get_settings()
        min_sec = min_sec or settings.min_action_delay
        max_sec = max_sec or settings.max_action_delay
        delay = random.uniform(min_sec, max_sec)
        await asyncio.sleep(delay)

    async def _human_type(self, text: str, element: Optional[ElementHandle] = None):
        """Type text with human-like delays between keystrokes"""
        target = element or self.page

        for char in text:
            await target.type(char)
            await asyncio.sleep(random.uniform(0.05, 0.15))

    async def _try_selector(
        self,
        selector_name: str,
        timeout: int = 5000,
        use_recovery: bool = True
    ) -> Optional[ElementHandle]:
        """
        Try to find element with selector, with optional AI recovery

        Args:
            selector_name: Name of selector from Selectors class
            timeout: Timeout in milliseconds
            use_recovery: Whether to try AI-based selector recovery on failure

        Returns:
            Element handle if found, None otherwise
        """
        selector = Selectors.get(selector_name)

        try:
            element = await self.page.wait_for_selector(selector, timeout=timeout)
            if element:
                await Selectors.record_success(selector_name)
                return element
        except PlaywrightTimeout:
            await Selectors.record_failure(selector_name)

            # Try AI recovery if enabled
            if use_recovery and self.selector_finder and get_settings().enable_mcp_recovery:
                try:
                    self.log(f"Attempting AI recovery for {selector_name}", "WARNING")
                    html = await self.page.content()
                    new_selector = await self.selector_finder.find_selector(
                        selector_name, html
                    )
                    if new_selector:
                        await Selectors.update(selector_name, new_selector)
                        element = await self.page.wait_for_selector(
                            new_selector, timeout=timeout
                        )
                        if element:
                            self.log(f"AI recovery successful for {selector_name}", "SUCCESS")
                            return element
                except Exception as e:
                    self.log(f"AI recovery failed: {e}", "ERROR")

        return None

    async def _scroll_to_element(self, element: ElementHandle):
        """Scroll element into view with natural behavior"""
        try:
            # First check if element is still attached
            is_visible = await element.is_visible()
            if is_visible:
                await element.scroll_into_view_if_needed()
                await self._random_delay(0.3, 0.6)
        except Exception:
            # Element may have been detached, just continue
            pass

    async def _wait_for_overlays_clear(self, timeout: int = 5000):
        """Wait for overlay dialogs to clear from the page"""
        try:
            start_time = asyncio.get_event_loop().time()
            while (asyncio.get_event_loop().time() - start_time) * 1000 < timeout:
                layers = await self.page.query_selector("#layers")
                if not layers:
                    return True

                # Check if layers has any visible overlay content
                children = await layers.query_selector_all(":scope > div")
                has_overlay = False
                for child in children:
                    try:
                        is_visible = await child.is_visible()
                        if is_visible:
                            inner_html = await child.inner_html()
                            if inner_html and len(inner_html.strip()) > 10:
                                has_overlay = True
                                break
                    except Exception:
                        continue

                if not has_overlay:
                    return True

                # Try to dismiss
                await self.page.keyboard.press("Escape")
                await asyncio.sleep(0.3)

            return False
        except Exception:
            return True

    async def navigate_to_profile(self, username: str) -> bool:
        """Navigate to a user's profile"""
        # Validate username - should not look like a URL or domain
        if not username or '.' in username or '/' in username or '@' in username:
            self.log(f"Invalid username format: {username}", "ERROR")
            return False

        url = f"https://x.com/{username}"
        try:
            # Use domcontentloaded instead of networkidle to avoid timeout on Twitter
            await self.page.goto(url, wait_until="domcontentloaded", timeout=30000)
            await self._random_delay(1, 2)  # Give page time to load dynamic content
            return True
        except Exception as e:
            self.log(f"Failed to navigate to {username}: {e}", "ERROR")
            return False

    async def get_current_username(self) -> Optional[str]:
        """
        Get the username of the currently logged-in user from the page

        Returns:
            Twitter username (without @) or None if not found
        """
        try:
            current_url = self.page.url

            # Navigate to home if not on Twitter
            if not current_url or ("x.com" not in current_url and "twitter.com" not in current_url):
                await self.page.goto("https://x.com/home", wait_until="domcontentloaded", timeout=30000)
                await self._random_delay(2, 3)
                current_url = self.page.url

            # Wait for page to be interactive
            await self._random_delay(1, 2)

            # Method 1: Get username from profile link in nav (most reliable)
            try:
                profile_link = await self.page.wait_for_selector(
                    'a[data-testid="AppTabBar_Profile_Link"]',
                    timeout=5000
                )
                if profile_link:
                    href = await profile_link.get_attribute('href')
                    if href and '/' in href:
                        username = href.rstrip('/').split('/')[-1]
                        if username and username != 'profile' and '.' not in username:
                            self.log(f"Found username from profile link: {username}")
                            return username
            except Exception:
                pass

            # Method 2: Try account switcher button
            try:
                account_switcher = await self.page.wait_for_selector(
                    Selectors.get(S.LOGGED_IN_INDICATOR),
                    timeout=5000
                )
                if account_switcher:
                    # Look for username in the account switcher
                    all_spans = await account_switcher.query_selector_all('span')
                    for span in all_spans:
                        text = await span.inner_text()
                        if text and text.startswith('@'):
                            username = text[1:]
                            self.log(f"Found username from account switcher: {username}")
                            return username
            except Exception:
                pass

            # Method 3: Check if URL contains username (if on profile page)
            if current_url and '/home' not in current_url and '/search' not in current_url:
                parts = current_url.replace('https://', '').split('/')
                if len(parts) >= 2:
                    potential_username = parts[1].split('?')[0]
                    if potential_username and '.' not in potential_username and len(potential_username) <= 15:
                        self.log(f"Found username from URL: {potential_username}")
                        return potential_username

            self.log("Could not find username with any method", "WARNING")
            return None

        except Exception as e:
            self.log(f"Error getting current username: {e}", "ERROR")
            return None

    async def follow_user(self, username: str) -> bool:
        """
        Follow a user

        Args:
            username: Twitter username to follow

        Returns:
            True if follow was successful
        """
        self.log(f"Following user: {username}")

        # Navigate to profile
        if not await self.navigate_to_profile(username):
            return False

        try:
            # Wait for page to load
            await self._random_delay(1, 2)

            # Try to find follow button
            follow_btn = await self._try_selector(S.FOLLOW_BUTTON, timeout=5000)

            if not follow_btn:
                # Check if already following
                unfollow_btn = await self._try_selector(
                    S.UNFOLLOW_BUTTON, timeout=2000, use_recovery=False
                )
                if unfollow_btn:
                    self.log(f"Already following {username}", "WARNING")
                    return True

                self.log(f"Could not find follow button for {username}", "ERROR")
                return False

            # Click follow
            await self._scroll_to_element(follow_btn)
            await follow_btn.click()
            await self._random_delay()

            self.log(f"Followed {username}", "SUCCESS")
            return True

        except Exception as e:
            self.log(f"Error following {username}: {e}", "ERROR")
            return False

    async def unfollow_user(self, username: str) -> bool:
        """
        Unfollow a user

        Args:
            username: Twitter username to unfollow

        Returns:
            True if unfollow was successful
        """
        self.log(f"Unfollowing user: {username}")

        if not await self.navigate_to_profile(username):
            return False

        try:
            await self._random_delay(1, 2)

            # Find unfollow/following button
            unfollow_btn = await self._try_selector(S.UNFOLLOW_BUTTON, timeout=5000)

            if not unfollow_btn:
                # Check if not following
                follow_btn = await self._try_selector(
                    S.FOLLOW_BUTTON, timeout=2000, use_recovery=False
                )
                if follow_btn:
                    self.log(f"Not following {username}", "WARNING")
                    return True

                self.log(f"Could not find unfollow button for {username}", "ERROR")
                return False

            # Click unfollow
            await self._scroll_to_element(unfollow_btn)
            await unfollow_btn.click()
            await self._random_delay(0.5, 1)

            # Confirm unfollow
            confirm_btn = await self._try_selector(S.CONFIRM_UNFOLLOW, timeout=3000)
            if confirm_btn:
                await confirm_btn.click()
                await self._random_delay()

            self.log(f"Unfollowed {username}", "SUCCESS")
            return True

        except Exception as e:
            self.log(f"Error unfollowing {username}: {e}", "ERROR")
            return False

    async def like_tweet(self, tweet_element: ElementHandle) -> bool:
        """
        Like a tweet

        Args:
            tweet_element: Element handle for the tweet

        Returns:
            True if like was successful
        """
        try:
            like_btn = await tweet_element.query_selector(Selectors.get(S.LIKE_BUTTON))

            if not like_btn:
                # Check if already liked
                unlike_btn = await tweet_element.query_selector(
                    Selectors.get(S.UNLIKE_BUTTON)
                )
                if unlike_btn:
                    self.log("Tweet already liked", "WARNING")
                    return True
                return False

            await self._scroll_to_element(like_btn)
            await like_btn.click()
            await self._random_delay(0.5, 1)

            self.log("Liked tweet", "SUCCESS")
            return True

        except Exception as e:
            self.log(f"Error liking tweet: {e}", "ERROR")
            return False

    async def retweet(self, tweet_element: ElementHandle) -> bool:
        """
        Retweet a tweet

        Args:
            tweet_element: Element handle for the tweet

        Returns:
            True if retweet was successful
        """
        try:
            retweet_btn = await tweet_element.query_selector(
                Selectors.get(S.RETWEET_BUTTON)
            )

            if not retweet_btn:
                # Check if already retweeted
                unretweet_btn = await tweet_element.query_selector(
                    Selectors.get(S.UNRETWEET_BUTTON)
                )
                if unretweet_btn:
                    self.log("Tweet already retweeted", "WARNING")
                    return True
                return False

            await self._scroll_to_element(retweet_btn)
            await retweet_btn.click()
            await self._random_delay(0.3, 0.6)

            # Click confirm retweet
            confirm = await self.page.wait_for_selector(
                Selectors.get(S.RETWEET_CONFIRM), timeout=3000
            )
            if confirm:
                await confirm.click()
                await self._random_delay()

            self.log("Retweeted", "SUCCESS")
            return True

        except Exception as e:
            self.log(f"Error retweeting: {e}", "ERROR")
            return False

    async def post_comment(self, tweet_url: str, comment: str) -> bool:
        """
        Post a comment/reply on a tweet

        Args:
            tweet_url: URL of the tweet to comment on
            comment: Comment text

        Returns:
            True if comment was posted successfully
        """
        self.log(f"Posting comment on {tweet_url}")

        try:
            # Navigate to tweet
            await self.page.goto(tweet_url, wait_until="networkidle", timeout=30000)
            await self._random_delay(1, 2)

            # Find reply textarea
            reply_box = await self._try_selector(S.REPLY_TEXTAREA, timeout=5000)

            if not reply_box:
                # Try clicking reply button first
                reply_btn = await self._try_selector(S.REPLY_BUTTON, timeout=3000)
                if reply_btn:
                    await reply_btn.click()
                    await self._random_delay(0.5, 1)
                    reply_box = await self._try_selector(S.REPLY_TEXTAREA, timeout=5000)

            if not reply_box:
                self.log("Could not find reply box", "ERROR")
                return False

            # Click to focus
            await reply_box.click()
            await self._random_delay(0.3, 0.5)

            # Type comment with human-like speed
            await self._human_type(comment)
            await self._random_delay(0.5, 1)

            # Post reply
            post_btn = await self._try_selector(S.POST_REPLY_BUTTON, timeout=3000)
            if not post_btn:
                self.log("Could not find post button", "ERROR")
                return False

            await post_btn.click()
            await self._random_delay(1, 2)

            self.log("Comment posted", "SUCCESS")
            return True

        except Exception as e:
            self.log(f"Error posting comment: {e}", "ERROR")
            return False

    async def post_tweet(self, text: str) -> bool:
        """
        Post a new tweet

        Args:
            text: Tweet text (max 280 characters)

        Returns:
            True if tweet was posted successfully
        """
        self.log("Posting new tweet")

        try:
            # Navigate to home
            await self.page.goto("https://twitter.com/home", wait_until="networkidle")
            await self._random_delay(1, 2)

            # Find tweet textarea
            textarea = await self._try_selector(S.TWEET_TEXTAREA, timeout=5000)

            if not textarea:
                self.log("Could not find tweet textarea", "ERROR")
                return False

            # Click to focus
            await textarea.click()
            await self._random_delay(0.3, 0.5)

            # Type tweet
            await self._human_type(text[:280])  # Truncate to 280 chars
            await self._random_delay(0.5, 1)

            # Post tweet
            post_btn = await self._try_selector(S.POST_TWEET_BUTTON, timeout=3000)
            if not post_btn:
                self.log("Could not find post button", "ERROR")
                return False

            await post_btn.click()
            await self._random_delay(1, 2)

            self.log("Tweet posted", "SUCCESS")
            return True

        except Exception as e:
            self.log(f"Error posting tweet: {e}", "ERROR")
            return False

    async def get_followers(self, username: str, max_count: int = 50) -> list[str]:
        """
        Get list of followers for a user

        Args:
            username: Twitter username
            max_count: Maximum number of followers to fetch

        Returns:
            List of follower usernames
        """
        followers = []

        try:
            # Navigate to followers page
            await self.page.goto(
                f"https://twitter.com/{username}/followers",
                wait_until="networkidle"
            )
            await self._random_delay(1, 2)

            while len(followers) < max_count:
                # Get user cells
                cells = await self.page.query_selector_all(Selectors.get(S.USER_CELL))

                for cell in cells:
                    if len(followers) >= max_count:
                        break

                    try:
                        # Extract username from link
                        link = await cell.query_selector("a[role='link']")
                        if link:
                            href = await link.get_attribute("href")
                            if href and href.startswith("/"):
                                follower_username = href[1:].split("/")[0]
                                if follower_username not in followers:
                                    followers.append(follower_username)
                    except Exception:
                        continue

                # Scroll to load more
                if len(followers) < max_count:
                    await self.page.keyboard.press("End")
                    await self._random_delay(1, 2)

                    # Check if we've reached the end
                    new_cells = await self.page.query_selector_all(
                        Selectors.get(S.USER_CELL)
                    )
                    if len(new_cells) == len(cells):
                        break

            self.log(f"Found {len(followers)} followers for {username}")
            return followers

        except Exception as e:
            self.log(f"Error getting followers: {e}", "ERROR")
            return followers

    async def get_timeline_tweets(
        self,
        username: str,
        max_count: int = 10
    ) -> list[dict]:
        """
        Get tweets from a user's timeline

        Args:
            username: Twitter username
            max_count: Maximum number of tweets to fetch

        Returns:
            List of tweet data dictionaries
        """
        tweets = []

        try:
            if not await self.navigate_to_profile(username):
                return tweets

            await self._random_delay(1, 2)

            tweet_elements = await self.page.query_selector_all(
                Selectors.get(S.TWEET)
            )

            for element in tweet_elements[:max_count]:
                try:
                    tweet_data = {
                        "element": element,
                        "text": "",
                        "url": ""
                    }

                    # Get text
                    text_el = await element.query_selector(Selectors.get(S.TWEET_TEXT))
                    if text_el:
                        tweet_data["text"] = await text_el.inner_text()

                    # Get URL
                    link = await element.query_selector(Selectors.get(S.TWEET_LINK))
                    if link:
                        href = await link.get_attribute("href")
                        tweet_data["url"] = f"https://twitter.com{href}"

                    tweets.append(tweet_data)

                except Exception:
                    continue

            self.log(f"Found {len(tweets)} tweets from {username}")
            return tweets

        except Exception as e:
            self.log(f"Error getting timeline: {e}", "ERROR")
            return tweets

    def _is_valid_username(self, username: str) -> bool:
        """Check if a string looks like a valid Twitter username"""
        if not username:
            return False
        # Username should not contain dots (like domain), slashes, or @
        # Twitter usernames are alphanumeric with underscores, max 15 chars
        if '.' in username or '/' in username or '@' in username:
            return False
        if len(username) > 15:
            return False
        return True

    async def get_profile_stats(self, username: str = None) -> dict:
        """
        Get profile statistics for a user

        Args:
            username: Twitter username (optional, will use current logged-in user if invalid)

        Returns:
            Dictionary with followers_count, following_count, bio
        """
        stats = {
            "followers_count": 0,
            "following_count": 0,
            "bio": "",
            "location": ""
        }

        try:
            # Validate username or get current logged-in user
            actual_username = username
            if not self._is_valid_username(username):
                self.log(f"Invalid username '{username}', trying to get current logged-in user", "WARNING")
                actual_username = await self.get_current_username()
                if not actual_username:
                    self.log("Could not determine Twitter username", "ERROR")
                    return stats
                self.log(f"Using current logged-in username: {actual_username}")

            if not await self.navigate_to_profile(actual_username):
                return stats

            # Wait for profile page to load
            await self._random_delay(2, 3)

            # Wait for followers link to appear (indicates profile loaded)
            try:
                await self.page.wait_for_selector(
                    'a[href*="followers"]',
                    timeout=10000
                )
                self.log(f"Profile page loaded for {actual_username}")
            except Exception:
                self.log(f"Profile page may not have loaded properly for {actual_username}", "WARNING")

            # Get followers count - try multiple selectors
            followers_el = None
            for selector in ['a[href*="followers"] > span:first-child span', 'a[href*="followers"] span span']:
                followers_el = await self.page.query_selector(selector)
                if followers_el:
                    break

            if followers_el:
                text = await followers_el.inner_text()
                stats["followers_count"] = self._parse_count(text)
                self.log(f"Found followers: {text} -> {stats['followers_count']}")
            else:
                self.log("Could not find followers element", "WARNING")

            # Get following count - try multiple selectors
            following_el = None
            for selector in ['a[href$="/following"] > span:first-child span', 'a[href$="/following"] span span']:
                following_el = await self.page.query_selector(selector)
                if following_el:
                    break

            if following_el:
                text = await following_el.inner_text()
                stats["following_count"] = self._parse_count(text)
                self.log(f"Found following: {text} -> {stats['following_count']}")
            else:
                self.log("Could not find following element", "WARNING")

            # Get bio
            bio_el = await self.page.query_selector(Selectors.get(S.BIO))
            if bio_el:
                stats["bio"] = await bio_el.inner_text()

            # Get location - try multiple methods
            location_el = await self.page.query_selector('[data-testid="UserLocation"]')
            if location_el:
                stats["location"] = await location_el.inner_text()
            else:
                # Try to find location in profile header items (look for span with location icon)
                try:
                    header_items = await self.page.query_selector('[data-testid="UserProfileHeader_Items"]')
                    if header_items:
                        # Look for spans that might contain location (usually first item after the join date)
                        spans = await header_items.query_selector_all('span')
                        for span in spans:
                            text = await span.inner_text()
                            # Skip if it's a link or other known fields
                            if text and not text.startswith('@') and not text.startswith('http') and 'Joined' not in text and len(text) > 2:
                                # Check if parent has a location icon (svg with specific path)
                                parent = await span.evaluate_handle('el => el.parentElement')
                                svg = await parent.query_selector('svg')
                                if svg:
                                    stats["location"] = text
                                    break
                except Exception:
                    pass

            self.log(f"Stats for {actual_username}: followers={stats['followers_count']}, following={stats['following_count']}, location={stats['location']}")
            return stats

        except Exception as e:
            self.log(f"Error getting profile stats: {e}", "ERROR")
            return stats

    def _parse_count(self, text: str) -> int:
        """Parse count from text (e.g., '1.2K' -> 1200)"""
        try:
            text = text.strip().upper()
            if "K" in text:
                return int(float(text.replace("K", "")) * 1000)
            elif "M" in text:
                return int(float(text.replace("M", "")) * 1000000)
            else:
                return int(text.replace(",", ""))
        except Exception:
            return 0

    async def is_logged_in(self) -> bool:
        """Check if user is logged into Twitter"""
        try:
            indicator = await self.page.query_selector(
                Selectors.get(S.LOGGED_IN_INDICATOR)
            )
            return indicator is not None
        except Exception:
            return False

    async def search_hashtag(self, hashtag: str, max_results: int = 10) -> list[dict]:
        """
        Search for tweets with a specific hashtag

        Args:
            hashtag: Hashtag to search (without # symbol)
            max_results: Maximum number of tweets to fetch

        Returns:
            List of tweet data dictionaries
        """
        tweets = []

        try:
            # Navigate to hashtag search
            search_url = f"https://twitter.com/search?q=%23{hashtag}&src=typed_query&f=live"
            await self.page.goto(search_url, wait_until="networkidle", timeout=30000)
            await self._random_delay(2, 3)

            scroll_count = 0
            max_scrolls = max(3, max_results // 5)

            while len(tweets) < max_results and scroll_count < max_scrolls:
                # Get tweet elements
                tweet_elements = await self.page.query_selector_all(
                    Selectors.get(S.TWEET)
                )

                for element in tweet_elements:
                    if len(tweets) >= max_results:
                        break

                    try:
                        tweet_data = {
                            "element": element,
                            "text": "",
                            "url": "",
                            "hashtag": hashtag
                        }

                        # Get text
                        text_el = await element.query_selector(Selectors.get(S.TWEET_TEXT))
                        if text_el:
                            tweet_data["text"] = await text_el.inner_text()

                        # Get URL
                        link = await element.query_selector(Selectors.get(S.TWEET_LINK))
                        if link:
                            href = await link.get_attribute("href")
                            if href and "/status/" in href:
                                tweet_data["url"] = f"https://twitter.com{href}"
                                # Only add if we haven't seen this URL
                                if not any(t["url"] == tweet_data["url"] for t in tweets):
                                    tweets.append(tweet_data)

                    except Exception:
                        continue

                # Scroll to load more
                if len(tweets) < max_results:
                    await self.page.keyboard.press("End")
                    await self._random_delay(1.5, 2.5)
                    scroll_count += 1

            self.log(f"Found {len(tweets)} tweets for #{hashtag}")
            return tweets

        except Exception as e:
            self.log(f"Error searching hashtag #{hashtag}: {e}", "ERROR")
            return tweets

    async def get_following(self, username: str, max_count: int = 100) -> list[str]:
        """
        Get list of users that a profile is following

        Args:
            username: Twitter username
            max_count: Maximum number of following to fetch

        Returns:
            List of following usernames
        """
        following = []

        try:
            # Navigate to following page
            await self.page.goto(
                f"https://twitter.com/{username}/following",
                wait_until="networkidle"
            )
            await self._random_delay(1, 2)

            prev_count = 0
            stall_count = 0

            while len(following) < max_count and stall_count < 3:
                # Get user cells
                cells = await self.page.query_selector_all(Selectors.get(S.USER_CELL))

                for cell in cells:
                    if len(following) >= max_count:
                        break

                    try:
                        # Extract username from link
                        link = await cell.query_selector("a[role='link']")
                        if link:
                            href = await link.get_attribute("href")
                            if href and href.startswith("/"):
                                following_username = href[1:].split("/")[0]
                                if following_username not in following and following_username != username:
                                    following.append(following_username)
                    except Exception:
                        continue

                # Check for stall
                if len(following) == prev_count:
                    stall_count += 1
                else:
                    stall_count = 0
                prev_count = len(following)

                # Scroll to load more
                if len(following) < max_count:
                    await self.page.keyboard.press("End")
                    await self._random_delay(1, 2)

            self.log(f"Found {len(following)} following for {username}")
            return following

        except Exception as e:
            self.log(f"Error getting following: {e}", "ERROR")
            return following

    async def navigate_to_tweet(self, tweet_url: str) -> bool:
        """
        Navigate to a specific tweet

        Args:
            tweet_url: URL of the tweet

        Returns:
            True if navigation was successful
        """
        try:
            await self.page.goto(tweet_url, wait_until="networkidle", timeout=30000)
            await self._random_delay(1, 2)
            return True
        except Exception as e:
            self.log(f"Failed to navigate to tweet: {e}", "ERROR")
            return False

    async def get_tweet_element(self) -> Optional[ElementHandle]:
        """
        Get the main tweet element on a tweet page

        Returns:
            Element handle for the tweet, or None
        """
        try:
            await self._random_delay(0.5, 1)
            tweet_el = await self.page.query_selector("[data-testid='tweet']")
            return tweet_el
        except Exception:
            return None

    async def get_tweet_text(self, tweet_url: str) -> str:
        """
        Get the text content of a tweet

        Args:
            tweet_url: URL of the tweet

        Returns:
            Tweet text content
        """
        try:
            if not await self.navigate_to_tweet(tweet_url):
                return ""

            tweet_text_el = await self.page.query_selector("[data-testid='tweetText']")
            if tweet_text_el:
                return await tweet_text_el.inner_text()
            return ""
        except Exception as e:
            self.log(f"Error getting tweet text: {e}", "ERROR")
            return ""

    async def like_tweet_by_url(self, tweet_url: str) -> bool:
        """
        Like a tweet by navigating to its URL

        Args:
            tweet_url: URL of the tweet to like

        Returns:
            True if like was successful
        """
        try:
            if not await self.navigate_to_tweet(tweet_url):
                return False

            tweet_el = await self.get_tweet_element()
            if tweet_el:
                return await self.like_tweet(tweet_el)
            return False
        except Exception as e:
            self.log(f"Error liking tweet: {e}", "ERROR")
            return False

    async def retweet_by_url(self, tweet_url: str) -> bool:
        """
        Retweet by navigating to the tweet URL

        Args:
            tweet_url: URL of the tweet to retweet

        Returns:
            True if retweet was successful
        """
        try:
            if not await self.navigate_to_tweet(tweet_url):
                return False

            tweet_el = await self.get_tweet_element()
            if tweet_el:
                return await self.retweet(tweet_el)
            return False
        except Exception as e:
            self.log(f"Error retweeting: {e}", "ERROR")
            return False

    async def _scroll_randomly(self, min_scrolls: int = 2, max_scrolls: int = 5):
        """Scroll the page randomly with human-like behavior"""
        scroll_count = random.randint(min_scrolls, max_scrolls)
        for _ in range(scroll_count):
            # Random scroll direction (mostly down, sometimes up)
            if random.random() < 0.8:
                # Scroll down
                scroll_amount = random.randint(200, 600)
                await self.page.evaluate(f"window.scrollBy(0, {scroll_amount})")
            else:
                # Scroll up
                scroll_amount = random.randint(100, 300)
                await self.page.evaluate(f"window.scrollBy(0, -{scroll_amount})")

            await self._random_delay(0.5, 1.5)

    async def _dismiss_overlays(self, max_attempts: int = 3):
        """Dismiss any overlay dialogs that might be blocking clicks"""
        for attempt in range(max_attempts):
            try:
                # Check if layers div has any children (overlay is present)
                layers = await self.page.query_selector("#layers")
                if layers:
                    # Check if there's content in the overlay
                    children = await layers.query_selector_all(":scope > div")
                    overlay_present = False
                    for child in children:
                        # Check if child has actual content (not empty)
                        inner_html = await child.inner_html()
                        if inner_html and len(inner_html.strip()) > 10:
                            overlay_present = True
                            break

                    if not overlay_present:
                        return  # No overlay to dismiss

                # Try pressing Escape
                await self.page.keyboard.press("Escape")
                await asyncio.sleep(0.3)

                # Also try clicking outside the modal area
                if attempt > 0:
                    try:
                        # Click at top-left corner of page to dismiss any modal
                        await self.page.mouse.click(10, 10)
                        await asyncio.sleep(0.2)
                    except Exception:
                        pass

            except Exception:
                pass

        # Final wait to ensure overlay is gone
        await asyncio.sleep(0.2)

    async def _interact_with_profile(self, num_likes: int = 2, should_repost: bool = False) -> bool:
        """
        Interact naturally with a user's profile

        - Scroll up and down randomly
        - Like 2-3 posts randomly
        - Optionally repost their posts

        Returns:
            True if interaction was successful
        """
        try:
            # Dismiss any existing overlays
            await self._dismiss_overlays()

            # Initial scroll to see content
            await self._scroll_randomly(1, 3)

            liked = 0
            reposted = 0
            attempts = 0
            max_attempts = num_likes + 3

            while (liked < num_likes or (should_repost and reposted < 1)) and attempts < max_attempts:
                attempts += 1

                # Re-query tweets each iteration to get fresh elements
                tweets = await self.page.query_selector_all("[data-testid='tweet']")

                if not tweets:
                    self.log("No tweets found on profile", "WARNING")
                    break

                # Pick a random tweet
                tweet_idx = random.randint(0, min(len(tweets) - 1, 5))
                tweet = tweets[tweet_idx]

                try:
                    # Check if element is still attached
                    is_visible = await tweet.is_visible()
                    if not is_visible:
                        continue

                    # Scroll to tweet
                    await self._scroll_to_element(tweet)
                    await self._random_delay(0.5, 1)

                    # Like the tweet
                    if liked < num_likes:
                        like_btn = await tweet.query_selector(Selectors.get(S.LIKE_BUTTON))
                        if like_btn:
                            try:
                                await like_btn.click()
                                liked += 1
                                self.log(f"Liked tweet {liked}/{num_likes}")
                                await self._random_delay(0.5, 1.5)
                            except Exception:
                                pass

                    # Repost if requested and haven't done it yet
                    if should_repost and reposted < 1 and random.random() < 0.5:
                        retweet_btn = await tweet.query_selector(Selectors.get(S.RETWEET_BUTTON))
                        if retweet_btn:
                            try:
                                await retweet_btn.click()
                                await self._random_delay(0.3, 0.6)
                                # Click confirm retweet
                                confirm = await self.page.wait_for_selector(
                                    Selectors.get(S.RETWEET_CONFIRM), timeout=3000
                                )
                                if confirm:
                                    await confirm.click()
                                    reposted += 1
                                    self.log("Reposted tweet")
                                    await self._random_delay(0.5, 1)
                                    # Wait for retweet overlay to close completely
                                    await self._wait_for_overlays_clear(timeout=3000)
                                    # Also dismiss any remaining overlays
                                    await self._dismiss_overlays(max_attempts=2)
                            except Exception:
                                # Dismiss overlay if retweet dialog is stuck
                                await self._dismiss_overlays(max_attempts=3)
                                await self._wait_for_overlays_clear(timeout=2000)

                    # Random scroll between actions
                    if random.random() < 0.3:
                        await self._scroll_randomly(1, 2)

                except Exception as e:
                    # Element might have been detached, continue with fresh elements
                    self.log(f"Tweet element issue, continuing: {str(e)[:50]}", "WARNING")
                    continue

            # Final scroll (up a bit, then down)
            await self.page.evaluate("window.scrollBy(0, -300)")
            await self._random_delay(0.3, 0.8)
            await self.page.evaluate("window.scrollBy(0, 150)")

            self.log(f"Interacted with profile: liked {liked} posts, reposted {reposted}")
            return True

        except Exception as e:
            self.log(f"Error interacting with profile: {e}", "ERROR")
            return False

    async def follow_followers_organic(
        self,
        target_username: str,
        max_follows: int = 10,
        likes_per_profile: int = 2,
        should_repost: bool = True
    ) -> list[str]:
        """
        Follow followers of a user with organic, human-like behavior

        Flow:
        1. Open the followers page of target user
        2. Scroll randomly
        3. Click on a follower's profile
        4. Interact with their profile (scroll, like 2-3 posts, repost)
        5. Follow the user
        6. Move to next follower

        Args:
            target_username: Username whose followers to follow
            max_follows: Maximum number of followers to follow
            likes_per_profile: Number of posts to like per profile (2-3)
            should_repost: Whether to repost some posts

        Returns:
            List of usernames that were followed
        """
        followed = []

        try:
            # Navigate to followers page
            followers_url = f"https://x.com/{target_username}/followers"
            self.log(f"Opening followers page of @{target_username}")

            await self.page.goto(followers_url, wait_until="domcontentloaded", timeout=30000)
            await self._random_delay(2, 3)

            # Initial random scroll to load content
            self.log("Scrolling through followers list...")
            await self._scroll_randomly(2, 4)

            processed_usernames = set()
            attempts = 0
            max_attempts = max_follows * 3  # Allow for some failures

            while len(followed) < max_follows and attempts < max_attempts:
                attempts += 1

                # Get user cells (follower entries)
                cells = await self.page.query_selector_all("[data-testid='cellInnerDiv']")

                if not cells:
                    self.log("No follower cells found", "WARNING")
                    break

                # Pick a random visible cell
                random.shuffle(cells)

                clicked_profile = False

                for cell in cells:
                    try:
                        # Find the user link in this cell
                        user_links = await cell.query_selector_all("a[role='link']")

                        for link in user_links:
                            href = await link.get_attribute("href")
                            if href and href.startswith("/") and "/status/" not in href:
                                follower_username = href.strip("/").split("/")[0]

                                # Skip if already processed or invalid
                                if (follower_username in processed_usernames or
                                    not follower_username or
                                    follower_username == target_username or
                                    '.' in follower_username):
                                    continue

                                processed_usernames.add(follower_username)

                                # Scroll cell into view
                                await self._scroll_to_element(cell)
                                await self._random_delay(0.3, 0.8)

                                # Click on the profile
                                self.log(f"Clicking on @{follower_username}'s profile")
                                await link.click()
                                await self._random_delay(2, 3)

                                clicked_profile = True
                                break

                        if clicked_profile:
                            break

                    except Exception:
                        continue

                if not clicked_profile:
                    # Scroll more to load new followers
                    self.log("Scrolling to find more followers...")
                    await self._scroll_randomly(2, 3)
                    continue

                # Now we're on the follower's profile
                current_username = await self._extract_username_from_url()

                if not current_username:
                    self.log("Could not determine profile username, going back", "WARNING")
                    await self.page.go_back()
                    await self._random_delay(1, 2)
                    continue

                self.log(f"Viewing @{current_username}'s profile")

                # Step 5: Interact with their profile
                self.log(f"Interacting with @{current_username}'s profile...")
                num_likes = random.randint(2, 3) if likes_per_profile > 0 else 0
                await self._interact_with_profile(num_likes, should_repost)

                # Step 6: Follow the user
                self.log(f"Following @{current_username}")

                # Wait for any overlays to clear (e.g., retweet confirmation)
                await self._wait_for_overlays_clear(timeout=3000)

                # Dismiss any remaining overlays
                await self._dismiss_overlays(max_attempts=2)
                await self._random_delay(0.3, 0.5)

                # Scroll up to see follow button
                await self.page.evaluate("window.scrollTo(0, 0)")
                await self._random_delay(0.5, 1)

                # Wait again for overlays (scrolling might trigger something)
                await self._wait_for_overlays_clear(timeout=2000)

                # Try to find and click follow button
                follow_btn = await self._try_selector(S.FOLLOW_BUTTON, timeout=5000)

                if follow_btn:
                    follow_success = False
                    for click_attempt in range(3):
                        try:
                            # Check for overlays before each click attempt
                            await self._wait_for_overlays_clear(timeout=2000)

                            # Try click
                            await follow_btn.click(timeout=5000)
                            follow_success = True
                            break
                        except Exception as click_err:
                            # If click fails, dismiss overlay and retry
                            self.log(f"Click attempt {click_attempt + 1} blocked, dismissing overlay", "WARNING")
                            await self._dismiss_overlays(max_attempts=3)
                            await self._random_delay(0.3, 0.5)

                            # Re-find the button (it might have moved)
                            follow_btn = await self._try_selector(S.FOLLOW_BUTTON, timeout=3000)
                            if not follow_btn:
                                break

                    if follow_success:
                        await self._random_delay(0.5, 1)
                        followed.append(current_username)
                        self.log(f"Followed @{current_username} ({len(followed)}/{max_follows})", "SUCCESS")
                    else:
                        self.log(f"Could not click follow button for @{current_username}", "WARNING")
                else:
                    # Check if already following
                    unfollow_btn = await self._try_selector(S.UNFOLLOW_BUTTON, timeout=2000, use_recovery=False)
                    if unfollow_btn:
                        self.log(f"Already following @{current_username}", "WARNING")
                    else:
                        self.log(f"Could not find follow button for @{current_username}", "WARNING")

                # Go back to followers list
                self.log("Going back to followers list...")
                await self.page.go_back()
                await self._random_delay(2, 3)

                # Random scroll on followers page before next pick
                if len(followed) < max_follows:
                    await self._scroll_randomly(1, 3)

            self.log(f"Followed {len(followed)} users from @{target_username}'s followers", "SUCCESS")
            return followed

        except Exception as e:
            self.log(f"Error in organic follow followers: {e}", "ERROR")
            return followed

    async def _extract_username_from_url(self) -> Optional[str]:
        """Extract username from current page URL"""
        try:
            current_url = self.page.url
            if 'x.com/' in current_url or 'twitter.com/' in current_url:
                # Extract username from URL like https://x.com/username
                parts = current_url.replace('https://', '').split('/')
                if len(parts) >= 2:
                    username = parts[1].split('?')[0].split('#')[0]
                    if username and '.' not in username and username not in ['home', 'search', 'explore', 'notifications', 'messages']:
                        return username
        except Exception:
            pass
        return None
