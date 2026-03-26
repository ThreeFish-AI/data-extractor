"""In-memory cache for scraping results."""

import hashlib
import json
from datetime import datetime
from typing import Any, Dict, Optional


class CacheManager:
    """Simple in-memory cache for scraping results."""

    def __init__(self, max_size: int = 1000, ttl_seconds: int = 3600):
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.timestamps: Dict[str, datetime] = {}

    def _generate_key(
        self, url: str, method: str, config: Optional[Dict] = None
    ) -> str:
        """Generate cache key."""
        key_data = (
            f"{url}:{method}:{json.dumps(config, sort_keys=True) if config else ''}"
        )
        return hashlib.md5(key_data.encode(), usedforsecurity=False).hexdigest()

    def get(
        self, url: str, method: str, config: Optional[Dict] = None
    ) -> Optional[Dict[str, Any]]:
        """Get cached result if available and not expired."""
        key = self._generate_key(url, method, config)

        if key not in self.cache:
            return None

        # Check if expired
        if key in self.timestamps:
            age = datetime.now() - self.timestamps[key]
            if age.total_seconds() > self.ttl_seconds:
                self._remove(key)
                return None

        return self.cache.get(key)

    def set(
        self,
        url: str,
        method: str,
        result: Dict[str, Any],
        config: Optional[Dict] = None,
    ) -> None:
        """Cache result."""
        key = self._generate_key(url, method, config)

        # Ensure cache size limit
        if len(self.cache) >= self.max_size:
            self._evict_oldest()

        self.cache[key] = result.copy()
        self.timestamps[key] = datetime.now()

    def _remove(self, key: str) -> None:
        """Remove item from cache."""
        self.cache.pop(key, None)
        self.timestamps.pop(key, None)

    def _evict_oldest(self) -> None:
        """Evict oldest cache entry."""
        if not self.timestamps:
            return

        oldest_key = min(self.timestamps.keys(), key=lambda k: self.timestamps[k])
        self._remove(oldest_key)

    def clear(self) -> int:
        """Clear all cache. Returns number of cleared items."""
        count = len(self.cache)
        self.cache.clear()
        self.timestamps.clear()
        return count

    def size(self) -> int:
        """Return current number of cached items."""
        return len(self.cache)

    def stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return {
            "size": len(self.cache),
            "max_size": self.max_size,
            "ttl_seconds": self.ttl_seconds,
            "hit_ratio": 0,  # Could implement hit/miss tracking
        }


cache_manager = CacheManager(max_size=500, ttl_seconds=1800)  # 30 minutes
