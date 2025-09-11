"""FastMCP Server implementation for web scraping."""

import logging
import time
from typing import Dict, Any, List, Optional, Annotated
from urllib.parse import urlparse
from datetime import datetime

from fastmcp import FastMCP
from pydantic import BaseModel, Field, field_validator

from .scraper import WebScraper
from .advanced_features import AntiDetectionScraper, FormHandler
from .markdown_converter import MarkdownConverter
from .config import settings
from .utils import (
    timing_decorator,
    URLValidator,
    TextCleaner,
    ConfigValidator,
    ErrorHandler,
    rate_limiter,
    retry_manager,
    cache_manager,
    metrics_collector,
)

logger = logging.getLogger(__name__)

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

app = FastMCP(settings.server_name, version=settings.server_version)
web_scraper = WebScraper()
anti_detection_scraper = AntiDetectionScraper()
markdown_converter = MarkdownConverter()


# 延迟初始化 PDF 处理器，避免启动时加载 PyMuPDF
def _get_pdf_processor():
    """获取 PDF 处理器实例，延迟导入以避免启动警告"""
    from .pdf_processor import PDFProcessor

    return PDFProcessor()


class ScrapeRequest(BaseModel):
    """Request model for scraping operations."""

    url: Annotated[
        str,
        Field(..., description="目标网页 URL，必须包含协议前缀（http://或https://）"),
    ]
    method: Annotated[str , Field(
        default="auto",
        description="抓取方法选择：auto（自动选择最佳方法）、simple（快速HTTP请求，不支持JavaScript）、scrapy（Scrapy框架，适合大规模抓取）、selenium（浏览器渲染，支持JavaScript和动态内容）",
    )]
    extract_config: Annotated[Optional[Dict[str, Any]] , Field(
        default=None,
        description="数据提取配置字典，支持CSS选择器和属性提取。示例：{'title': 'h1', 'content': {'selector': '.content p', 'multiple': True, 'attr': 'text'}}",
    )]
    wait_for_element: Annotated[Optional[str] , Field(
        default=None,
        description="等待元素的 CSS 选择器（仅 Selenium 方法有效），确保页面完全加载后再提取内容。示例：'.content'、'#main-content'",
    )]

    @field_validator("url")
    def validate_url(cls, v: str) -> str:
        """Validate URL format."""
        parsed = urlparse(v)
        if not parsed.scheme or not parsed.netloc:
            raise ValueError("Invalid URL format")
        return v

    @field_validator("method")
    def validate_method(cls, v: str) -> str:
        """Validate scraping method."""
        if v not in ["auto", "simple", "scrapy", "selenium"]:
            raise ValueError("Method must be one of: auto, simple, scrapy, selenium")
        return v


class BatchScrapeRequest(BaseModel):
    """Request model for scraping multiple URLs."""

    urls: List[str] = Field(
        ...,
        description="要抓取的 URL 列表，每个 URL 必须包含协议前缀。支持并发抓取以提高效率",
    )
    method: str = Field(
        default="auto",
        description="抓取方法选择：auto（自动选择最佳方法）、simple（快速HTTP请求）、scrapy（Scrapy框架，适合批量处理）、selenium（浏览器渲染，支持JavaScript）",
    )
    extract_config: Optional[Dict[str, Any]] = Field(
        default=None,
        description="统一的数据提取配置，应用于所有URL。格式：{'字段名': '选择器', '复杂字段': {'selector': 'CSS选择器', 'multiple': True/False, 'attr': '属性名'}}",
    )

    @field_validator("urls")
    def validate_urls(cls, v: List[str]) -> List[str]:
        """Validate URLs format."""
        if not v:
            raise ValueError("URLs list cannot be empty")

        for url in v:
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                raise ValueError(f"Invalid URL format: {url}")
        return v

    @field_validator("method")
    def validate_method(cls, v: str) -> str:
        """Validate scraping method."""
        if v not in ["auto", "simple", "scrapy", "selenium"]:
            raise ValueError("Method must be one of: auto, simple, scrapy, selenium")
        return v


class ExtractLinksRequest(BaseModel):
    """Request model for extracting links from a page."""

    url: str = Field(..., description="要提取链接的网页URL")
    filter_domains: Optional[List[str]] = Field(
        default=None,
        description="仅包含这些域名的链接，支持多域名过滤。示例：['example.com', 'subdomain.example.com']",
    )
    exclude_domains: Optional[List[str]] = Field(
        default=None,
        description="排除这些域名的链接，用于过滤不需要的外部链接。示例：['ads.com', 'tracker.net']",
    )
    internal_only: bool = Field(
        default=False,
        description="是否仅提取内部链接（同域名链接），设为True时只返回与源页面相同域名的链接",
    )

    @field_validator("url")
    def validate_url(cls, v: str) -> str:
        """Validate URL format."""
        parsed = urlparse(v)
        if not parsed.scheme or not parsed.netloc:
            raise ValueError("Invalid URL format")
        return v


class GetPageInfoRequest(BaseModel):
    """Request model for getting page information."""

    url: str = Field(..., description="要获取信息的网页URL")

    @field_validator("url")
    def validate_url(cls, v: str) -> str:
        """Validate URL format."""
        parsed = urlparse(v)
        if not parsed.scheme or not parsed.netloc:
            raise ValueError("Invalid URL format")
        return v


class CheckRobotsRequest(BaseModel):
    """Request model for checking robots.txt."""

    url: str = Field(..., description="要检查robots.txt的网站URL")

    @field_validator("url")
    def validate_url(cls, v: str) -> str:
        """Validate URL format."""
        parsed = urlparse(v)
        if not parsed.scheme or not parsed.netloc:
            raise ValueError("Invalid URL format")
        return v


class ExtractStructuredDataRequest(BaseModel):
    """Request model for extracting structured data."""

    url: str = Field(..., description="要提取结构化数据的网页URL")
    data_type: str = Field(
        default="all",
        description="数据类型: all（全部）、contact（联系信息）、social（社交媒体）、content（内容）、products（产品）、addresses（地址）",
    )

    @field_validator("url")
    def validate_url(cls, v: str) -> str:
        """Validate URL format."""
        parsed = urlparse(v)
        if not parsed.scheme or not parsed.netloc:
            raise ValueError("Invalid URL format")
        return v

    @field_validator("data_type")
    def validate_data_type(cls, v: str) -> str:
        """Validate data type."""
        valid_types = ["all", "contact", "social", "content", "products", "addresses"]
        if v not in valid_types:
            raise ValueError(f"Data type must be one of: {', '.join(valid_types)}")
        return v


# Response Models
class ScrapeResponse(BaseModel):
    """Response model for scraping operations."""

    success: bool = Field(..., description="操作是否成功")
    url: str = Field(..., description="被抓取的URL")
    method: str = Field(..., description="使用的抓取方法")
    data: Optional[Dict[str, Any]] = Field(default=None, description="抓取到的数据")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="页面元数据")
    error: Optional[str] = Field(default=None, description="错误信息（如果有）")
    timestamp: datetime = Field(default_factory=datetime.now, description="抓取时间戳")


class BatchScrapeResponse(BaseModel):
    """Response model for batch scraping operations."""

    success: bool = Field(..., description="整体操作是否成功")
    total_urls: int = Field(..., description="总URL数量")
    successful_count: int = Field(..., description="成功抓取的数量")
    failed_count: int = Field(..., description="失败的数量")
    results: List[ScrapeResponse] = Field(..., description="每个URL的抓取结果")
    summary: Dict[str, Any] = Field(..., description="批量操作摘要信息")


class LinkItem(BaseModel):
    """Individual link item model."""

    url: str = Field(..., description="链接URL")
    text: str = Field(..., description="链接文本")
    is_internal: bool = Field(..., description="是否为内部链接")


class LinksResponse(BaseModel):
    """Response model for link extraction."""

    success: bool = Field(..., description="操作是否成功")
    url: str = Field(..., description="源页面URL")
    total_links: int = Field(..., description="总链接数量")
    links: List[LinkItem] = Field(..., description="提取的链接列表")
    internal_links_count: int = Field(..., description="内部链接数量")
    external_links_count: int = Field(..., description="外部链接数量")
    error: Optional[str] = Field(default=None, description="错误信息（如果有）")


class PageInfoResponse(BaseModel):
    """Response model for page information."""

    success: bool = Field(..., description="操作是否成功")
    url: str = Field(..., description="页面URL")
    title: Optional[str] = Field(default=None, description="页面标题")
    description: Optional[str] = Field(default=None, description="页面描述")
    status_code: int = Field(..., description="HTTP状态码")
    content_type: Optional[str] = Field(default=None, description="内容类型")
    content_length: Optional[int] = Field(default=None, description="内容长度")
    last_modified: Optional[str] = Field(default=None, description="最后修改时间")
    error: Optional[str] = Field(default=None, description="错误信息（如果有）")


