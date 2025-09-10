"""FastMCP Server implementation for web scraping."""

import logging
import time
from typing import Dict, Any, List, Optional
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

    url: str = Field(
        ..., description="目标网页 URL，必须包含协议前缀（http://或https://）"
    )
    method: str = Field(
        default="auto",
        description="抓取方法选择：auto（自动选择最佳方法）、simple（快速HTTP请求，不支持JavaScript）、scrapy（Scrapy框架，适合大规模抓取）、selenium（浏览器渲染，支持JavaScript和动态内容）",
    )
    extract_config: Optional[Dict[str, Any]] = Field(
        default=None,
        description="数据提取配置字典，支持CSS选择器和属性提取。示例：{'title': 'h1', 'content': {'selector': '.content p', 'multiple': True, 'attr': 'text'}}",
    )
    wait_for_element: Optional[str] = Field(
        default=None,
        description="等待元素的 CSS 选择器（仅 Selenium 方法有效），确保页面完全加载后再提取内容。示例：'.content'、'#main-content'",
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


class MultipleScrapeRequest(BaseModel):
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


@app.tool()
async def scrape_webpage(
    url: str,
    method: str = "auto",
    extract_config: Optional[Dict[str, Any]] = None,
    wait_for_element: Optional[str] = None,
) -> Dict[str, Any]:
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
        # Validate inputs
        parsed = urlparse(url)
        if (
            not parsed.scheme
            or not parsed.netloc
            or parsed.scheme.lower() not in ["http", "https"]
        ):
            return {"success": False, "error": "Invalid URL format", "url": url}

        if method not in ["auto", "simple", "scrapy", "selenium"]:
            return {
                "success": False,
                "error": "Method must be one of: auto, simple, scrapy, selenium",
                "url": url,
            }

        logger.info(f"Scraping webpage: {url} with method: {method}")

        result = await web_scraper.scrape_url(
            url=url,
            method=method,
            extract_config=extract_config,
            wait_for_element=wait_for_element,
        )

        # Check if the scraper returned an error
        if "error" in result:
            return {"success": False, "error": result["error"], "url": url}

        return {"success": True, "data": result, "method_used": method}

    except Exception as e:
        logger.error(f"Error scraping webpage {url}: {str(e)}")
        return {"success": False, "error": str(e), "url": url}


@app.tool()
async def scrape_multiple_webpages(
    urls: List[str],
    method: str = "auto",
    extract_config: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
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
        # Validate inputs
        if not urls:
            return {"success": False, "error": "URLs list cannot be empty"}

        for url in urls:
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                return {"success": False, "error": f"Invalid URL format: {url}"}

        if method not in ["auto", "simple", "scrapy", "selenium"]:
            return {
                "success": False,
                "error": "Method must be one of: auto, simple, scrapy, selenium",
            }

        logger.info(f"Scraping {len(urls)} webpages with method: {method}")

        results = await web_scraper.scrape_multiple_urls(
            urls=urls, method=method, extract_config=extract_config
        )

        successful_results = [r for r in results if "error" not in r]
        failed_results = [r for r in results if "error" in r]

        return {
            "success": True,
            "data": results,
            "summary": {
                "total": len(urls),
                "successful": len(successful_results),
                "failed": len(failed_results),
            },
            "method_used": method,
        }

    except Exception as e:
        logger.error(f"Error scraping multiple webpages: {str(e)}")
        return {"success": False, "error": str(e), "urls": urls}


@app.tool()
async def extract_links(
    url: str,
    filter_domains: Optional[List[str]] = None,
    exclude_domains: Optional[List[str]] = None,
    internal_only: bool = False,
) -> Dict[str, Any]:
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
        # Validate URL
        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            return {"success": False, "error": "Invalid URL format", "url": url}

        logger.info(f"Extracting links from: {url}")

        # Scrape the page to get links
        scrape_result = await web_scraper.scrape_url(
            url=url,
            method="simple",  # Use simple method for link extraction
        )

        if "error" in scrape_result:
            return {"success": False, "error": scrape_result["error"], "url": url}

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
                {
                    "url": link_url,
                    "text": link.get("text", "").strip(),
                    "domain": link_domain,
                    "is_internal": link_domain == base_domain,
                }
            )

        return {
            "success": True,
            "data": {
                "base_url": url,
                "base_domain": base_domain,
                "links": filtered_links,
                "total_found": len(all_links),
                "total_filtered": len(filtered_links),
            },
        }

    except Exception as e:
        logger.error(f"Error extracting links from {url}: {str(e)}")
        return {"success": False, "error": str(e), "url": url}


@app.tool()
async def get_page_info(url: str) -> Dict[str, Any]:
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
        logger.info(f"Getting page info for: {url}")

        # Validate URL
        parsed = urlparse(url)
        if (
            not parsed.scheme
            or not parsed.netloc
            or parsed.scheme.lower() not in ["http", "https"]
        ):
            return {"success": False, "error": "Invalid URL format", "url": url}

        # Use simple scraper for quick info
        result = await web_scraper.simple_scraper.scrape(url, extract_config={})

        if "error" in result:
            return {"success": False, "error": result["error"], "url": url}

        return {
            "success": True,
            "data": {
                "url": result.get("url", url),
                "status_code": result.get("status_code"),
                "title": result.get("title"),
                "meta_description": result.get("meta_description"),
                "domain": urlparse(result.get("url", url)).netloc,
            },
        }

    except Exception as e:
        logger.error(f"Error getting page info for {url}: {str(e)}")
        return {"success": False, "error": str(e), "url": url}


@app.tool()
async def check_robots_txt(url: str) -> Dict[str, Any]:
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
        logger.info(f"Checking robots.txt for: {url}")

        # Parse URL to get base domain
        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            return {"success": False, "error": "Invalid URL format", "url": url}

        robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"

        # Scrape robots.txt
        result = await web_scraper.simple_scraper.scrape(robots_url, extract_config={})

        if "error" in result:
            return {
                "success": False,
                "error": f"Could not fetch robots.txt: {result['error']}",
                "url": robots_url,
            }

        robots_content = result.get("content", {}).get("text", "")

        return {
            "success": True,
            "data": {
                "robots_url": robots_url,
                "content": robots_content,
                "base_domain": parsed.netloc,
                "has_content": bool(robots_content.strip()),
            },
        }

    except Exception as e:
        logger.error(f"Error checking robots.txt for {url}: {str(e)}")
        return {"success": False, "error": str(e), "url": url}


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
async def scrape_with_stealth(
    url: str,
    method: str = "selenium",
    extract_config: Optional[Dict[str, Any]] = None,
    wait_for_element: Optional[str] = None,
    scroll_page: bool = False,
) -> Dict[str, Any]:
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
        if not URLValidator.is_valid_url(url):
            return {"success": False, "error": "Invalid URL format", "url": url}

        if method not in ["selenium", "playwright"]:
            return {
                "success": False,
                "error": "Method must be one of: selenium, playwright",
                "url": url,
            }

        start_time = time.time()
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
                normalized_url, f"stealth_{method}", result, cache_key_data
            )

            metrics_collector.record_request(
                normalized_url, True, duration_ms, f"stealth_{method}"
            )

            return {
                "success": True,
                "data": result,
                "method_used": f"stealth_{method}",
                "duration_ms": duration_ms,
                "from_cache": False,
            }
        else:
            error_response = ErrorHandler.handle_scraping_error(
                Exception(result.get("error", "Unknown error")),
                normalized_url,
                f"stealth_{method}",
            )
            metrics_collector.record_request(
                normalized_url,
                False,
                duration_ms,
                f"stealth_{method}",
                error_response["error"]["category"],
            )
            return error_response

    except Exception as e:
        duration_ms = (
            int((time.time() - start_time) * 1000) if "start_time" in locals() else 0
        )
        error_response = ErrorHandler.handle_scraping_error(e, url, f"stealth_{method}")
        metrics_collector.record_request(
            url,
            False,
            duration_ms,
            f"stealth_{method}",
            error_response["error"]["category"],
        )
        return error_response


