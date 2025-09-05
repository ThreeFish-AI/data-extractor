"""Utility functions for the Data Extractor MCP Server."""

import asyncio
import hashlib
import json
import logging
import time
from typing import Dict, Any, List, Optional
from urllib.parse import urlparse
import re
from functools import wraps
from dataclasses import dataclass, asdict
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class ScrapingResult:
    """Standard result format for scraping operations."""

    url: str
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    timestamp: Optional[datetime] = None
    duration_ms: Optional[int] = None
    method_used: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = asdict(self)
        if self.timestamp:
            result["timestamp"] = self.timestamp.isoformat()
        return result


class RateLimiter:
    """Simple rate limiter for requests."""

    def __init__(self, requests_per_second: float = 1.0):
        self.requests_per_second = requests_per_second
        self.min_interval = 1.0 / requests_per_second
        self.last_request_time = 0.0

    async def wait(self):
        """Wait if necessary to respect rate limit."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time

        if time_since_last < self.min_interval:
            sleep_time = self.min_interval - time_since_last
            await asyncio.sleep(sleep_time)

        self.last_request_time = time.time()


class RetryManager:
    """Handle retry logic with exponential backoff."""

    def __init__(
        self, max_retries: int = 3, base_delay: float = 1.0, backoff_factor: float = 2.0
    ):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.backoff_factor = backoff_factor

    async def retry_async(self, func, *args, **kwargs):
        """Retry an async function with exponential backoff."""
        last_exception = None

        for attempt in range(self.max_retries + 1):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                last_exception = e

                if attempt == self.max_retries:
                    break

                delay = self.base_delay * (self.backoff_factor**attempt)
                logger.warning(
                    f"Attempt {attempt + 1} failed: {str(e)}. Retrying in {delay:.2f}s..."
                )
                await asyncio.sleep(delay)

        raise last_exception


def timing_decorator(func):
    """Decorator to measure function execution time."""

    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            duration_ms = int((time.time() - start_time) * 1000)

            if isinstance(result, dict) and "duration_ms" not in result:
                result["duration_ms"] = duration_ms

            return result
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            logger.error(
                f"Function {func.__name__} failed after {duration_ms}ms: {str(e)}"
            )
            raise

    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            duration_ms = int((time.time() - start_time) * 1000)

            if isinstance(result, dict) and "duration_ms" not in result:
                result["duration_ms"] = duration_ms

            return result
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            logger.error(
                f"Function {func.__name__} failed after {duration_ms}ms: {str(e)}"
            )
            raise

    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper


class URLValidator:
    """Validate and normalize URLs."""

    @staticmethod
    def is_valid_url(url: str) -> bool:
        """Check if URL is valid."""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except Exception:
            return False

    @staticmethod
    def normalize_url(url: str) -> str:
        """Normalize URL format."""
        if not url.startswith(("http://", "https://")):
            url = "https://" + url

        parsed = urlparse(url)
        # Remove fragment and normalize
        normalized = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        if parsed.query:
            normalized += f"?{parsed.query}"

        return normalized

    @staticmethod
    def extract_domain(url: str) -> str:
        """Extract domain from URL."""
        return urlparse(url).netloc


class TextCleaner:
    """Clean and process extracted text."""

    @staticmethod
    def clean_text(text: str) -> str:
        """Clean extracted text."""
        if not text:
            return ""

        # Remove extra whitespace
        text = re.sub(r"\s+", " ", text)
        # Remove control characters
        text = re.sub(r"[\x00-\x1f\x7f-\x9f]", "", text)
        # Strip leading/trailing whitespace
        text = text.strip()

        return text

    @staticmethod
    def extract_emails(text: str) -> List[str]:
        """Extract email addresses from text."""
        email_pattern = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
        return re.findall(email_pattern, text)

    @staticmethod
    def extract_phone_numbers(text: str) -> List[str]:
        """Extract phone numbers from text."""
        # Basic phone number patterns
        phone_patterns = [
            r"\b\d{3}-\d{3}-\d{4}\b",  # 123-456-7890
            r"\b\(\d{3}\)\s*\d{3}-\d{4}\b",  # (123) 456-7890
            r"\b\d{3}\.\d{3}\.\d{4}\b",  # 123.456.7890
            r"\b\d{10}\b",  # 1234567890
        ]

        phone_numbers = []
        for pattern in phone_patterns:
            phone_numbers.extend(re.findall(pattern, text))

        return phone_numbers

    @staticmethod
    def truncate_text(text: str, max_length: int = 1000) -> str:
        """Truncate text to maximum length."""
        if len(text) <= max_length:
            return text

        return text[:max_length] + "..."


class ConfigValidator:
    """Validate extraction configurations."""

    @staticmethod
    def validate_extract_config(config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and normalize extraction configuration."""
        if not isinstance(config, dict):
            raise ValueError("Extract config must be a dictionary")

        validated_config = {}

        for key, value in config.items():
            if isinstance(value, str):
                # Simple CSS selector
                validated_config[key] = {"selector": value, "multiple": True}
            elif isinstance(value, dict):
                # Complex configuration
                if "selector" not in value:
                    raise ValueError(f"Missing 'selector' for key '{key}'")

                validated_config[key] = {
                    "selector": value["selector"],
                    "attr": value.get("attr", "text"),
                    "multiple": value.get("multiple", False),
                    "type": value.get("type", "css"),
                }
            else:
                raise ValueError(f"Invalid config value for key '{key}'")

        return validated_config


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
        return hashlib.md5(key_data.encode()).hexdigest()

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
    ):
        """Cache result."""
        key = self._generate_key(url, method, config)

        # Ensure cache size limit
        if len(self.cache) >= self.max_size:
            self._evict_oldest()

        self.cache[key] = result.copy()
        self.timestamps[key] = datetime.now()

    def _remove(self, key: str):
        """Remove item from cache."""
        self.cache.pop(key, None)
        self.timestamps.pop(key, None)

    def _evict_oldest(self):
        """Evict oldest cache entry."""
        if not self.timestamps:
            return

        oldest_key = min(self.timestamps.keys(), key=lambda k: self.timestamps[k])
        self._remove(oldest_key)

    def clear(self):
        """Clear all cache."""
        self.cache.clear()
        self.timestamps.clear()

    def stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return {
            "size": len(self.cache),
            "max_size": self.max_size,
            "ttl_seconds": self.ttl_seconds,
            "hit_ratio": 0,  # Could implement hit/miss tracking
        }


