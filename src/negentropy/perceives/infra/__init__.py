"""横切基础设施：缓存、指标、韧性、解析、跟踪。"""

from .cache import CacheManager, cache_manager
from .metrics import MetricsCollector, metrics_collector
from .parsing import (
    TextCleaner,
    URLValidator,
    clean_text,
    extract_domain,
    extract_emails,
    extract_phone_numbers,
    is_valid_url,
    normalize_url,
)
from .resilience import RateLimiter, RetryManager, rate_limiter, retry_manager
from .validation_trace import (
    TraceEventRecord,
    TraceRecorder,
    active_trace,
    get_recorder,
    trace_event,
)

__all__ = [
    "CacheManager",
    "cache_manager",
    "MetricsCollector",
    "metrics_collector",
    "RateLimiter",
    "RetryManager",
    "rate_limiter",
    "retry_manager",
    "TextCleaner",
    "URLValidator",
    "clean_text",
    "extract_domain",
    "extract_emails",
    "extract_phone_numbers",
    "is_valid_url",
    "normalize_url",
    "TraceEventRecord",
    "TraceRecorder",
    "active_trace",
    "get_recorder",
    "trace_event",
]
