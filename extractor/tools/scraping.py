"""Web scraping MCP tools."""

import logging
import time
from typing import Annotated, Any, Dict, List, Optional
from urllib.parse import urlparse

from pydantic import Field

from ..cache import cache_manager
from ..config_validator import ConfigValidator
from ..metrics import metrics_collector
from ..rate_limiter import rate_limiter
from ..retry import retry_manager
from ..schemas import (
    BatchScrapeResponse,
    LinkItem,
    LinksResponse,
    PageInfoResponse,
    ScrapeResponse,
    StructuredDataResponse,
)
from ..text_utils import TextCleaner
from ..url_utils import URLValidator
from ._registry import (
    app,
    anti_detection_scraper,
    elapsed_ms,
    record_error,
    web_scraper,
)

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
    parsed = urlparse(url)
    if not parsed.scheme or not parsed.netloc:
        return ScrapeResponse(
            success=False, url=url, method=method, error="Invalid URL format"
        )

    if method not in ["auto", "simple", "scrapy", "selenium"]:
        return ScrapeResponse(
            success=False,
            url=url,
            method=method,
            error="Method must be one of: auto, simple, scrapy, selenium",
        )

    try:
        logger.info(f"Scraping webpage: {url} with method: {method}")

        # Validate extract_config if provided
        parsed_extract_config = None
        if extract_config:
            if not isinstance(extract_config, dict):
                return ScrapeResponse(
                    success=False,
                    url=url,
                    method=method,
                    error="extract_config must be a dictionary",
                )
            parsed_extract_config = extract_config

        result = await web_scraper.scrape_url(
            url=url,
            method=method,
            extract_config=parsed_extract_config,
            wait_for_element=wait_for_element,
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
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                raise ValueError(f"Invalid URL format: {url}")

        if method not in ["auto", "simple", "scrapy", "selenium"]:
            raise ValueError("Method must be one of: auto, simple, scrapy, selenium")

        logger.info(f"Scraping {len(urls)} webpages with method: {method}")

        # Validate extract_config if provided
        parsed_extract_config = None
        if extract_config:
            if not isinstance(extract_config, dict):
                return BatchScrapeResponse(
                    success=False,
                    total_urls=len(urls),
                    successful_count=0,
                    failed_count=len(urls),
                    results=[],
                    summary={"error": "extract_config must be a dictionary"},
                )
            parsed_extract_config = extract_config

        results = await web_scraper.scrape_multiple_urls(
            urls=urls,
            method=method,
            extract_config=parsed_extract_config,
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
    start_time = time.time()
    try:
        # Validate inputs
        if not URLValidator.is_valid_url(url):
            return ScrapeResponse(
                success=False, url=url, method=method, error="Invalid URL format",
            )

        if method not in ["selenium", "playwright"]:
            return ScrapeResponse(
                success=False, url=url, method=method,
                error="Method must be one of: selenium, playwright",
            )

        logger.info(f"Stealth scraping: {url} with method: {method}")

        # Apply rate limiting
        await rate_limiter.wait()

        # Normalize URL
        normalized_url = URLValidator.normalize_url(url)

        # Check cache first
        cache_key_data = {
            "extract_config": extract_config,
            "wait_for_element": wait_for_element,
            "scroll_page": scroll_page,
        }
        cached_result = cache_manager.get(
            normalized_url, f"stealth_{method}", cache_key_data
        )
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

        duration_ms = elapsed_ms(start_time)
        success = "error" not in result

        if success:
            # Clean text content if present
            if "content" in result and "text" in result["content"]:
                result["content"]["text"] = TextCleaner.clean_text(
                    result["content"]["text"]
                )

            # Cache successful result
            cache_manager.set(
                normalized_url, f"stealth_{method}", result, cache_key_data
            )

            metrics_collector.record_request(
                normalized_url, True, duration_ms, f"stealth_{method}"
            )

            return ScrapeResponse(
                success=True, url=url, method=f"stealth_{method}",
                data=result, duration_ms=duration_ms, from_cache=False,
            )
        else:
            error_msg = record_error(
                Exception(result.get("error", "Unknown error")),
                normalized_url, f"stealth_{method}", duration_ms,
            )
            return ScrapeResponse(
                success=False, url=url, method=f"stealth_{method}", error=error_msg,
            )

    except Exception as e:
        duration_ms = elapsed_ms(start_time) if "start_time" in dir() else 0
        error_msg = record_error(e, url, f"stealth_{method}", duration_ms)
        return ScrapeResponse(
            success=False, url=url, method=f"stealth_{method}", error=error_msg,
        )


@app.tool()
async def extract_links(
    url: Annotated[
        str,
        Field(
            ...,
            description="""目标网页 URL，必须包含协议前缀（http://或https://），将从此页面提取所有链接。
                支持 http 和 https 协议的有效 URL 格式""",
        ),
    ],
    filter_domains: Annotated[
        Optional[List[str]],
        Field(
            default=None,
            description="""白名单域名列表，仅包含这些域名的链接。设置后只返回指定域名的链接。
                示例：["example.com", "subdomain.example.com", "blog.example.org"]""",
        ),
    ],
    exclude_domains: Annotated[
        Optional[List[str]],
        Field(
            default=None,
            description="""黑名单域名列表，排除这些域名的链接。用于过滤广告、跟踪器等不需要的外部链接。
                示例：["ads.com", "tracker.net", "analytics.google.com"]""",
        ),
    ],
    internal_only: Annotated[
        bool,
        Field(
            default=False,
            description="是否仅提取内部链接（同域名链接）。设为 True 时只返回与源页面相同域名的链接，忽略所有外部链接",
        ),
    ],
) -> LinksResponse:
    """
    Extract all links from a webpage.

    This tool is specialized for link extraction and can filter links by domain,
    extract only internal links, or exclude specific domains.

    Returns:
        LinksResponse object containing success status, extracted links list, and optional filtering statistics.
        Each link includes url, text, and additional attributes if available.
    """
    try:
        # Validate inputs
        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            raise ValueError("Invalid URL format")

        logger.info(f"Extracting links from: {url}")

        # Scrape the page to get links
        scrape_result = await web_scraper.scrape_url(
            url=url, method="simple",
        )

        if "error" in scrape_result:
            return LinksResponse(
                success=False, url=url, total_links=0, links=[],
                internal_links_count=0, external_links_count=0,
                error=scrape_result["error"],
            )

        # Extract and filter links
        all_links = scrape_result.get("content", {}).get("links", [])
        base_domain = urlparse(url).netloc

        filtered_links = []
        for link in all_links:
            link_url = link.get("url", "")
            if not link_url:
                continue

            link_domain = urlparse(link_url).netloc

            # Apply filters
            if internal_only and link_domain != base_domain:
                continue

            if filter_domains and link_domain not in filter_domains:
                continue

            if exclude_domains and link_domain in exclude_domains:
                continue

            filtered_links.append(
                LinkItem(
                    url=link_url,
                    text=link.get("text", "").strip(),
                    is_internal=link_domain == base_domain,
                )
            )

        internal_count = sum(1 for link in filtered_links if link.is_internal)
        external_count = len(filtered_links) - internal_count

        return LinksResponse(
            success=True, url=url, total_links=len(filtered_links),
            links=filtered_links,
            internal_links_count=internal_count, external_links_count=external_count,
        )

    except Exception as e:
        logger.error(f"Error extracting links from {url}: {str(e)}")
        return LinksResponse(
            success=False, url=url, total_links=0, links=[],
            internal_links_count=0, external_links_count=0, error=str(e),
        )


@app.tool()
async def get_page_info(
    url: Annotated[
        str,
        Field(
            ...,
            description="""目标网页 URL，必须包含协议前缀（http://或https://），用于获取页面基础信息和元数据。
                这是一个轻量级工具，不会提取完整页面内容""",
        ),
    ],
) -> PageInfoResponse:
    """
    Get basic information about a webpage (title, description, status).

    This is a lightweight tool for quickly checking page accessibility and
    getting basic metadata without full content extraction.

    Returns:
        PageInfoResponse object containing success status, URL, status_code, title, meta_description, and domain.
        Useful for quick page validation and metadata extraction.
    """
    try:
        # Validate inputs
        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            raise ValueError("Invalid URL format")

        logger.info(f"Getting page info for: {url}")

        # Use simple scraper for quick info
        result = await web_scraper.simple_scraper.scrape(url, extract_config={})

        if "error" in result:
            return PageInfoResponse(
                success=False, url=url, status_code=0, error=result["error"]
            )

        return PageInfoResponse(
            success=True,
            url=result.get("url", url),
            title=result.get("title"),
            description=result.get("meta_description"),
            status_code=result.get("status_code", 200),
            content_type=result.get("content_type"),
            content_length=result.get("content_length"),
        )

    except Exception as e:
        logger.error(f"Error getting page info for {url}: {str(e)}")
        return PageInfoResponse(success=False, url=url, status_code=0, error=str(e))


@app.tool()
async def extract_structured_data(
    url: Annotated[
        str,
        Field(
            ...,
            description="""目标网页URL，必须包含协议前缀（http:// 或 https://），从中提取结构化数据。
            支持自动识别联系信息、社交媒体链接等内容""",
        ),
    ],
    data_type: Annotated[
        str,
        Field(
            default="all",
            description="""数据类型过滤器，指定要提取的结构化数据类型。可选值：
                all（提取所有类型）、
                contact（联系信息：邮箱、电话号码）、
                social（社交媒体链接：Facebook、Twitter等）、
                content（文章内容和元数据）、
                products（产品信息和价格）、
                addresses（地址和位置信息）""",
        ),
    ],
) -> StructuredDataResponse:
    """
    Extract structured data from a webpage using advanced techniques.

    Automatically detects and extracts:
    - Contact information (emails, phone numbers)
    - Social media links
    - Addresses
    - Prices and product information
    - Article content

    Returns:
        StructuredDataResponse object containing success status and structured data organized by type.
        Supports filtering for specific data categories as needed.
    """
    try:
        # Validate inputs
        if not URLValidator.is_valid_url(url):
            raise ValueError("Invalid URL format")

        valid_types = ["all", "contact", "social", "content", "products", "addresses"]
        if data_type not in valid_types:
            raise ValueError(f"Data type must be one of: {', '.join(valid_types)}")

        logger.info(f"Extracting structured data from: {url}")

        # Apply rate limiting
        await rate_limiter.wait()

        normalized_url = URLValidator.normalize_url(url)

        # Scrape page content
        scrape_result = await web_scraper.scrape_url(
            url=normalized_url, method="simple"
        )

        if "error" in scrape_result:
            return StructuredDataResponse(
                success=False, url=normalized_url, data_type=data_type,
                extracted_data={}, data_count=0, error=scrape_result["error"],
            )

        content = scrape_result.get("content", {})
        text_content = content.get("text", "")
        links = content.get("links", [])

        extracted_data = {}

        # Extract contact information
        if data_type in ["all", "contact"]:
            extracted_data["contact"] = {
                "emails": TextCleaner.extract_emails(text_content),
                "phone_numbers": TextCleaner.extract_phone_numbers(text_content),
            }

        # Extract social media links
        if data_type in ["all", "social"]:
            social_domains = [
                "facebook.com", "twitter.com", "instagram.com", "linkedin.com",
                "youtube.com", "tiktok.com", "pinterest.com", "snapchat.com",
            ]

            social_links = []
            for link in links:
                link_url = link.get("url", "")
                domain = URLValidator.extract_domain(link_url)

                for social_domain in social_domains:
                    if social_domain in domain:
                        social_links.append({
                            "platform": social_domain.split(".")[0],
                            "url": link_url,
                            "text": link.get("text", ""),
                        })
                        break

            extracted_data["social_media"] = social_links

        # Extract basic content structure
        if data_type in ["all", "content"]:
            extracted_data["content"] = {
                "title": scrape_result.get("title"),
                "meta_description": scrape_result.get("meta_description"),
                "text_length": len(text_content),
                "link_count": len(links),
                "domain": URLValidator.extract_domain(normalized_url),
            }

        return StructuredDataResponse(
            success=True, url=normalized_url, data_type=data_type,
            extracted_data=extracted_data,
            data_count=sum(
                len(v) if isinstance(v, (list, dict)) else 1
                for v in extracted_data.values()
            ),
        )

    except Exception as e:
        logger.error(f"Error extracting structured data from {url}: {str(e)}")
        return StructuredDataResponse(
            success=False, url=url, data_type=data_type,
            extracted_data={}, data_count=0, error=str(e),
        )
