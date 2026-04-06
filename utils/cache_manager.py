"""Cache management for CreditPolicyIQ."""
import json
import hashlib
from pathlib import Path
from typing import Any, Optional, Dict
import logging

logger = logging.getLogger(__name__)


class CacheManager:
    """Simple file-based cache manager."""

    def __init__(self, cache_dir: str = "data/cache"):
        """
        Initialize cache manager.

        Args:
            cache_dir: Directory for cache files
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _get_cache_key(self, key: str) -> str:
        """Generate cache file name from key."""
        hash_key = hashlib.md5(key.encode()).hexdigest()
        return str(self.cache_dir / f"{hash_key}.json")

    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found
        """
        try:
            cache_file = self._get_cache_key(key)
            if Path(cache_file).exists():
                with open(cache_file, "r") as f:
                    data = json.load(f)
                logger.debug(f"Cache hit for key: {key}")
                return data.get("value")
        except Exception as e:
            logger.warning(f"Cache read error for {key}: {e}")
        return None

    def set(self, key: str, value: Any) -> bool:
        """
        Set value in cache.

        Args:
            key: Cache key
            value: Value to cache

        Returns:
            True if successful, False otherwise
        """
        try:
            cache_file = self._get_cache_key(key)
            with open(cache_file, "w") as f:
                json.dump({"key": key, "value": value}, f)
            logger.debug(f"Cache set for key: {key}")
            return True
        except Exception as e:
            logger.warning(f"Cache write error for {key}: {e}")
            return False

    def clear(self) -> bool:
        """
        Clear all cache.

        Returns:
            True if successful
        """
        try:
            for cache_file in self.cache_dir.glob("*.json"):
                cache_file.unlink()
            logger.info("Cache cleared")
            return True
        except Exception as e:
            logger.warning(f"Cache clear error: {e}")
            return False

    def get_multiple(self, keys: list) -> Dict[str, Any]:
        """
        Get multiple cache values.

        Args:
            keys: List of cache keys

        Returns:
            Dictionary of found values
        """
        results = {}
        for key in keys:
            value = self.get(key)
            if value is not None:
                results[key] = value
        return results


# Global cache instance
cache_manager = CacheManager()
