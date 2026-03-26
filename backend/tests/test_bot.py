"""
Tests for the Bot API routes
"""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock


class TestBotStatus:
    """Tests for bot status endpoint"""

    @pytest.mark.asyncio
    async def test_get_status_with_api_key(self, test_client, mock_settings):
        """Test status endpoint when API key is configured"""
        with patch("config.get_settings", return_value=mock_settings):
            response = await test_client.get("/api/v1/bot/status")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "ready"
            assert data["api_configured"] is True

    @pytest.mark.asyncio
    async def test_get_status_without_api_key(self, test_client, mock_settings):
        """Test status endpoint when API key is not configured"""
        mock_settings.anthropic_api_key = None
        with patch("config.get_settings", return_value=mock_settings):
            response = await test_client.get("/api/v1/bot/status")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "needs_configuration"
            assert data["api_configured"] is False


class TestBotChat:
    """Tests for bot chat endpoint"""

    @pytest.mark.asyncio
    async def test_chat_requires_api_key(self, test_client, mock_settings):
        """Test chat endpoint requires API key"""
        mock_settings.anthropic_api_key = None
        with patch("config.get_settings", return_value=mock_settings):
            response = await test_client.post(
                "/api/v1/bot/chat",
                json={"message": "Hello"}
            )
            assert response.status_code == 400
            assert "API key" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_chat_with_valid_message(self, test_client, mock_settings):
        """Test chat endpoint with valid message"""
        mock_response = MagicMock()
        mock_response.content = [
            MagicMock(type="text", text="I'll help you with that!")
        ]

        with patch("config.get_settings", return_value=mock_settings):
            with patch("anthropic.Anthropic") as mock_anthropic:
                mock_client = MagicMock()
                mock_client.messages.create.return_value = mock_response
                mock_anthropic.return_value = mock_client

                response = await test_client.post(
                    "/api/v1/bot/chat",
                    json={"message": "Follow @testuser"}
                )

                assert response.status_code == 200
                data = response.json()
                assert "message" in data

    @pytest.mark.asyncio
    async def test_chat_message_too_long(self, test_client, mock_settings):
        """Test chat endpoint rejects messages that are too long"""
        with patch("config.get_settings", return_value=mock_settings):
            long_message = "a" * 2001
            response = await test_client.post(
                "/api/v1/bot/chat",
                json={"message": long_message}
            )
            assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_chat_empty_message(self, test_client, mock_settings):
        """Test chat endpoint rejects empty messages"""
        with patch("config.get_settings", return_value=mock_settings):
            response = await test_client.post(
                "/api/v1/bot/chat",
                json={"message": ""}
            )
            assert response.status_code == 422  # Validation error


class TestBotExecute:
    """Tests for bot execute actions endpoint"""

    @pytest.mark.asyncio
    async def test_execute_without_profile_id(self, test_client, mock_settings, mock_action_service):
        """Test execute endpoint requires profile ID"""
        with patch("config.get_settings", return_value=mock_settings):
            with patch("api.dependencies.get_action_service", return_value=mock_action_service):
                response = await test_client.post(
                    "/api/v1/bot/execute",
                    json={
                        "actions": [
                            {"type": "follow_user", "params": {"username": "testuser"}, "status": "pending"}
                        ]
                    }
                )

                assert response.status_code == 200
                data = response.json()
                # Should have error because no profile_id
                assert "Error" in data["results"][0]

    @pytest.mark.asyncio
    async def test_execute_with_valid_action(self, test_client, mock_settings, mock_action_service):
        """Test execute endpoint with valid follow action"""
        with patch("config.get_settings", return_value=mock_settings):
            with patch("api.dependencies.get_action_service", return_value=mock_action_service):
                response = await test_client.post(
                    "/api/v1/bot/execute",
                    json={
                        "profile_id": "profile-123",
                        "actions": [
                            {"type": "follow_user", "params": {"username": "testuser"}, "status": "pending"}
                        ]
                    }
                )

                assert response.status_code == 200
                data = response.json()
                assert data["status"] == "queued"
                assert len(data["results"]) == 1
                assert "follow @testuser" in data["results"][0]

    @pytest.mark.asyncio
    async def test_execute_multiple_actions(self, test_client, mock_settings, mock_action_service):
        """Test execute endpoint with multiple actions"""
        with patch("config.get_settings", return_value=mock_settings):
            with patch("api.dependencies.get_action_service", return_value=mock_action_service):
                response = await test_client.post(
                    "/api/v1/bot/execute",
                    json={
                        "profile_id": "profile-123",
                        "actions": [
                            {"type": "follow_user", "params": {"username": "user1"}, "status": "pending"},
                            {"type": "follow_user", "params": {"username": "user2"}, "status": "pending"},
                        ]
                    }
                )

                assert response.status_code == 200
                data = response.json()
                assert len(data["results"]) == 2

    @pytest.mark.asyncio
    async def test_execute_unknown_action_type(self, test_client, mock_settings, mock_action_service):
        """Test execute endpoint with unknown action type"""
        with patch("config.get_settings", return_value=mock_settings):
            with patch("api.dependencies.get_action_service", return_value=mock_action_service):
                response = await test_client.post(
                    "/api/v1/bot/execute",
                    json={
                        "profile_id": "profile-123",
                        "actions": [
                            {"type": "unknown_action", "params": {}, "status": "pending"}
                        ]
                    }
                )

                assert response.status_code == 200
                data = response.json()
                assert "Error" in data["results"][0]
                assert "Unknown action type" in data["results"][0]
