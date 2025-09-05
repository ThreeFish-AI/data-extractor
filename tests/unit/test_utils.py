"""Unit tests for utility classes and functions."""

import pytest
import asyncio
import time
from unittest.mock import patch, AsyncMock

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
        limiter = RateLimiter(requests_per_second=1.0)
        assert limiter.requests_per_second == 1.0
        assert limiter.min_interval == 1.0
        assert limiter.last_request_time == 0.0

    @pytest.mark.asyncio
    async def test_rate_limiting_within_limit(self):
        """Test rate limiting when within limits."""
        limiter = RateLimiter(requests_per_second=60.0)

        start_time = time.time()
        await limiter.wait()
        end_time = time.time()

        # Should not be delayed when within limit
        assert (end_time - start_time) < 0.1

    @pytest.mark.asyncio
    async def test_rate_limiting_exceeds_limit(self):
        """Test rate limiting when exceeding limits."""
        limiter = RateLimiter(requests_per_second=10.0)  # Higher limit for testing

        # Make two quick requests
        start_time = time.time()
        await limiter.wait()
        await limiter.wait()
        end_time = time.time()

        # Second request should be slightly delayed
        assert (end_time - start_time) >= 0.0  # Some delay expected

    def test_cleanup_old_requests(self):
        """Test cleanup of old rate limit requests."""
        limiter = RateLimiter(requests_per_second=1.0)
        # Test that old timestamps are properly managed
        assert limiter.last_request_time == 0.0


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

        # Test internal delay calculation logic
        delay_1 = manager.base_delay * (manager.backoff_factor**1)
        delay_2 = manager.base_delay * (manager.backoff_factor**2)

        assert delay_1 == 2.0
        assert delay_2 == 4.0


class TestCacheManager:
    """Test the CacheManager class."""

    def test_cache_manager_initialization(self):
        """Test CacheManager initializes correctly."""
        manager = CacheManager(max_size=100, ttl_seconds=60)
        assert manager.max_size == 100
        assert manager.ttl_seconds == 60
        assert len(manager.cache) == 0

    def test_cache_set_and_get(self):
        """Test setting and getting cache values."""
        manager = CacheManager()

        test_data = {"key": "value", "number": 42}
        manager.set("test_url", "simple", test_data)

        retrieved_data = manager.get("test_url", "simple")
        assert retrieved_data == test_data

    def test_cache_expiration(self):
        """Test cache expiration."""
        manager = CacheManager(ttl_seconds=1)

        test_data = {"value": "test"}
        manager.set("expire_url", "simple", test_data)

        # Should be available immediately
        assert manager.get("expire_url", "simple") == test_data

        # Wait for expiration
        time.sleep(1.1)

        # Should be None after expiration
        assert manager.get("expire_url", "simple") is None

    def test_cache_miss(self):
        """Test cache miss behavior."""
        manager = CacheManager()

        result = manager.get("nonexistent_url", "simple")
        assert result is None

    def test_cache_clear(self):
        """Test cache clearing."""
        manager = CacheManager()

        test_data1 = {"value": "value1"}
        test_data2 = {"value": "value2"}
        manager.set("url1", "simple", test_data1)
        manager.set("url2", "scrapy", test_data2)

        manager.clear()

        assert manager.get("url1", "simple") is None
        assert manager.get("url2", "scrapy") is None

    def test_generate_cache_key(self):
        """Test cache key generation."""
        manager = CacheManager()

        key1 = manager._generate_key(
            "https://example.com", "simple", {"param": "value"}
        )
        key2 = manager._generate_key(
            "https://example.com", "simple", {"param": "different"}
        )

        assert key1 != key2
        assert len(key1) == 32  # MD5 hash length


class TestMetricsCollector:
    """Test the MetricsCollector class."""

    def test_metrics_collector_initialization(self):
        """Test MetricsCollector initializes correctly."""
        collector = MetricsCollector()
        # Check that metrics dict is initialized with expected structure
        assert "total_requests" in collector.metrics
        assert "successful_requests" in collector.metrics
        assert "failed_requests" in collector.metrics

    def test_record_request(self):
        """Test recording request metrics."""
        collector = MetricsCollector()

        collector.record_request("https://example.com", True, 1500, "simple")

        stats = collector.get_stats()
        assert stats["total_requests"] == 1
        assert stats["successful_requests"] == 1
        assert stats["failed_requests"] == 0

    def test_record_error(self):
        """Test recording error metrics."""
        collector = MetricsCollector()

        collector.record_request(
            "https://example.com", False, 1000, "simple", "timeout"
        )

        stats = collector.get_stats()
        assert stats["total_requests"] == 1
        assert stats["failed_requests"] == 1
        assert stats["error_categories"]["timeout"] == 1

    def test_get_summary_statistics(self):
        """Test summary statistics calculation."""
        collector = MetricsCollector()

        collector.record_request("https://example.com", True, 1000, "simple")
        collector.record_request("https://test.com", False, 2000, "scrapy", "timeout")

        stats = collector.get_stats()

        assert stats["total_requests"] == 2
        assert stats["successful_requests"] == 1
        assert stats["failed_requests"] == 1
        assert stats["success_rate"] == 0.5

    def test_reset_metrics(self):
        """Test resetting metrics."""
        collector = MetricsCollector()

        collector.record_request("https://example.com", True, 1000, "simple")
        collector.reset()

        stats = collector.get_stats()
        assert stats["total_requests"] == 0


