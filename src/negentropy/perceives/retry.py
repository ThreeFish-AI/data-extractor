"""指数退避重试逻辑。"""

import asyncio
import logging
from typing import Any, Callable

logger = logging.getLogger(__name__)


class RetryManager:
    """带指数退避的重试逻辑管理器。"""

    def __init__(
        self, max_retries: int = 3, base_delay: float = 1.0, backoff_factor: float = 2.0
    ):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.backoff_factor = backoff_factor

    async def retry_async(
        self, func: Callable[..., Any], *args: Any, **kwargs: Any
    ) -> Any:
        """以指数退避策略重试异步函数。"""
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

        if last_exception:
            raise last_exception
        else:
            raise RuntimeError("Retry failed without capturing exception")


retry_manager = RetryManager(max_retries=3)
