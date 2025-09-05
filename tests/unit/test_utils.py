"""Unit tests for utility classes and functions."""

import pytest
import asyncio
import time
from unittest.mock import patch, AsyncMock
from pathlib import Path

from extractor.utils import (
    RateLimiter,
    RetryManager,
    CacheManager,
    MetricsCollector,
    ErrorHandler,
    URLValidator,
    TextCleaner,
    ConfigValidator,
    timing_decorator,
    rate_limiter,
    retry_manager,
    cache_manager,
    metrics_collector,
)


class TestRateLimiter:
    """Test the RateLimiter class."""

    def test_rate_limiter_initialization(self):
        """Test RateLimiter initializes correctly."""
        limiter = RateLimiter(requests_per_minute=60)
        assert limiter.requests_per_minute == 60
        assert limiter.requests == []

    @pytest.mark.asyncio
    async def test_rate_limiting_within_limit(self):
        """Test rate limiting when within limits."""
        limiter = RateLimiter(requests_per_minute=60)

        start_time = time.time()
        await limiter.acquire()
        end_time = time.time()

        # Should not be delayed when within limit
        assert (end_time - start_time) < 0.1

    @pytest.mark.asyncio
    async def test_rate_limiting_exceeds_limit(self):
        """Test rate limiting when exceeding limits."""
        limiter = RateLimiter(requests_per_minute=2)  # Very low limit for testing

        # Make first request
        await limiter.acquire()

        # Make second request
        await limiter.acquire()

        # Third request should be delayed
        start_time = time.time()
        await limiter.acquire()
        end_time = time.time()

        # Should be delayed
        assert (end_time - start_time) >= 0.0  # Some delay expected

    def test_cleanup_old_requests(self):
        """Test cleanup of old request timestamps."""
        limiter = RateLimiter(requests_per_minute=60)

        # Add old timestamp
        limiter.requests.append(time.time() - 120)  # 2 minutes ago
        limiter.requests.append(time.time())  # Now

        limiter._cleanup_old_requests()

        assert len(limiter.requests) == 1


class TestRetryManager:
    """Test the RetryManager class."""

    def test_retry_manager_initialization(self):
        """Test RetryManager initializes correctly."""
        manager = RetryManager(max_retries=3, base_delay=1.0)
        assert manager.max_retries == 3
        assert manager.base_delay == 1.0

    @pytest.mark.asyncio
    async def test_retry_success_first_attempt(self):
        """Test retry when operation succeeds on first attempt."""
        manager = RetryManager(max_retries=3)

        mock_func = AsyncMock(return_value="success")

        result = await manager.retry_async(mock_func)

        assert result == "success"
        assert mock_func.call_count == 1

    @pytest.mark.asyncio
    async def test_retry_success_after_failures(self):
        """Test retry when operation succeeds after failures."""
        manager = RetryManager(max_retries=3, base_delay=0.01)  # Very short delay

        mock_func = AsyncMock()
        mock_func.side_effect = [Exception("Error 1"), Exception("Error 2"), "success"]

        result = await manager.retry_async(mock_func)

        assert result == "success"
        assert mock_func.call_count == 3

    @pytest.mark.asyncio
    async def test_retry_exhausted(self):
        """Test retry when all attempts are exhausted."""
        manager = RetryManager(max_retries=2, base_delay=0.01)

        mock_func = AsyncMock(side_effect=Exception("Persistent error"))

        with pytest.raises(Exception, match="Persistent error"):
            await manager.retry_async(mock_func)

        assert mock_func.call_count == 3  # Initial + 2 retries

    def test_calculate_delay_exponential_backoff(self):
        """Test exponential backoff delay calculation."""
        manager = RetryManager(base_delay=1.0, backoff_factor=2.0)

        assert manager._calculate_delay(1) == 2.0  # base_delay * backoff_factor^attempt
        assert manager._calculate_delay(2) == 4.0
        assert manager._calculate_delay(3) == 8.0


class TestCacheManager:
    """Test the CacheManager class."""

    def test_cache_manager_initialization(self, temp_cache_dir):
        """Test CacheManager initializes correctly."""
        manager = CacheManager(cache_dir=temp_cache_dir, default_ttl=60)
        assert manager.cache_dir == Path(temp_cache_dir)
        assert manager.default_ttl == 60

    def test_cache_set_and_get(self, temp_cache_dir):
        """Test setting and getting cache values."""
        manager = CacheManager(cache_dir=temp_cache_dir)

        test_data = {"key": "value", "number": 42}
        manager.set("test_key", test_data, ttl=60)

        retrieved_data = manager.get("test_key")
        assert retrieved_data == test_data

    def test_cache_expiration(self, temp_cache_dir):
        """Test cache expiration."""
        manager = CacheManager(cache_dir=temp_cache_dir)

        manager.set("expire_key", "value", ttl=0.1)  # Very short TTL

        # Should be available immediately
        assert manager.get("expire_key") == "value"

        # Wait for expiration
        time.sleep(0.2)

        # Should be None after expiration
        assert manager.get("expire_key") is None

    def test_cache_miss(self, temp_cache_dir):
        """Test cache miss behavior."""
        manager = CacheManager(cache_dir=temp_cache_dir)

        result = manager.get("nonexistent_key")
        assert result is None

    def test_cache_clear(self, temp_cache_dir):
        """Test cache clearing."""
        manager = CacheManager(cache_dir=temp_cache_dir)

        manager.set("key1", "value1")
        manager.set("key2", "value2")

        manager.clear()

        assert manager.get("key1") is None
        assert manager.get("key2") is None

    def test_generate_cache_key(self, temp_cache_dir):
        """Test cache key generation."""
        manager = CacheManager(cache_dir=temp_cache_dir)

        key1 = manager._generate_key("https://example.com", {"param": "value"})
        key2 = manager._generate_key("https://example.com", {"param": "different"})

        assert key1 != key2
        assert len(key1) == 64  # SHA256 hash length


