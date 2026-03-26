"""
Bot action API routes
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status

from db.models import (
    FollowRequest,
    FollowFollowersRequest,
    TimelineRequest,
    PostTweetRequest,
    BulkFollowRequest,
    BulkUnfollowRequest,
    BulkLikeRequest,
    BulkRetweetRequest,
    BulkCommentRequest,
    MultiProfileActionRequest,
    BulkActionResponse,
    HashtagRequest,
    PostUrlsRequest,
    UserActionsRequest,
    UnfollowNonFollowersRequest,
    RefactorPostRequest
)
from services.action_service import ActionService
from api.dependencies import get_action_service

router = APIRouter()


@router.post("/follow")
async def follow_user(
    request: FollowRequest,
    background_tasks: BackgroundTasks,
    service: ActionService = Depends(get_action_service)
):
    """
    Follow a user

    Optionally uses AI to analyze the profile before following.
    Runs in background to avoid blocking.
    """
    background_tasks.add_task(service.follow_user, request)
    return {
        "status": "queued",
        "message": f"Following @{request.username} for profile {request.profile_id}"
    }


@router.post("/unfollow")
async def unfollow_user(
    profile_id: str,
    username: str,
    background_tasks: BackgroundTasks,
    service: ActionService = Depends(get_action_service)
):
    """
    Unfollow a user
    """
    background_tasks.add_task(service.unfollow_user, profile_id, username)
    return {
        "status": "queued",
        "message": f"Unfollowing @{username} for profile {profile_id}"
    }


@router.post("/follow-followers")
async def follow_followers(
    request: FollowFollowersRequest,
    service: ActionService = Depends(get_action_service)
):
    """
    Queue batch follow of target's followers

    Creates tasks to follow multiple users from another user's followers list.
    Tasks are processed in batches with delays to appear more natural.
    """
    task_id = await service.queue_follow_followers(request)
    return {
        "status": "queued",
        "batch_id": task_id,
        "message": f"Queued following {request.batch_size} followers of @{request.target_username}"
    }


@router.post("/process-timeline")
async def process_timeline(
    request: TimelineRequest,
    background_tasks: BackgroundTasks,
    service: ActionService = Depends(get_action_service)
):
    """
    Process a user's timeline with selected actions

    Can like, retweet, and/or comment on tweets from the target's timeline.
    Optionally uses AI to generate relevant comments.
    """
    background_tasks.add_task(service.process_timeline, request)
    return {
        "status": "queued",
        "message": f"Processing timeline of @{request.username}"
    }


@router.post("/post-tweet")
async def post_tweet(
    request: PostTweetRequest,
    background_tasks: BackgroundTasks,
    service: ActionService = Depends(get_action_service)
):
    """
    Post a new tweet

    Can post provided text or use AI to generate a tweet on a topic.
    """
    if not request.text and not request.use_ai_generation:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either text or use_ai_generation must be provided"
        )

    if request.use_ai_generation and not request.topic:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Topic is required when using AI generation"
        )

    background_tasks.add_task(service.post_tweet, request)
    return {
        "status": "queued",
        "message": f"Posting tweet for profile {request.profile_id}"
    }


@router.post("/comment")
async def post_comment(
    profile_id: str,
    tweet_url: str,
    comment: str = None,
    use_ai_generation: bool = False,
    background_tasks: BackgroundTasks = None,
    service: ActionService = Depends(get_action_service)
):
    """
    Post a comment on a tweet

    Can post provided comment or use AI to generate a relevant comment.
    """
    if not comment and not use_ai_generation:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either comment or use_ai_generation must be provided"
        )

    background_tasks.add_task(
        service.post_comment,
        profile_id,
        tweet_url,
        comment,
        use_ai_generation
    )
    return {
        "status": "queued",
        "message": f"Posting comment for profile {profile_id}"
    }


@router.post("/like")
async def like_tweet(
    profile_id: str,
    tweet_url: str,
    background_tasks: BackgroundTasks,
    service: ActionService = Depends(get_action_service)
):
    """
    Like a tweet
    """
    background_tasks.add_task(service.like_tweet, profile_id, tweet_url)
    return {
        "status": "queued",
        "message": f"Liking tweet for profile {profile_id}"
    }


@router.post("/retweet")
async def retweet(
    profile_id: str,
    tweet_url: str,
    background_tasks: BackgroundTasks,
    service: ActionService = Depends(get_action_service)
):
    """
    Retweet a tweet
    """
    background_tasks.add_task(service.retweet, profile_id, tweet_url)
    return {
        "status": "queued",
        "message": f"Retweeting for profile {profile_id}"
    }


@router.get("/history/{profile_id}")
async def get_action_history(
    profile_id: str,
    service: ActionService = Depends(get_action_service)
):
    """
    Get action history for a profile

    Returns summary of all actions performed by this profile.
    """
    return await service.get_history(profile_id)


@router.get("/statistics")
async def get_action_statistics(
    service: ActionService = Depends(get_action_service)
):
    """
    Get overall action statistics

    Returns aggregated statistics for all actions across all profiles.
    """
    return await service.get_statistics()


@router.post("/stop/{profile_id}")
async def stop_actions(
    profile_id: str,
    service: ActionService = Depends(get_action_service)
):
    """
    Stop all running actions for a profile

    Cancels any pending tasks and stops the current action.
    """
    await service.stop_actions(profile_id)
    return {
        "status": "success",
        "message": f"Stopped all actions for profile {profile_id}"
    }


# ==================== BULK ACTIONS ====================

@router.post("/bulk/follow", response_model=BulkActionResponse)
async def bulk_follow(
    request: BulkFollowRequest,
    service: ActionService = Depends(get_action_service)
):
    """
    Bulk follow multiple users

    Accepts a list of usernames to follow with configurable delays.
    Optionally uses AI to analyze each profile before following.
    """
    batch_id = await service.bulk_follow(request)
    return BulkActionResponse(
        status="queued",
        batch_id=batch_id,
        total_items=len(request.usernames),
        message=f"Queued {len(request.usernames)} users to follow for profile {request.profile_id}"
    )


@router.post("/bulk/unfollow", response_model=BulkActionResponse)
async def bulk_unfollow(
    request: BulkUnfollowRequest,
    service: ActionService = Depends(get_action_service)
):
    """
    Bulk unfollow multiple users

    Accepts a list of usernames to unfollow with configurable delays.
    """
    batch_id = await service.bulk_unfollow(request)
    return BulkActionResponse(
        status="queued",
        batch_id=batch_id,
        total_items=len(request.usernames),
        message=f"Queued {len(request.usernames)} users to unfollow for profile {request.profile_id}"
    )


@router.post("/bulk/like", response_model=BulkActionResponse)
async def bulk_like(
    request: BulkLikeRequest,
    service: ActionService = Depends(get_action_service)
):
    """
    Bulk like multiple tweets

    Accepts a list of tweet URLs to like with configurable delays.
    """
    batch_id = await service.bulk_like(request)
    return BulkActionResponse(
        status="queued",
        batch_id=batch_id,
        total_items=len(request.tweet_urls),
        message=f"Queued {len(request.tweet_urls)} tweets to like for profile {request.profile_id}"
    )


@router.post("/bulk/retweet", response_model=BulkActionResponse)
async def bulk_retweet(
    request: BulkRetweetRequest,
    service: ActionService = Depends(get_action_service)
):
    """
    Bulk retweet multiple tweets

    Accepts a list of tweet URLs to retweet with configurable delays.
    """
    batch_id = await service.bulk_retweet(request)
    return BulkActionResponse(
        status="queued",
        batch_id=batch_id,
        total_items=len(request.tweet_urls),
        message=f"Queued {len(request.tweet_urls)} tweets to retweet for profile {request.profile_id}"
    )


@router.post("/bulk/comment", response_model=BulkActionResponse)
async def bulk_comment(
    request: BulkCommentRequest,
    service: ActionService = Depends(get_action_service)
):
    """
    Bulk comment on multiple tweets

    Accepts a list of tweet URLs to comment on with AI-generated or template comments.
    """
    batch_id = await service.bulk_comment(request)
    return BulkActionResponse(
        status="queued",
        batch_id=batch_id,
        total_items=len(request.tweet_urls),
        message=f"Queued {len(request.tweet_urls)} tweets to comment for profile {request.profile_id}"
    )


@router.post("/multi-profile", response_model=BulkActionResponse)
async def multi_profile_action(
    request: MultiProfileActionRequest,
    service: ActionService = Depends(get_action_service)
):
    """
    Execute an action across multiple profiles

    Performs the same action (follow, like, retweet, etc.) using multiple profiles
    with configurable delays between each profile's execution.
    """
    batch_id = await service.multi_profile_action(request)
    return BulkActionResponse(
        status="queued",
        batch_id=batch_id,
        total_items=len(request.profile_ids),
        message=f"Queued {request.action_type} action for {len(request.profile_ids)} profiles"
    )


@router.get("/bulk/status/{batch_id}")
async def get_bulk_status(
    batch_id: str,
    service: ActionService = Depends(get_action_service)
):
    """
    Get status of a bulk action batch

    Returns progress information for a batch of actions.
    """
    return await service.get_batch_status(batch_id)


# ==================== NEW ENDPOINTS FOR TKINTER PARITY ====================

@router.post("/process-hashtag")
async def process_hashtag(
    request: HashtagRequest,
    background_tasks: BackgroundTasks,
    service: ActionService = Depends(get_action_service)
):
    """
    Process posts from hashtag searches

    Search for hashtags and perform selected actions on found tweets.
    Supports like, retweet, comment (manual/AI), and refactor.
    """
    background_tasks.add_task(service.process_hashtag, request)
    return {
        "status": "queued",
        "message": f"Processing {len(request.hashtags)} hashtags for profile {request.profile_id}"
    }


@router.post("/process-post-urls")
async def process_post_urls(
    request: PostUrlsRequest,
    background_tasks: BackgroundTasks,
    service: ActionService = Depends(get_action_service)
):
    """
    Process actions on specific post URLs

    Navigate to each post URL and perform selected actions.
    Supports like, retweet, comment (manual/AI), and refactor.
    """
    background_tasks.add_task(service.process_post_urls, request)
    return {
        "status": "queued",
        "message": f"Processing {len(request.post_urls)} post URLs for profile {request.profile_id}"
    }


@router.post("/process-users")
async def process_user_actions(
    request: UserActionsRequest,
    background_tasks: BackgroundTasks,
    service: ActionService = Depends(get_action_service)
):
    """
    Process actions on users

    Follow/unfollow users and/or perform timeline actions.
    Combined User Actions tab functionality.
    """
    background_tasks.add_task(service.process_user_actions, request)
    return {
        "status": "queued",
        "message": f"Processing {len(request.usernames)} users for profile {request.profile_id}"
    }


@router.post("/unfollow-non-followers")
async def unfollow_non_followers(
    request: UnfollowNonFollowersRequest,
    background_tasks: BackgroundTasks,
    service: ActionService = Depends(get_action_service)
):
    """
    Unfollow users who don't follow back

    Gets following list, checks followers, unfollows non-followers.
    """
    background_tasks.add_task(service.unfollow_non_followers, request)
    return {
        "status": "queued",
        "message": f"Queued unfollow non-followers (max {request.max_unfollow}) for profile {request.profile_id}"
    }


@router.post("/refactor-post")
async def refactor_post(
    request: RefactorPostRequest,
    background_tasks: BackgroundTasks,
    service: ActionService = Depends(get_action_service)
):
    """
    Refactor/rewrite a post with AI

    Gets original tweet text, uses AI to rewrite in selected style, posts new version.
    """
    background_tasks.add_task(service.refactor_post, request)
    return {
        "status": "queued",
        "message": f"Refactoring post for profile {request.profile_id}"
    }
