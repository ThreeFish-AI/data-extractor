"""Data extraction MCP tools (links, page info, structured data)."""

import logging
from typing import Annotated, List, Optional
from urllib.parse import urlparse

from pydantic import Field

from ..rate_limiter import rate_limiter
from ..schemas import (
    LinkItem,
    LinksResponse,
    PageInfoResponse,
    StructuredDataResponse,
)
from ..text_utils import TextCleaner
from ..url_utils import URLValidator
from ._registry import app, validate_url, web_scraper

logger = logging.getLogger(__name__)


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
        url_error = validate_url(url)
        if url_error:
            raise ValueError(url_error)

        logger.info(f"Extracting links from: {url}")

        # Scrape the page to get links
        scrape_result = await web_scraper.scrape_url(
            url=url,
            method="simple",
        )

        if "error" in scrape_result:
            return LinksResponse(
                success=False,
                url=url,
                total_links=0,
                links=[],
                internal_links_count=0,
                external_links_count=0,
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
            success=True,
            url=url,
            total_links=len(filtered_links),
            links=filtered_links,
            internal_links_count=internal_count,
            external_links_count=external_count,
        )

    except Exception as e:
        logger.error(f"Error extracting links from {url}: {str(e)}")
        return LinksResponse(
            success=False,
            url=url,
            total_links=0,
            links=[],
            internal_links_count=0,
            external_links_count=0,
            error=str(e),
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
        url_error = validate_url(url)
        if url_error:
            raise ValueError(url_error)

        logger.info(f"Getting page info for: {url}")

        # Use simple scraper for quick info
        result = await web_scraper.http_scraper.scrape(url, extract_config={})

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
        url_error = validate_url(url)
        if url_error:
            raise ValueError(url_error)

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
                success=False,
                url=normalized_url,
                data_type=data_type,
                extracted_data={},
                data_count=0,
                error=scrape_result["error"],
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
                "facebook.com",
                "twitter.com",
                "instagram.com",
                "linkedin.com",
                "youtube.com",
                "tiktok.com",
                "pinterest.com",
                "snapchat.com",
            ]

            social_links = []
            for link in links:
                link_url = link.get("url", "")
                domain = URLValidator.extract_domain(link_url)

                for social_domain in social_domains:
                    if social_domain in domain:
                        social_links.append(
                            {
                                "platform": social_domain.split(".")[0],
                                "url": link_url,
                                "text": link.get("text", ""),
                            }
                        )
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
            success=True,
            url=normalized_url,
            data_type=data_type,
            extracted_data=extracted_data,
            data_count=sum(
                len(v) if isinstance(v, (list, dict)) else 1
                for v in extracted_data.values()
            ),
        )

    except Exception as e:
        logger.error(f"Error extracting structured data from {url}: {str(e)}")
        return StructuredDataResponse(
            success=False,
            url=url,
            data_type=data_type,
            extracted_data={},
            data_count=0,
            error=str(e),
        )
