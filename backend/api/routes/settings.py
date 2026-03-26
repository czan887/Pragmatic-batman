"""
Settings API routes for configuration management
"""
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import Optional
import os
from pathlib import Path

from db.models import SettingsUpdateRequest, SettingsResponse
from config import get_settings

router = APIRouter()


def mask_api_key(key: Optional[str]) -> str:
    """Mask an API key for display"""
    if not key:
        return ""
    if len(key) < 8:
        return "*" * len(key)
    return key[:4] + "*" * (len(key) - 8) + key[-4:]


@router.get("/", response_model=SettingsResponse)
async def get_current_settings():
    """
    Get current application settings

    Returns masked API keys for security.
    """
    settings = get_settings()

    return SettingsResponse(
        adspower_url=settings.adspower_url,
        adspower_api_key=mask_api_key(settings.adspower_api_key),
        gemini_api_key=mask_api_key(settings.gemini_api_key),
        anthropic_api_key=mask_api_key(settings.anthropic_api_key),
        default_batch_size=settings.default_batch_size,
        default_batch_delay_minutes=settings.default_batch_delay_minutes,
        min_action_delay=settings.min_action_delay,
        max_action_delay=settings.max_action_delay,
        enable_profile_analysis=settings.enable_profile_analysis,
        enable_behavior_planning=settings.enable_behavior_planning,
        enable_mcp_recovery=settings.enable_mcp_recovery,
        ai_model=settings.ai_model
    )


@router.patch("/")
async def update_settings(request: SettingsUpdateRequest):
    """
    Update application settings

    Updates are written to the .env file and applied on next restart.
    Some settings take effect immediately.
    """
    env_path = Path(__file__).parent.parent.parent / ".env"

    # Read existing .env content
    env_content = {}
    if env_path.exists():
        with open(env_path, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    env_content[key.strip()] = value.strip()

    # Update values from request
    updates = {}

    if request.gemini_api_key is not None:
        env_content["GEMINI_API_KEY"] = request.gemini_api_key
        updates["gemini_api_key"] = "updated"
        os.environ["GEMINI_API_KEY"] = request.gemini_api_key

    if request.anthropic_api_key is not None:
        env_content["ANTHROPIC_API_KEY"] = request.anthropic_api_key
        updates["anthropic_api_key"] = "updated"
        os.environ["ANTHROPIC_API_KEY"] = request.anthropic_api_key

    if request.adspower_api_key is not None:
        env_content["ADSPOWER_API_KEY"] = request.adspower_api_key
        updates["adspower_api_key"] = "updated"
        os.environ["ADSPOWER_API_KEY"] = request.adspower_api_key

    if request.default_batch_size is not None:
        env_content["DEFAULT_BATCH_SIZE"] = str(request.default_batch_size)
        updates["default_batch_size"] = request.default_batch_size

    if request.default_batch_delay_minutes is not None:
        env_content["DEFAULT_BATCH_DELAY_MINUTES"] = str(request.default_batch_delay_minutes)
        updates["default_batch_delay_minutes"] = request.default_batch_delay_minutes

    if request.min_action_delay is not None:
        env_content["MIN_ACTION_DELAY"] = str(request.min_action_delay)
        updates["min_action_delay"] = request.min_action_delay

    if request.max_action_delay is not None:
        env_content["MAX_ACTION_DELAY"] = str(request.max_action_delay)
        updates["max_action_delay"] = request.max_action_delay

    if request.enable_profile_analysis is not None:
        env_content["ENABLE_PROFILE_ANALYSIS"] = str(request.enable_profile_analysis).lower()
        updates["enable_profile_analysis"] = request.enable_profile_analysis

    if request.enable_behavior_planning is not None:
        env_content["ENABLE_BEHAVIOR_PLANNING"] = str(request.enable_behavior_planning).lower()
        updates["enable_behavior_planning"] = request.enable_behavior_planning

    if request.enable_mcp_recovery is not None:
        env_content["ENABLE_MCP_RECOVERY"] = str(request.enable_mcp_recovery).lower()
        updates["enable_mcp_recovery"] = request.enable_mcp_recovery

    # Write updated .env file
    try:
        with open(env_path, "w") as f:
            for key, value in env_content.items():
                f.write(f"{key}={value}\n")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to write settings: {e}"
        )

    # Clear settings cache to reload on next access
    get_settings.cache_clear()

    return {
        "status": "success",
        "message": "Settings updated successfully",
        "updates": updates,
        "note": "Some settings may require a restart to take full effect"
    }


@router.post("/test-gemini")
async def test_gemini_connection():
    """
    Test Gemini API connection

    Verifies the API key is valid and the service is reachable.
    """
    settings = get_settings()

    if not settings.gemini_api_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Gemini API key not configured"
        )

    try:
        import google.generativeai as genai
        genai.configure(api_key=settings.gemini_api_key)
        model = genai.GenerativeModel(settings.ai_model)

        # Simple test prompt
        response = model.generate_content("Say 'Connection successful'")

        return {
            "status": "success",
            "message": "Gemini API connection successful",
            "model": settings.ai_model,
            "response": response.text[:100] if response.text else "OK"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Gemini API test failed: {e}"
        )


@router.post("/test-adspower")
async def test_adspower_connection():
    """
    Test AdsPower API connection

    Verifies the API URL is reachable and API key is valid.
    """
    settings = get_settings()

    import httpx

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{settings.adspower_url}/api/v1/user/list",
                params={"page_size": 1},
                headers={"Authorization": f"Bearer {settings.adspower_api_key}"} if settings.adspower_api_key else {},
                timeout=10.0
            )

            data = response.json()

            if data.get("code") == 0:
                return {
                    "status": "success",
                    "message": "AdsPower API connection successful",
                    "url": settings.adspower_url
                }
            else:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=f"AdsPower API error: {data.get('msg', 'Unknown error')}"
                )
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"AdsPower connection failed: {e}"
        )