class RobotsResponse(BaseModel):
    """Response model for robots.txt check."""

    success: bool = Field(..., description="操作是否成功")
    url: str = Field(..., description="检查的URL")
    robots_txt_url: str = Field(..., description="robots.txt文件URL")
    robots_content: Optional[str] = Field(default=None, description="robots.txt内容")
    is_allowed: bool = Field(..., description="是否允许抓取")
    user_agent: str = Field(..., description="使用的User-Agent")
    error: Optional[str] = Field(default=None, description="错误信息（如果有）")


class StructuredDataResponse(BaseModel):
    """Response model for structured data extraction."""

    success: bool = Field(..., description="操作是否成功")
    url: str = Field(..., description="源页面URL")
    data_type: str = Field(..., description="提取的数据类型")
    extracted_data: Dict[str, Any] = Field(..., description="提取的结构化数据")
    data_count: int = Field(..., description="提取的数据项数量")
    error: Optional[str] = Field(default=None, description="错误信息（如果有）")


class MarkdownResponse(BaseModel):
    """Response model for Markdown conversion."""

    success: bool = Field(..., description="操作是否成功")
    url: str = Field(..., description="源页面URL")
    method: str = Field(..., description="使用的转换方法")
    markdown_content: Optional[str] = Field(
        default=None, description="转换后的Markdown内容"
    )
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="页面元数据")
    word_count: int = Field(default=0, description="字数统计")
    images_embedded: int = Field(default=0, description="嵌入的图片数量")
    conversion_time: float = Field(..., description="转换耗时（秒）")
    error: Optional[str] = Field(default=None, description="错误信息（如果有）")


class BatchMarkdownResponse(BaseModel):
    """Response model for batch Markdown conversion."""

    success: bool = Field(..., description="整体操作是否成功")
    total_urls: int = Field(..., description="总URL数量")
    successful_count: int = Field(..., description="成功转换的数量")
    failed_count: int = Field(..., description="失败的数量")
    results: List[MarkdownResponse] = Field(..., description="每个URL的转换结果")
    total_word_count: int = Field(default=0, description="总字数")
    total_conversion_time: float = Field(..., description="总转换时间（秒）")


class PDFResponse(BaseModel):
    """Response model for PDF conversion."""

    success: bool = Field(..., description="操作是否成功")
    pdf_source: str = Field(..., description="PDF源路径或URL")
    method: str = Field(..., description="使用的转换方法")
    output_format: str = Field(..., description="输出格式")
    content: Optional[str] = Field(default=None, description="转换后的内容")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="PDF元数据")
    page_count: int = Field(default=0, description="页数")
    word_count: int = Field(default=0, description="字数统计")
    conversion_time: float = Field(..., description="转换耗时（秒）")
    error: Optional[str] = Field(default=None, description="错误信息（如果有）")


class BatchPDFResponse(BaseModel):
    """Response model for batch PDF conversion."""

    success: bool = Field(..., description="整体操作是否成功")
    total_pdfs: int = Field(..., description="总PDF数量")
    successful_count: int = Field(..., description="成功转换的数量")
    failed_count: int = Field(..., description="失败的数量")
    results: List[PDFResponse] = Field(..., description="每个PDF的转换结果")
    total_pages: int = Field(default=0, description="总页数")
    total_word_count: int = Field(default=0, description="总字数")
    total_conversion_time: float = Field(..., description="总转换时间（秒）")


class MetricsResponse(BaseModel):
    """Response model for server metrics."""

    success: bool = Field(..., description="操作是否成功")
    total_requests: int = Field(..., description="总请求数")
    successful_requests: int = Field(..., description="成功请求数")
    failed_requests: int = Field(..., description="失败请求数")
    success_rate: float = Field(..., description="成功率")
    average_response_time: float = Field(..., description="平均响应时间（秒）")
    uptime_seconds: float = Field(..., description="运行时间（秒）")
    cache_stats: Dict[str, Any] = Field(..., description="缓存统计")
    method_usage: Dict[str, int] = Field(..., description="方法使用统计")
    error_categories: Dict[str, int] = Field(..., description="错误分类统计")


class CacheOperationResponse(BaseModel):
    """Response model for cache clearing."""

    success: bool = Field(..., description="操作是否成功")
    cleared_items: int = Field(..., description="清理的缓存项数量")
    cache_size_before: int = Field(..., description="清理前缓存大小")
    cache_size_after: int = Field(..., description="清理后缓存大小")
    operation_time: float = Field(..., description="操作耗时（秒）")
    message: str = Field(..., description="操作结果消息")


@app.tool()
async def scrape_webpage(request: ScrapeRequest) -> ScrapeResponse:
    """
    Scrape a single webpage and extract its content.

    Args:
        url: URL to scrape
        method: Scraping method: auto, simple, scrapy, selenium (default: auto)
        extract_config: Configuration for data extraction (optional)
        wait_for_element: CSS selector to wait for - Selenium only (optional)

    This tool can scrape web pages using different methods:
    - auto: Automatically choose the best method
    - simple: Fast HTTP requests (no JavaScript)
    - scrapy: Robust scraping with Scrapy framework
    - selenium: Full browser rendering (supports JavaScript)

    You can specify extraction rules to get specific data from the page.
    """
    try:
        logger.info(f"Scraping webpage: {request.url} with method: {request.method}")

        result = await web_scraper.scrape_url(
            url=request.url,
            method=request.method,
            extract_config=request.extract_config,
            wait_for_element=request.wait_for_element,
        )

        # Check if the scraper returned an error
        if "error" in result:
            return ScrapeResponse(
                success=False,
                url=request.url,
                method=request.method,
                error=result["error"],
            )

        return ScrapeResponse(
            success=True, url=request.url, method=request.method, data=result
        )

    except Exception as e:
        logger.error(f"Error scraping webpage {request.url}: {str(e)}")
        return ScrapeResponse(
            success=False, url=request.url, method=request.method, error=str(e)
        )


@app.tool()
async def scrape_multiple_webpages(request: BatchScrapeRequest) -> BatchScrapeResponse:
    """
    Scrape multiple webpages concurrently.

    Args:
        urls: List of URLs to scrape
        method: Scraping method: auto, simple, scrapy, selenium (default: auto)
        extract_config: Configuration for data extraction (optional)

    This tool allows you to scrape multiple URLs at once, which is much faster
    than scraping them one by one. All URLs will be processed concurrently.
    """
    try:
        logger.info(
            f"Scraping {len(request.urls)} webpages with method: {request.method}"
        )

        results = await web_scraper.scrape_multiple_urls(
            urls=request.urls,
            method=request.method,
            extract_config=request.extract_config,
        )

        # Convert results to ScrapeResponse objects
        scrape_responses = []
        for i, result in enumerate(results):
            url = request.urls[i]
            if "error" in result:
                response = ScrapeResponse(
                    success=False, url=url, method=request.method, error=result["error"]
                )
            else:
                response = ScrapeResponse(
                    success=True, url=url, method=request.method, data=result
                )
            scrape_responses.append(response)

        successful_count = sum(1 for r in scrape_responses if r.success)
        failed_count = len(scrape_responses) - successful_count

        return BatchScrapeResponse(
            success=True,
            total_urls=len(request.urls),
            successful_count=successful_count,
            failed_count=failed_count,
            results=scrape_responses,
            summary={
                "total": len(request.urls),
                "successful": successful_count,
                "failed": failed_count,
                "method_used": request.method,
            },
        )

    except Exception as e:
        logger.error(f"Error scraping multiple webpages: {str(e)}")
        return BatchScrapeResponse(
            success=False,
            total_urls=len(request.urls),
            successful_count=0,
            failed_count=len(request.urls),
            results=[],
            summary={"error": str(e)},
        )


@app.tool()
async def extract_links(request: ExtractLinksRequest) -> LinksResponse:
    """
    Extract all links from a webpage.

    Args:
        url (str): 目标网页URL，必须包含协议前缀（http://或https://），将从此页面提取所有链接
        filter_domains (List[str], optional): 白名单域名列表，仅包含这些域名的链接。
            示例：['example.com', 'subdomain.example.com']
        exclude_domains (List[str], optional): 黑名单域名列表，排除这些域名的链接。
            示例：['ads.com', 'tracker.net']
        internal_only (bool, optional): 是否仅提取内部链接，即与源页面相同域名的链接。
            默认值：False

    This tool is specialized for link extraction and can filter links by domain,
    extract only internal links, or exclude specific domains.

    Returns:
        Dict containing success status, extracted links list, and optional filtering statistics.
        Each link includes url, text, and additional attributes if available.
    """
    try:
        logger.info(f"Extracting links from: {request.url}")

        # Scrape the page to get links
        scrape_result = await web_scraper.scrape_url(
            url=request.url,
            method="simple",  # Use simple method for link extraction
        )

        if "error" in scrape_result:
            return LinksResponse(
                success=False,
                url=request.url,
                total_links=0,
                links=[],
                internal_links_count=0,
                external_links_count=0,
                error=scrape_result["error"],
            )

        # Extract and filter links
        all_links = scrape_result.get("content", {}).get("links", [])
        base_domain = urlparse(request.url).netloc

        filtered_links = []
        for link in all_links:
            link_url = link.get("url", "")
            if not link_url:
                continue

            link_domain = urlparse(link_url).netloc

            # Apply filters
            if request.internal_only and link_domain != base_domain:
                continue

            if request.filter_domains and link_domain not in request.filter_domains:
                continue

            if request.exclude_domains and link_domain in request.exclude_domains:
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
            url=request.url,
            total_links=len(filtered_links),
            links=filtered_links,
            internal_links_count=internal_count,
            external_links_count=external_count,
        )

    except Exception as e:
        logger.error(f"Error extracting links from {request.url}: {str(e)}")
        return LinksResponse(
            success=False,
            url=request.url,
            total_links=0,
            links=[],
            internal_links_count=0,
            external_links_count=0,
            error=str(e),
        )


