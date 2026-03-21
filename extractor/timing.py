"""Execution timing decorator."""

import asyncio
import logging
import time
from functools import wraps
from typing import Any, Callable

logger = logging.getLogger(__name__)


def timing_decorator(func: Callable[..., Any]) -> Callable[..., Any]:
    """Decorator to measure function execution time."""

    @wraps(func)
    async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
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
    def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
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
