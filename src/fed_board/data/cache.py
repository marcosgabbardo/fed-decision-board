"""Caching layer for FRED API responses."""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class CacheEntry(BaseModel):
    """A cached data entry."""

    data: Any = Field(..., description="Cached data")
    cached_at: datetime = Field(
        default_factory=datetime.now,
        description="When the data was cached",
    )
    ttl_seconds: int = Field(
        ...,
        description="Time-to-live in seconds",
    )

    @property
    def is_expired(self) -> bool:
        """Check if the cache entry has expired."""
        age = (datetime.now() - self.cached_at).total_seconds()
        return age > self.ttl_seconds

    @property
    def age_seconds(self) -> float:
        """Get the age of the cache entry in seconds."""
        return (datetime.now() - self.cached_at).total_seconds()


class FREDCache:
    """File-based cache for FRED API responses."""

    def __init__(self, cache_dir: Path, ttl_monthly: int = 86400, ttl_daily: int = 3600) -> None:
        """
        Initialize the cache.

        Args:
            cache_dir: Directory to store cache files
            ttl_monthly: TTL for monthly data in seconds (default: 24h)
            ttl_daily: TTL for daily data in seconds (default: 1h)
        """
        self.cache_dir = cache_dir
        self.ttl_monthly = ttl_monthly
        self.ttl_daily = ttl_daily
        self._ensure_cache_dir()

    def _ensure_cache_dir(self) -> None:
        """Ensure the cache directory exists."""
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _get_cache_path(self, series_id: str) -> Path:
        """Get the cache file path for a series."""
        return self.cache_dir / f"{series_id.lower()}.json"

    def get(self, series_id: str) -> dict[str, Any] | None:
        """
        Get cached data for a series if available and not expired.

        Args:
            series_id: FRED series ID

        Returns:
            Cached data or None if not available/expired
        """
        cache_path = self._get_cache_path(series_id)
        if not cache_path.exists():
            return None

        try:
            with open(cache_path, "r") as f:
                raw_data = json.load(f)

            entry = CacheEntry(**raw_data)
            if entry.is_expired:
                # Clean up expired cache
                cache_path.unlink(missing_ok=True)
                return None

            return entry.data
        except (json.JSONDecodeError, ValueError):
            # Corrupted cache file
            cache_path.unlink(missing_ok=True)
            return None

    def set(
        self,
        series_id: str,
        data: dict[str, Any],
        frequency: str = "monthly",
    ) -> None:
        """
        Cache data for a series.

        Args:
            series_id: FRED series ID
            data: Data to cache
            frequency: Data frequency ('monthly', 'daily', 'weekly', 'quarterly')
        """
        ttl = self._get_ttl(frequency)
        entry = CacheEntry(data=data, ttl_seconds=ttl)

        cache_path = self._get_cache_path(series_id)
        with open(cache_path, "w") as f:
            json.dump(entry.model_dump(mode="json"), f, default=str)

    def _get_ttl(self, frequency: str) -> int:
        """Get TTL based on data frequency."""
        if frequency in ("daily", "weekly"):
            return self.ttl_daily
        return self.ttl_monthly

    def invalidate(self, series_id: str) -> bool:
        """
        Invalidate (delete) cached data for a series.

        Args:
            series_id: FRED series ID

        Returns:
            True if cache was deleted, False if it didn't exist
        """
        cache_path = self._get_cache_path(series_id)
        if cache_path.exists():
            cache_path.unlink()
            return True
        return False

    def clear(self) -> int:
        """
        Clear all cached data.

        Returns:
            Number of cache entries cleared
        """
        count = 0
        for cache_file in self.cache_dir.glob("*.json"):
            cache_file.unlink()
            count += 1
        return count

    def get_stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        cache_files = list(self.cache_dir.glob("*.json"))
        total_size = sum(f.stat().st_size for f in cache_files)

        valid_count = 0
        expired_count = 0

        for cache_file in cache_files:
            try:
                with open(cache_file, "r") as f:
                    raw_data = json.load(f)
                entry = CacheEntry(**raw_data)
                if entry.is_expired:
                    expired_count += 1
                else:
                    valid_count += 1
            except (json.JSONDecodeError, ValueError):
                expired_count += 1

        return {
            "total_entries": len(cache_files),
            "valid_entries": valid_count,
            "expired_entries": expired_count,
            "total_size_bytes": total_size,
            "total_size_kb": total_size / 1024,
            "cache_dir": str(self.cache_dir),
        }
