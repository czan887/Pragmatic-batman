"""
Profile management API routes
"""
from fastapi import APIRouter, Depends, HTTPException, status

from db.models import Profile, ProfileWithActions, ProfileUpdate
from services.profile_service import ProfileService
from api.dependencies import get_profile_service

router = APIRouter()


@router.get("/", response_model=list[Profile])
async def list_profiles(
    service: ProfileService = Depends(get_profile_service)
):
    """
    List all profiles

    Returns all profiles stored in the database.
    """
    return await service.get_all()


@router.post("/sync")
async def sync_profiles(
    service: ProfileService = Depends(get_profile_service)
):
    """
    Sync profiles from AdsPower

    Fetches all profiles from AdsPower API and updates the local database.
    Also removes profiles that no longer exist in AdsPower.
    """
    result = await service.sync_from_adspower()
    return {"status": "success", "synced": result["synced"], "deleted": result["deleted"]}


@router.get("/{profile_id}", response_model=ProfileWithActions)
async def get_profile(
    profile_id: str,
    service: ProfileService = Depends(get_profile_service)
):
    """
    Get profile details with action summary

    Returns profile information along with aggregated action statistics.
    """
    profile = await service.get_with_actions(profile_id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Profile {profile_id} not found"
        )
    return profile


@router.patch("/{profile_id}", response_model=Profile)
async def update_profile(
    profile_id: str,
    update: ProfileUpdate,
    service: ProfileService = Depends(get_profile_service)
):
    """
    Update profile information

    Updates profile fields such as name, followers count, etc.
    """
    profile = await service.update(profile_id, update)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Profile {profile_id} not found"
        )
    return profile


@router.post("/{profile_id}/open")
async def open_profile(
    profile_id: str,
    service: ProfileService = Depends(get_profile_service)
):
    """
    Open browser for profile

    Connects to AdsPower and opens the browser for this profile.
    Returns connection status.
    """
    try:
        await service.open_browser(profile_id)
        return {"status": "success", "message": f"Browser opened for profile {profile_id}"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/{profile_id}/close")
async def close_profile(
    profile_id: str,
    service: ProfileService = Depends(get_profile_service)
):
    """
    Close browser for profile

    Closes the browser and disconnects from AdsPower for this profile.
    """
    try:
        await service.close_browser(profile_id)
        return {"status": "success", "message": f"Browser closed for profile {profile_id}"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/{profile_id}/status")
async def get_profile_status(
    profile_id: str,
    service: ProfileService = Depends(get_profile_service)
):
    """
    Get profile browser status

    Returns whether the browser is currently open for this profile.
    """
    is_connected = await service.is_browser_open(profile_id)
    return {
        "profile_id": profile_id,
        "browser_open": is_connected
    }


@router.post("/{profile_id}/refresh-stats")
async def refresh_profile_stats(
    profile_id: str,
    service: ProfileService = Depends(get_profile_service)
):
    """
    Refresh profile statistics

    Opens browser, navigates to Twitter, and fetches current followers/following counts.
    """
    try:
        stats = await service.refresh_stats(profile_id)
        return {"status": "success", "stats": stats}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.delete("/{profile_id}")
async def delete_profile(
    profile_id: str,
    service: ProfileService = Depends(get_profile_service)
):
    """
    Delete a profile from the database

    Note: This only removes the profile from the local database,
    not from AdsPower.
    """
    await service.delete(profile_id)
    return {"status": "success", "message": f"Profile {profile_id} deleted"}
