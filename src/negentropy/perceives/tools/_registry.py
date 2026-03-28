"""MCP 工具注册枢纽。"""

import logging
from typing import Optional

from fastmcp import FastMCP

from ..config import settings
from ..infra import metrics_collector
from ..markdown.converter import MarkdownConverter
from ..scraping import AntiDetectionScraper, WebScraper
from . import _observability
from ._support import (
    BrowserMethod,
    PDFMethod,
    PDFOutputFormat,
    ScrapeMethod,
    StructuredDataType,
    normalize_extract_config as _normalize_extract_config,
    validate_page_range as _validate_page_range,
    validate_url as _validate_url,
)

logger = logging.getLogger(__name__)

__all__ = [
    # 类型别名
    "ScrapeMethod",
    "BrowserMethod",
    "PDFMethod",
    "PDFOutputFormat",
    "StructuredDataType",
    # FastMCP 实例
    "app",
    # 共享服务实例
    "web_scraper",
    "anti_detection_scraper",
    "markdown_converter",
    # 工厂函数
    "create_pdf_processor",
    # 辅助函数
    "validate_url",
    "validate_page_range",
    "normalize_extract_config",
    "record_error",
    "elapsed_ms",
    "ToolTimer",
]

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


# 直接赋值导出（消除纯转发的中间层）
validate_url = _validate_url
validate_page_range = _validate_page_range
normalize_extract_config = _normalize_extract_config


def record_error(e: Exception, url: str, method: str, duration_ms: int) -> str:
    """记录失败指标并返回原始错误消息（绑定共享 metrics_collector 与 logger）。"""
    return _observability.record_error(
        e,
        url,
        method,
        duration_ms,
        metrics=metrics_collector,
        log=logger,
    )


def elapsed_ms(start_time: float) -> int:
    """计算开始时间到当前的毫秒耗时。"""
    return _observability.elapsed_ms(start_time)


class ToolTimer(_observability.ToolTimer):
    """基于共享指标记录的工具执行计时器。"""

    def __init__(self, url: str, method: str) -> None:
        super().__init__(
            url,
            method,
            metrics=metrics_collector,
            record_error_func=record_error,
        )
