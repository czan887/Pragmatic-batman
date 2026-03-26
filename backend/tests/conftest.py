"""
Pytest configuration and fixtures
"""
import pytest
import asyncio
from httpx import AsyncClient, ASGITransport
from unittest.mock import MagicMock, AsyncMock

# Set up event loop for async tests
@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_settings():
    """Mock settings for testing"""
    settings = MagicMock()
    settings.anthropic_api_key = "test-api-key"
    settings.gemini_api_key = "test-gemini-key"
    settings.adspower_url = "http://localhost:50325"
    settings.debug = True
    settings.host = "localhost"
    settings.port = 8081
    settings.allowed_origins = ["*"]
    settings.ssl_certfile = None
    settings.ssl_keyfile = None
    settings.enable_profile_analysis = False
    settings.enable_behavior_planning = False
    settings.enable_mcp_recovery = False
    return settings


@pytest.fixture
def mock_action_service():
    """Mock action service for testing"""
    service = MagicMock()
    service.follow_user = AsyncMock(return_value=True)
    service.unfollow_user = AsyncMock(return_value=True)
    service.process_post_urls = AsyncMock(return_value=True)
    service.process_hashtag = AsyncMock(return_value=True)
    service.process_user_actions = AsyncMock(return_value=True)
    service.unfollow_non_followers = AsyncMock(return_value=True)
    service.queue_follow_followers = AsyncMock(return_value="batch-123")
    service.post_tweet = AsyncMock(return_value=True)
    return service


@pytest.fixture
async def test_client(mock_settings):
    """Create a test client for the FastAPI app"""
    from unittest.mock import patch

    with patch("config.get_settings", return_value=mock_settings):
        with patch("db.database.init_db", new=AsyncMock()):
            with patch("db.database.close_db", new=AsyncMock()):
                with patch("core.playwright_manager.PlaywrightManager.create", new=AsyncMock(return_value=None)):
                    from main import create_app
                    app = create_app()

                    transport = ASGITransport(app=app)
                    async with AsyncClient(transport=transport, base_url="http://test") as client:
                        yield client
