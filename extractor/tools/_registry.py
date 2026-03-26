"""MCP tool registry: app instance, shared services, and common helpers."""

import logging
import time
from typing import Any, Dict, List, Literal, Optional
from urllib.parse import urlparse

from fastmcp import FastMCP

from ..anti_detection import AntiDetectionScraper
from ..cache import cache_manager
from ..config import settings
from ..markdown.converter import MarkdownConverter
from ..metrics import metrics_collector
from ..rate_limiter import rate_limiter
from ..retry import retry_manager
from ..scraper import WebScraper
from ..text_utils import TextCleaner
from ..url_utils import URLValidator

logger = logging.getLogger(__name__)

# --- Literal 类型别名（由 Pydantic/MCP 层自动进行参数验证） ---

ScrapeMethod = Literal["auto", "simple", "scrapy", "selenium"]
BrowserMethod = Literal["selenium", "playwright"]
PDFMethod = Literal["auto", "pymupdf", "pypdf"]
PDFOutputFormat = Literal["markdown", "text"]
StructuredDataType = Literal[
    "all", "contact", "social", "content", "products", "addresses"
]

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# FastMCP application instance
app = FastMCP(settings.server_name, version=settings.server_version)

# Shared service instances
web_scraper = WebScraper()
anti_detection_scraper = AntiDetectionScraper()
markdown_converter = MarkdownConverter()


def create_pdf_processor(
    enable_enhanced_features: bool = True, output_dir: Optional[str] = None
):
    """获取 PDF 处理器实例，延迟导入以避免启动警告"""
    from ..pdf import PDFProcessor

    return PDFProcessor(
        enable_enhanced_features=enable_enhanced_features, output_dir=output_dir
    )


# --- Common helper functions to eliminate duplication ---


def validate_url(url: str) -> Optional[str]:
    """Validate URL format. Returns error message or None if valid."""
    parsed = urlparse(url)
    if not parsed.scheme or not parsed.netloc:
        return "Invalid URL format"
    return None


def validate_page_range(
    page_range: Optional[List[int]],
) -> tuple[Optional[tuple], Optional[str]]:
    """Validate and convert page_range. Returns (tuple_or_none, error_or_none)."""
    if not page_range:
        return None, None
    if len(page_range) != 2:
        return None, "Page range must contain exactly 2 elements: [start, end]"
    if page_range[0] < 0 or page_range[1] < 0:
        return None, "Page numbers must be non-negative"
    if page_range[0] >= page_range[1]:
        return None, "Start page must be less than end page"
    return tuple(page_range), None


def normalize_extract_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """校验并规范化提取配置字典。

    将简写形式（字符串 CSS 选择器）展开为完整配置字典，
    并为缺失字段补充默认值。
    """
    if not isinstance(config, dict):
        raise ValueError("Extract config must be a dictionary")

    normalized: Dict[str, Any] = {}
    for key, value in config.items():
        if isinstance(value, str):
            normalized[key] = {"selector": value, "multiple": True}
        elif isinstance(value, dict):
            if "selector" not in value:
                raise ValueError(f"Missing 'selector' for key '{key}'")
            normalized[key] = {
                "selector": value["selector"],
                "attr": value.get("attr", "text"),
                "multiple": value.get("multiple", False),
                "type": value.get("type", "css"),
            }
        else:
            raise ValueError(f"Invalid config value for key '{key}'")
    return normalized


def record_error(e: Exception, url: str, method: str, duration_ms: int) -> str:
    """Handle error + record metrics. Returns original error message."""
    error_message = str(e)
    msg_lower = error_message.lower()

    if "timeout" in msg_lower:
        category = "timeout"
    elif "connection" in msg_lower:
        category = "connection"
    elif "404" in error_message:
        category = "not_found"
    elif "403" in error_message:
        category = "forbidden"
    elif "cloudflare" in msg_lower:
        category = "anti_bot"
    else:
        category = "unknown"

    logger.error(
        f"Scraping error for {url} using {method}: "
        f"{type(e).__name__}: {error_message}"
    )
    metrics_collector.record_request(url, False, duration_ms, method, category)
    return error_message


def elapsed_ms(start_time: float) -> int:
    """Calculate elapsed milliseconds from start_time."""
    return int((time.time() - start_time) * 1000)


class ToolTimer:
    """Unified timing and metrics helper for MCP tool execution.

    Encapsulates start_time tracking, elapsed calculation, and metrics recording
    to eliminate repeated boilerplate across tool modules.

    Usage::

        timer = ToolTimer(url, f"stealth_{method}")
        try:
            result = await do_work()
            if result.get("success"):
                return Response(success=True, duration_ms=timer.record_success())
            else:
                return Response(success=False, error=timer.record_failure(Exception(result["error"])))
        except Exception as e:
            return Response(success=False, error=timer.record_failure(e))
    """

    __slots__ = ("url", "method", "_start", "duration_ms")

    def __init__(self, url: str, method: str) -> None:
        self.url = url
        self.method = method
        self._start = time.time()
        self.duration_ms = 0

    def elapsed(self) -> int:
        """Compute and cache elapsed milliseconds."""
        self.duration_ms = elapsed_ms(self._start)
        return self.duration_ms

    def record_success(self) -> int:
        """Record success metrics. Returns duration_ms."""
        self.elapsed()
        metrics_collector.record_request(self.url, True, self.duration_ms, self.method)
        return self.duration_ms

    def record_failure(self, error: Exception) -> str:
        """Record failure metrics. Returns user-facing error message."""
        self.elapsed()
        return record_error(error, self.url, self.method, self.duration_ms)
