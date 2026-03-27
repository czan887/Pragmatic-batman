"""
Centralized configuration for Twitter Bot v2.0
Uses pydantic-settings for environment variable management
"""
from pydantic_settings import BaseSettings
from pydantic import Field
from functools import lru_cache
from pathlib import Path


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # AdsPower Configuration
    adspower_url: str = Field(default="http://localhost:50325", description="AdsPower API URL")
    adspower_api_key: str = Field(default="", description="AdsPower API key")

    # AI API Keys
    gemini_api_key: str = Field(default="", description="Google Gemini API key")
    anthropic_api_key: str | None = Field(default=None, description="Anthropic Claude API key")

    # Database
    database_path: str = Field(default="twitter_bot.db", description="SQLite database path")

    # Server Configuration
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8080, description="Server port")
    debug: bool = Field(default=False, description="Debug mode")

    # Bot Settings
    default_batch_size: int = Field(default=15, description="Default batch size for operations")
    default_batch_delay_minutes: int = Field(default=60, description="Delay between batches in minutes")
    min_action_delay: float = Field(default=2.0, description="Minimum delay between actions in seconds")
    max_action_delay: float = Field(default=5.0, description="Maximum delay between actions in seconds")

    # AI Feature Flags
    ai_model: str = Field(default="gemini-2.0-flash", description="Default AI model")
    enable_profile_analysis: bool = Field(default=True, description="Enable AI profile analysis")
    enable_behavior_planning: bool = Field(default=True, description="Enable AI behavior planning")
    enable_mcp_recovery: bool = Field(default=True, description="Enable MCP self-healing selectors")

    # Logging Configuration
    log_level: str = Field(default="INFO", description="Logging level (DEBUG, INFO, WARNING, ERROR)")
    log_dir: str = Field(default="logs", description="Directory for log files")
    log_file: str = Field(default="twitter_bot.log", description="Log file name")
    log_rotation: str = Field(default="10 MB", description="Log rotation size")
    log_retention: str = Field(default="7 days", description="Log retention period")
    log_to_db: bool = Field(default=True, description="Save logs to database")

    # Security
    ssl_certfile: str | None = Field(default=None, description="SSL certificate file path")
    ssl_keyfile: str | None = Field(default=None, description="SSL key file path")
    allowed_origins: list[str] = Field(
        default=["*"],
        description="Allowed CORS origins (use * to allow all)"
    )

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore"
    }

    @property
    def database_url(self) -> str:
        """Get the database URL for async SQLite"""
        return f"sqlite+aiosqlite:///{self.database_path}"

    @property
    def log_file_path(self) -> str:
        """Get the full path for the log file"""
        return str(Path(self.log_dir) / self.log_file)

    @property
    def is_production(self) -> bool:
        """Check if running in production mode"""
        return not self.debug and self.ssl_certfile is not None


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()
