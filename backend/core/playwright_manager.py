"""
Playwright browser manager for Twitter Bot v2.0
Handles browser lifecycle and AdsPower integration
"""
import sys
import asyncio

# Fix for Windows asyncio subprocess issue with Playwright
# Must be set before any event loop is created
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from playwright.async_api import async_playwright, Browser, BrowserContext, Page, Playwright
from typing import Optional
import httpx

from config import get_settings
from utils.logger import setup_logger

logger = setup_logger(__name__)


class PlaywrightManager:
    """Manages Playwright browser instances and AdsPower connections"""

    def __init__(self):
        self.playwright: Optional[Playwright] = None
        self.browsers: dict[str, Browser] = {}
        self.contexts: dict[str, BrowserContext] = {}
        self.pages: dict[str, Page] = {}
        self._lock = asyncio.Lock()

    @classmethod
    async def create(cls) -> "PlaywrightManager":
        """Factory method to create PlaywrightManager instance"""
        instance = cls()
        instance.playwright = await async_playwright().start()
        logger.info("Playwright initialized")
        return instance

    async def connect_to_adspower(self, profile_id: str) -> Page:
        """
        Connect to an AdsPower browser instance

        Args:
            profile_id: The AdsPower profile user_id

        Returns:
            Playwright Page object connected to the browser
        """
        settings = get_settings()

        async with self._lock:
            # Check if already connected
            if profile_id in self.pages:
                page = self.pages[profile_id]
                if not page.is_closed():
                    logger.info(f"Reusing existing connection for profile {profile_id}")
                    return page
                else:
                    # Clean up stale connection
                    await self._cleanup_profile(profile_id)

            # Start AdsPower profile
            async with httpx.AsyncClient(timeout=30.0) as client:
                start_url = f"{settings.adspower_url}/api/v1/browser/start"
                params = {"user_id": profile_id}
                headers = {}

                if settings.adspower_api_key:
                    headers["Authorization"] = f"Bearer {settings.adspower_api_key}"

                logger.info(f"Starting AdsPower profile: {profile_id}")
                resp = await client.get(start_url, params=params, headers=headers)
                data = resp.json()

            if data.get("code") != 0:
                error_msg = data.get("msg", "Unknown error")
                logger.error(f"AdsPower start failed: {error_msg}")
                raise Exception(f"AdsPower error: {error_msg}")

            # Get WebSocket endpoint for Playwright connection
            ws_endpoint = data["data"]["ws"]["puppeteer"]
            logger.info(f"Connecting to WebSocket: {ws_endpoint}")

            # Connect Playwright to existing browser via CDP
            browser = await self.playwright.chromium.connect_over_cdp(ws_endpoint)
            self.browsers[profile_id] = browser

            # Get existing context and page (AdsPower already has one open)
            context = browser.contexts[0] if browser.contexts else await browser.new_context()
            self.contexts[profile_id] = context

            # Get existing page or create new one
            if context.pages:
                page = context.pages[0]
            else:
                page = await context.new_page()

            self.pages[profile_id] = page

            # Close extra tabs
            for p in context.pages[1:]:
                try:
                    await p.close()
                except Exception:
                    pass

            logger.info(f"Successfully connected to profile {profile_id}")

            # Navigate to x.com (Twitter) if not already there
            try:
                current_url = page.url
                if not current_url or "x.com" not in current_url and "twitter.com" not in current_url:
                    logger.info(f"Navigating to x.com for profile {profile_id}")
                    await page.goto("https://x.com/home", wait_until="domcontentloaded", timeout=30000)
                    logger.info(f"Profile {profile_id} is now on x.com")
            except Exception as e:
                logger.warning(f"Failed to navigate to x.com for profile {profile_id}: {e}")

            return page

    async def close_profile(self, profile_id: str) -> bool:
        """
        Close an AdsPower profile and cleanup resources

        Args:
            profile_id: The AdsPower profile user_id

        Returns:
            True if successful
        """
        settings = get_settings()

        async with self._lock:
            await self._cleanup_profile(profile_id)

            # Stop AdsPower profile via API
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    stop_url = f"{settings.adspower_url}/api/v1/browser/stop"
                    params = {"user_id": profile_id}
                    headers = {}

                    if settings.adspower_api_key:
                        headers["Authorization"] = f"Bearer {settings.adspower_api_key}"

                    await client.get(stop_url, params=params, headers=headers)
                    logger.info(f"Stopped AdsPower profile: {profile_id}")
            except Exception as e:
                logger.warning(f"Failed to stop AdsPower profile {profile_id}: {e}")

            return True

    async def _cleanup_profile(self, profile_id: str):
        """Clean up resources for a profile"""
        if profile_id in self.pages:
            try:
                page = self.pages[profile_id]
                if not page.is_closed():
                    await page.close()
            except Exception:
                pass
            del self.pages[profile_id]

        if profile_id in self.contexts:
            del self.contexts[profile_id]

        if profile_id in self.browsers:
            try:
                browser = self.browsers[profile_id]
                await browser.close()
            except Exception:
                pass
            del self.browsers[profile_id]

    async def get_page(self, profile_id: str) -> Optional[Page]:
        """Get page for a profile if it exists and is still open"""
        page = self.pages.get(profile_id)
        if page and not page.is_closed():
            return page
        return None

    async def is_connected(self, profile_id: str) -> bool:
        """Check if a profile is currently connected"""
        page = await self.get_page(profile_id)
        return page is not None

    async def get_connected_profiles(self) -> list[str]:
        """Get list of currently connected profile IDs"""
        connected = []
        for profile_id, page in list(self.pages.items()):
            if not page.is_closed():
                connected.append(profile_id)
            else:
                await self._cleanup_profile(profile_id)
        return connected

    async def navigate(self, profile_id: str, url: str, wait_until: str = "networkidle") -> bool:
        """
        Navigate to a URL

        Args:
            profile_id: Profile ID
            url: URL to navigate to
            wait_until: Wait condition (load, domcontentloaded, networkidle)

        Returns:
            True if successful
        """
        page = await self.get_page(profile_id)
        if not page:
            raise Exception(f"Profile {profile_id} not connected")

        try:
            await page.goto(url, wait_until=wait_until, timeout=30000)
            return True
        except Exception as e:
            logger.error(f"Navigation failed: {e}")
            return False

    async def close(self):
        """Close all connections and shutdown Playwright"""
        logger.info("Closing Playwright manager...")

        # Close all profiles
        for profile_id in list(self.pages.keys()):
            await self.close_profile(profile_id)

        # Stop Playwright
        if self.playwright:
            await self.playwright.stop()
            self.playwright = None

        logger.info("Playwright manager closed")

    async def screenshot(self, profile_id: str, path: str) -> bool:
        """Take a screenshot of the current page"""
        page = await self.get_page(profile_id)
        if not page:
            return False

        try:
            await page.screenshot(path=path, full_page=True)
            return True
        except Exception as e:
            logger.error(f"Screenshot failed: {e}")
            return False
