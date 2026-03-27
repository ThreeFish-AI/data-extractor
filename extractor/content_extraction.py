"""统一内容提取导出：兼容保留原入口，内部按职责拆分。"""

from .content_extraction_pages import (
    extract_default_content,
    extract_default_content_playwright,
    extract_page_data_playwright,
    extract_page_data_selenium,
)
from .content_extraction_selectors import (
    extract_with_bs4_config,
    extract_with_playwright_config,
    extract_with_selenium_config,
)

__all__ = [
    "extract_default_content",
    "extract_with_bs4_config",
    "extract_with_selenium_config",
    "extract_with_playwright_config",
    "extract_default_content_playwright",
    "extract_page_data_selenium",
    "extract_page_data_playwright",
]
