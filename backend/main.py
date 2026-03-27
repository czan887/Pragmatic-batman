"""
Twitter Bot v2.0 - FastAPI Backend Entry Point
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import logging

from config import get_settings
from db.database import init_db, close_db
from core.playwright_manager import PlaywrightManager
from api.routes import profiles, tasks, actions, dashboard, websocket, file_import, bot, logs, stats, sessions
from api.routes import settings as settings_routes
from api.middleware import register_exception_handlers
from utils.logger import init_logger_from_settings, set_log_repository
from db.repositories.log_repo import LogRepository

# Setup logging from settings (with file logging enabled)
logger = init_logger_from_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown"""
    settings = get_settings()
    logger.info("Starting Twitter Bot v2.0...")

    # Initialize database
    await init_db()
    logger.info("Database initialized")

    # Initialize log repository for database logging
    if settings.log_to_db:
        log_repo = LogRepository()
        set_log_repository(log_repo)
        logger.info("Database logging enabled")

    # Initialize Playwright manager (lazy - will be created on first use)
    # On Windows, Playwright requires ProactorEventLoop which uvicorn doesn't use by default
    app.state.playwright = None
    try:
        app.state.playwright = await PlaywrightManager.create()
        logger.info("Playwright manager initialized")
    except NotImplementedError:
        logger.warning("Playwright initialization failed (Windows asyncio issue) - will use lazy initialization")
    except Exception as e:
        logger.warning(f"Playwright initialization failed: {e} - will use lazy initialization")

    yield

    # Shutdown
    logger.info("Shutting down Twitter Bot v2.0...")
    if app.state.playwright:
        await app.state.playwright.close()
    await close_db()
    logger.info("Shutdown complete")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application"""
    settings = get_settings()

    app = FastAPI(
        title="Twitter Bot API",
        description="Twitter automation bot with AI-powered decision making",
        version="2.0.0",
        lifespan=lifespan,
        docs_url="/api/docs" if settings.debug else None,
        redoc_url="/api/redoc" if settings.debug else None,
        openapi_url="/api/openapi.json" if settings.debug else None,
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register exception handlers for standardized error responses
    register_exception_handlers(app)

    # API Routes
    app.include_router(
        profiles.router,
        prefix="/api/v1/profiles",
        tags=["profiles"]
    )
    app.include_router(
        tasks.router,
        prefix="/api/v1/tasks",
        tags=["tasks"]
    )
    app.include_router(
        actions.router,
        prefix="/api/v1/actions",
        tags=["actions"]
    )
    app.include_router(
        dashboard.router,
        prefix="/api/v1/dashboard",
        tags=["dashboard"]
    )
    app.include_router(
        websocket.router,
        prefix="/ws",
        tags=["websocket"]
    )
    app.include_router(
        settings_routes.router,
        prefix="/api/v1/settings",
        tags=["settings"]
    )
    app.include_router(
        file_import.router,
        prefix="/api/v1/import",
        tags=["import"]
    )
    app.include_router(
        bot.router,
        prefix="/api/v1/bot",
        tags=["bot"]
    )
    app.include_router(
        logs.router,
        prefix="/api/v1/logs",
        tags=["logs"]
    )
    app.include_router(
        stats.router,
        prefix="/api/v1/stats",
        tags=["stats"]
    )
    app.include_router(
        sessions.router,
        prefix="/api/v1/sessions",
        tags=["sessions"]
    )

    # Serve frontend static files in production
    frontend_dist = Path(__file__).parent.parent / "frontend" / "dist"
    if frontend_dist.exists():
        app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="frontend")

    return app


# Create app instance
app = create_app()


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "version": "2.0.0"}


if __name__ == "__main__":
    import uvicorn
    settings = get_settings()

    uvicorn_config = {
        "app": "main:app",
        "host": settings.host,
        "port": settings.port,
        "reload": settings.debug,
    }

    if settings.ssl_certfile and settings.ssl_keyfile:
        uvicorn_config["ssl_certfile"] = settings.ssl_certfile
        uvicorn_config["ssl_keyfile"] = settings.ssl_keyfile

    uvicorn.run(**uvicorn_config)
