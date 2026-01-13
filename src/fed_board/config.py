"""Configuration management using Pydantic Settings."""

from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # API Keys
    anthropic_api_key: str = Field(
        ...,
        description="Anthropic API key for Claude access",
    )
    fred_api_key: str = Field(
        ...,
        description="FRED API key for economic data",
    )

    # Model Configuration
    anthropic_model: str = Field(
        default="claude-opus-4-5-20251101",
        description="Default Claude model for FOMC agents",
    )

    # Data Directory
    data_dir: Path = Field(
        default=Path("./data"),
        description="Directory for storing simulations, minutes, and cache",
    )

    # Cache Settings
    fred_cache_ttl_monthly: int = Field(
        default=86400,
        description="Cache TTL for monthly data in seconds (default: 24h)",
    )
    fred_cache_ttl_daily: int = Field(
        default=3600,
        description="Cache TTL for daily data in seconds (default: 1h)",
    )

    # Logging
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO",
        description="Logging level",
    )

    @field_validator("data_dir", mode="before")
    @classmethod
    def ensure_path(cls, v: str | Path) -> Path:
        """Convert string to Path."""
        return Path(v) if isinstance(v, str) else v

    @property
    def cache_dir(self) -> Path:
        """Get cache directory path."""
        return self.data_dir / "cache"

    @property
    def fred_cache_dir(self) -> Path:
        """Get FRED cache directory path."""
        return self.cache_dir / "fred"

    @property
    def simulations_dir(self) -> Path:
        """Get simulations directory path."""
        return self.data_dir / "simulations"

    @property
    def minutes_dir(self) -> Path:
        """Get minutes directory path."""
        return self.data_dir / "minutes"

    @property
    def dotplots_dir(self) -> Path:
        """Get dot plots directory path."""
        return self.data_dir / "dotplots"

    def ensure_directories(self) -> None:
        """Create all required directories if they don't exist."""
        for directory in [
            self.data_dir,
            self.cache_dir,
            self.fred_cache_dir,
            self.simulations_dir,
            self.minutes_dir,
            self.dotplots_dir,
        ]:
            directory.mkdir(parents=True, exist_ok=True)


def get_settings() -> Settings:
    """Get application settings singleton."""
    return Settings()