@app.tool()
async def get_page_info(request: GetPageInfoRequest) -> PageInfoResponse:
    """
    Get basic information about a webpage (title, description, status).

    Args:
        url (str): 目标网页URL，必须包含协议前缀（http://或https://），用于获取页面基础信息和元数据

    This is a lightweight tool for quickly checking page accessibility and
    getting basic metadata without full content extraction.

    Returns:
        Dict containing success status, URL, status_code, title, meta_description, and domain.
        Useful for quick page validation and metadata extraction.
    """
    try:
        logger.info(f"Getting page info for: {request.url}")

        # Use simple scraper for quick info
        result = await web_scraper.simple_scraper.scrape(request.url, extract_config={})

        if "error" in result:
            return PageInfoResponse(
                success=False, url=request.url, status_code=0, error=result["error"]
            )

        return PageInfoResponse(
            success=True,
            url=result.get("url", request.url),
            title=result.get("title"),
            description=result.get("meta_description"),
            status_code=result.get("status_code", 200),
            content_type=result.get("content_type"),
            content_length=result.get("content_length"),
        )

    except Exception as e:
        logger.error(f"Error getting page info for {request.url}: {str(e)}")
        return PageInfoResponse(
            success=False, url=request.url, status_code=0, error=str(e)
        )


@app.tool()
async def check_robots_txt(request: CheckRobotsRequest) -> RobotsResponse:
    """
    Check the robots.txt file for a domain to understand crawling permissions.

    Args:
        url (str): 网站域名URL，必须包含协议前缀（http://或https://），将检查该域名的robots.txt文件。
            示例：'https://example.com' 将检查 'https://example.com/robots.txt'

    This tool helps ensure ethical scraping by checking the robots.txt file
    of a website to see what crawling rules are in place.

    Returns:
        Dict containing success status, robots.txt content, base domain, and content availability.
        Helps determine crawling permissions and restrictions for the specified domain.
    """
    try:
        logger.info(f"Checking robots.txt for: {request.url}")

        # Parse URL to get base domain
        parsed = urlparse(request.url)
        robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"

        # Scrape robots.txt
        result = await web_scraper.simple_scraper.scrape(robots_url, extract_config={})

        if "error" in result:
            return RobotsResponse(
                success=False,
                url=request.url,
                robots_txt_url=robots_url,
                is_allowed=False,
                user_agent="*",
                error=f"Could not fetch robots.txt: {result['error']}",
            )

        robots_content = result.get("content", {}).get("text", "")

        return RobotsResponse(
            success=True,
            url=request.url,
            robots_txt_url=robots_url,
            robots_content=robots_content,
            is_allowed=True,  # Basic check, could be enhanced
            user_agent="*",
        )

    except Exception as e:
        logger.error(f"Error checking robots.txt for {request.url}: {str(e)}")
        return RobotsResponse(
            success=False,
            url=request.url,
            robots_txt_url="",
            is_allowed=False,
            user_agent="*",
            error=str(e),
        )


class StealthScrapeRequest(BaseModel):
    """Request model for stealth scraping operations."""

    url: str = Field(
        ..., description="要使用隐身技术抓取的URL，适用于具有反爿虫保护的网站"
    )
    method: str = Field(
        default="selenium",
        description="隐身抓取方法：selenium（使用undetected-chromedriver，适合大部分场景）或playwright（Microsoft Playwright，更多浏览器支持）",
    )
    extract_config: Optional[Dict[str, Any]] = Field(
        default=None,
        description="数据提取配置，支持复杂的CSS选择器和属性提取。隐身模式下推荐使用简单配置以减少检测风险",
    )
    wait_for_element: Optional[str] = Field(
        default=None,
        description="等待特定元素出现的CSS选择器，确保动态内容加载完成再提取。隐身模式下建议设置以提高成功率",
    )
    scroll_page: bool = Field(
        default=False,
        description="是否滚动页面以加载动态内容，适用于无限滚动或懒加载的页面。滚动行为会模拟真实用户操作",
    )

    @field_validator("url")
    def validate_url(cls, v: str) -> str:
        """Validate URL format."""
        if not URLValidator.is_valid_url(v):
            raise ValueError("Invalid URL format")
        return URLValidator.normalize_url(v)

    @field_validator("method")
    def validate_method(cls, v: str) -> str:
        """Validate stealth method."""
        if v not in ["selenium", "playwright"]:
            raise ValueError("Method must be one of: selenium, playwright")
        return v


class FormRequest(BaseModel):
    """Request model for form interaction operations."""

    url: str = Field(
        ..., description="包含表单的页面URL，将在此页面上执行表单填写和提交操作"
    )
    form_data: Dict[str, Any] = Field(
        ...,
        description="表单字段数据，格式为 {'选择器': '值'}。支持文本输入、密码、单选框、多选框、下拉选择等。示例：{'#username': '用户名', 'input[name=\"password\"]': '密码', '#submit-btn': 'click'}",
    )
    submit: bool = Field(
        default=False,
        description="是否在填写完成后自动提交表单。设为False时仅填写不提交，适合预处理或测试场景",
    )
    submit_button_selector: Optional[str] = Field(
        default=None,
        description="提交按钮的CSS选择器，如未指定则尝试自动检测。建议明确指定以提高成功率。示例：'button[type=\"submit\"]'、'#login-btn'",
    )
    method: str = Field(
        default="selenium",
        description="表单交互方法：selenium（成熟稳定，支持复杂表单）或playwright（现代化，性能更好）",
    )
    wait_for_element: Optional[str] = Field(
        default=None,
        description="在开始填写表单前等待的元素CSS选择器，确保表单完全加载。示例：'form'、'.login-form'",
    )

    @field_validator("url")
    def validate_url(cls, v: str) -> str:
        """Validate URL format."""
        if not URLValidator.is_valid_url(v):
            raise ValueError("Invalid URL format")
        return URLValidator.normalize_url(v)

    @field_validator("method")
    def validate_method(cls, v: str) -> str:
        """Validate method."""
        if v not in ["selenium", "playwright"]:
            raise ValueError("Method must be one of: selenium, playwright")
        return v


class ConvertToMarkdownRequest(BaseModel):
    """Request model for converting webpage to Markdown."""

    url: str = Field(..., description="要转换为Markdown的网页URL")
    method: str = Field(
        default="auto",
        description="抓取方法：auto（自动选择）、simple（HTTP请求）、scrapy（Scrapy框架）、selenium（浏览器渲染，适合动态内容）",
    )
    extract_main_content: bool = Field(
        default=True,
        description="是否仅提取主要内容区域，启用时会移除导航栏、广告、侧边栏等非核心内容，提供更清晰的Markdown输出",
    )
    include_metadata: bool = Field(
        default=True,
        description="是否在结果中包含页面元数据（标题、描述、字数统计、链接数等）",
    )
    custom_options: Optional[Dict[str, Any]] = Field(
        default=None,
        description="自定义markdownify转换选项，支持strip、convert、wrap等参数。示例：{'strip': ['script', 'style'], 'convert': ['p', 'br']}",
    )
    wait_for_element: Optional[str] = Field(
        default=None,
        description="等待特定元素出现的CSS选择器（仅Selenium方法），确保动态内容加载完成。示例：'.article-content'、'#main'",
    )
    embed_images: bool = Field(
        default=False,
        description="是否嵌入图片作为数据URI，默认值：False",
    )
    embed_options: Optional[Dict[str, Any]] = Field(
        default=None,
        description="图片嵌入选项配置，支持quality、format、max_size等选项",
    )

    @field_validator("url")
    def validate_url(cls, v: str) -> str:
        """Validate URL format."""
        parsed = urlparse(v)
        if not parsed.scheme or not parsed.netloc:
            raise ValueError("Invalid URL format")
        return v

    @field_validator("method")
    def validate_method(cls, v: str) -> str:
        """Validate scraping method."""
        if v not in ["auto", "simple", "scrapy", "selenium"]:
            raise ValueError("Method must be one of: auto, simple, scrapy, selenium")
        return v


