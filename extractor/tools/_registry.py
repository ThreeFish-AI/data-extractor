"""MCP tool registry: app instance, shared services, and common helpers."""

import logging
import time
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

from fastmcp import FastMCP

from ..anti_detection import AntiDetectionScraper
from ..config import settings
from ..error_handler import ErrorHandler
from ..markdown_converter import MarkdownConverter
from ..metrics import metrics_collector
from ..scraper import WebScraper

logger = logging.getLogger(__name__)

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


def _get_pdf_processor(
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


def record_error(e: Exception, url: str, method: str, duration_ms: int) -> str:
    """Handle error + record metrics. Returns user-facing error message."""
    error_response = ErrorHandler.handle_scraping_error(e, url, method)
    metrics_collector.record_request(
        url,
        False,
        duration_ms,
        method,
        error_response["error"]["category"],
    )
    return error_response["error"]["message"]


def elapsed_ms(start_time: float) -> int:
    """Calculate elapsed milliseconds from start_time."""
    return int((time.time() - start_time) * 1000)