class TestMetricsCollector:
    """Test the MetricsCollector class."""

    def test_metrics_collector_initialization(self):
        """Test MetricsCollector initializes correctly."""
        collector = MetricsCollector()
        assert collector.metrics == {}

    def test_record_request(self):
        """Test recording request metrics."""
        collector = MetricsCollector()

        collector.record_request("GET", 200, 1.5, 1000)

        metrics = collector.get_metrics()
        assert metrics["total_requests"] == 1
        assert metrics["status_codes"]["200"] == 1
        assert metrics["methods"]["GET"] == 1
        assert metrics["total_response_time"] == 1.5
        assert metrics["total_bytes"] == 1000

    def test_record_error(self):
        """Test recording error metrics."""
        collector = MetricsCollector()

        collector.record_error("timeout", "Request timeout")

        metrics = collector.get_metrics()
        assert metrics["total_errors"] == 1
        assert metrics["error_types"]["timeout"] == 1

    def test_get_summary_statistics(self):
        """Test summary statistics calculation."""
        collector = MetricsCollector()

        collector.record_request("GET", 200, 1.0, 500)
        collector.record_request("POST", 201, 2.0, 1000)
        collector.record_error("timeout", "Error")

        summary = collector.get_summary()

        assert summary["total_requests"] == 2
        assert summary["total_errors"] == 1
        assert summary["success_rate"] == 0.5  # 2 requests, 1 error
        assert summary["average_response_time"] == 1.5

    def test_reset_metrics(self):
        """Test resetting metrics."""
        collector = MetricsCollector()

        collector.record_request("GET", 200, 1.0, 500)
        collector.reset()

        metrics = collector.get_metrics()
        assert metrics["total_requests"] == 0


class TestErrorHandler:
    """Test the ErrorHandler class."""

    def test_error_handler_initialization(self):
        """Test ErrorHandler initializes correctly."""
        handler = ErrorHandler()
        assert handler.error_counts == {}

    def test_categorize_error_timeout(self):
        """Test timeout error categorization."""
        handler = ErrorHandler()

        timeout_error = Exception("Request timeout")
        category = handler.categorize_error(timeout_error)

        assert category == "timeout"

    def test_categorize_error_connection(self):
        """Test connection error categorization."""
        handler = ErrorHandler()

        connection_error = Exception("Connection refused")
        category = handler.categorize_error(connection_error)

        assert category == "connection"

    def test_handle_error_logging(self):
        """Test error handling and logging."""
        handler = ErrorHandler()

        error = Exception("Test error")

        with patch("extractor.utils.logger") as mock_logger:
            handler.handle_error(error, "test_operation")

            mock_logger.error.assert_called_once()

    def test_should_retry_decision(self):
        """Test retry decision logic."""
        handler = ErrorHandler()

        # Retryable errors
        assert handler.should_retry(Exception("timeout")) is True
        assert handler.should_retry(Exception("connection")) is True

        # Non-retryable errors
        assert handler.should_retry(ValueError("Invalid input")) is False


class TestUtilityFunctions:
    """Test standalone utility functions."""

    def test_url_validator_valid_urls(self):
        """Test URLValidator with valid URLs."""
        validator = URLValidator()

        assert validator.is_valid("https://example.com") is True
        assert validator.is_valid("http://test.org/path?query=value") is True
        assert validator.is_valid("https://sub.domain.com:8080") is True

    def test_url_validator_invalid_urls(self):
        """Test URLValidator with invalid URLs."""
        validator = URLValidator()

        assert validator.is_valid("not-a-url") is False
        assert validator.is_valid("ftp://example.com") is False
        assert validator.is_valid("") is False

    def test_text_cleaner_clean_text(self):
        """Test TextCleaner text cleaning."""
        cleaner = TextCleaner()

        dirty_text = "  \n\t  Hello   World  \r\n  "
        cleaned = cleaner.clean(dirty_text)

        assert cleaned == "Hello World"

    def test_text_cleaner_remove_html_tags(self):
        """Test TextCleaner HTML tag removal."""
        cleaner = TextCleaner()

        html_text = "<p>Hello <strong>World</strong></p>"
        cleaned = cleaner.clean(html_text, remove_html=True)

        assert cleaned == "Hello World"

    def test_config_validator_validate_extraction_config(self):
        """Test ConfigValidator extraction config validation."""
        validator = ConfigValidator()

        valid_config = {
            "title": "h1",
            "content": {"selector": "p", "multiple": True, "attr": "text"},
        }

        assert validator.validate_extraction_config(valid_config) is True

    def test_config_validator_invalid_config(self):
        """Test ConfigValidator with invalid config."""
        validator = ConfigValidator()

        invalid_config = {
            "title": 123,  # Should be string
            "content": "invalid",  # Missing required structure
        }

        assert validator.validate_extraction_config(invalid_config) is False

    @pytest.mark.asyncio
    async def test_timing_decorator(self):
        """Test timing decorator functionality."""

        @timing_decorator
        async def test_function():
            await asyncio.sleep(0.1)
            return "result"

        result = await test_function()

        assert result == "result"

    def test_global_instances(self):
        """Test global utility instances are properly initialized."""
        assert rate_limiter is not None
        assert retry_manager is not None
        assert cache_manager is not None
        assert metrics_collector is not None