class ErrorHandler:
    """Centralized error handling."""

    @staticmethod
    def handle_scraping_error(e: Exception, url: str, method: str) -> Dict[str, Any]:
        """Handle scraping errors and return standardized error response."""
        error_type = type(e).__name__
        error_message = str(e)

        logger.error(
            f"Scraping error for {url} using {method}: {error_type}: {error_message}"
        )

        # Categorize common errors
        if "timeout" in error_message.lower():
            category = "timeout"
            user_message = (
                "Request timed out. The website might be slow or unavailable."
            )
        elif "connection" in error_message.lower():
            category = "connection"
            user_message = (
                "Connection failed. Please check the URL and your internet connection."
            )
        elif "404" in error_message:
            category = "not_found"
            user_message = "Page not found (404). Please verify the URL is correct."
        elif "403" in error_message:
            category = "forbidden"
            user_message = (
                "Access forbidden (403). The website might be blocking scraping."
            )
        elif "cloudflare" in error_message.lower():
            category = "anti_bot"
            user_message = "Anti-bot protection detected. Try using stealth mode or a different method."
        else:
            category = "unknown"
            user_message = "An unexpected error occurred while scraping."

        return {
            "success": False,
            "error": {
                "type": error_type,
                "message": error_message,
                "category": category,
                "user_message": user_message,
                "url": url,
                "method": method,
                "timestamp": datetime.now().isoformat(),
            },
        }


class MetricsCollector:
    """Collect scraping metrics."""

    def __init__(self):
        self.metrics = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "total_duration_ms": 0,
            "methods_used": {},
            "error_categories": {},
            "domains_scraped": set(),
        }

    def record_request(
        self,
        url: str,
        success: bool,
        duration_ms: int,
        method: str,
        error_category: Optional[str] = None,
    ):
        """Record scraping request metrics."""
        self.metrics["total_requests"] += 1
        self.metrics["total_duration_ms"] += duration_ms

        if success:
            self.metrics["successful_requests"] += 1
        else:
            self.metrics["failed_requests"] += 1
            if error_category:
                self.metrics["error_categories"][error_category] = (
                    self.metrics["error_categories"].get(error_category, 0) + 1
                )

        # Track method usage
        self.metrics["methods_used"][method] = (
            self.metrics["methods_used"].get(method, 0) + 1
        )

        # Track domains
        domain = URLValidator.extract_domain(url)
        self.metrics["domains_scraped"].add(domain)

    def get_stats(self) -> Dict[str, Any]:
        """Get current metrics."""
        stats = self.metrics.copy()
        stats["domains_scraped"] = list(stats["domains_scraped"])
        stats["success_rate"] = self.metrics["successful_requests"] / max(
            1, self.metrics["total_requests"]
        )
        stats["average_duration_ms"] = self.metrics["total_duration_ms"] / max(
            1, self.metrics["total_requests"]
        )
        return stats

    def reset(self):
        """Reset metrics."""
        self.metrics = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "total_duration_ms": 0,
            "methods_used": {},
            "error_categories": {},
            "domains_scraped": set(),
        }


# Global instances
rate_limiter = RateLimiter(requests_per_second=2.0)
retry_manager = RetryManager(max_retries=3)
cache_manager = CacheManager(max_size=500, ttl_seconds=1800)  # 30 minutes
metrics_collector = MetricsCollector()
