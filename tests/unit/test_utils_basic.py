"""Basic unit tests for utility classes."""

import pytest
import asyncio
import time

from extractor.utils import (
    RateLimiter,
    RetryManager,
    URLValidator,
    TextCleaner,
    ConfigValidator,
    ErrorHandler,
    timing_decorator,
)


class TestRateLimiterBasic:
    """Test basic RateLimiter functionality."""

    def test_rate_limiter_initialization(self):
        """Test RateLimiter initializes correctly."""
        limiter = RateLimiter(requests_per_second=2.0)
        assert limiter.requests_per_second == 2.0
        assert limiter.min_interval == 0.5

    @pytest.mark.asyncio
    async def test_rate_limiter_wait(self):
        """Test rate limiter wait functionality."""
        limiter = RateLimiter(requests_per_second=10.0)  # High rate for fast test

        # First call should be immediate
        start = time.time()
        await limiter.wait()
        elapsed = time.time() - start
        assert elapsed < 0.1  # Should be very fast


class TestRetryManagerBasic:
    """Test basic RetryManager functionality."""

    def test_retry_manager_initialization(self):
        """Test RetryManager initializes correctly."""
        manager = RetryManager(max_retries=3, base_delay=1.0)
        assert manager.max_retries == 3
        assert manager.base_delay == 1.0

    @pytest.mark.asyncio
    async def test_retry_success_immediate(self):
        """Test retry when operation succeeds immediately."""
        manager = RetryManager(max_retries=3, base_delay=0.01)

        async def success_func():
            return "success"

        result = await manager.retry_async(success_func)
        assert result == "success"


class TestUtilityClasses:
    """Test utility classes basic functionality."""

    def test_url_validator_initialization(self):
        """Test URLValidator can be created."""
        validator = URLValidator()
        assert validator is not None

    def test_text_cleaner_initialization(self):
        """Test TextCleaner can be created."""
        cleaner = TextCleaner()
        assert cleaner is not None

    def test_config_validator_initialization(self):
        """Test ConfigValidator can be created."""
        validator = ConfigValidator()
        assert validator is not None

    def test_error_handler_initialization(self):
        """Test ErrorHandler can be created."""
        handler = ErrorHandler()
        assert handler is not None


class TestTimingDecorator:
    """Test timing decorator functionality."""

    @pytest.mark.asyncio
    async def test_timing_decorator_basic(self):
        """Test timing decorator works."""

        @timing_decorator
        async def test_function():
            await asyncio.sleep(0.01)  # Small delay
            return "result"

        result = await test_function()
        assert result == "result"

    def test_timing_decorator_sync(self):
        """Test timing decorator works with sync functions."""

        @timing_decorator
        def test_function():
            time.sleep(0.01)  # Small delay
            return "result"

        result = test_function()
        assert result == "result"