class BatchConvertToMarkdownRequest(BaseModel):
    """Request model for batch converting webpages to Markdown."""

    urls: List[str] = Field(
        ..., description="要批量转换为Markdown的URL列表，支持并发处理以提高效率"
    )
    method: str = Field(
        default="auto",
        description="统一的抓取方法：auto（智能选择）、simple（轻量级HTTP）、scrapy（适合大批量）、selenium（支持JavaScript动态页面）",
    )
    extract_main_content: bool = Field(
        default=True,
        description="是否统一提取主要内容区域，过滤掉导航、广告、页脚等非核心内容，获得更纯净的Markdown文档",
    )
    include_metadata: bool = Field(
        default=True,
        description="是否在每个转换结果中包含页面元数据，包含标题、URL、字数、处理时间等信息",
    )
    custom_options: Optional[Dict[str, Any]] = Field(
        default=None,
        description="统一的markdownify自定义选项，应用于所有URL。支持HTML标签处理、格式化选项等",
    )
    embed_images: bool = Field(
        default=False,
        description="是否在所有页面中嵌入图片作为数据URI，默认值：False",
    )
    embed_options: Optional[Dict[str, Any]] = Field(
        default=None,
        description="统一的图片嵌入选项配置，应用于所有URL",
    )

    @field_validator("urls")
    def validate_urls(cls, v: List[str]) -> List[str]:
        """Validate URLs format."""
        if not v:
            raise ValueError("URLs list cannot be empty")

        for url in v:
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                raise ValueError(f"Invalid URL format: {url}")
        return v

    @field_validator("method")
    def validate_method(cls, v: str) -> str:
        """Validate scraping method."""
        if v not in ["auto", "simple", "scrapy", "selenium"]:
            raise ValueError("Method must be one of: auto, simple, scrapy, selenium")
        return v


class PDFToMarkdownRequest(BaseModel):
    """Request model for converting PDF to Markdown."""

    pdf_source: str = Field(
        ...,
        description="PDF源路径，支持HTTP/HTTPS URL或本地文件绝对路径。URL将自动下载处理，本地路径需确保文件存在",
    )
    method: str = Field(
        default="auto",
        description="PDF提取方法：auto（自动选择最佳引擎）、pymupdf（PyMuPDF引擎，适合复杂布局）、pypdf（PyPDF引擎，适合简单文本）",
    )
    include_metadata: bool = Field(
        default=True,
        description="是否在结果中包含PDF元数据（标题、作者、创建日期、页数等）和处理统计信息",
    )
    page_range: Optional[List[int]] = Field(
        default=None,
        description="页面范围[start, end]用于部分提取，两个整数表示起始页和结束页。示例：[1, 10]提取第1-10页。页码从0开始计数",
    )
    output_format: str = Field(
        default="markdown",
        description="输出格式选择：markdown（结构化Markdown文档，保留格式信息）或text（纯文本内容，去除所有格式）",
    )

    @field_validator("method")
    def validate_method(cls, v: str) -> str:
        """Validate extraction method."""
        if v not in ["auto", "pymupdf", "pypdf"]:
            raise ValueError("Method must be one of: auto, pymupdf, pypdf")
        return v

    @field_validator("output_format")
    def validate_output_format(cls, v: str) -> str:
        """Validate output format."""
        if v not in ["markdown", "text"]:
            raise ValueError("Output format must be one of: markdown, text")
        return v

    @field_validator("page_range")
    def validate_page_range(cls, v: Optional[List[int]]) -> Optional[tuple]:
        """Validate and convert page range."""
        if v is None:
            return None
        if len(v) != 2:
            raise ValueError("Page range must contain exactly 2 elements: [start, end]")
        if v[0] < 0 or v[1] < 0:
            raise ValueError("Page numbers must be non-negative")
        if v[0] >= v[1]:
            raise ValueError("Start page must be less than end page")
        return tuple(v)


class BatchPDFToMarkdownRequest(BaseModel):
    """Request model for batch converting PDFs to Markdown."""

    pdf_sources: List[str] = Field(
        ...,
        description="PDF源列表，支持混合使用URL和本地文件路径。URL将并发下载，本地文件需确保存在且可读",
    )
    method: str = Field(
        default="auto",
        description="统一的PDF提取方法：auto（智能选择）、pymupdf（适合复杂排版和图表）、pypdf（适合简单纯文本文档）",
    )
    include_metadata: bool = Field(
        default=True,
        description="是否在每个转换结果中包含PDF元数据和处理统计，包括文件名、大小、页数、处理时间等",
    )
    page_range: Optional[List[int]] = Field(
        default=None,
        description="应用于所有PDF的统一页面范围[start, end]。如未指定则提取全部页面。页码从0开始计数",
    )
    output_format: str = Field(
        default="markdown",
        description="统一输出格式：markdown（保留标题、列表等结构化信息）或text（纯文本，去除所有格式化）",
    )

    @field_validator("pdf_sources")
    def validate_pdf_sources(cls, v: List[str]) -> List[str]:
        """Validate PDF sources."""
        if not v:
            raise ValueError("PDF sources list cannot be empty")
        return v

    @field_validator("method")
    def validate_method(cls, v: str) -> str:
        """Validate extraction method."""
        if v not in ["auto", "pymupdf", "pypdf"]:
            raise ValueError("Method must be one of: auto, pymupdf, pypdf")
        return v

    @field_validator("output_format")
    def validate_output_format(cls, v: str) -> str:
        """Validate output format."""
        if v not in ["markdown", "text"]:
            raise ValueError("Output format must be one of: markdown, text")
        return v

    @field_validator("page_range")
    def validate_page_range(cls, v: Optional[List[int]]) -> Optional[tuple]:
        """Validate and convert page range."""
        if v is None:
            return None
        if len(v) != 2:
            raise ValueError("Page range must contain exactly 2 elements: [start, end]")
        if v[0] < 0 or v[1] < 0:
            raise ValueError("Page numbers must be non-negative")
        if v[0] >= v[1]:
            raise ValueError("Start page must be less than end page")
        return tuple(v)


@app.tool()
@timing_decorator
async def scrape_with_stealth(request: StealthScrapeRequest) -> ScrapeResponse:
    """
    Scrape a webpage using advanced stealth techniques to avoid detection.

    Args:
        url (str): 目标网页URL，必须包含协议前缀（http://或https://），使用反检测技术抓取
        method (str, optional): 隐身方法选择，默认值："selenium"
            - "selenium": 使用undetected-chromedriver反检测技术
            - "playwright": 使用Playwright隐身模式
        extract_config (Dict[str, Any], optional): 数据提取配置字典，格式同标准抓取工具。
            示例：{"title": "h1", "content": ".article-body"}
        wait_for_element (str, optional): 等待加载的元素CSS选择器，确保动态内容完全加载。
            示例：".content", "#main-article"
        scroll_page (bool, optional): 是否滚动页面加载动态内容，默认值：False

    This tool uses sophisticated anti-detection methods including:
    - Undetected browser automation
    - Randomized behavior patterns
    - Human-like interactions
    - Advanced evasion techniques

    Use this for websites with strong anti-bot protection.

    Returns:
        Dict containing success status, scraped data, stealth method used, and performance metrics.
        Designed for bypassing sophisticated bot detection systems.
    """
    try:
        from .utils import URLValidator

        # Validate inputs
        if not URLValidator.is_valid_url(request.url):
            return ScrapeResponse(
                success=False,
                url=request.url,
                method=request.method,
                error="Invalid URL format",
            )

        if request.method not in ["selenium", "playwright"]:
            return ScrapeResponse(
                success=False,
                url=request.url,
                method=request.method,
                error="Method must be one of: selenium, playwright",
            )

        start_time = time.time()
        logger.info(f"Stealth scraping: {request.url} with method: {request.method}")

        # Apply rate limiting
        await rate_limiter.wait()

        # Normalize URL
        normalized_url = URLValidator.normalize_url(request.url)

        # Check cache first
        cache_key_data = {
            "extract_config": request.extract_config,
            "wait_for_element": request.wait_for_element,
            "scroll_page": request.scroll_page,
        }
        cached_result = cache_manager.get(
            normalized_url, f"stealth_{request.method}", cache_key_data
        )
        if cached_result:
            logger.info(f"Returning cached result for {normalized_url}")
            cached_result["from_cache"] = True
            return cached_result

        # Validate and normalize extract config
        extract_config = request.extract_config
        if extract_config:
            extract_config = ConfigValidator.validate_extract_config(extract_config)

        # Perform stealth scraping with retry
        result = await retry_manager.retry_async(
            anti_detection_scraper.scrape_with_stealth,
            url=normalized_url,
            method=request.method,
            extract_config=extract_config,
            wait_for_element=request.wait_for_element,
            scroll_page=request.scroll_page,
        )

        duration_ms = int((time.time() - start_time) * 1000)
        success = "error" not in result

        if success:
            # Clean text content if present
            if "content" in result and "text" in result["content"]:
                result["content"]["text"] = TextCleaner.clean_text(
                    result["content"]["text"]
                )

            # Cache successful result
            cache_manager.set(
                normalized_url, f"stealth_{request.method}", result, cache_key_data
            )

            metrics_collector.record_request(
                normalized_url, True, duration_ms, f"stealth_{request.method}"
            )

            return ScrapeResponse(
                success=True,
                url=request.url,
                method=f"stealth_{request.method}",
                data=result,
                duration_ms=duration_ms,
                from_cache=False,
            )
        else:
            error_response = ErrorHandler.handle_scraping_error(
                Exception(result.get("error", "Unknown error")),
                normalized_url,
                f"stealth_{request.method}",
            )
            metrics_collector.record_request(
                normalized_url,
                False,
                duration_ms,
                f"stealth_{request.method}",
                error_response["error"]["category"],
            )
            return ScrapeResponse(
                success=False,
                url=request.url,
                method=f"stealth_{request.method}",
                error=error_response["error"]["message"],
            )

    except Exception as e:
        duration_ms = (
            int((time.time() - start_time) * 1000) if "start_time" in locals() else 0
        )
        error_response = ErrorHandler.handle_scraping_error(
            e, request.url, f"stealth_{request.method}"
        )
        metrics_collector.record_request(
            request.url,
            False,
            duration_ms,
            f"stealth_{request.method}",
            error_response["error"]["category"],
        )
        return ScrapeResponse(
            success=False,
            url=request.url,
            method=f"stealth_{request.method}",
            error=error_response["error"]["message"],
        )


