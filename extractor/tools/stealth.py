"""Stealth scraping MCP tools using anti-detection techniques."""

import logging
from typing import Annotated, Any, Dict, Optional

from pydantic import Field

from ..cache import cache_manager
from ..config import ConfigValidator
from ..rate_limiter import rate_limiter
from ..retry import retry_manager
from ..schemas import ScrapeResponse
from ..text_utils import TextCleaner
from ..url_utils import URLValidator
from ._registry import app, anti_detection_scraper, ToolTimer

logger = logging.getLogger(__name__)


@app.tool()
async def scrape_with_stealth(
    url: Annotated[
        str,
        Field(
            ...,
            description="目标网页 URL，必须包含协议前缀（http:// 或 https://），使用反检测技术抓取复杂的反爬虫网站",
        ),
    ],
    method: Annotated[
        str,
        Field(
            default="selenium",
            description="""隐身方法选择，可选值：
                "selenium"（使用 undetected-chromedriver 反检测技术）、
                "playwright"（使用 Playwright 隐身模式）""",
        ),
    ],
    extract_config: Annotated[
        Optional[Dict[str, Any]],
        Field(
            default=None,
            description="""数据提取配置字典，支持 CSS 选择器和属性提取。
                示例：{"title": "h1", "content": ".article-body", "links": {"selector": "a", "attr": "href", "multiple": True}}""",
        ),
    ],
    wait_for_element: Annotated[
        Optional[str],
        Field(
            default=None,
            description="""等待加载的元素 CSS 选择器，确保动态内容完全加载。
                示例：".content"、"#main-article\"""",
        ),
    ],
    scroll_page: Annotated[
        bool,
        Field(
            default=False,
            description="是否滚动页面以加载动态内容，适用于无限滚动或懒加载的页面",
        ),
    ],
) -> ScrapeResponse:
    """
    Scrape a webpage using advanced stealth techniques to avoid detection.

    This tool uses sophisticated anti-detection methods including:
    - Undetected browser automation
    - Randomized behavior patterns
    - Human-like interactions
    - Advanced evasion techniques

    Use this for websites with strong anti-bot protection.

    Returns:
        ScrapeResponse object containing success status, scraped data, stealth method used, and performance metrics.
        Designed for bypassing sophisticated bot detection systems.
    """
    method_key = f"stealth_{method}"
    timer = ToolTimer(url, method_key)
    try:
        # Validate inputs
        if not URLValidator.is_valid_url(url):
            return ScrapeResponse(
                success=False,
                url=url,
                method=method,
                error="Invalid URL format",
            )

        if method not in ["selenium", "playwright"]:
            return ScrapeResponse(
                success=False,
                url=url,
                method=method,
                error="Method must be one of: selenium, playwright",
            )

        logger.info(f"Stealth scraping: {url} with method: {method}")

        # Apply rate limiting
        await rate_limiter.wait()

        # Normalize URL
        normalized_url = URLValidator.normalize_url(url)
        timer.url = normalized_url

        # Check cache first
        cache_key_data = {
            "extract_config": extract_config,
            "wait_for_element": wait_for_element,
            "scroll_page": scroll_page,
        }
        cached_result = cache_manager.get(normalized_url, method_key, cache_key_data)
        if cached_result:
            logger.info(f"Returning cached result for {normalized_url}")
            cached_result["from_cache"] = True
            return cached_result

        # Validate and normalize extract config
        if extract_config:
            extract_config = ConfigValidator.validate_extract_config(extract_config)

        # Perform stealth scraping with retry
        result = await retry_manager.retry_async(
            anti_detection_scraper.scrape_with_stealth,
            url=normalized_url,
            method=method,
            extract_config=extract_config,
            wait_for_element=wait_for_element,
            scroll_page=scroll_page,
        )

        if "error" not in result:
            # Clean text content if present
            if "content" in result and "text" in result["content"]:
                result["content"]["text"] = TextCleaner.clean_text(
                    result["content"]["text"]
                )

            # Cache successful result
            cache_manager.set(normalized_url, method_key, result, cache_key_data)

            return ScrapeResponse(
                success=True,
                url=url,
                method=method_key,
                data=result,
                duration_ms=timer.record_success(),
                from_cache=False,
            )
        else:
            return ScrapeResponse(
                success=False,
                url=url,
                method=method_key,
                error=timer.record_failure(
                    Exception(result.get("error", "Unknown error"))
                ),
            )

    except Exception as e:
        return ScrapeResponse(
            success=False,
            url=url,
            method=method_key,
            error=timer.record_failure(e),
        )
