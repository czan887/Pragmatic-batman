"""
Tests for the File Import API routes
"""
import pytest
import io
from unittest.mock import patch


class TestFileImport:
    """Tests for file import endpoint"""

    @pytest.mark.asyncio
    async def test_import_txt_file(self, test_client, mock_settings):
        """Test importing a text file"""
        with patch("config.get_settings", return_value=mock_settings):
            content = "user1\nuser2\nuser3"
            files = {
                "file": ("usernames.txt", io.BytesIO(content.encode()), "text/plain")
            }

            response = await test_client.post(
                "/api/v1/import",
                files=files
            )

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert len(data["items"]) == 3
            assert "user1" in data["items"]

    @pytest.mark.asyncio
    async def test_import_csv_file(self, test_client, mock_settings):
        """Test importing a CSV file"""
        with patch("config.get_settings", return_value=mock_settings):
            content = "username\nuser1\nuser2\nuser3"
            files = {
                "file": ("usernames.csv", io.BytesIO(content.encode()), "text/csv")
            }

            response = await test_client.post(
                "/api/v1/import",
                files=files
            )

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            # CSV header should be excluded
            assert len(data["items"]) >= 1

    @pytest.mark.asyncio
    async def test_import_empty_file(self, test_client, mock_settings):
        """Test importing an empty file"""
        with patch("config.get_settings", return_value=mock_settings):
            content = ""
            files = {
                "file": ("empty.txt", io.BytesIO(content.encode()), "text/plain")
            }

            response = await test_client.post(
                "/api/v1/import",
                files=files
            )

            assert response.status_code == 200
            data = response.json()
            assert len(data["items"]) == 0

    @pytest.mark.asyncio
    async def test_validate_file_valid(self, test_client, mock_settings):
        """Test validating a valid file"""
        with patch("config.get_settings", return_value=mock_settings):
            content = "user1\nuser2"
            files = {
                "file": ("usernames.txt", io.BytesIO(content.encode()), "text/plain")
            }

            response = await test_client.post(
                "/api/v1/import/validate",
                files=files
            )

            assert response.status_code == 200
            data = response.json()
            assert data["valid"] is True

    @pytest.mark.asyncio
    async def test_import_with_whitespace(self, test_client, mock_settings):
        """Test importing a file with extra whitespace"""
        with patch("config.get_settings", return_value=mock_settings):
            content = "  user1  \n  user2  \n\n  user3  "
            files = {
                "file": ("usernames.txt", io.BytesIO(content.encode()), "text/plain")
            }

            response = await test_client.post(
                "/api/v1/import",
                files=files
            )

            assert response.status_code == 200
            data = response.json()
            # Items should be trimmed and empty lines removed
            assert "user1" in data["items"]
