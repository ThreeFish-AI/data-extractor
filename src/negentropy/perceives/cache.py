"""抓取结果的内存缓存管理。"""

import hashlib
import json
from datetime import datetime
from typing import Any, Dict, Optional


class CacheManager:
    """抓取结果的简易内存缓存管理器。"""

    def __init__(self, max_size: int = 1000, ttl_seconds: int = 3600):
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.timestamps: Dict[str, datetime] = {}

    def _generate_key(
        self, url: str, method: str, config: Optional[Dict] = None
    ) -> str:
        """生成缓存键。"""
        key_data = (
            f"{url}:{method}:{json.dumps(config, sort_keys=True) if config else ''}"
        )
        return hashlib.md5(key_data.encode(), usedforsecurity=False).hexdigest()

    def get(
        self, url: str, method: str, config: Optional[Dict] = None
    ) -> Optional[Dict[str, Any]]:
        """获取缓存结果（若存在且未过期）。"""
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
        """缓存抓取结果。"""
        key = self._generate_key(url, method, config)

        # Ensure cache size limit
        if len(self.cache) >= self.max_size:
            self._evict_oldest()

        self.cache[key] = result.copy()
        self.timestamps[key] = datetime.now()

    def _remove(self, key: str) -> None:
        """从缓存中移除条目。"""
        self.cache.pop(key, None)
        self.timestamps.pop(key, None)

    def _evict_oldest(self) -> None:
        """淘汰最旧的缓存条目。"""
        if not self.timestamps:
            return

        oldest_key = min(self.timestamps.keys(), key=lambda k: self.timestamps[k])
        self._remove(oldest_key)

    def clear(self) -> int:
        """清空所有缓存，返回被清除的条目数量。"""
        count = len(self.cache)
        self.cache.clear()
        self.timestamps.clear()
        return count

    def size(self) -> int:
        """返回当前缓存条目数量。"""
        return len(self.cache)

    def stats(self) -> Dict[str, Any]:
        """获取缓存统计信息。"""
        return {
            "size": len(self.cache),
            "max_size": self.max_size,
            "ttl_seconds": self.ttl_seconds,
            "hit_ratio": 0,  # Could implement hit/miss tracking
        }


cache_manager = CacheManager(max_size=500, ttl_seconds=1800)  # 30 minutes
