"""工具层计时、错误归类与指标记录。"""

import logging
import time

logger = logging.getLogger(__name__)


def categorize_error(error_message: str) -> str:
    """将错误消息归类为稳定的指标标签。"""
    msg_lower = error_message.lower()
    if "timeout" in msg_lower:
        return "timeout"
    if "connection" in msg_lower:
        return "connection"
    if "404" in error_message:
        return "not_found"
    if "403" in error_message:
        return "forbidden"
    if "cloudflare" in msg_lower:
        return "anti_bot"
    return "unknown"


def record_error(
    error: Exception,
    url: str,
    method: str,
    duration_ms: int,
    *,
    metrics,
    log=None,
) -> str:
    """记录失败指标并返回原始错误消息。"""
    error_message = str(error)
    category = categorize_error(error_message)
    active_logger = log or logger
    active_logger.error(
        "Scraping error for %s using %s: %s: %s",
        url,
        method,
        type(error).__name__,
        error_message,
    )
    metrics.record_request(url, False, duration_ms, method, category)
    return error_message


def elapsed_ms(start_time: float) -> int:
    """计算开始时间到当前的毫秒耗时。"""
    return int((time.time() - start_time) * 1000)


class ToolTimer:
    """统一的工具执行计时器。"""

    __slots__ = ("url", "method", "_metrics", "_record_error", "_start", "duration_ms")

    def __init__(self, url: str, method: str, *, metrics, record_error_func) -> None:
        self.url = url
        self.method = method
        self._metrics = metrics
        self._record_error = record_error_func
        self._start = time.time()
        self.duration_ms = 0

    def elapsed(self) -> int:
        self.duration_ms = elapsed_ms(self._start)
        return self.duration_ms

    def record_success(self) -> int:
        self.elapsed()
        self._metrics.record_request(self.url, True, self.duration_ms, self.method)
        return self.duration_ms

    def record_failure(self, error: Exception) -> str:
        self.elapsed()
        return self._record_error(error, self.url, self.method, self.duration_ms)
