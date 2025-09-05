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
from .pdf_processor import PDFProcessor
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
pdf_processor = PDFProcessor()


class ScrapeRequest(BaseModel):
    """Request model for scraping operations."""

    url: str = Field(..., description="URL to scrape")
    method: str = Field(
        default="auto", description="Scraping method: auto, simple, scrapy, selenium"
    )
    extract_config: Optional[Dict[str, Any]] = Field(
        default=None, description="Configuration for data extraction"
    )
    wait_for_element: Optional[str] = Field(
        default=None, description="CSS selector to wait for (Selenium only)"
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

    urls: List[str] = Field(..., description="List of URLs to scrape")
    method: str = Field(
        default="auto", description="Scraping method: auto, simple, scrapy, selenium"
    )
    extract_config: Optional[Dict[str, Any]] = Field(
        default=None, description="Configuration for data extraction"
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

    url: str = Field(..., description="URL to extract links from")
    filter_domains: Optional[List[str]] = Field(
        default=None, description="Only include links from these domains"
    )
    exclude_domains: Optional[List[str]] = Field(
        default=None, description="Exclude links from these domains"
    )
    internal_only: bool = Field(
        default=False, description="Only extract internal links"
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
        if not parsed.scheme or not parsed.netloc:
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
        url: URL to extract links from
        filter_domains: Only include links from these domains (optional)
        exclude_domains: Exclude links from these domains (optional)
        internal_only: Only extract internal links (default: False)

    This tool is specialized for link extraction and can filter links by domain,
    extract only internal links, or exclude specific domains.
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

    This is a lightweight tool for quickly checking page accessibility and
    getting basic metadata without full content extraction.
    """
    try:
        logger.info(f"Getting page info for: {url}")

        # Validate URL
        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
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

    This tool helps ensure ethical scraping by checking the robots.txt file
    of a website to see what crawling rules are in place.
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

    url: str = Field(..., description="URL to scrape using stealth techniques")
    method: str = Field(
        default="selenium", description="Stealth method: selenium or playwright"
    )
    extract_config: Optional[Dict[str, Any]] = Field(
        default=None, description="Configuration for data extraction"
    )
    wait_for_element: Optional[str] = Field(
        default=None, description="CSS selector to wait for"
    )
    scroll_page: bool = Field(
        default=False, description="Whether to scroll page to load dynamic content"
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

    url: str = Field(..., description="URL of the page containing the form")
    form_data: Dict[str, Any] = Field(
        ..., description="Form field data (selector: value pairs)"
    )
    submit: bool = Field(default=False, description="Whether to submit the form")
    submit_button_selector: Optional[str] = Field(
        default=None, description="Selector for submit button"
    )
    method: str = Field(
        default="selenium", description="Method to use: selenium or playwright"
    )
    wait_for_element: Optional[str] = Field(
        default=None, description="Element to wait for before filling form"
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

    url: str = Field(..., description="URL to scrape and convert to Markdown")
    method: str = Field(
        default="auto", description="Scraping method: auto, simple, scrapy, selenium"
    )
    extract_main_content: bool = Field(
        default=True, description="Extract main content area only"
    )
    include_metadata: bool = Field(
        default=True, description="Include page metadata in result"
    )
    custom_options: Optional[Dict[str, Any]] = Field(
        default=None, description="Custom markdownify options"
    )
    wait_for_element: Optional[str] = Field(
        default=None, description="CSS selector to wait for (Selenium only)"
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

    urls: List[str] = Field(..., description="List of URLs to scrape and convert")
    method: str = Field(
        default="auto", description="Scraping method: auto, simple, scrapy, selenium"
    )
    extract_main_content: bool = Field(
        default=True, description="Extract main content area only"
    )
    include_metadata: bool = Field(
        default=True, description="Include page metadata in results"
    )
    custom_options: Optional[Dict[str, Any]] = Field(
        default=None, description="Custom markdownify options"
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

    pdf_source: str = Field(..., description="PDF URL or local file path")
    method: str = Field(
        default="auto", description="Extraction method: auto, pymupdf, pypdf2"
    )
    include_metadata: bool = Field(
        default=True, description="Include PDF metadata in result"
    )
    page_range: Optional[List[int]] = Field(
        default=None, description="Page range [start, end] for partial extraction"
    )
    output_format: str = Field(
        default="markdown", description="Output format: markdown, text"
    )

    @field_validator("method")
    def validate_method(cls, v: str) -> str:
        """Validate extraction method."""
        if v not in ["auto", "pymupdf", "pypdf2"]:
            raise ValueError("Method must be one of: auto, pymupdf, pypdf2")
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

    pdf_sources: List[str] = Field(..., description="List of PDF URLs or local file paths")
    method: str = Field(
        default="auto", description="Extraction method: auto, pymupdf, pypdf2"
    )
    include_metadata: bool = Field(
        default=True, description="Include PDF metadata in results"
    )
    page_range: Optional[List[int]] = Field(
        default=None, description="Page range [start, end] for all PDFs"
    )
    output_format: str = Field(
        default="markdown", description="Output format: markdown, text"
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
        if v not in ["auto", "pymupdf", "pypdf2"]:
            raise ValueError("Method must be one of: auto, pymupdf, pypdf2")
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
        url: URL to scrape using stealth techniques
        method: Stealth method: selenium or playwright (default: selenium)
        extract_config: Configuration for data extraction (optional)
        wait_for_element: CSS selector to wait for (optional)
        scroll_page: Whether to scroll page to load dynamic content (default: False)

    This tool uses sophisticated anti-detection methods including:
    - Undetected browser automation
    - Randomized behavior patterns
    - Human-like interactions
    - Advanced evasion techniques

    Use this for websites with strong anti-bot protection.
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
        url: URL of the page containing the form
        form_data: Form field data (selector: value pairs)
        submit: Whether to submit the form (default: False)
        submit_button_selector: Selector for submit button (optional)
        method: Method to use: selenium or playwright (default: selenium)
        wait_for_element: Element to wait for before filling form (optional)

    This tool can handle various form elements including:
    - Text inputs
    - Checkboxes and radio buttons
    - Dropdown selects
    - File uploads
    - Form submission

    Useful for interacting with search forms, contact forms, login forms, etc.
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

    Returns information about:
    - Request counts and success rates
    - Performance metrics
    - Method usage statistics
    - Error categories
    - Cache statistics
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

    This removes all cached scraping results, forcing fresh requests
    for all subsequent scraping operations.
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

    Automatically detects and extracts:
    - Contact information (emails, phone numbers)
    - Social media links
    - Addresses
    - Prices and product information
    - Article content

    data_type can be: all, contact, social, content, products, or addresses
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
) -> Dict[str, Any]:
    """
    Scrape a webpage and convert it to Markdown format.

    Args:
        url: URL to scrape and convert to Markdown
        method: Scraping method: auto, simple, scrapy, selenium (default: auto)
        extract_main_content: Extract main content area only (default: True)
        include_metadata: Include page metadata in result (default: True)
        custom_options: Custom markdownify options (optional)
        wait_for_element: CSS selector to wait for - Selenium only (optional)
        formatting_options: Advanced formatting options like table alignment, code detection, etc.

    This tool combines web scraping with Markdown conversion to provide clean,
    readable text format suitable for documentation, analysis, or storage.

    Features:
    - Automatic main content extraction (removes nav, ads, etc.)
    - Customizable Markdown formatting options
    - Metadata extraction (title, description, word count, etc.)
    - Support for all scraping methods
    """
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

        start_time = time.time()
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
) -> Dict[str, Any]:
    """
    Scrape multiple webpages and convert them to Markdown format.

    Args:
        urls: List of URLs to scrape and convert
        method: Scraping method: auto, simple, scrapy, selenium (default: auto)
        extract_main_content: Extract main content area only (default: True)
        include_metadata: Include page metadata in results (default: True)
        custom_options: Custom markdownify options (optional)
        formatting_options: Advanced formatting options like table alignment, code detection, etc.

    This tool provides batch processing for converting multiple webpages to Markdown.
    It processes all URLs concurrently for better performance.

    Features:
    - Concurrent processing of multiple URLs
    - Consistent formatting across all converted pages
    - Detailed summary statistics
    - Error handling for individual failures
    - Same conversion options as single page tool
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
    output_format: str = "markdown"
) -> Dict[str, Any]:
    """
    Convert a PDF document to Markdown format.

    Args:
        pdf_source: PDF URL or local file path
        method: Extraction method: auto, pymupdf, pypdf2 (default: auto)
        include_metadata: Include PDF metadata in result (default: True)
        page_range: Page range [start, end] for partial extraction (optional)
        output_format: Output format: markdown, text (default: markdown)

    This tool can process PDF files from URLs or local file paths:
    - auto: Automatically choose the best extraction method
    - pymupdf: Use PyMuPDF (fitz) library for extraction
    - pypdf2: Use PyPDF2 library for extraction

    Features:
    - Support for PDF URLs and local file paths
    - Partial page extraction with page range
    - Metadata extraction (title, author, etc.)
    - Text cleaning and Markdown formatting
    - Multiple extraction methods for reliability
    """
    try:
        # Validate inputs
        if method not in ["auto", "pymupdf", "pypdf2"]:
            return {
                "success": False,
                "error": "Method must be one of: auto, pymupdf, pypdf2",
                "pdf_source": pdf_source
            }

        if output_format not in ["markdown", "text"]:
            return {
                "success": False,
                "error": "Output format must be one of: markdown, text",
                "pdf_source": pdf_source
            }

        # Convert page_range list to tuple if provided
        page_range_tuple = None
        if page_range:
            if len(page_range) != 2:
                return {
                    "success": False,
                    "error": "Page range must contain exactly 2 elements: [start, end]",
                    "pdf_source": pdf_source
                }
            if page_range[0] < 0 or page_range[1] < 0:
                return {
                    "success": False,
                    "error": "Page numbers must be non-negative",
                    "pdf_source": pdf_source
                }
            if page_range[0] >= page_range[1]:
                return {
                    "success": False,
                    "error": "Start page must be less than end page",
                    "pdf_source": pdf_source
                }
            page_range_tuple = tuple(page_range)

        start_time = time.time()
        logger.info(f"Converting PDF to {output_format}: {pdf_source} with method: {method}")

        # Apply rate limiting
        await rate_limiter.wait()

        # Process PDF
        result = await pdf_processor.process_pdf(
            pdf_source=pdf_source,
            method=method,
            include_metadata=include_metadata,
            page_range=page_range_tuple,
            output_format=output_format
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
                "duration_ms": duration_ms
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
        error_response = ErrorHandler.handle_scraping_error(e, pdf_source, f"pdf_{method}")
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
    output_format: str = "markdown"
) -> Dict[str, Any]:
    """
    Convert multiple PDF documents to Markdown format concurrently.

    Args:
        pdf_sources: List of PDF URLs or local file paths
        method: Extraction method: auto, pymupdf, pypdf2 (default: auto)
        include_metadata: Include PDF metadata in results (default: True)
        page_range: Page range [start, end] for all PDFs (optional)
        output_format: Output format: markdown, text (default: markdown)

    This tool provides batch processing for converting multiple PDFs to Markdown.
    It processes all PDFs concurrently for better performance.

    Features:
    - Concurrent processing of multiple PDFs
    - Support for both URLs and local file paths
    - Consistent extraction settings across all PDFs
    - Detailed summary statistics
    - Error handling for individual failures
    - Same conversion options as single PDF tool
    """
    try:
        # Validate inputs
        if not pdf_sources:
            return {"success": False, "error": "PDF sources list cannot be empty"}

        if method not in ["auto", "pymupdf", "pypdf2"]:
            return {
                "success": False,
                "error": "Method must be one of: auto, pymupdf, pypdf2"
            }

        if output_format not in ["markdown", "text"]:
            return {
                "success": False,
                "error": "Output format must be one of: markdown, text"
            }

        # Convert page_range list to tuple if provided
        page_range_tuple = None
        if page_range:
            if len(page_range) != 2:
                return {
                    "success": False,
                    "error": "Page range must contain exactly 2 elements: [start, end]"
                }
            if page_range[0] < 0 or page_range[1] < 0:
                return {
                    "success": False,
                    "error": "Page numbers must be non-negative"
                }
            if page_range[0] >= page_range[1]:
                return {
                    "success": False,
                    "error": "Start page must be less than end page"
                }
            page_range_tuple = tuple(page_range)

        start_time = time.time()
        logger.info(
            f"Batch converting {len(pdf_sources)} PDFs to {output_format} with method: {method}"
        )

        # Process all PDFs
        result = await pdf_processor.batch_process_pdfs(
            pdf_sources=pdf_sources,
            method=method,
            include_metadata=include_metadata,
            page_range=page_range_tuple,
            output_format=output_format
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
                pdf_source, success, duration_ms // len(pdf_sources), f"batch_pdf_{method}"
            )

        if result.get("success"):
            return {
                "success": True,
                "data": result,
                "method_used": f"batch_pdf_{method}",
                "duration_ms": duration_ms
            }
        else:
            return {
                "success": False,
                "error": result.get("error", "Batch PDF conversion failed"),
                "data": result.get("results", []),
                "method_used": f"batch_pdf_{method}",
                "duration_ms": duration_ms
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
            "duration_ms": duration_ms
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