@app.tool()
@timing_decorator
async def fill_and_submit_form(
    url: str,
    form_data: Dict[str, Any],
    submit: bool = False,
    submit_button_selector: Optional[str] = None,
    method: str = "selenium",
    wait_for_element: Optional[str] = None,
) -> Dict[str, Any]:
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
        if not URLValidator.is_valid_url(url):
            return {"success": False, "error": "Invalid URL format", "url": url}

        if method not in ["selenium", "playwright"]:
            return {
                "success": False,
                "error": "Method must be one of: selenium, playwright",
                "url": url,
            }

        start_time = time.time()
        logger.info(f"Form interaction for: {url}")

        # Apply rate limiting
        await rate_limiter.wait()

        # Setup browser based on method
        if method == "selenium":
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options as ChromeOptions

            options = ChromeOptions()
            if settings.browser_headless:
                options.add_argument("--headless")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")

            driver = webdriver.Chrome(options=options)
            try:
                driver.get(url)

                # Wait for element if specified
                if wait_for_element:
                    from selenium.webdriver.common.by import By
                    from selenium.webdriver.support.ui import WebDriverWait
                    from selenium.webdriver.support import expected_conditions as EC

                    WebDriverWait(driver, settings.browser_timeout).until(
                        EC.presence_of_element_located(
                            (By.CSS_SELECTOR, wait_for_element)
                        )
                    )

                # Fill and submit form
                form_handler = FormHandler(driver)
                result = await form_handler.fill_form(
                    form_data=form_data,
                    submit=submit,
                    submit_button_selector=submit_button_selector,
                )

                # Get final page info
                final_url = driver.current_url
                final_title = driver.title

            finally:
                driver.quit()

        elif method == "playwright":
            from playwright.async_api import async_playwright

            playwright = await async_playwright().start()
            try:
                browser = await playwright.chromium.launch(
                    headless=settings.browser_headless
                )
                context = await browser.new_context()
                page = await context.new_page()

                await page.goto(url, timeout=60000)

                # Wait for element if specified
                if wait_for_element:
                    await page.wait_for_selector(
                        wait_for_element, timeout=settings.browser_timeout * 1000
                    )

                # Fill and submit form
                form_handler = FormHandler(page)
                result = await form_handler.fill_form(
                    form_data=form_data,
                    submit=submit,
                    submit_button_selector=submit_button_selector,
                )

                # Get final page info
                final_url = page.url
                final_title = await page.title()

            finally:
                await browser.close()
                await playwright.stop()

        duration_ms = int((time.time() - start_time) * 1000)

        if result.get("success"):
            metrics_collector.record_request(url, True, duration_ms, f"form_{method}")

            return {
                "success": True,
                "data": {
                    "form_results": result,
                    "final_url": final_url,
                    "final_title": final_title,
                    "original_url": url,
                },
                "method_used": f"form_{method}",
                "duration_ms": duration_ms,
            }
        else:
            error_response = ErrorHandler.handle_scraping_error(
                Exception(result.get("error", "Form interaction failed")),
                url,
                f"form_{method}",
            )
            metrics_collector.record_request(
                url,
                False,
                duration_ms,
                f"form_{method}",
                error_response["error"]["category"],
            )
            return error_response

    except Exception as e:
        duration_ms = (
            int((time.time() - start_time) * 1000) if "start_time" in locals() else 0
        )
        error_response = ErrorHandler.handle_scraping_error(e, url, f"form_{method}")
        metrics_collector.record_request(
            url,
            False,
            duration_ms,
            f"form_{method}",
            error_response["error"]["category"],
        )
        return error_response


