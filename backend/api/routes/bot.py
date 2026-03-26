"""
AI Bot Chat Route - Claude-powered conversational interface for Twitter automation
Uses Claude's tool use capabilities to interpret natural language and execute Twitter actions
"""
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import json
import re
from anthropic import Anthropic

from config import get_settings
from utils.logger import setup_logger
from services.action_service import ActionService
from api.dependencies import get_action_service
from api.routes.websocket import broadcast_log

logger = setup_logger(__name__)
router = APIRouter()


async def log_bot_action(message: str, level: str = "INFO", profile_id: str = None):
    """Log a bot action with broadcast"""
    logger.info(message)
    await broadcast_log(level, f"[AI Bot] {message}", profile_id)


class BotAction(BaseModel):
    """Represents a planned bot action"""
    type: str
    target: Optional[str] = None
    params: Optional[Dict[str, Any]] = None
    status: str = "pending"
    result: Optional[str] = None


class ChatMessageRequest(BaseModel):
    """Request model for chat messages"""
    message: str = Field(..., min_length=1, max_length=2000)
    profile_id: Optional[str] = None
    conversation_history: Optional[List[Dict[str, str]]] = None


class ChatMessageResponse(BaseModel):
    """Response model for chat messages"""
    message: str
    actions: Optional[List[BotAction]] = None
    profile_used: Optional[str] = None


class ExecuteActionsRequest(BaseModel):
    """Request model for executing planned actions"""
    actions: List[BotAction]
    profile_id: Optional[str] = None


class ExecuteActionsResponse(BaseModel):
    """Response model for action execution"""
    status: str
    results: List[str]


# Define available tools for Claude
TWITTER_TOOLS = [
    {
        "name": "follow_user",
        "description": "Follow a Twitter user by their username",
        "input_schema": {
            "type": "object",
            "properties": {
                "username": {
                    "type": "string",
                    "description": "The Twitter username to follow (without @ symbol)"
                }
            },
            "required": ["username"]
        }
    },
    {
        "name": "unfollow_user",
        "description": "Unfollow a Twitter user by their username",
        "input_schema": {
            "type": "object",
            "properties": {
                "username": {
                    "type": "string",
                    "description": "The Twitter username to unfollow (without @ symbol)"
                }
            },
            "required": ["username"]
        }
    },
    {
        "name": "like_tweet",
        "description": "Like a specific tweet by its URL",
        "input_schema": {
            "type": "object",
            "properties": {
                "tweet_url": {
                    "type": "string",
                    "description": "The full URL of the tweet to like"
                }
            },
            "required": ["tweet_url"]
        }
    },
    {
        "name": "retweet",
        "description": "Retweet a specific tweet by its URL",
        "input_schema": {
            "type": "object",
            "properties": {
                "tweet_url": {
                    "type": "string",
                    "description": "The full URL of the tweet to retweet"
                }
            },
            "required": ["tweet_url"]
        }
    },
    {
        "name": "post_tweet",
        "description": "Create and post a new tweet",
        "input_schema": {
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "The text content of the tweet (max 280 characters)"
                },
                "use_ai": {
                    "type": "boolean",
                    "description": "Whether to use AI to generate or enhance the tweet"
                },
                "topic": {
                    "type": "string",
                    "description": "Topic for AI-generated tweet (if use_ai is true)"
                }
            },
            "required": ["text"]
        }
    },
    {
        "name": "process_hashtag",
        "description": "Search a hashtag and perform actions on found tweets",
        "input_schema": {
            "type": "object",
            "properties": {
                "hashtag": {
                    "type": "string",
                    "description": "The hashtag to search (without # symbol)"
                },
                "actions": {
                    "type": "array",
                    "items": {"type": "string", "enum": ["like", "retweet", "comment", "refactor"]},
                    "description": "Actions to perform on found tweets"
                },
                "max_posts": {
                    "type": "integer",
                    "description": "Maximum number of posts to process"
                }
            },
            "required": ["hashtag"]
        }
    },
    {
        "name": "process_user_timeline",
        "description": "Process tweets from a user's timeline with specified actions",
        "input_schema": {
            "type": "object",
            "properties": {
                "username": {
                    "type": "string",
                    "description": "The Twitter username whose timeline to process"
                },
                "actions": {
                    "type": "array",
                    "items": {"type": "string", "enum": ["like", "retweet", "comment", "refactor"]},
                    "description": "Actions to perform on the user's tweets"
                },
                "max_tweets": {
                    "type": "integer",
                    "description": "Maximum number of tweets to process"
                }
            },
            "required": ["username"]
        }
    },
    {
        "name": "unfollow_non_followers",
        "description": "Unfollow users who don't follow you back",
        "input_schema": {
            "type": "object",
            "properties": {
                "max_unfollow": {
                    "type": "integer",
                    "description": "Maximum number of users to unfollow"
                }
            }
        }
    },
    {
        "name": "follow_followers",
        "description": "Follow the followers of a specified user",
        "input_schema": {
            "type": "object",
            "properties": {
                "target_username": {
                    "type": "string",
                    "description": "Username whose followers to follow"
                },
                "count": {
                    "type": "integer",
                    "description": "Number of followers to follow"
                }
            },
            "required": ["target_username"]
        }
    }
]