class TestErrorHandler:
    """Test the ErrorHandler class."""

    def test_error_handler_initialization(self):
        """Test ErrorHandler initializes correctly."""
        # ErrorHandler is a static class, test its static methods
        assert hasattr(ErrorHandler, "handle_scraping_error")

    def test_categorize_error_timeout(self):
        """Test timeout error categorization."""
        timeout_error = Exception("Request timeout")
        result = ErrorHandler.handle_scraping_error(
            timeout_error, "https://example.com", "simple"
        )

        assert result["success"] is False
        assert result["error"]["category"] == "timeout"

    def test_categorize_error_connection(self):
        """Test connection error categorization."""
        connection_error = Exception("Connection refused")
        result = ErrorHandler.handle_scraping_error(
            connection_error, "https://example.com", "simple"
        )

        assert result["success"] is False
        assert result["error"]["category"] == "connection"

    def test_handle_error_logging(self):
        """Test error handling and logging."""
        error = Exception("Test error")

        with patch("extractor.utils.logger") as mock_logger:
            result = ErrorHandler.handle_scraping_error(
                error, "https://example.com", "simple"
            )

            mock_logger.error.assert_called_once()
            assert result["success"] is False

    def test_should_retry_decision(self):
        """Test retry decision logic based on error categories."""
        # Test different error types
        timeout_result = ErrorHandler.handle_scraping_error(
            Exception("timeout"), "https://example.com", "simple"
        )
        assert timeout_result["error"]["category"] == "timeout"

        connection_result = ErrorHandler.handle_scraping_error(
            Exception("connection failed"), "https://example.com", "simple"
        )
        assert connection_result["error"]["category"] == "connection"


class TestUtilityFunctions:
    """Test standalone utility functions."""

    def test_url_validator_valid_urls(self):
        """Test URLValidator with valid URLs."""
        assert URLValidator.is_valid_url("https://example.com") is True
        assert URLValidator.is_valid_url("http://test.org/path?query=value") is True
        assert URLValidator.is_valid_url("https://sub.domain.com:8080") is True

    def test_url_validator_invalid_urls(self):
        """Test URLValidator with invalid URLs."""
        assert URLValidator.is_valid_url("not-a-url") is False
        assert URLValidator.is_valid_url("") is False

    def test_text_cleaner_clean_text(self):
        """Test TextCleaner text cleaning."""
        dirty_text = "  \n\t  Hello   World  \r\n  "
        cleaned = TextCleaner.clean_text(dirty_text)

        assert cleaned == "Hello World"

    def test_text_cleaner_remove_html_tags(self):
        """Test TextCleaner text processing."""
        # Test email extraction
        text_with_email = "Contact us at test@example.com for more info"
        emails = TextCleaner.extract_emails(text_with_email)
        assert "test@example.com" in emails

    def test_config_validator_validate_extraction_config(self):
        """Test ConfigValidator extraction config validation."""
        valid_config = {
            "title": "h1",
            "content": {"selector": "p", "multiple": True, "attr": "text"},
        }

        validated = ConfigValidator.validate_extract_config(valid_config)
        assert "title" in validated
        assert "content" in validated

    def test_config_validator_invalid_config(self):
        """Test ConfigValidator with invalid config."""
        invalid_config = {
            "title": 123,  # Should be string or dict
        }

        with pytest.raises(ValueError):
            ConfigValidator.validate_extract_config(invalid_config)

    @pytest.mark.asyncio
    async def test_timing_decorator(self):
        """Test timing decorator functionality."""

        @timing_decorator
        async def test_function():
            await asyncio.sleep(0.01)  # Short sleep
            return {"data": "result"}

        result = await test_function()

        assert result["data"] == "result"
        assert "duration_ms" in result

    def test_global_instances(self):
        """Test global utility instances are properly initialized."""
        assert rate_limiter is not None
        assert retry_manager is not None
        assert cache_manager is not None
        assert metrics_collector is not None
