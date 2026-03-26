"""
Action service - business logic for bot actions
"""
from typing import Optional
import uuid
import asyncio

from db.repositories.profile_repo import ProfileRepository
from db.repositories.action_repo import ActionRepository
from db.repositories.task_repo import TaskRepository
from db.models import (
    Task, TaskCreate, TaskType, TaskStatus,
    FollowRequest, FollowFollowersRequest, TimelineRequest, PostTweetRequest,
    BulkFollowRequest, BulkUnfollowRequest, BulkLikeRequest,
    BulkRetweetRequest, BulkCommentRequest, MultiProfileActionRequest,
    HashtagRequest, PostUrlsRequest, UserActionsRequest,
    UnfollowNonFollowersRequest, RefactorPostRequest
)
from core.playwright_manager import PlaywrightManager
from core.twitter_actions import TwitterActions
from ai.profile_analyzer import ProfileAnalyzer
from ai.content_generator import ContentGenerator
from ai.behavior_planner import BehaviorPlanner
from ai.selector_finder import SelectorFinder
from config import get_settings
from utils.logger import setup_logger
from api.routes.websocket import broadcast_log

logger = setup_logger(__name__)


class ActionService:
    """
    Service for executing bot actions

    Handles:
    - Individual actions (follow, like, comment, etc.)
    - Batch operations
    - AI-powered decisions
    - Action logging
    """

    def __init__(
        self,
        profile_repo: ProfileRepository,
        action_repo: ActionRepository,
        task_repo: TaskRepository,
        playwright: PlaywrightManager
    ):
        self.profile_repo = profile_repo
        self.action_repo = action_repo
        self.task_repo = task_repo
        self.playwright = playwright
        self.settings = get_settings()

        # AI components
        self.profile_analyzer = ProfileAnalyzer()
        self.content_generator = ContentGenerator()
        self.behavior_planner = BehaviorPlanner()
        self.selector_finder = SelectorFinder()

        # Stop flags per profile
        self._stop_flags: dict[str, bool] = {}

    def _log(self, message: str, level: str = "INFO", profile_id: Optional[str] = None):
        """Log with broadcast"""
        getattr(logger, level.lower(), logger.info)(message)
        asyncio.create_task(broadcast_log(level, message, profile_id))

    async def _get_twitter_actions(self, profile_id: str) -> TwitterActions:
        """Get Twitter actions helper for a profile"""
        page = await self.playwright.get_page(profile_id)
        if not page:
            page = await self.playwright.connect_to_adspower(profile_id)

        return TwitterActions(
            page=page,
            profile_id=profile_id,
            log_callback=lambda msg, lvl="INFO": self._log(msg, lvl, profile_id),
            selector_finder=self.selector_finder if self.settings.enable_mcp_recovery else None
        )

    async def follow_user(self, request: FollowRequest):
        """
        Follow a user with optional AI analysis

        Args:
            request: Follow request parameters
        """
        profile_id = request.profile_id
        username = request.username

        self._log(f"Following @{username}", "INFO", profile_id)

        try:
            actions = await self._get_twitter_actions(profile_id)

            # AI profile analysis if enabled
            if request.use_ai_analysis and self.settings.enable_profile_analysis:
                try:
                    profile_data = await actions.get_profile_stats(username)
                    profile_data["username"] = username

                    score = await self.profile_analyzer.analyze(profile_data)

                    if not score.should_follow:
                        self._log(
                            f"Skipping @{username}: {score.reason} (score: {score.score:.2f})",
                            "WARNING",
                            profile_id
                        )
                        await self.action_repo.log_completed(profile_id, "follow", username, False)
                        return

                    self._log(
                        f"AI approved @{username}: {score.reason} (score: {score.score:.2f})",
                        "INFO",
                        profile_id
                    )
                except Exception as e:
                    self._log(f"AI analysis failed, proceeding anyway: {e}", "WARNING", profile_id)

            # Add delay based on behavior planner
            delay = self.behavior_planner.get_next_delay()
            await asyncio.sleep(delay)

            # Execute follow
            success = await actions.follow_user(username)

            # Log action
            await self.action_repo.log_completed(profile_id, "follow", username, success)

        except Exception as e:
            self._log(f"Error following @{username}: {e}", "ERROR", profile_id)
            await self.action_repo.log_completed(profile_id, "follow", username, False)

    async def unfollow_user(self, profile_id: str, username: str):
        """Unfollow a user"""
        self._log(f"Unfollowing @{username}", "INFO", profile_id)

        try:
            actions = await self._get_twitter_actions(profile_id)

            delay = self.behavior_planner.get_next_delay()
            await asyncio.sleep(delay)

            success = await actions.unfollow_user(username)
            await self.action_repo.log_completed(profile_id, "unfollow", username, success)

        except Exception as e:
            self._log(f"Error unfollowing @{username}: {e}", "ERROR", profile_id)
            await self.action_repo.log_completed(profile_id, "unfollow", username, False)

    async def queue_follow_followers(self, request: FollowFollowersRequest) -> str:
        """
        Follow target's followers with organic, human-like behavior

        Flow:
        1. Open the followers page of target user
        2. Scroll randomly
        3. Click on a follower's profile
        4. Interact with their profile (scroll, like 2-3 posts, repost)
        5. Follow the user
        6. Move to next follower

        Returns:
            Batch ID
        """
        profile_id = request.profile_id
        target = request.target_username

        self._log(f"Starting organic follow of @{target}'s followers", "INFO", profile_id)

        try:
            actions = await self._get_twitter_actions(profile_id)

            # Log assigned
            batch_id = str(uuid.uuid4())
            await self.action_repo.log_assigned(
                profile_id,
                "follow",
                f"followers_of_{target}",
                request.batch_size
            )

            # Use organic follow method
            followed = await actions.follow_followers_organic(
                target_username=target,
                max_follows=request.batch_size,
                likes_per_profile=2,
                should_repost=True
            )

            # Log completed follows
            for username in followed:
                await self.action_repo.log_completed(profile_id, "follow", username, True)

            if not followed:
                self._log(f"No followers could be followed from @{target}", "WARNING", profile_id)
            else:
                self._log(
                    f"Organically followed {len(followed)} users from @{target}'s followers",
                    "SUCCESS",
                    profile_id
                )

            return batch_id

        except Exception as e:
            self._log(f"Error following followers: {e}", "ERROR", profile_id)
            raise

    async def process_timeline(self, request: TimelineRequest):
        """
        Process a user's timeline with selected actions

        Like, retweet, and/or comment on tweets.
        """
        profile_id = request.profile_id
        username = request.username

        self._log(f"Processing timeline of @{username}", "INFO", profile_id)

        try:
            actions = await self._get_twitter_actions(profile_id)

            # Get timeline tweets
            tweets = await actions.get_timeline_tweets(username, request.max_tweets)

            if not tweets:
                self._log(f"No tweets found for @{username}", "WARNING", profile_id)
                return

            self._log(f"Found {len(tweets)} tweets to process", "INFO", profile_id)

            processed = 0
            for tweet in tweets:
                if self._stop_flags.get(profile_id, False):
                    self._log("Processing stopped by user", "WARNING", profile_id)
                    break

                tweet_element = tweet["element"]
                tweet_text = tweet["text"]
                tweet_url = tweet["url"]

                # Add natural delay
                delay = self.behavior_planner.get_next_delay()
                await asyncio.sleep(delay)

                # Like if requested
                if request.should_like:
                    success = await actions.like_tweet(tweet_element)
                    await self.action_repo.log_completed(profile_id, "like", username, success)

                # Retweet if requested
                if request.should_retweet:
                    await asyncio.sleep(1)
                    success = await actions.retweet(tweet_element)
                    await self.action_repo.log_completed(profile_id, "retweet", username, success)

                # Comment if requested
                if request.should_comment and tweet_url:
                    await asyncio.sleep(2)

                    comment = request.comment_template
                    if request.use_ai_comment:
                        try:
                            comment = await self.content_generator.generate_comment(tweet_text)
                        except Exception as e:
                            self._log(f"AI comment generation failed: {e}", "WARNING", profile_id)

                    if comment:
                        success = await actions.post_comment(tweet_url, comment)
                        await self.action_repo.log_completed(profile_id, "comment", username, success)

                processed += 1

                # Check for break
                should_break, break_duration = self.behavior_planner.should_take_break(processed)
                if should_break:
                    self._log(f"Taking a {break_duration:.0f}s break", "INFO", profile_id)
                    await asyncio.sleep(break_duration)

            self._log(f"Processed {processed} tweets from @{username}", "SUCCESS", profile_id)

        except Exception as e:
            self._log(f"Error processing timeline: {e}", "ERROR", profile_id)

    async def post_tweet(self, request: PostTweetRequest):
        """Post a new tweet"""
        profile_id = request.profile_id

        self._log("Posting tweet", "INFO", profile_id)

        try:
            actions = await self._get_twitter_actions(profile_id)

            text = request.text
            if request.use_ai_generation and request.topic:
                try:
                    text = await self.content_generator.generate_tweet(
                        request.topic,
                        request.style
                    )
                except Exception as e:
                    self._log(f"AI tweet generation failed: {e}", "ERROR", profile_id)
                    return

            if not text:
                self._log("No tweet text provided", "ERROR", profile_id)
                return

            delay = self.behavior_planner.get_next_delay()
            await asyncio.sleep(delay)

            success = await actions.post_tweet(text)
            await self.action_repo.log_completed(profile_id, "tweet", "post", success)

        except Exception as e:
            self._log(f"Error posting tweet: {e}", "ERROR", profile_id)
            await self.action_repo.log_completed(profile_id, "tweet", "post", False)

    async def post_comment(
        self,
        profile_id: str,
        tweet_url: str,
        comment: Optional[str] = None,
        use_ai_generation: bool = False
    ):
        """Post a comment on a tweet"""
        self._log(f"Commenting on tweet", "INFO", profile_id)

        try:
            actions = await self._get_twitter_actions(profile_id)

            if use_ai_generation:
                # Navigate to get tweet text for context
                await actions.page.goto(tweet_url, wait_until="networkidle")
                await asyncio.sleep(2)

                tweet_text_el = await actions.page.query_selector("[data-testid='tweetText']")
                tweet_text = await tweet_text_el.inner_text() if tweet_text_el else ""

                try:
                    comment = await self.content_generator.generate_comment(tweet_text)
                except Exception as e:
                    self._log(f"AI comment generation failed: {e}", "ERROR", profile_id)
                    return

            if not comment:
                self._log("No comment text", "ERROR", profile_id)
                return

            delay = self.behavior_planner.get_next_delay()
            await asyncio.sleep(delay)

            success = await actions.post_comment(tweet_url, comment)
            await self.action_repo.log_completed(profile_id, "comment", "manual", success)

        except Exception as e:
            self._log(f"Error posting comment: {e}", "ERROR", profile_id)
            await self.action_repo.log_completed(profile_id, "comment", "manual", False)

    async def like_tweet(self, profile_id: str, tweet_url: str):
        """Like a specific tweet"""
        self._log(f"Liking tweet", "INFO", profile_id)

        try:
            actions = await self._get_twitter_actions(profile_id)

            await actions.page.goto(tweet_url, wait_until="networkidle")
            await asyncio.sleep(2)

            tweet_el = await actions.page.query_selector("[data-testid='tweet']")
            if tweet_el:
                delay = self.behavior_planner.get_next_delay()
                await asyncio.sleep(delay)

                success = await actions.like_tweet(tweet_el)
                await self.action_repo.log_completed(profile_id, "like", "manual", success)
            else:
                self._log("Tweet element not found", "ERROR", profile_id)

        except Exception as e:
            self._log(f"Error liking tweet: {e}", "ERROR", profile_id)
            await self.action_repo.log_completed(profile_id, "like", "manual", False)

    async def retweet(self, profile_id: str, tweet_url: str):
        """Retweet a specific tweet"""
        self._log(f"Retweeting", "INFO", profile_id)

        try:
            actions = await self._get_twitter_actions(profile_id)

            await actions.page.goto(tweet_url, wait_until="networkidle")
            await asyncio.sleep(2)

            tweet_el = await actions.page.query_selector("[data-testid='tweet']")
            if tweet_el:
                delay = self.behavior_planner.get_next_delay()
                await asyncio.sleep(delay)

                success = await actions.retweet(tweet_el)
                await self.action_repo.log_completed(profile_id, "retweet", "manual", success)
            else:
                self._log("Tweet element not found", "ERROR", profile_id)

        except Exception as e:
            self._log(f"Error retweeting: {e}", "ERROR", profile_id)
            await self.action_repo.log_completed(profile_id, "retweet", "manual", False)

    async def get_history(self, profile_id: str) -> list[dict]:
        """Get action history for a profile"""
        actions = await self.action_repo.get_by_profile(profile_id)
        return [
            {
                "action_type": a.action_type,
                "action_name": a.action_name,
                "assigned": a.assigned_count,
                "completed": a.completed_count,
                "failed": a.failed_count,
                "success_rate": a.success_rate,
                "last_updated": a.last_updated
            }
            for a in actions
        ]

    async def get_statistics(self) -> dict:
        """Get overall action statistics"""
        return await self.action_repo.get_statistics()

    async def stop_actions(self, profile_id: str):
        """Stop all actions for a profile"""
        self._stop_flags[profile_id] = True
        self._log("Stopping actions", "WARNING", profile_id)

        # Cancel pending tasks
        tasks = await self.task_repo.get_by_profile(profile_id)
        for task in tasks:
            if task.status == TaskStatus.PENDING:
                await self.task_repo.update_status(task.id, TaskStatus.CANCELLED)

    def resume_actions(self, profile_id: str):
        """Resume actions for a profile"""
        self._stop_flags[profile_id] = False

    # ==================== BULK ACTIONS ====================

    async def bulk_follow(self, request: BulkFollowRequest) -> str:
        """
        Queue bulk follow of multiple users

        Returns:
            Batch ID
        """
        profile_id = request.profile_id

        self._log(f"Queuing bulk follow of {len(request.usernames)} users", "INFO", profile_id)

        batch_id = str(uuid.uuid4())
        tasks = []

        for username in request.usernames:
            tasks.append(TaskCreate(
                profile_id=profile_id,
                task_type=TaskType.FOLLOW,
                task_data={
                    "target": username,
                    "use_ai_analysis": request.use_ai_analysis,
                    "delay": request.delay_between_follows
                },
                batch_id=batch_id
            ))

        await self.task_repo.create_batch(tasks)

        # Log assigned
        await self.action_repo.log_assigned(
            profile_id,
            "follow",
            "bulk_follow",
            len(request.usernames)
        )

        self._log(
            f"Queued {len(request.usernames)} bulk follow tasks",
            "SUCCESS",
            profile_id
        )

        return batch_id

    async def bulk_unfollow(self, request: BulkUnfollowRequest) -> str:
        """
        Queue bulk unfollow of multiple users

        Returns:
            Batch ID
        """
        profile_id = request.profile_id

        self._log(f"Queuing bulk unfollow of {len(request.usernames)} users", "INFO", profile_id)

        batch_id = str(uuid.uuid4())
        tasks = []

        for username in request.usernames:
            tasks.append(TaskCreate(
                profile_id=profile_id,
                task_type=TaskType.UNFOLLOW,
                task_data={
                    "target": username,
                    "delay": request.delay_between_unfollows
                },
                batch_id=batch_id
            ))

        await self.task_repo.create_batch(tasks)

        await self.action_repo.log_assigned(
            profile_id,
            "unfollow",
            "bulk_unfollow",
            len(request.usernames)
        )

        self._log(
            f"Queued {len(request.usernames)} bulk unfollow tasks",
            "SUCCESS",
            profile_id
        )

        return batch_id

    async def bulk_like(self, request: BulkLikeRequest) -> str:
        """
        Queue bulk like of multiple tweets

        Returns:
            Batch ID
        """
        profile_id = request.profile_id

        self._log(f"Queuing bulk like of {len(request.tweet_urls)} tweets", "INFO", profile_id)

        batch_id = str(uuid.uuid4())
        tasks = []

        for tweet_url in request.tweet_urls:
            tasks.append(TaskCreate(
                profile_id=profile_id,
                task_type=TaskType.LIKE,
                task_data={
                    "tweet_url": tweet_url,
                    "delay": request.delay_between_likes
                },
                batch_id=batch_id
            ))

        await self.task_repo.create_batch(tasks)

        await self.action_repo.log_assigned(
            profile_id,
            "like",
            "bulk_like",
            len(request.tweet_urls)
        )

        self._log(
            f"Queued {len(request.tweet_urls)} bulk like tasks",
            "SUCCESS",
            profile_id
        )

        return batch_id

    async def bulk_retweet(self, request: BulkRetweetRequest) -> str:
        """
        Queue bulk retweet of multiple tweets

        Returns:
            Batch ID
        """
        profile_id = request.profile_id

        self._log(f"Queuing bulk retweet of {len(request.tweet_urls)} tweets", "INFO", profile_id)

        batch_id = str(uuid.uuid4())
        tasks = []

        for tweet_url in request.tweet_urls:
            tasks.append(TaskCreate(
                profile_id=profile_id,
                task_type=TaskType.RETWEET,
                task_data={
                    "tweet_url": tweet_url,
                    "delay": request.delay_between_retweets
                },
                batch_id=batch_id
            ))

        await self.task_repo.create_batch(tasks)

        await self.action_repo.log_assigned(
            profile_id,
            "retweet",
            "bulk_retweet",
            len(request.tweet_urls)
        )

        self._log(
            f"Queued {len(request.tweet_urls)} bulk retweet tasks",
            "SUCCESS",
            profile_id
        )

        return batch_id

    async def bulk_comment(self, request: BulkCommentRequest) -> str:
        """
        Queue bulk comment on multiple tweets

        Returns:
            Batch ID
        """
        profile_id = request.profile_id

        self._log(f"Queuing bulk comment on {len(request.tweet_urls)} tweets", "INFO", profile_id)

        batch_id = str(uuid.uuid4())
        tasks = []

        for tweet_url in request.tweet_urls:
            tasks.append(TaskCreate(
                profile_id=profile_id,
                task_type=TaskType.COMMENT,
                task_data={
                    "tweet_url": tweet_url,
                    "use_ai_generation": request.use_ai_generation,
                    "comment_template": request.comment_template,
                    "delay": request.delay_between_comments
                },
                batch_id=batch_id
            ))

        await self.task_repo.create_batch(tasks)

        await self.action_repo.log_assigned(
            profile_id,
            "comment",
            "bulk_comment",
            len(request.tweet_urls)
        )

        self._log(
            f"Queued {len(request.tweet_urls)} bulk comment tasks",
            "SUCCESS",
            profile_id
        )

        return batch_id

    async def multi_profile_action(self, request: MultiProfileActionRequest) -> str:
        """
        Execute an action across multiple profiles

        Returns:
            Batch ID
        """
        self._log(f"Queuing {request.action_type} action for {len(request.profile_ids)} profiles", "INFO")

        batch_id = str(uuid.uuid4())
        tasks = []

        # Map action type to TaskType
        action_type_map = {
            "follow": TaskType.FOLLOW,
            "unfollow": TaskType.UNFOLLOW,
            "like": TaskType.LIKE,
            "retweet": TaskType.RETWEET,
            "comment": TaskType.COMMENT
        }

        task_type = action_type_map.get(request.action_type)
        if not task_type:
            raise ValueError(f"Unknown action type: {request.action_type}")

        for profile_id in request.profile_ids:
            tasks.append(TaskCreate(
                profile_id=profile_id,
                task_type=task_type,
                task_data={
                    "target": request.target,
                    "use_ai": request.use_ai,
                    "delay": request.delay_between_profiles,
                    "multi_profile": True
                },
                batch_id=batch_id
            ))

            await self.action_repo.log_assigned(
                profile_id,
                request.action_type,
                f"multi_profile_{request.target}",
                1
            )

        await self.task_repo.create_batch(tasks)

        self._log(
            f"Queued {request.action_type} action for {len(request.profile_ids)} profiles",
            "SUCCESS"
        )

        return batch_id

    async def get_batch_status(self, batch_id: str) -> dict:
        """
        Get status of a bulk action batch

        Returns:
            Batch status with progress
        """
        tasks = await self.task_repo.get_by_batch(batch_id)

        if not tasks:
            return {
                "batch_id": batch_id,
                "found": False,
                "message": "Batch not found"
            }

        total = len(tasks)
        pending = sum(1 for t in tasks if t.status == TaskStatus.PENDING)
        in_progress = sum(1 for t in tasks if t.status == TaskStatus.IN_PROGRESS)
        completed = sum(1 for t in tasks if t.status == TaskStatus.COMPLETED)
        failed = sum(1 for t in tasks if t.status == TaskStatus.FAILED)
        cancelled = sum(1 for t in tasks if t.status == TaskStatus.CANCELLED)

        progress = ((completed + failed + cancelled) / total) * 100 if total > 0 else 0

        return {
            "batch_id": batch_id,
            "found": True,
            "total": total,
            "pending": pending,
            "in_progress": in_progress,
            "completed": completed,
            "failed": failed,
            "cancelled": cancelled,
            "progress": round(progress, 1),
            "status": "completed" if pending == 0 and in_progress == 0 else "in_progress"
        }

    # ==================== NEW METHODS FOR TKINTER PARITY ====================

    async def process_hashtag(self, request: HashtagRequest):
        """
        Process posts from hashtag searches

        Search for hashtags and perform actions on found tweets.
        """
        profile_id = request.profile_id

        self._log(f"Processing {len(request.hashtags)} hashtags", "INFO", profile_id)

        try:
            actions = await self._get_twitter_actions(profile_id)

            total_processed = 0
            for hashtag in request.hashtags:
                if self._stop_flags.get(profile_id, False):
                    self._log("Processing stopped by user", "WARNING", profile_id)
                    break

                self._log(f"Searching hashtag #{hashtag}", "INFO", profile_id)

                # Search for hashtag tweets
                tweets = await actions.search_hashtag(hashtag, request.max_posts_per_hashtag)

                if not tweets:
                    self._log(f"No tweets found for #{hashtag}", "WARNING", profile_id)
                    continue

                self._log(f"Found {len(tweets)} tweets for #{hashtag}", "INFO", profile_id)

                for tweet in tweets:
                    if self._stop_flags.get(profile_id, False):
                        break

                    tweet_url = tweet.get("url", "")
                    tweet_text = tweet.get("text", "")
                    tweet_element = tweet.get("element")

                    # Add natural delay
                    delay = self.behavior_planner.get_next_delay()
                    await asyncio.sleep(delay)

                    # Like if requested
                    if request.should_like and tweet_element:
                        success = await actions.like_tweet(tweet_element)
                        await self.action_repo.log_completed(profile_id, "like", f"hashtag_{hashtag}", success)

                    # Retweet if requested
                    if request.should_retweet and tweet_element:
                        await asyncio.sleep(1)
                        success = await actions.retweet(tweet_element)
                        await self.action_repo.log_completed(profile_id, "retweet", f"hashtag_{hashtag}", success)

                    # Comment if requested
                    if request.should_comment and tweet_url:
                        await asyncio.sleep(2)
                        comment = request.comment_template
                        if request.use_ai_comment:
                            try:
                                comment = await self.content_generator.generate_comment(tweet_text)
                            except Exception as e:
                                self._log(f"AI comment generation failed: {e}", "WARNING", profile_id)

                        if comment:
                            success = await actions.post_comment(tweet_url, comment)
                            await self.action_repo.log_completed(profile_id, "comment", f"hashtag_{hashtag}", success)

                    # Refactor/repost if requested
                    if request.should_refactor and tweet_text:
                        await asyncio.sleep(2)
                        try:
                            refactored_text = await self.content_generator.refactor_tweet(tweet_text)
                            if refactored_text:
                                success = await actions.post_tweet(refactored_text)
                                await self.action_repo.log_completed(profile_id, "refactor", f"hashtag_{hashtag}", success)
                        except Exception as e:
                            self._log(f"Refactor failed: {e}", "WARNING", profile_id)

                    total_processed += 1

                    # Check for break
                    should_break, break_duration = self.behavior_planner.should_take_break(total_processed)
                    if should_break:
                        self._log(f"Taking a {break_duration:.0f}s break", "INFO", profile_id)
                        await asyncio.sleep(break_duration)

            self._log(f"Processed {total_processed} tweets from hashtags", "SUCCESS", profile_id)

        except Exception as e:
            self._log(f"Error processing hashtags: {e}", "ERROR", profile_id)

    async def process_post_urls(self, request: PostUrlsRequest):
        """
        Process actions on specific post URLs

        Navigate to each post URL and perform selected actions.
        """
        profile_id = request.profile_id

        self._log(f"Processing {len(request.post_urls)} post URLs", "INFO", profile_id)

        try:
            actions = await self._get_twitter_actions(profile_id)

            processed = 0
            for tweet_url in request.post_urls:
                if self._stop_flags.get(profile_id, False):
                    self._log("Processing stopped by user", "WARNING", profile_id)
                    break

                self._log(f"Processing {tweet_url}", "INFO", profile_id)

                # Navigate to tweet
                if not await actions.navigate_to_tweet(tweet_url):
                    await self.action_repo.log_completed(profile_id, "process_url", tweet_url, False)
                    continue

                tweet_element = await actions.get_tweet_element()
                tweet_text = await actions.get_tweet_text(tweet_url)

                # Add natural delay
                delay = self.behavior_planner.get_next_delay()
                await asyncio.sleep(delay)

                # Like if requested
                if request.should_like and tweet_element:
                    success = await actions.like_tweet(tweet_element)
                    await self.action_repo.log_completed(profile_id, "like", tweet_url, success)

                # Retweet if requested
                if request.should_retweet and tweet_element:
                    await asyncio.sleep(1)
                    success = await actions.retweet(tweet_element)
                    await self.action_repo.log_completed(profile_id, "retweet", tweet_url, success)

                # Comment if requested
                if request.should_comment:
                    await asyncio.sleep(2)
                    comment = request.comment_template
                    if request.use_ai_comment:
                        try:
                            comment = await self.content_generator.generate_comment(tweet_text)
                        except Exception as e:
                            self._log(f"AI comment generation failed: {e}", "WARNING", profile_id)

                    if comment:
                        success = await actions.post_comment(tweet_url, comment)
                        await self.action_repo.log_completed(profile_id, "comment", tweet_url, success)

                # Refactor/repost if requested
                if request.should_refactor and tweet_text:
                    await asyncio.sleep(2)
                    try:
                        refactored_text = await self.content_generator.refactor_tweet(tweet_text)
                        if refactored_text:
                            success = await actions.post_tweet(refactored_text)
                            await self.action_repo.log_completed(profile_id, "refactor", tweet_url, success)
                    except Exception as e:
                        self._log(f"Refactor failed: {e}", "WARNING", profile_id)

                processed += 1

                # Check for break
                should_break, break_duration = self.behavior_planner.should_take_break(processed)
                if should_break:
                    self._log(f"Taking a {break_duration:.0f}s break", "INFO", profile_id)
                    await asyncio.sleep(break_duration)

            self._log(f"Processed {processed} post URLs", "SUCCESS", profile_id)

        except Exception as e:
            self._log(f"Error processing post URLs: {e}", "ERROR", profile_id)

    async def process_user_actions(self, request: UserActionsRequest):
        """
        Process actions on users (follow, unfollow, timeline actions)

        Similar to Tkinter User Actions tab functionality.
        """
        profile_id = request.profile_id

        self._log(f"Processing {len(request.usernames)} users", "INFO", profile_id)

        try:
            actions = await self._get_twitter_actions(profile_id)

            processed = 0
            for username in request.usernames:
                if self._stop_flags.get(profile_id, False):
                    self._log("Processing stopped by user", "WARNING", profile_id)
                    break

                self._log(f"Processing user @{username}", "INFO", profile_id)

                # Add natural delay
                delay = self.behavior_planner.get_next_delay()
                await asyncio.sleep(delay)

                # Follow if requested
                if request.should_follow:
                    success = await actions.follow_user(username)
                    await self.action_repo.log_completed(profile_id, "follow", username, success)

                # Unfollow if requested
                if request.should_unfollow:
                    await asyncio.sleep(1)
                    success = await actions.unfollow_user(username)
                    await self.action_repo.log_completed(profile_id, "unfollow", username, success)

                # Process timeline if any timeline actions requested
                if request.should_like or request.should_retweet or request.should_comment or request.should_refactor:
                    tweets = await actions.get_timeline_tweets(username, request.max_tweets_per_user)

                    for tweet in tweets:
                        if self._stop_flags.get(profile_id, False):
                            break

                        tweet_element = tweet.get("element")
                        tweet_url = tweet.get("url", "")
                        tweet_text = tweet.get("text", "")

                        delay = self.behavior_planner.get_next_delay()
                        await asyncio.sleep(delay)

                        if request.should_like and tweet_element:
                            success = await actions.like_tweet(tweet_element)
                            await self.action_repo.log_completed(profile_id, "like", username, success)

                        if request.should_retweet and tweet_element:
                            await asyncio.sleep(1)
                            success = await actions.retweet(tweet_element)
                            await self.action_repo.log_completed(profile_id, "retweet", username, success)

                        if request.should_comment and tweet_url:
                            await asyncio.sleep(2)
                            comment = request.comment_template
                            if request.use_ai_comment:
                                try:
                                    comment = await self.content_generator.generate_comment(tweet_text)
                                except Exception as e:
                                    self._log(f"AI comment generation failed: {e}", "WARNING", profile_id)

                            if comment:
                                success = await actions.post_comment(tweet_url, comment)
                                await self.action_repo.log_completed(profile_id, "comment", username, success)

                        if request.should_refactor and tweet_text:
                            await asyncio.sleep(2)
                            try:
                                refactored_text = await self.content_generator.refactor_tweet(tweet_text)
                                if refactored_text:
                                    success = await actions.post_tweet(refactored_text)
                                    await self.action_repo.log_completed(profile_id, "refactor", username, success)
                            except Exception as e:
                                self._log(f"Refactor failed: {e}", "WARNING", profile_id)

                processed += 1

                # Check for break
                should_break, break_duration = self.behavior_planner.should_take_break(processed)
                if should_break:
                    self._log(f"Taking a {break_duration:.0f}s break", "INFO", profile_id)
                    await asyncio.sleep(break_duration)

            self._log(f"Processed {processed} users", "SUCCESS", profile_id)

        except Exception as e:
            self._log(f"Error processing users: {e}", "ERROR", profile_id)

    async def unfollow_non_followers(self, request: UnfollowNonFollowersRequest):
        """
        Unfollow users who don't follow back

        Gets following list, checks followers, unfollows non-followers.
        """
        profile_id = request.profile_id

        self._log("Starting unfollow non-followers", "INFO", profile_id)

        try:
            actions = await self._get_twitter_actions(profile_id)

            # First, get the profile's username from the page
            await actions.page.goto("https://twitter.com/home", wait_until="networkidle")
            await asyncio.sleep(2)

            # Get current user's username from the account switcher
            account_btn = await actions.page.query_selector("[data-testid='SideNav_AccountSwitcher_Button']")
            if not account_btn:
                self._log("Could not determine current user", "ERROR", profile_id)
                return

            # Click to get username from account menu
            username_el = await account_btn.query_selector("span")
            if not username_el:
                self._log("Could not determine current user", "ERROR", profile_id)
                return

            # Navigate to own profile to get username
            await account_btn.click()
            await asyncio.sleep(1)

            # Try to find Profile link in menu
            profile_link = await actions.page.query_selector("a[data-testid='AccountSwitcher_Dropdown_Menu_Profile']")
            if profile_link:
                href = await profile_link.get_attribute("href")
                current_username = href.replace("/", "") if href else None
            else:
                self._log("Could not determine current user", "ERROR", profile_id)
                # Close menu
                await actions.page.keyboard.press("Escape")
                return

            # Close menu
            await actions.page.keyboard.press("Escape")
            await asyncio.sleep(0.5)

            if not current_username:
                self._log("Could not determine current user", "ERROR", profile_id)
                return

            self._log(f"Current user: @{current_username}", "INFO", profile_id)

            # Get following list
            self._log("Fetching following list...", "INFO", profile_id)
            following = await actions.get_following(current_username, max_count=200)

            if not following:
                self._log("No following found", "WARNING", profile_id)
                return

            self._log(f"Found {len(following)} following", "INFO", profile_id)

            # Get followers list
            self._log("Fetching followers list...", "INFO", profile_id)
            followers = await actions.get_followers(current_username, max_count=500)
            followers_set = set(followers)

            self._log(f"Found {len(followers)} followers", "INFO", profile_id)

            # Find non-followers
            non_followers = [u for u in following if u not in followers_set]
            self._log(f"Found {len(non_followers)} non-followers", "INFO", profile_id)

            if not non_followers:
                self._log("No non-followers to unfollow", "SUCCESS", profile_id)
                return

            # Unfollow non-followers (up to max_unfollow)
            unfollowed = 0
            for username in non_followers[:request.max_unfollow]:
                if self._stop_flags.get(profile_id, False):
                    self._log("Processing stopped by user", "WARNING", profile_id)
                    break

                self._log(f"Unfollowing @{username}", "INFO", profile_id)

                success = await actions.unfollow_user(username)
                await self.action_repo.log_completed(profile_id, "unfollow", username, success)

                if success:
                    unfollowed += 1

                await asyncio.sleep(request.delay_between_unfollows)

            self._log(f"Unfollowed {unfollowed} non-followers", "SUCCESS", profile_id)

        except Exception as e:
            self._log(f"Error unfollowing non-followers: {e}", "ERROR", profile_id)

    async def refactor_post(self, request: RefactorPostRequest):
        """
        Refactor/rewrite a post with AI and post it

        Gets original tweet text, uses AI to rewrite, posts new version.
        """
        profile_id = request.profile_id

        self._log(f"Refactoring post: {request.original_tweet_url}", "INFO", profile_id)

        try:
            actions = await self._get_twitter_actions(profile_id)

            # Get original tweet text
            original_text = await actions.get_tweet_text(request.original_tweet_url)

            if not original_text:
                self._log("Could not get original tweet text", "ERROR", profile_id)
                return

            self._log(f"Original text: {original_text[:100]}...", "INFO", profile_id)

            # Generate refactored version
            try:
                refactored_text = await self.content_generator.refactor_tweet(
                    original_text,
                    style=request.style
                )
            except Exception as e:
                self._log(f"AI refactoring failed: {e}", "ERROR", profile_id)
                return

            if not refactored_text:
                self._log("Failed to generate refactored text", "ERROR", profile_id)
                return

            self._log(f"Refactored text: {refactored_text[:100]}...", "INFO", profile_id)

            # Post the refactored tweet
            delay = self.behavior_planner.get_next_delay()
            await asyncio.sleep(delay)

            success = await actions.post_tweet(refactored_text)
            await self.action_repo.log_completed(profile_id, "refactor", request.original_tweet_url, success)

            if success:
                self._log("Refactored post published", "SUCCESS", profile_id)
            else:
                self._log("Failed to post refactored tweet", "ERROR", profile_id)

        except Exception as e:
            self._log(f"Error refactoring post: {e}", "ERROR", profile_id)
            await self.action_repo.log_completed(profile_id, "refactor", request.original_tweet_url, False)
