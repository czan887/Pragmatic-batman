"""
Tests for the Actions API routes (new Tkinter parity endpoints)
"""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock


class TestHashtagActions:
    """Tests for hashtag processing endpoint"""

    @pytest.mark.asyncio
    async def test_process_hashtag_valid(self, test_client, mock_settings, mock_action_service):
        """Test process hashtag with valid data"""
        with patch("config.get_settings", return_value=mock_settings):
            with patch("api.dependencies.get_action_service", return_value=mock_action_service):
                response = await test_client.post(
                    "/api/v1/actions/process-hashtag",
                    json={
                        "profile_id": "profile-123",
                        "hashtags": ["python", "coding"],
                        "should_like": True,
                        "should_retweet": False,
                        "should_comment": False,
                        "use_ai_comment": False,
                        "should_refactor": False,
                        "comment_template": None,
                        "max_posts_per_hashtag": 10
                    }
                )

                assert response.status_code == 200
                data = response.json()
                assert data["status"] == "queued"

    @pytest.mark.asyncio
    async def test_process_hashtag_empty_list(self, test_client, mock_settings):
        """Test process hashtag with empty hashtag list"""
        with patch("config.get_settings", return_value=mock_settings):
            response = await test_client.post(
                "/api/v1/actions/process-hashtag",
                json={
                    "profile_id": "profile-123",
                    "hashtags": [],
                    "should_like": True,
                    "max_posts_per_hashtag": 10
                }
            )

            assert response.status_code == 422  # Validation error


class TestPostUrlActions:
    """Tests for post URL processing endpoint"""

    @pytest.mark.asyncio
    async def test_process_post_urls_valid(self, test_client, mock_settings, mock_action_service):
        """Test process post URLs with valid data"""
        with patch("config.get_settings", return_value=mock_settings):
            with patch("api.dependencies.get_action_service", return_value=mock_action_service):
                response = await test_client.post(
                    "/api/v1/actions/process-post-urls",
                    json={
                        "profile_id": "profile-123",
                        "post_urls": [
                            "https://twitter.com/user/status/123456789"
                        ],
                        "should_like": True,
                        "should_retweet": True,
                        "should_comment": False,
                        "use_ai_comment": False,
                        "should_refactor": False,
                        "comment_template": None
                    }
                )

                assert response.status_code == 200
                data = response.json()
                assert data["status"] == "queued"


class TestUserActions:
    """Tests for user actions endpoint"""

    @pytest.mark.asyncio
    async def test_process_users_valid(self, test_client, mock_settings, mock_action_service):
        """Test process users with valid data"""
        with patch("config.get_settings", return_value=mock_settings):
            with patch("api.dependencies.get_action_service", return_value=mock_action_service):
                response = await test_client.post(
                    "/api/v1/actions/process-users",
                    json={
                        "profile_id": "profile-123",
                        "usernames": ["user1", "user2"],
                        "should_follow": True,
                        "should_unfollow": False,
                        "should_like": False,
                        "should_retweet": False,
                        "should_comment": False,
                        "use_ai_comment": False,
                        "should_refactor": False,
                        "comment_template": None,
                        "max_tweets_per_user": 10
                    }
                )

                assert response.status_code == 200
                data = response.json()
                assert data["status"] == "queued"


class TestUnfollowNonFollowers:
    """Tests for unfollow non-followers endpoint"""

    @pytest.mark.asyncio
    async def test_unfollow_non_followers_valid(self, test_client, mock_settings, mock_action_service):
        """Test unfollow non-followers with valid data"""
        with patch("config.get_settings", return_value=mock_settings):
            with patch("api.dependencies.get_action_service", return_value=mock_action_service):
                response = await test_client.post(
                    "/api/v1/actions/unfollow-non-followers",
                    json={
                        "profile_id": "profile-123",
                        "max_unfollow": 50,
                        "delay_between_unfollows": 30
                    }
                )

                assert response.status_code == 200
                data = response.json()
                assert data["status"] == "queued"


class TestRefactorPost:
    """Tests for refactor post endpoint"""

    @pytest.mark.asyncio
    async def test_refactor_post_valid(self, test_client, mock_settings, mock_action_service):
        """Test refactor post with valid data"""
        with patch("config.get_settings", return_value=mock_settings):
            with patch("api.dependencies.get_action_service", return_value=mock_action_service):
                response = await test_client.post(
                    "/api/v1/actions/refactor-post",
                    json={
                        "profile_id": "profile-123",
                        "original_tweet_url": "https://twitter.com/user/status/123",
                        "style": "professional"
                    }
                )

                assert response.status_code == 200
                data = response.json()
                assert data["status"] == "queued"