@app.tool()
@timing_decorator
async def fill_and_submit_form(request: FormRequest) -> ScrapeResponse:
    """
    Fill and optionally submit a form on a webpage.

    Args:
        url (str): 包含表单的网页URL，必须包含协议前缀（http://或https://）
        form_data (Dict[str, Any]): 表单字段数据，格式为{"选择器": "值"}，支持各种表单元素。
            示例：{
                "#username": "admin",
                "input[name='password']": "secret",
                "select[name='country']": "US",
                "input[type='checkbox']": True
            }
        submit (bool, optional): 是否提交表单，默认值：False
        submit_button_selector (str, optional): 提交按钮的CSS选择器，如未指定则尝试自动查找。
            示例："button[type='submit']", "#submit-btn"
        method (str, optional): 自动化方法选择，默认值："selenium"
            - "selenium": 使用Selenium WebDriver
            - "playwright": 使用Playwright浏览器自动化
        wait_for_element (str, optional): 表单填写前等待加载的元素CSS选择器。
            示例：".form-container", "#login-form"

    This tool can handle various form elements including:
    - Text inputs
    - Checkboxes and radio buttons
    - Dropdown selects
    - File uploads
    - Form submission

    Useful for interacting with search forms, contact forms, login forms, etc.

    Returns:
        Dict containing success status, form interaction results, and optional submission response.
        Supports complex form automation workflows.
    """
    try:
        from .utils import URLValidator

        # Validate inputs
        if not URLValidator.is_valid_url(request.url):
            return ScrapeResponse(
                success=False,
                url=request.url,
                method=request.method,
                error="Invalid URL format",
            )

        if request.method not in ["selenium", "playwright"]:
            return ScrapeResponse(
                success=False,
                url=request.url,
                method=request.method,
                error="Method must be one of: selenium, playwright",
            )

        start_time = time.time()
        logger.info(f"Form interaction for: {request.url}")

        # Apply rate limiting
        await rate_limiter.wait()

        # Setup browser based on method
        if request.method == "selenium":
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options as ChromeOptions

            options = ChromeOptions()
            if settings.browser_headless:
                options.add_argument("--headless")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")

            driver = webdriver.Chrome(options=options)
            try:
                driver.get(request.url)

                # Wait for element if specified
                if request.wait_for_element:
                    from selenium.webdriver.common.by import By
                    from selenium.webdriver.support.ui import WebDriverWait
                    from selenium.webdriver.support import expected_conditions as EC

                    WebDriverWait(driver, settings.browser_timeout).until(
                        EC.presence_of_element_located(
                            (By.CSS_SELECTOR, request.wait_for_element)
                        )
                    )

                # Fill and submit form
                form_handler = FormHandler(driver)
                result = await form_handler.fill_form(
                    form_data=request.form_data,
                    submit=request.submit,
                    submit_button_selector=request.submit_button_selector,
                )

                # Get final page info
                final_url = driver.current_url
                final_title = driver.title

            finally:
                driver.quit()

        elif request.method == "playwright":
            from playwright.async_api import async_playwright

            playwright = await async_playwright().start()
            try:
                browser = await playwright.chromium.launch(
                    headless=settings.browser_headless
                )
                context = await browser.new_context()
                page = await context.new_page()

                await page.goto(request.url, timeout=60000)

                # Wait for element if specified
                if request.wait_for_element:
                    await page.wait_for_selector(
                        request.wait_for_element,
                        timeout=settings.browser_timeout * 1000,
                    )

                # Fill and submit form
                form_handler = FormHandler(page)
                result = await form_handler.fill_form(
                    form_data=request.form_data,
                    submit=request.submit,
                    submit_button_selector=request.submit_button_selector,
                )

                # Get final page info
                final_url = page.url
                final_title = await page.title()

            finally:
                await browser.close()
                await playwright.stop()

        duration_ms = int((time.time() - start_time) * 1000)

        if result.get("success"):
            metrics_collector.record_request(
                request.url, True, duration_ms, f"form_{request.method}"
            )

            return ScrapeResponse(
                success=True,
                url=request.url,
                method=f"form_{request.method}",
                data={
                    "form_results": result,
                    "final_url": final_url,
                    "final_title": final_title,
                    "original_url": request.url,
                },
            )
        else:
            error_response = ErrorHandler.handle_scraping_error(
                Exception(result.get("error", "Form interaction failed")),
                request.url,
                f"form_{request.method}",
            )
            metrics_collector.record_request(
                request.url,
                False,
                duration_ms,
                f"form_{request.method}",
                error_response["error"]["category"],
            )
            return ScrapeResponse(
                success=False,
                url=request.url,
                method=f"form_{request.method}",
                error=error_response["error"]["message"],
            )

    except Exception as e:
        duration_ms = (
            int((time.time() - start_time) * 1000) if "start_time" in locals() else 0
        )
        error_response = ErrorHandler.handle_scraping_error(
            e, request.url, f"form_{request.method}"
        )
        metrics_collector.record_request(
            request.url,
            False,
            duration_ms,
            f"form_{request.method}",
            error_response["error"]["category"],
        )
        return ScrapeResponse(
            success=False,
            url=request.url,
            method=f"form_{request.method}",
            error=error_response["error"]["message"],
        )


@app.tool()
async def get_server_metrics() -> MetricsResponse:
    """
    Get server performance metrics and statistics.

    Args: 无需参数，返回服务器性能指标和统计信息

    Returns information about:
    - Request counts and success rates
    - Performance metrics
    - Method usage statistics
    - Error categories
    - Cache statistics
    - Server configuration details

    Returns:
        Dict containing detailed server metrics including scraping performance,
        cache statistics, server configuration, and real-time statistics.
    """
    try:
        metrics = metrics_collector.get_stats()
        cache_stats = cache_manager.stats()

        return MetricsResponse(
            success=True,
            total_requests=metrics.get("total_requests", 0),
            successful_requests=metrics.get("successful_requests", 0),
            failed_requests=metrics.get("failed_requests", 0),
            success_rate=metrics.get("success_rate", 0.0),
            average_response_time=metrics.get("average_response_time", 0.0),
            uptime_seconds=metrics.get("uptime_seconds", 0.0),
            cache_stats=cache_stats,
            method_usage=metrics.get("method_usage", {}),
            error_categories=metrics.get("error_categories", {}),
        )
    except Exception as e:
        return MetricsResponse(
            success=False,
            total_requests=0,
            successful_requests=0,
            failed_requests=0,
            success_rate=0.0,
            average_response_time=0.0,
            uptime_seconds=0.0,
            cache_stats={},
            method_usage={},
            error_categories={},
        )