SYSTEM_PROMPT = """You are a helpful Twitter Bot Assistant. You help users automate their Twitter activities using natural language commands.

You have access to tools that can:
- Follow/Unfollow users
- Like and retweet tweets
- Post new tweets (with optional AI generation)
- Process hashtags (like, retweet, comment on posts from hashtag searches)
- Process user timelines (interact with a user's recent posts)
- Unfollow non-followers
- Follow followers of other accounts

When the user gives you a command:
1. Understand what they want to accomplish
2. Use the appropriate tool(s) to plan the actions
3. Explain what actions you're planning to take
4. Wait for confirmation before executing

Be conversational and helpful. If you need more information, ask clarifying questions.
Always explain what actions you plan to take before using tools.

Important:
- Remove @ symbols from usernames when using tools
- Twitter/X URLs can be twitter.com or x.com
- For hashtags, remove the # symbol
- Keep tweet content under 280 characters
"""


def get_anthropic_client():
    """Get Anthropic client instance"""
    settings = get_settings()
    if not settings.anthropic_api_key:
        raise HTTPException(
            status_code=400,
            detail="Anthropic API key not configured. Please add it in Settings."
        )
    return Anthropic(api_key=settings.anthropic_api_key)


def parse_tool_calls(response) -> List[BotAction]:
    """Parse tool calls from Claude's response into BotAction list"""
    actions = []

    for block in response.content:
        if block.type == "tool_use":
            action = BotAction(
                type=block.name,
                target=block.input.get("username") or block.input.get("tweet_url") or block.input.get("hashtag") or block.input.get("target_username"),
                params=block.input,
                status="pending"
            )
            actions.append(action)

    return actions


def extract_text_response(response) -> str:
    """Extract text content from Claude's response"""
    text_parts = []
    for block in response.content:
        if block.type == "text":
            text_parts.append(block.text)
    return "\n".join(text_parts) if text_parts else "I'll help you with that."


@router.post("/chat", response_model=ChatMessageResponse)
async def chat(request: ChatMessageRequest):
    """
    Send a message to the AI Bot and receive a response with planned actions
    """
    try:
        await log_bot_action(f"Processing message: {request.message[:50]}...", "INFO", request.profile_id)

        client = get_anthropic_client()

        # Build conversation messages
        messages = []

        # Add conversation history if provided
        if request.conversation_history:
            for msg in request.conversation_history[-10:]:  # Keep last 10 messages for context
                if msg.get("role") in ["user", "assistant"]:
                    messages.append({
                        "role": msg["role"],
                        "content": msg["content"]
                    })

        # Add current message
        messages.append({
            "role": "user",
            "content": request.message
        })

        await log_bot_action("Sending request to Claude AI...", "INFO", request.profile_id)

        # Call Claude with tools
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            tools=TWITTER_TOOLS,
            messages=messages
        )

        # Parse response
        text_response = extract_text_response(response)
        actions = parse_tool_calls(response)

        if actions:
            await log_bot_action(f"Claude planned {len(actions)} actions", "SUCCESS", request.profile_id)
            for action in actions:
                await log_bot_action(f"  - {action.type}: {action.target or 'N/A'}", "INFO", request.profile_id)
        else:
            await log_bot_action("Claude responded (no actions planned)", "INFO", request.profile_id)

        return ChatMessageResponse(
            message=text_response,
            actions=actions if actions else None,
            profile_used=request.profile_id
        )

    except Exception as e:
        await log_bot_action(f"Error: {str(e)}", "ERROR", request.profile_id)
        logger.error(f"Bot chat error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/execute", response_model=ExecuteActionsResponse)
async def execute_actions(
    request: ExecuteActionsRequest,
    background_tasks: BackgroundTasks,
    action_service: ActionService = Depends(get_action_service)
):
    """
    Execute planned bot actions
    """
    await log_bot_action(f"Executing {len(request.actions)} actions...", "INFO", request.profile_id)
    results = []

    for action in request.actions:
        try:
            result = await execute_single_action(
                action,
                request.profile_id,
                action_service,
                background_tasks
            )
            await log_bot_action(f"Queued: {result}", "SUCCESS", request.profile_id)
            results.append(f"Queued: {result}")
        except Exception as e:
            await log_bot_action(f"Failed: {action.type} - {str(e)}", "ERROR", request.profile_id)
            results.append(f"Error: {str(e)}")

    await log_bot_action(f"Finished queueing {len(results)} actions", "SUCCESS", request.profile_id)

    return ExecuteActionsResponse(
        status="queued",
        results=results
    )


