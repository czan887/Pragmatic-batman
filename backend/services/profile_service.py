"""
Profile service - business logic for profile management
"""
from typing import Optional
import httpx

from db.repositories.profile_repo import ProfileRepository
from db.models import Profile, ProfileWithActions, ProfileUpdate
from core.playwright_manager import PlaywrightManager
from core.twitter_actions import TwitterActions
from config import get_settings
from utils.logger import setup_logger
from api.routes.websocket import broadcast_log

logger = setup_logger(__name__)


class ProfileService:
    """
    Service for managing profiles

    Handles:
    - Profile CRUD operations
    - AdsPower synchronization
    - Browser management
    - Profile statistics
    """

    def __init__(
        self,
        profile_repo: ProfileRepository,
        playwright: PlaywrightManager
    ):
        self.profile_repo = profile_repo
        self.playwright = playwright
        self.settings = get_settings()

    async def get_all(self) -> list[Profile]:
        """Get all profiles"""
        return await self.profile_repo.get_all()

    async def get_by_id(self, profile_id: str) -> Optional[Profile]:
        """Get profile by ID"""
        return await self.profile_repo.get_by_id(profile_id)

    async def get_with_actions(self, profile_id: str) -> Optional[ProfileWithActions]:
        """Get profile with action summary"""
        return await self.profile_repo.get_with_actions(profile_id)

    async def update(self, profile_id: str, update: ProfileUpdate) -> Optional[Profile]:
        """Update profile information"""
        return await self.profile_repo.update(profile_id, update)

    async def delete(self, profile_id: str):
        """Delete a profile"""
        # Close browser if open
        if await self.playwright.is_connected(profile_id):
            await self.close_browser(profile_id)

        await self.profile_repo.delete(profile_id)
        logger.info(f"Deleted profile {profile_id}")

    async def sync_from_adspower(self) -> dict:
        """
        Sync profiles from AdsPower API

        Returns:
            Dict with added, updated, and deleted counts
        """
        logger.info("Syncing profiles from AdsPower...")

        try:
            profiles_data = await self._fetch_all_profiles()
            adspower_ids = {p.get('user_id') for p in profiles_data}

            # Get existing profiles from database
            existing_profiles = await self.profile_repo.get_all()
            existing_ids = {p.user_id for p in existing_profiles}

            # Upsert profiles from AdsPower
            count = 0
            for profile_data in profiles_data:
                await self.profile_repo.upsert_from_adspower(profile_data)
                count += 1

            # Delete profiles that no longer exist in AdsPower
            deleted_count = 0
            profiles_to_delete = existing_ids - adspower_ids
            for profile_id in profiles_to_delete:
                await self.profile_repo.delete(profile_id)
                deleted_count += 1
                logger.info(f"Deleted profile {profile_id} (no longer in AdsPower)")

            logger.info(f"Synced {count} profiles, deleted {deleted_count} from AdsPower")
            await broadcast_log("SUCCESS", f"Synced {count} profiles, deleted {deleted_count} obsolete profiles")
            return {"synced": count, "deleted": deleted_count}

        except Exception as e:
            logger.error(f"Failed to sync profiles: {e}")
            await broadcast_log("ERROR", f"Failed to sync profiles: {e}")
            raise

    async def _fetch_all_profiles(self) -> list[dict]:
        """Fetch all profiles from AdsPower API"""
        all_profiles = []
        page = 1
        page_size = 100

        async with httpx.AsyncClient(timeout=30.0) as client:
            headers = {}
            if self.settings.adspower_api_key:
                headers["Authorization"] = f"Bearer {self.settings.adspower_api_key}"

            while True:
                url = f"{self.settings.adspower_url}/api/v1/user/list"
                params = {"page": page, "page_size": page_size}

                response = await client.get(url, params=params, headers=headers)
                data = response.json()

                if data.get("code") != 0:
                    raise Exception(f"AdsPower API error: {data.get('msg')}")

                profiles = data.get("data", {}).get("list", [])
                if not profiles:
                    break

                all_profiles.extend(profiles)

                if len(profiles) < page_size:
                    break

                page += 1

        return all_profiles

    async def open_browser(self, profile_id: str):
        """
        Open browser for a profile

        Connects to AdsPower and opens the browser.
        """
        logger.info(f"Opening browser for profile {profile_id}")
        await broadcast_log("INFO", f"Opening browser for profile {profile_id}", profile_id)

        try:
            await self.playwright.connect_to_adspower(profile_id)
            await broadcast_log("SUCCESS", f"Browser opened for profile {profile_id}", profile_id)
        except Exception as e:
            await broadcast_log("ERROR", f"Failed to open browser: {e}", profile_id)
            raise

    async def close_browser(self, profile_id: str):
        """
        Close browser for a profile

        Closes the browser and disconnects from AdsPower.
        """
        logger.info(f"Closing browser for profile {profile_id}")
        await broadcast_log("INFO", f"Closing browser for profile {profile_id}", profile_id)

        try:
            await self.playwright.close_profile(profile_id)
            await broadcast_log("SUCCESS", f"Browser closed for profile {profile_id}", profile_id)
        except Exception as e:
            await broadcast_log("ERROR", f"Failed to close browser: {e}", profile_id)
            raise

    async def is_browser_open(self, profile_id: str) -> bool:
        """Check if browser is open for a profile"""
        return await self.playwright.is_connected(profile_id)

    async def refresh_stats(self, profile_id: str) -> dict:
        """
        Refresh profile statistics from Twitter

        Opens browser, navigates to Twitter, and fetches current stats.
        """
        logger.info(f"Refreshing stats for profile {profile_id}")
        await broadcast_log("INFO", f"Refreshing stats for profile {profile_id}", profile_id)

        # Ensure browser is open
        page = await self.playwright.get_page(profile_id)
        if not page:
            page = await self.playwright.connect_to_adspower(profile_id)

        # Create Twitter actions helper
        actions = TwitterActions(page, profile_id)

        try:
            # Get the profile's Twitter username from domain_name
            profile = await self.profile_repo.get_by_id(profile_id)
            username = profile.domain_name if profile else None

            # Get stats from Twitter (will auto-detect username if domain_name is invalid)
            stats = await actions.get_profile_stats(username)

            # Update in database
            await self.profile_repo.update_followers_following(
                profile_id,
                stats["followers_count"],
                stats["following_count"],
                stats.get("bio"),
                stats.get("location")
            )

            await broadcast_log(
                "SUCCESS",
                f"Updated stats: {stats['followers_count']} followers, {stats['following_count']} following",
                profile_id
            )

            return stats

        except Exception as e:
            await broadcast_log("ERROR", f"Failed to refresh stats: {e}", profile_id)
            raise

    async def get_connected_profiles(self) -> list[str]:
        """Get list of profiles with open browsers"""
        return await self.playwright.get_connected_profiles()
