"""请求速率限制器。"""

import asyncio
import time


class RateLimiter:
    """简易请求速率限制器。"""

    def __init__(self, requests_per_second: float = 1.0):
        self.requests_per_second = requests_per_second
        self.min_interval = 1.0 / requests_per_second
        self.last_request_time = 0.0

    async def wait(self) -> None:
        """在必要时等待以遵守速率限制。"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time

        if time_since_last < self.min_interval:
            sleep_time = self.min_interval - time_since_last
            await asyncio.sleep(sleep_time)

        self.last_request_time = time.time()


rate_limiter = RateLimiter(requests_per_second=2.0)