@app.tool()
async def clear_cache() -> CacheOperationResponse:
    """
    Clear the scraping results cache.

    Args: 无需参数，清理全局抓取结果缓存

    This removes all cached scraping results, forcing fresh requests
    for all subsequent scraping operations.

    Returns:
        Dict containing success status and cache clearing confirmation message.
        Useful for forcing fresh data retrieval and managing memory usage.
    """
    try:
        start_time = time.time()
        cache_size_before = (
            cache_manager.size() if hasattr(cache_manager, "size") else 0
        )
        cleared_items = cache_manager.clear()
        cache_size_after = 0
        operation_time = time.time() - start_time

        return CacheOperationResponse(
            success=True,
            cleared_items=cleared_items if isinstance(cleared_items, int) else 0,
            cache_size_before=cache_size_before,
            cache_size_after=cache_size_after,
            operation_time=operation_time,
            message="Cache cleared successfully",
        )
    except Exception as e:
        return CacheOperationResponse(
            success=False,
            cleared_items=0,
            cache_size_before=0,
            cache_size_after=0,
            operation_time=0.0,
            message=f"Error clearing cache: {str(e)}",
        )


@app.tool()
async def extract_structured_data(
    request: ExtractStructuredDataRequest,
) -> StructuredDataResponse:
    """
    Extract structured data from a webpage using advanced techniques.

    Args:
        url (str): 目标网页URL，必须包含协议前缀（http://或https://），从中提取结构化数据
        data_type (str, optional): 数据类型过滤，默认值："all"
            - "all": 提取所有结构化数据
            - "contact": 仅提取联系信息（邮箱、电话）
            - "social": 仅提取社交媒体链接
            - "content": 仅提取文章内容
            - "products": 仅提取产品信息
            - "addresses": 仅提取地址信息

    Automatically detects and extracts:
    - Contact information (emails, phone numbers)
    - Social media links
    - Addresses
    - Prices and product information
    - Article content

    Returns:
        Dict containing success status and structured data organized by type.
        Supports filtering for specific data categories as needed.
    """
    try:
        logger.info(f"Extracting structured data from: {request.url}")

        # Apply rate limiting
        await rate_limiter.wait()

        # Validate URL
        if not URLValidator.is_valid_url(request.url):
            return StructuredDataResponse(
                success=False,
                url=request.url,
                data_type=request.data_type,
                extracted_data={},
                data_count=0,
                error="Invalid URL format",
            )

        normalized_url = URLValidator.normalize_url(request.url)

        # Scrape page content
        scrape_result = await web_scraper.scrape_url(
            url=normalized_url, method="simple"
        )

        if "error" in scrape_result:
            return StructuredDataResponse(
                success=False,
                url=normalized_url,
                data_type=request.data_type,
                extracted_data={},
                data_count=0,
                error=scrape_result["error"],
            )

        content = scrape_result.get("content", {})
        text_content = content.get("text", "")
        links = content.get("links", [])

        extracted_data = {}

        # Extract contact information
        if request.data_type in ["all", "contact"]:
            extracted_data["contact"] = {
                "emails": TextCleaner.extract_emails(text_content),
                "phone_numbers": TextCleaner.extract_phone_numbers(text_content),
            }

        # Extract social media links
        if request.data_type in ["all", "social"]:
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
        if request.data_type in ["all", "content"]:
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
            data_type=request.data_type,
            extracted_data=extracted_data,
            data_count=sum(
                len(v) if isinstance(v, (list, dict)) else 1
                for v in extracted_data.values()
            ),
        )

    except Exception as e:
        logger.error(f"Error extracting structured data from {request.url}: {str(e)}")
        return StructuredDataResponse(
            success=False,
            url=request.url,
            data_type=request.data_type,
            extracted_data={},
            data_count=0,
            error=str(e),
        )


@app.tool()
@timing_decorator
async def convert_webpage_to_markdown(
    request: ConvertToMarkdownRequest,
) -> MarkdownResponse:
    """
    Scrape a webpage and convert it to Markdown format.

    Args:
        url (str): 目标网页URL，必须包含协议前缀（http://或https://），将抓取并转换为Markdown格式
        method (str, optional): 抓取方法选择，默认值："auto"
            - "auto": 自动选择最佳方法
            - "simple": 快速HTTP请求（不支持JavaScript）
            - "scrapy": Scrapy框架（适合大规模抓取）
            - "selenium": 浏览器渲染（支持JavaScript和动态内容）
        extract_main_content (bool, optional): 是否仅提取主要内容区域，默认值：True
            设为True时排除导航、广告、侧边栏等
        include_metadata (bool, optional): 是否在结果中包含页面元数据，默认值：True
            包含标题、描述、字数统计等信息
        custom_options (Dict[str, Any], optional): 自定义Markdown转换选项，用于控制转换行为。
            示例：{"strip": ["a", "img"], "convert": ["div"]}
        wait_for_element (str, optional): CSS选择器，等待特定元素加载（仅Selenium方法有效）。
            示例：".content", "#main-article"
        formatting_options (Dict[str, bool], optional): 高级格式化选项，控制输出格式。
            选项：format_tables, detect_code_language, apply_typography等
        embed_images (bool, optional): 是否嵌入图片作为数据URI，默认值：False
        embed_options (Dict[str, Any], optional): 图片嵌入选项配置。
            示例：{"max_bytes_per_image": 100000, "allowed_types": ["png", "jpg"]}

    This tool combines web scraping with Markdown conversion to provide clean,
    readable text format suitable for documentation, analysis, or storage.

    Features:
    - Automatic main content extraction (removes nav, ads, etc.)
    - Customizable Markdown formatting options
    - Metadata extraction (title, description, word count, etc.)
    - Support for all scraping methods
    - Advanced formatting and image embedding capabilities

    Returns:
        Dict containing success status, Markdown content, conversion metadata,
        and optional image embedding statistics.
    """

    start_time = time.time()
    try:
        # Validate inputs
        parsed = urlparse(request.url)
        if not parsed.scheme or not parsed.netloc:
            return MarkdownResponse(
                success=False,
                url=request.url,
                method=request.method,
                error="Invalid URL format",
                conversion_time=0,
            )

        if request.method not in ["auto", "simple", "scrapy", "selenium"]:
            return MarkdownResponse(
                success=False,
                url=request.url,
                method=request.method,
                error="Method must be one of: auto, simple, scrapy, selenium",
                conversion_time=0,
            )

        logger.info(
            f"Converting webpage to Markdown: {request.url} with method: {request.method}"
        )

        # Apply rate limiting
        await rate_limiter.wait()

        # Scrape the webpage first
        scrape_result = await web_scraper.scrape_url(
            url=request.url,
            method=request.method,
            extract_config=None,  # We'll handle HTML extraction in markdown converter
            wait_for_element=request.wait_for_element,
        )

        if "error" in scrape_result:
            return MarkdownResponse(
                success=False,
                url=request.url,
                method=request.method,
                error=scrape_result["error"],
                conversion_time=time.time() - start_time,
            )

        # Convert to Markdown
        conversion_result = markdown_converter.convert_webpage_to_markdown(
            scrape_result=scrape_result,
            extract_main_content=request.extract_main_content,
            include_metadata=request.include_metadata,
            custom_options=request.custom_options,
            embed_images=request.embed_images,
            embed_options=request.embed_options,
        )

        duration_ms = int((time.time() - start_time) * 1000)

        if conversion_result.get("success"):
            metrics_collector.record_request(
                request.url, True, duration_ms, f"markdown_{request.method}"
            )

            return MarkdownResponse(
                success=True,
                url=request.url,
                method=f"markdown_{request.method}",
                markdown_content=conversion_result.get(
                    "markdown_content", conversion_result.get("markdown", "")
                ),
                metadata=conversion_result.get("metadata", {}),
                word_count=conversion_result.get("word_count", 0),
                images_embedded=conversion_result.get("images_embedded", 0),
                conversion_time=duration_ms / 1000.0,
            )
        else:
            error_response = ErrorHandler.handle_scraping_error(
                Exception(conversion_result.get("error", "Markdown conversion failed")),
                request.url,
                f"markdown_{request.method}",
            )
            metrics_collector.record_request(
                request.url,
                False,
                duration_ms,
                f"markdown_{request.method}",
                error_response["error"]["category"],
            )
            return MarkdownResponse(
                success=False,
                url=request.url,
                method=f"markdown_{request.method}",
                error=error_response["error"]["message"],
                conversion_time=duration_ms,
            )

    except Exception as e:
        duration_ms = (
            int((time.time() - start_time) * 1000) if "start_time" in locals() else 0
        )
        error_response = ErrorHandler.handle_scraping_error(
            e, request.url, f"markdown_{request.method}"
        )
        metrics_collector.record_request(
            request.url,
            False,
            duration_ms,
            f"markdown_{request.method}",
            error_response["error"]["category"],
        )
        return MarkdownResponse(
            success=False,
            url=request.url,
            method=f"markdown_{request.method}",
            error=error_response["error"]["message"],
            conversion_time=duration_ms,
        )


