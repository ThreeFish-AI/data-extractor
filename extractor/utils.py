"""Backward-compatible re-exports. Import from specific modules for new code."""

from .models import ScrapingResult
from .rate_limiter import RateLimiter, rate_limiter
from .retry import RetryManager, retry_manager
from .timing import timing_decorator
from .url_utils import URLValidator
from .text_utils import TextCleaner
from .config_validator import ConfigValidator
from .cache import CacheManager, cache_manager
from .error_handler import ErrorHandler
from .metrics import MetricsCollector, metrics_collector

__all__ = [
    "ScrapingResult",
    "RateLimiter",
    "rate_limiter",
    "RetryManager",
    "retry_manager",
    "timing_decorator",
    "URLValidator",
    "TextCleaner",
    "ConfigValidator",
    "CacheManager",
    "cache_manager",
    "ErrorHandler",
    "MetricsCollector",
    "metrics_collector",
]
