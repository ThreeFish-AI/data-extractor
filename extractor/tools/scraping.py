"""Web scraping MCP tools."""

import logging
from typing import Annotated, Any, Dict, List, Optional

from pydantic import Field

from ..schemas import BatchScrapeResponse, ScrapeResponse
from ..validation_trace import trace_event
from ._registry import app, validate_url, web_scraper

logger = logging.getLogger(__name__)


@app.tool()
async def scrape_webpage(
    url: Annotated[
        str,
        Field(..., description="目标网页 URL，必须包含协议前缀（http://或https://）"),
    ],
    method: Annotated[
        str,
        Field(
            default="auto",
            description="""抓取方法选择：
                auto（自动选择最佳方法）、
                simple（快速 HTTP 请求，不支持 JavaScript）、
                scrapy（Scrapy 框架，适合大规模抓取）、
                selenium（浏览器渲染，支持 JavaScript 和动态内容）""",
        ),
    ],
    extract_config: Annotated[
        Optional[Dict[str, Any]],
        Field(
            default=None,
            description="""数据提取配置字典，支持 CSS 选择器和属性提取。
                格式：配置字典，键为字段名，值为选择器或配置对象。
                示例：{"title": "h1", "content": {"selector": ".content p", "multiple": true, "attr": "text"}}""",
        ),
    ],
    wait_for_element: Annotated[
        Optional[str],
        Field(
            default=None,
            description="""等待元素的 CSS 选择器（仅 Selenium 方法有效），确保页面完全加载后再提取内容。
                示例：".content"、"#main-content\"""",
        ),
    ],
) -> ScrapeResponse:
    """
    Scrape a single webpage and extract its content.

    You can specify extraction rules to get specific data from the page.
    """

    # Validate inputs and return ScrapeResponse instead of raising exceptions
    url_error = validate_url(url)
    if url_error:
        return ScrapeResponse(success=False, url=url, method=method, error=url_error)

    if method not in ["auto", "simple", "scrapy", "selenium"]:
        return ScrapeResponse(
            success=False,
            url=url,
            method=method,
            error="Method must be one of: auto, simple, scrapy, selenium",
        )

    try:
        logger.info(f"Scraping webpage: {url} with method: {method}")
        trace_event("scrape_webpage", "input_validated", url=url, method=method)

        # Validate extract_config if provided
        if extract_config:
            if not isinstance(extract_config, dict):
                return ScrapeResponse(
                    success=False,
                    url=url,
                    method=method,
                    error="extract_config must be a dictionary",
                )
            trace_event(
                "scrape_webpage",
                "extract_config_received",
                field_count=len(extract_config),
            )

        result = await web_scraper.scrape_url(
            url=url,
            method=method,
            extract_config=extract_config,
            wait_for_element=wait_for_element,
        )
        trace_event(
            "scrape_webpage",
            "scrape_completed",
            has_error="error" in result,
            has_title=bool(result.get("title")),
        )

        # Check if the scraper returned an error
        if "error" in result:
            return ScrapeResponse(
                success=False,
                url=url,
                method=method,
                error=result["error"],
            )

        return ScrapeResponse(success=True, url=url, method=method, data=result)

    except Exception as e:
        logger.error(f"Error scraping webpage {url}: {str(e)}")
        trace_event("scrape_webpage", "scrape_failed", error=str(e))
        return ScrapeResponse(success=False, url=url, method=method, error=str(e))


@app.tool()
async def scrape_multiple_webpages(
    urls: Annotated[
        List[str],
        Field(
            ...,
            description="""要抓取的 URL 列表，每个 URL 必须包含协议前缀（http://或https://），支持并发抓取以提高效率。
                示例：["https://example.com", "https://another.com"]""",
        ),
    ],
    method: Annotated[
        str,
        Field(
            default="auto",
            description="""抓取方法选择：
                auto（自动选择最佳方法）、
                simple（快速HTTP请求，适合静态页面）、
                scrapy（Scrapy框架，适合批量处理和大规模抓取）、
                selenium（浏览器渲染，支持JavaScript和动态内容）""",
        ),
    ],
    extract_config: Annotated[
        Optional[Dict[str, Any]],
        Field(
            default=None,
            description="""统一的数据提取配置字典，应用于所有URL。
                格式：配置字典，键为字段名，值为选择器或配置对象。
                示例：{"title": "h1", "links": {"selector": "a", "multiple": true, "attr": "href"}}""",
        ),
    ],
) -> BatchScrapeResponse:
    """
    Scrape multiple webpages concurrently.

    This tool allows you to scrape multiple URLs at once, which is much faster
    than scraping them one by one. All URLs will be processed concurrently.
    """
    try:
        # Validate inputs
        if not urls:
            raise ValueError("URLs list cannot be empty")

        for url in urls:
            url_error = validate_url(url)
            if url_error:
                raise ValueError(f"{url_error}: {url}")

        if method not in ["auto", "simple", "scrapy", "selenium"]:
            raise ValueError("Method must be one of: auto, simple, scrapy, selenium")

        logger.info(f"Scraping {len(urls)} webpages with method: {method}")

        # Validate extract_config if provided
        if extract_config and not isinstance(extract_config, dict):
            return BatchScrapeResponse(
                success=False,
                total_urls=len(urls),
                successful_count=0,
                failed_count=len(urls),
                results=[],
                summary={"error": "extract_config must be a dictionary"},
            )

        results = await web_scraper.scrape_multiple_urls(
            urls=urls,
            method=method,
            extract_config=extract_config,
        )

        # Convert results to ScrapeResponse objects
        scrape_responses = []
        for i, result in enumerate(results):
            url = urls[i]
            if "error" in result:
                response = ScrapeResponse(
                    success=False, url=url, method=method, error=result["error"]
                )
            else:
                response = ScrapeResponse(
                    success=True, url=url, method=method, data=result
                )
            scrape_responses.append(response)

        successful_count = sum(1 for r in scrape_responses if r.success)
        failed_count = len(scrape_responses) - successful_count

        return BatchScrapeResponse(
            success=True,
            total_urls=len(urls),
            successful_count=successful_count,
            failed_count=failed_count,
            results=scrape_responses,
            summary={
                "total": len(urls),
                "successful": successful_count,
                "failed": failed_count,
                "method_used": method,
            },
        )

    except Exception as e:
        logger.error(f"Error scraping multiple webpages: {str(e)}")
        return BatchScrapeResponse(
            success=False,
            total_urls=len(urls),
            successful_count=0,
            failed_count=len(urls),
            results=[],
            summary={"error": str(e)},
        )