async def execute_single_action(
    action: BotAction,
    profile_id: Optional[str],
    action_service: ActionService,
    background_tasks: BackgroundTasks
) -> str:
    """Execute a single bot action using background tasks"""
    from db.models import (
        FollowRequest, PostUrlsRequest, HashtagRequest,
        UserActionsRequest, UnfollowNonFollowersRequest, FollowFollowersRequest,
        PostTweetRequest
    )

    if not profile_id:
        raise ValueError("Profile ID is required to execute actions")

    params = action.params or {}

    if action.type == "follow_user":
        username = params.get("username", "").lstrip("@")
        request = FollowRequest(
            profile_id=profile_id,
            username=username,
            use_ai_analysis=False
        )
        background_tasks.add_task(action_service.follow_user, request)
        return f"follow @{username}"

    elif action.type == "unfollow_user":
        username = params.get("username", "").lstrip("@")
        background_tasks.add_task(action_service.unfollow_user, profile_id, username)
        return f"unfollow @{username}"

    elif action.type == "like_tweet":
        tweet_url = params.get("tweet_url", "")
        request = PostUrlsRequest(
            profile_id=profile_id,
            post_urls=[tweet_url],
            should_like=True,
            should_retweet=False,
            should_comment=False,
            use_ai_comment=False,
            should_refactor=False,
            comment_template=None
        )
        background_tasks.add_task(action_service.process_post_urls, request)
        return f"like tweet"

    elif action.type == "retweet":
        tweet_url = params.get("tweet_url", "")
        request = PostUrlsRequest(
            profile_id=profile_id,
            post_urls=[tweet_url],
            should_like=False,
            should_retweet=True,
            should_comment=False,
            use_ai_comment=False,
            should_refactor=False,
            comment_template=None
        )
        background_tasks.add_task(action_service.process_post_urls, request)
        return f"retweet"

    elif action.type == "post_tweet":
        text = params.get("text", "")
        use_ai = params.get("use_ai", False)
        topic = params.get("topic", "")

        request = PostTweetRequest(
            profile_id=profile_id,
            text=text if not use_ai else None,
            use_ai_generation=use_ai,
            topic=topic if use_ai else None,
            style="informative"
        )
        background_tasks.add_task(action_service.post_tweet, request)
        return f"post tweet"

    elif action.type == "process_hashtag":
        hashtag = params.get("hashtag", "").lstrip("#")
        actions_list = params.get("actions", ["like"])
        max_posts = params.get("max_posts", 10)

        request = HashtagRequest(
            profile_id=profile_id,
            hashtags=[hashtag],
            should_like="like" in actions_list,
            should_retweet="retweet" in actions_list,
            should_comment="comment" in actions_list,
            use_ai_comment=True,
            should_refactor="refactor" in actions_list,
            comment_template=None,
            max_posts_per_hashtag=max_posts
        )
        background_tasks.add_task(action_service.process_hashtag, request)
        return f"process #{hashtag}"

    elif action.type == "process_user_timeline":
        username = params.get("username", "").lstrip("@")
        actions_list = params.get("actions", ["like"])
        max_tweets = params.get("max_tweets", 10)

        request = UserActionsRequest(
            profile_id=profile_id,
            usernames=[username],
            should_follow=False,
            should_unfollow=False,
            should_like="like" in actions_list,
            should_retweet="retweet" in actions_list,
            should_comment="comment" in actions_list,
            use_ai_comment=True,
            should_refactor="refactor" in actions_list,
            comment_template=None,
            max_tweets_per_user=max_tweets
        )
        background_tasks.add_task(action_service.process_user_actions, request)
        return f"process @{username} timeline"

    elif action.type == "unfollow_non_followers":
        max_unfollow = params.get("max_unfollow", 50)

        request = UnfollowNonFollowersRequest(
            profile_id=profile_id,
            max_unfollow=max_unfollow,
            delay_between_unfollows=30
        )
        background_tasks.add_task(action_service.unfollow_non_followers, request)
        return f"unfollow non-followers (max {max_unfollow})"

    elif action.type == "follow_followers":
        target_username = params.get("target_username", "").lstrip("@")
        count = params.get("count", 10)

        request = FollowFollowersRequest(
            profile_id=profile_id,
            target_username=target_username,
            batch_size=count,
            batch_delay_minutes=5,
            use_ai_analysis=False
        )
        background_tasks.add_task(action_service.queue_follow_followers, request)
        return f"follow followers of @{target_username}"

    else:
        raise ValueError(f"Unknown action type: {action.type}")


@router.get("/status")
async def get_status():
    """Get bot status"""
    settings = get_settings()
    has_api_key = bool(settings.anthropic_api_key)

    return {
        "status": "ready" if has_api_key else "needs_configuration",
        "active_agents": 0,
        "api_configured": has_api_key
    }