@app.tool()
@timing_decorator
async def batch_convert_webpages_to_markdown(
    request: BatchConvertToMarkdownRequest,
) -> BatchMarkdownResponse:
    """
    Scrape multiple webpages and convert them to Markdown format.

    Args:
    - urls (List[str]): URL列表，每个URL必须包含协议前缀，将批量转换为Markdown格式
    - method (str, optional): 批量抓取方法，默认值："auto"，应用于所有URL
        - "auto": 自动选择最佳方法
        - "simple": 快速HTTP请求（适合静态内容）
        - "scrapy": Scrapy框架（适合大规模抓取）
        - "selenium": 浏览器渲染（支持JavaScript）
    - extract_main_content (bool, optional): 统一的主要内容提取设置，默认值：True
        应用于所有页面，排除导航和广告
    - include_metadata (bool, optional): 统一的元数据包含设置，默认值：True
        为每个页面包含标题、描述等元数据
    - custom_options (Dict[str, Any], optional): 统一的自定义转换选项，应用于所有页面。
        示例：{"strip": ["nav", "footer"], "convert": ["article"]}
    - formatting_options (Dict[str, bool], optional): 统一的高级格式化选项。
        选项：format_tables, detect_code_language, apply_typography等
    - embed_images (bool, optional): 是否在所有页面中嵌入图片，默认值：False
    - embed_options (Dict[str, Any], optional): 统一的图片嵌入配置。
        示例：{"max_bytes_per_image": 100000}

    This tool provides batch processing for converting multiple webpages to Markdown.
    It processes all URLs concurrently for better performance.

    Features:
    - Concurrent processing of multiple URLs
    - Consistent formatting across all converted pages
    - Detailed summary statistics
    - Error handling for individual failures
    - Same conversion options as single page tool

    Returns:
        Dict containing success status, batch conversion results, summary statistics,
        and individual page conversion details with error handling.
    """
    try:
        # Validate inputs
        if not request.urls:
            return BatchMarkdownResponse(
                success=False,
                total_urls=0,
                successful_count=0,
                failed_count=0,
                results=[],
                total_conversion_time=0,
            )

        for url in request.urls:
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                return BatchMarkdownResponse(
                    success=False,
                    total_urls=0,
                    successful_count=0,
                    failed_count=0,
                    results=[],
                    total_conversion_time=0,
                )

        if request.method not in ["auto", "simple", "scrapy", "selenium"]:
            return BatchMarkdownResponse(
                success=False,
                total_urls=0,
                successful_count=0,
                failed_count=0,
                results=[],
                total_conversion_time=0,
            )

        start_time = time.time()
        logger.info(
            f"Batch converting {len(request.urls)} webpages to Markdown with method: {request.method}"
        )

        # Scrape all URLs first
        scrape_results = await web_scraper.scrape_multiple_urls(
            urls=request.urls, method=request.method, extract_config=None
        )

        # Convert all results to Markdown
        conversion_result = markdown_converter.batch_convert_to_markdown(
            scrape_results=scrape_results,
            extract_main_content=request.extract_main_content,
            include_metadata=request.include_metadata,
            custom_options=request.custom_options,
            embed_images=request.embed_images,
            embed_options=request.embed_options,
        )

        duration_ms = int((time.time() - start_time) * 1000)

        # Record metrics for each URL
        for i, url in enumerate(request.urls):
            result = (
                conversion_result["results"][i]
                if i < len(conversion_result["results"])
                else {"success": False}
            )
            success = result.get("success", False)
            metrics_collector.record_request(
                url,
                success,
                duration_ms // len(request.urls),
                f"batch_markdown_{request.method}",
            )

        # Convert the conversion results to MarkdownResponse objects
        markdown_responses = []
        for i, result in enumerate(conversion_result.get("results", [])):
            url = request.urls[i] if i < len(request.urls) else ""
            markdown_responses.append(
                MarkdownResponse(
                    success=result.get("success", False),
                    url=url,
                    method=f"markdown_{request.method}",
                    markdown_content=result.get("markdown_content", ""),
                    metadata=result.get("metadata", {}),
                    word_count=result.get("word_count", 0),
                    images_embedded=result.get("images_embedded", 0),
                    conversion_time=result.get("conversion_time", 0),
                    error=result.get("error"),
                )
            )

        successful_count = sum(1 for r in markdown_responses if r.success)
        failed_count = len(markdown_responses) - successful_count
        total_word_count = sum(r.word_count for r in markdown_responses)

        if conversion_result.get("success"):
            return BatchMarkdownResponse(
                success=True,
                total_urls=len(request.urls),
                successful_count=successful_count,
                failed_count=failed_count,
                results=markdown_responses,
                total_word_count=total_word_count,
                total_conversion_time=duration_ms / 1000.0,
            )
        else:
            return BatchMarkdownResponse(
                success=False,
                total_urls=len(request.urls),
                successful_count=successful_count,
                failed_count=failed_count,
                results=markdown_responses,
                total_word_count=total_word_count,
                total_conversion_time=duration_ms / 1000.0,
            )

    except Exception as e:
        duration_ms = (
            int((time.time() - start_time) * 1000) if "start_time" in locals() else 0
        )
        logger.error(f"Error in batch Markdown conversion: {str(e)}")
        return BatchMarkdownResponse(
            success=False,
            total_urls=len(request.urls) if hasattr(request, "urls") else 0,
            successful_count=0,
            failed_count=len(request.urls) if hasattr(request, "urls") else 0,
            results=[],
            total_word_count=0,
            total_conversion_time=duration_ms / 1000.0,
        )


@app.tool()
@timing_decorator
async def convert_pdf_to_markdown(request: PDFToMarkdownRequest) -> PDFResponse:
    """
    Convert a PDF document to Markdown format.

    Args:
        pdf_source (str): PDF来源，可以是URL或本地文件路径。
            URL示例："https://example.com/document.pdf"
            本地路径示例："/path/to/document.pdf"
        method (str, optional): PDF处理引擎选择，默认值："auto"
            - "auto": 自动选择最佳引擎（PyMuPDF → PyPDF2）
            - "pymupdf": 使用PyMuPDF(fitz)引擎，功能强大，支持复杂排版
            - "pypdf": 使用PyPDF2引擎，兼容性好，适合简单文档
        include_metadata (bool, optional): 是否在结果中包含PDF元数据，默认值：True
            包含标题、作者、创建日期等信息
        page_range (List[int], optional): 页面范围[开始页, 结束页]，用于部分提取。
            示例：[1, 10] 提取第1-10页，页码从0开始计数
        output_format (str, optional): 输出格式选择，默认值："markdown"
            - "markdown": Markdown格式输出，适合文档处理
            - "text": 纯文本格式输出，适合简单文本提取

    This tool can process PDF files from URLs or local file paths:
    - auto: Automatically choose the best extraction method
    - pymupdf: Use PyMuPDF (fitz) library for extraction
    - pypdf: Use pypdf library for extraction

    Features:
    - Support for PDF URLs and local file paths
    - Partial page extraction with page range
    - Metadata extraction (title, author, etc.)
    - Text cleaning and Markdown formatting
    - Multiple extraction methods for reliability

    Returns:
        Dict containing success status, extracted content, metadata, processing method used,
        and page/word count statistics.
    """
    try:
        # Validate inputs
        if request.method not in ["auto", "pymupdf", "pypdf"]:
            return PDFResponse(
                success=False,
                pdf_source=request.pdf_source,
                method=request.method,
                output_format=request.output_format,
                error="Method must be one of: auto, pymupdf, pypdf",
                conversion_time=0,
            )

        if request.output_format not in ["markdown", "text"]:
            return PDFResponse(
                success=False,
                pdf_source=request.pdf_source,
                method=request.method,
                output_format=request.output_format,
                error="Output format must be one of: markdown, text",
                conversion_time=0,
            )

        # Convert page_range list to tuple if provided
        page_range_tuple = None
        if request.page_range:
            if len(request.page_range) != 2:
                return PDFResponse(
                    success=False,
                    pdf_source=request.pdf_source,
                    method=request.method,
                    output_format=request.output_format,
                    error="Page range must contain exactly 2 elements: [start, end]",
                    conversion_time=0,
                )
            if request.page_range[0] < 0 or request.page_range[1] < 0:
                return PDFResponse(
                    success=False,
                    pdf_source=request.pdf_source,
                    method=request.method,
                    output_format=request.output_format,
                    error="Page numbers must be non-negative",
                    conversion_time=0,
                )
            if request.page_range[0] >= request.page_range[1]:
                return PDFResponse(
                    success=False,
                    pdf_source=request.pdf_source,
                    method=request.method,
                    output_format=request.output_format,
                    error="Start page must be less than end page",
                    conversion_time=0,
                )
            page_range_tuple = tuple(request.page_range)

        start_time = time.time()
        logger.info(
            f"Converting PDF to {request.output_format}: {request.pdf_source} with method: {request.method}"
        )

        # Apply rate limiting
        await rate_limiter.wait()

        # Process PDF
        pdf_processor = _get_pdf_processor()
        result = await pdf_processor.process_pdf(
            pdf_source=request.pdf_source,
            method=request.method,
            include_metadata=request.include_metadata,
            page_range=page_range_tuple,
            output_format=request.output_format,
        )

        duration_ms = int((time.time() - start_time) * 1000)

        if result.get("success"):
            metrics_collector.record_request(
                request.pdf_source, True, duration_ms, f"pdf_{request.method}"
            )

            return PDFResponse(
                success=True,
                pdf_source=request.pdf_source,
                method=request.method,
                output_format=request.output_format,
                content=result.get("content", result.get("markdown", "")),
                metadata=result.get("metadata", {}),
                page_count=result.get("page_count", result.get("pages", 0)),
                word_count=result.get("word_count", 0),
                conversion_time=duration_ms / 1000.0,
            )
        else:
            error_response = ErrorHandler.handle_scraping_error(
                Exception(result.get("error", "PDF conversion failed")),
                request.pdf_source,
                f"pdf_{request.method}",
            )
            metrics_collector.record_request(
                request.pdf_source,
                False,
                duration_ms,
                f"pdf_{request.method}",
                error_response["error"]["category"],
            )
            return PDFResponse(
                success=False,
                pdf_source=request.pdf_source,
                method=request.method,
                output_format=request.output_format,
                error=error_response["error"]["message"],
                conversion_time=duration_ms / 1000.0,
            )

    except Exception as e:
        duration_ms = (
            int((time.time() - start_time) * 1000) if "start_time" in locals() else 0
        )
        error_response = ErrorHandler.handle_scraping_error(
            e, request.pdf_source, f"pdf_{request.method}"
        )
        metrics_collector.record_request(
            request.pdf_source,
            False,
            duration_ms,
            f"pdf_{request.method}",
            error_response["error"]["category"],
        )
        return PDFResponse(
            success=False,
            pdf_source=request.pdf_source,
            method=request.method,
            output_format=request.output_format,
            error=error_response["error"]["message"],
            conversion_time=duration_ms / 1000.0,
        )