@app.tool()
async def get_server_metrics() -> Dict[str, Any]:
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

        return {
            "success": True,
            "data": {
                "scraping_metrics": metrics,
                "cache_statistics": cache_stats,
                "server_info": {
                    "name": settings.server_name,
                    "version": settings.server_version,
                    "javascript_support": settings.enable_javascript,
                    "proxy_enabled": settings.use_proxy,
                    "random_user_agent": settings.use_random_user_agent,
                },
                "timestamp": datetime.now().isoformat(),
            },
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.tool()
async def clear_cache() -> Dict[str, Any]:
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
        cache_manager.clear()
        return {"success": True, "message": "Cache cleared successfully"}
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.tool()
async def extract_structured_data(url: str, data_type: str = "all") -> Dict[str, Any]:
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
        logger.info(f"Extracting structured data from: {url}")

        # Apply rate limiting
        await rate_limiter.wait()

        # Validate URL
        if not URLValidator.is_valid_url(url):
            return {"success": False, "error": "Invalid URL format"}

        normalized_url = URLValidator.normalize_url(url)

        # Scrape page content
        scrape_result = await web_scraper.scrape_url(
            url=normalized_url, method="simple"
        )

        if "error" in scrape_result:
            return {
                "success": False,
                "error": scrape_result["error"],
                "url": normalized_url,
            }

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

        return {
            "success": True,
            "data": extracted_data,
            "url": normalized_url,
            "data_type": data_type,
        }

    except Exception as e:
        logger.error(f"Error extracting structured data from {url}: {str(e)}")
        return {"success": False, "error": str(e), "url": url}


@app.tool()
@timing_decorator
async def convert_webpage_to_markdown(
    url: str,
    method: str = "auto",
    extract_main_content: bool = True,
    include_metadata: bool = True,
    custom_options: Optional[Dict[str, Any]] = None,
    wait_for_element: Optional[str] = None,
    formatting_options: Optional[Dict[str, bool]] = None,
    embed_images: bool = False,
    embed_options: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
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
        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            return {"success": False, "error": "Invalid URL format", "url": url}

        if method not in ["auto", "simple", "scrapy", "selenium"]:
            return {
                "success": False,
                "error": "Method must be one of: auto, simple, scrapy, selenium",
                "url": url,
            }

        logger.info(f"Converting webpage to Markdown: {url} with method: {method}")

        # Apply rate limiting
        await rate_limiter.wait()

        # Scrape the webpage first
        scrape_result = await web_scraper.scrape_url(
            url=url,
            method=method,
            extract_config=None,  # We'll handle HTML extraction in markdown converter
            wait_for_element=wait_for_element,
        )

        if "error" in scrape_result:
            return {
                "success": False,
                "error": scrape_result["error"],
                "url": url,
                "method_used": method,
            }

        # Convert to Markdown
        conversion_result = markdown_converter.convert_webpage_to_markdown(
            scrape_result=scrape_result,
            extract_main_content=extract_main_content,
            include_metadata=include_metadata,
            custom_options=custom_options,
            formatting_options=formatting_options,
            embed_images=embed_images,
            embed_options=embed_options,
        )

        duration_ms = int((time.time() - start_time) * 1000)

        if conversion_result.get("success"):
            metrics_collector.record_request(
                url, True, duration_ms, f"markdown_{method}"
            )

            result = {
                "success": True,
                "data": conversion_result,
                "method_used": f"markdown_{method}",
                "duration_ms": duration_ms,
            }

            return result
        else:
            error_response = ErrorHandler.handle_scraping_error(
                Exception(conversion_result.get("error", "Markdown conversion failed")),
                url,
                f"markdown_{method}",
            )
            metrics_collector.record_request(
                url,
                False,
                duration_ms,
                f"markdown_{method}",
                error_response["error"]["category"],
            )
            return error_response

    except Exception as e:
        duration_ms = (
            int((time.time() - start_time) * 1000) if "start_time" in locals() else 0
        )
        error_response = ErrorHandler.handle_scraping_error(
            e, url, f"markdown_{method}"
        )
        metrics_collector.record_request(
            url,
            False,
            duration_ms,
            f"markdown_{method}",
            error_response["error"]["category"],
        )
        return error_response


@app.tool()
@timing_decorator
async def batch_convert_webpages_to_markdown(
    urls: List[str],
    method: str = "auto",
    extract_main_content: bool = True,
    include_metadata: bool = True,
    custom_options: Optional[Dict[str, Any]] = None,
    formatting_options: Optional[Dict[str, bool]] = None,
    embed_images: bool = False,
    embed_options: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Scrape multiple webpages and convert them to Markdown format.

    Args:
        urls (List[str]): URL列表，每个URL必须包含协议前缀，将批量转换为Markdown格式
        method (str, optional): 批量抓取方法，默认值："auto"，应用于所有URL
            - "auto": 自动选择最佳方法
            - "simple": 快速HTTP请求（适合静态内容）
            - "scrapy": Scrapy框架（适合大规模抓取）
            - "selenium": 浏览器渲染（支持JavaScript）
        extract_main_content (bool, optional): 统一的主要内容提取设置，默认值：True
            应用于所有页面，排除导航和广告
        include_metadata (bool, optional): 统一的元数据包含设置，默认值：True
            为每个页面包含标题、描述等元数据
        custom_options (Dict[str, Any], optional): 统一的自定义转换选项，应用于所有页面。
            示例：{"strip": ["nav", "footer"], "convert": ["article"]}
        formatting_options (Dict[str, bool], optional): 统一的高级格式化选项。
            选项：format_tables, detect_code_language, apply_typography等
        embed_images (bool, optional): 是否在所有页面中嵌入图片，默认值：False
        embed_options (Dict[str, Any], optional): 统一的图片嵌入配置。
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
        if not urls:
            return {"success": False, "error": "URLs list cannot be empty"}

        for url in urls:
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                return {"success": False, "error": f"Invalid URL format: {url}"}

        if method not in ["auto", "simple", "scrapy", "selenium"]:
            return {
                "success": False,
                "error": "Method must be one of: auto, simple, scrapy, selenium",
            }

        start_time = time.time()
        logger.info(
            f"Batch converting {len(urls)} webpages to Markdown with method: {method}"
        )

        # Scrape all URLs first
        scrape_results = await web_scraper.scrape_multiple_urls(
            urls=urls, method=method, extract_config=None
        )

        # Convert all results to Markdown
        conversion_result = markdown_converter.batch_convert_to_markdown(
            scrape_results=scrape_results,
            extract_main_content=extract_main_content,
            include_metadata=include_metadata,
            custom_options=custom_options,
            formatting_options=formatting_options,
            embed_images=embed_images,
            embed_options=embed_options,
        )

        duration_ms = int((time.time() - start_time) * 1000)

        # Record metrics for each URL
        for i, url in enumerate(urls):
            result = (
                conversion_result["results"][i]
                if i < len(conversion_result["results"])
                else {"success": False}
            )
            success = result.get("success", False)
            metrics_collector.record_request(
                url, success, duration_ms // len(urls), f"batch_markdown_{method}"
            )

        if conversion_result.get("success"):
            return {
                "success": True,
                "data": conversion_result,
                "method_used": f"batch_markdown_{method}",
                "duration_ms": duration_ms,
            }
        else:
            return {
                "success": False,
                "error": conversion_result.get("error", "Batch conversion failed"),
                "data": conversion_result.get("results", []),
                "method_used": f"batch_markdown_{method}",
                "duration_ms": duration_ms,
            }

    except Exception as e:
        duration_ms = (
            int((time.time() - start_time) * 1000) if "start_time" in locals() else 0
        )
        logger.error(f"Error in batch Markdown conversion: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "urls": urls,
            "method_used": f"batch_markdown_{method}",
            "duration_ms": duration_ms,
        }


@app.tool()
@timing_decorator
async def convert_pdf_to_markdown(
    pdf_source: str,
    method: str = "auto",
    include_metadata: bool = True,
    page_range: Optional[List[int]] = None,
    output_format: str = "markdown",
) -> Dict[str, Any]:
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
        if method not in ["auto", "pymupdf", "pypdf"]:
            return {
                "success": False,
                "error": "Method must be one of: auto, pymupdf, pypdf",
                "pdf_source": pdf_source,
            }

        if output_format not in ["markdown", "text"]:
            return {
                "success": False,
                "error": "Output format must be one of: markdown, text",
                "pdf_source": pdf_source,
            }

        # Convert page_range list to tuple if provided
        page_range_tuple = None
        if page_range:
            if len(page_range) != 2:
                return {
                    "success": False,
                    "error": "Page range must contain exactly 2 elements: [start, end]",
                    "pdf_source": pdf_source,
                }
            if page_range[0] < 0 or page_range[1] < 0:
                return {
                    "success": False,
                    "error": "Page numbers must be non-negative",
                    "pdf_source": pdf_source,
                }
            if page_range[0] >= page_range[1]:
                return {
                    "success": False,
                    "error": "Start page must be less than end page",
                    "pdf_source": pdf_source,
                }
            page_range_tuple = tuple(page_range)

        start_time = time.time()
        logger.info(
            f"Converting PDF to {output_format}: {pdf_source} with method: {method}"
        )

        # Apply rate limiting
        await rate_limiter.wait()

        # Process PDF
        pdf_processor = _get_pdf_processor()
        result = await pdf_processor.process_pdf(
            pdf_source=pdf_source,
            method=method,
            include_metadata=include_metadata,
            page_range=page_range_tuple,
            output_format=output_format,
        )

        duration_ms = int((time.time() - start_time) * 1000)

        if result.get("success"):
            metrics_collector.record_request(
                pdf_source, True, duration_ms, f"pdf_{method}"
            )

            return {
                "success": True,
                "data": result,
                "method_used": f"pdf_{method}",
                "duration_ms": duration_ms,
            }
        else:
            error_response = ErrorHandler.handle_scraping_error(
                Exception(result.get("error", "PDF conversion failed")),
                pdf_source,
                f"pdf_{method}",
            )
            metrics_collector.record_request(
                pdf_source,
                False,
                duration_ms,
                f"pdf_{method}",
                error_response["error"]["category"],
            )
            return error_response

    except Exception as e:
        duration_ms = (
            int((time.time() - start_time) * 1000) if "start_time" in locals() else 0
        )
        error_response = ErrorHandler.handle_scraping_error(
            e, pdf_source, f"pdf_{method}"
        )
        metrics_collector.record_request(
            pdf_source,
            False,
            duration_ms,
            f"pdf_{method}",
            error_response["error"]["category"],
        )
        return error_response


@app.tool()
@timing_decorator
async def batch_convert_pdfs_to_markdown(
    pdf_sources: List[str],
    method: str = "auto",
    include_metadata: bool = True,
    page_range: Optional[List[int]] = None,
    output_format: str = "markdown",
) -> Dict[str, Any]:
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
        if not pdf_sources:
            return {"success": False, "error": "PDF sources list cannot be empty"}

        if method not in ["auto", "pymupdf", "pypdf"]:
            return {
                "success": False,
                "error": "Method must be one of: auto, pymupdf, pypdf",
            }

        if output_format not in ["markdown", "text"]:
            return {
                "success": False,
                "error": "Output format must be one of: markdown, text",
            }

        # Convert page_range list to tuple if provided
        page_range_tuple = None
        if page_range:
            if len(page_range) != 2:
                return {
                    "success": False,
                    "error": "Page range must contain exactly 2 elements: [start, end]",
                }
            if page_range[0] < 0 or page_range[1] < 0:
                return {"success": False, "error": "Page numbers must be non-negative"}
            if page_range[0] >= page_range[1]:
                return {
                    "success": False,
                    "error": "Start page must be less than end page",
                }
            page_range_tuple = tuple(page_range)

        start_time = time.time()
        logger.info(
            f"Batch converting {len(pdf_sources)} PDFs to {output_format} with method: {method}"
        )

        # Process all PDFs
        pdf_processor = _get_pdf_processor()
        result = await pdf_processor.batch_process_pdfs(
            pdf_sources=pdf_sources,
            method=method,
            include_metadata=include_metadata,
            page_range=page_range_tuple,
            output_format=output_format,
        )

        duration_ms = int((time.time() - start_time) * 1000)

        # Record metrics for each PDF
        for i, pdf_source in enumerate(pdf_sources):
            pdf_result = (
                result["results"][i]
                if i < len(result["results"])
                else {"success": False}
            )
            success = pdf_result.get("success", False)
            metrics_collector.record_request(
                pdf_source,
                success,
                duration_ms // len(pdf_sources),
                f"batch_pdf_{method}",
            )

        if result.get("success"):
            return {
                "success": True,
                "data": result,
                "method_used": f"batch_pdf_{method}",
                "duration_ms": duration_ms,
            }
        else:
            return {
                "success": False,
                "error": result.get("error", "Batch PDF conversion failed"),
                "data": result.get("results", []),
                "method_used": f"batch_pdf_{method}",
                "duration_ms": duration_ms,
            }

    except Exception as e:
        duration_ms = (
            int((time.time() - start_time) * 1000) if "start_time" in locals() else 0
        )
        logger.error(f"Error in batch PDF conversion: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "pdf_sources": pdf_sources,
            "method_used": f"batch_pdf_{method}",
            "duration_ms": duration_ms,
        }


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