@app.tool()
@timing_decorator
async def batch_convert_pdfs_to_markdown(
    request: BatchPDFToMarkdownRequest,
) -> BatchPDFResponse:
    """
    Convert multiple PDF documents to Markdown format concurrently.

    Args:
        pdf_sources (List[str]): PDF来源列表，可混合URL和本地文件路径。
            示例：[
                "https://example.com/doc1.pdf",
                "/path/to/doc2.pdf",
                "https://example.com/doc3.pdf"
            ]
        method (str, optional): 批量处理的统一引擎选择，默认值："auto"
            - "auto": 自动选择最佳引擎，应用于所有PDF
            - "pymupdf": 使用PyMuPDF引擎处理所有PDF
            - "pypdf": 使用PyPDF2引擎处理所有PDF
        include_metadata (bool, optional): 统一的元数据包含设置，默认值：True
            为所有PDF包含标题、作者等元数据
        page_range (List[int], optional): 统一的页面范围设置，应用于所有PDF。
            示例：[0, 5] 为所有PDF提取前5页
        output_format (str, optional): 统一的输出格式设置，默认值："markdown"
            - "markdown": 所有PDF输出为Markdown格式
            - "text": 所有PDF输出为纯文本格式

    This tool provides batch processing for converting multiple PDFs to Markdown.
    It processes all PDFs concurrently for better performance.

    Features:
    - Concurrent processing of multiple PDFs
    - Support for both URLs and local file paths
    - Consistent extraction settings across all PDFs
    - Detailed summary statistics
    - Error handling for individual failures
    - Same conversion options as single PDF tool

    Returns:
        Dict containing success status, batch conversion results, comprehensive statistics
        (total PDFs, success/failure counts, total pages, total words), and individual PDF results.
    """
    try:
        # Validate inputs
        if not request.pdf_sources:
            return BatchPDFResponse(
                success=False,
                total_pdfs=0,
                successful_count=0,
                failed_count=0,
                results=[],
                total_conversion_time=0,
            )

        if request.method not in ["auto", "pymupdf", "pypdf"]:
            return BatchPDFResponse(
                success=False,
                total_pdfs=len(request.pdf_sources),
                successful_count=0,
                failed_count=len(request.pdf_sources),
                results=[],
                total_conversion_time=0,
            )

        if request.output_format not in ["markdown", "text"]:
            return BatchPDFResponse(
                success=False,
                total_pdfs=len(request.pdf_sources),
                successful_count=0,
                failed_count=len(request.pdf_sources),
                results=[],
                total_conversion_time=0,
            )

        # Convert page_range list to tuple if provided
        page_range_tuple = None
        if request.page_range:
            if len(request.page_range) != 2:
                return BatchPDFResponse(
                    success=False,
                    total_pdfs=len(request.pdf_sources),
                    successful_count=0,
                    failed_count=len(request.pdf_sources),
                    results=[],
                    total_conversion_time=0,
                )
            if request.page_range[0] < 0 or request.page_range[1] < 0:
                return BatchPDFResponse(
                    success=False,
                    total_pdfs=len(request.pdf_sources),
                    successful_count=0,
                    failed_count=len(request.pdf_sources),
                    results=[],
                    total_conversion_time=0,
                )
            if request.page_range[0] >= request.page_range[1]:
                return BatchPDFResponse(
                    success=False,
                    total_pdfs=len(request.pdf_sources),
                    successful_count=0,
                    failed_count=len(request.pdf_sources),
                    results=[],
                    total_conversion_time=0,
                )
            page_range_tuple = tuple(request.page_range)

        start_time = time.time()
        logger.info(
            f"Batch converting {len(request.pdf_sources)} PDFs to {request.output_format} with method: {request.method}"
        )

        # Process all PDFs
        pdf_processor = _get_pdf_processor()
        result = await pdf_processor.batch_process_pdfs(
            pdf_sources=request.pdf_sources,
            method=request.method,
            include_metadata=request.include_metadata,
            page_range=page_range_tuple,
            output_format=request.output_format,
        )

        duration_ms = int((time.time() - start_time) * 1000)

        # Record metrics for each PDF
        for i, pdf_source in enumerate(request.pdf_sources):
            pdf_result = (
                result["results"][i]
                if i < len(result["results"])
                else {"success": False}
            )
            success = pdf_result.get("success", False)
            metrics_collector.record_request(
                pdf_source,
                success,
                duration_ms // len(request.pdf_sources),
                f"batch_pdf_{request.method}",
            )

        # Convert results to PDFResponse objects
        pdf_responses = []
        for i, result_item in enumerate(result.get("results", [])):
            pdf_source = request.pdf_sources[i] if i < len(request.pdf_sources) else ""
            pdf_responses.append(
                PDFResponse(
                    success=result_item.get("success", False),
                    pdf_source=pdf_source,
                    method=request.method,
                    output_format=request.output_format,
                    content=result_item.get("content", ""),
                    metadata=result_item.get("metadata", {}),
                    page_count=result_item.get("page_count", 0),
                    word_count=result_item.get("word_count", 0),
                    conversion_time=result_item.get("conversion_time", 0),
                    error=result_item.get("error"),
                )
            )

        successful_count = sum(1 for r in pdf_responses if r.success)
        failed_count = len(pdf_responses) - successful_count
        total_pages = sum(r.page_count for r in pdf_responses)
        total_word_count = sum(r.word_count for r in pdf_responses)

        if result.get("success"):
            return BatchPDFResponse(
                success=True,
                total_pdfs=len(request.pdf_sources),
                successful_count=successful_count,
                failed_count=failed_count,
                results=pdf_responses,
                total_pages=total_pages,
                total_word_count=total_word_count,
                total_conversion_time=duration_ms / 1000.0,
            )
        else:
            return BatchPDFResponse(
                success=False,
                total_pdfs=len(request.pdf_sources),
                successful_count=successful_count,
                failed_count=failed_count,
                results=pdf_responses,
                total_pages=total_pages,
                total_word_count=total_word_count,
                total_conversion_time=duration_ms / 1000.0,
            )

    except Exception as e:
        duration_ms = (
            int((time.time() - start_time) * 1000) if "start_time" in locals() else 0
        )
        logger.error(f"Error in batch PDF conversion: {str(e)}")
        return BatchPDFResponse(
            success=False,
            total_pdfs=len(request.pdf_sources)
            if hasattr(request, "pdf_sources")
            else 0,
            successful_count=0,
            failed_count=len(request.pdf_sources)
            if hasattr(request, "pdf_sources")
            else 0,
            results=[],
            total_pages=0,
            total_word_count=0,
            total_conversion_time=duration_ms / 1000.0,
        )


def main() -> None:
    """Run the MCP server."""
    print(f"Starting {settings.server_name} v{settings.server_version}")
    print(
        f"JavaScript support: {'Enabled' if settings.enable_javascript else 'Disabled'}"
    )
    print(
        f"Random User-Agent: {'Enabled' if settings.use_random_user_agent else 'Disabled'}"
    )
    print(f"Proxy: {'Enabled' if settings.use_proxy else 'Disabled'}")

    app.run()


if __name__ == "__main__":
    main()
