"""Markdown conversion MCP tools."""

import logging
import time
from typing import Annotated, Any, Dict, List, Optional
from urllib.parse import urlparse

from pydantic import Field

from ..metrics import metrics_collector
from ..rate_limiter import rate_limiter
from ..schemas import BatchMarkdownResponse, MarkdownResponse
from ..timing import timing_decorator
from ._registry import app, elapsed_ms, markdown_converter, record_error, web_scraper

logger = logging.getLogger(__name__)


@app.tool()
@timing_decorator
async def convert_webpage_to_markdown(
    url: Annotated[
        str,
        Field(
            ...,
            description="目标网页URL，必须包含协议前缀（http:// 或 https://），将抓取并转换为 Markdown 格式",
        ),
    ],
    method: Annotated[
        str,
        Field(
            default="auto",
            description="""抓取方法选择，可选值：
                "auto"（自动选择最佳方法）、
                "simple"（快速 HTTP 请求，不支持 JavaScript）、
                "scrapy"（Scrapy 框架，适合大规模抓取）、
                "selenium"（浏览器渲染，支持 JavaScript）""",
        ),
    ],
    extract_main_content: Annotated[
        bool,
        Field(
            default=True,
            description="是否仅提取主要内容区域，设为 True 时排除导航、广告、侧边栏等非主要内容",
        ),
    ],
    include_metadata: Annotated[
        bool,
        Field(
            default=True, description="是否在结果中包含页面元数据（标题、描述、字数等）"
        ),
    ],
    custom_options: Annotated[
        Optional[Dict[str, Any]],
        Field(
            default=None,
            description="自定义 Markdown 转换选项，支持 markitdown 库的各种参数配置",
        ),
    ],
    wait_for_element: Annotated[
        Optional[str],
        Field(
            default=None,
            description="""Selenium模式下等待加载的元素CSS选择器。
                示例：".content"、"#main-article\"""",
        ),
    ],
    formatting_options: Annotated[
        Optional[Dict[str, bool]],
        Field(
            default=None,
            description="""高级格式化选项，如表格对齐、代码检测等。
                示例：{"table_alignment": True, "code_detection": True}""",
        ),
    ],
    embed_images: Annotated[
        bool,
        Field(default=False, description="是否嵌入图片作为数据 URI，默认值：False"),
    ],
    embed_options: Annotated[
        Optional[Dict[str, Any]],
        Field(
            default=None,
            description="""图片嵌入选项配置。
                示例：{"max_bytes_per_image": 100000, "allowed_types": ["png", "jpg"]}""",
        ),
    ],
) -> MarkdownResponse:
    """
    Scrape a webpage and convert it to Markdown format.

    This tool combines web scraping with Markdown conversion to provide clean,
    readable text format suitable for documentation, analysis, or storage.

    Features:
    - Automatic main content extraction (removes nav, ads, etc.)
    - Customizable Markdown formatting options
    - Metadata extraction (title, description, word count, etc.)
    - Support for all scraping methods
    - Advanced formatting and image embedding capabilities

    Returns:
        MarkdownResponse object containing success status, Markdown content, conversion metadata,
        and optional image embedding statistics.
    """

    start_time = time.time()
    try:
        # Validate inputs
        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            return MarkdownResponse(
                success=False, url=url, method=method,
                error="Invalid URL format", conversion_time=0,
            )

        if method not in ["auto", "simple", "scrapy", "selenium"]:
            return MarkdownResponse(
                success=False, url=url, method=method,
                error="Method must be one of: auto, simple, scrapy, selenium",
                conversion_time=0,
            )

        logger.info(f"Converting webpage to Markdown: {url} with method: {method}")

        # Apply rate limiting
        await rate_limiter.wait()

        # Scrape the webpage first
        scrape_result = await web_scraper.scrape_url(
            url=url, method=method, extract_config=None,
            wait_for_element=wait_for_element,
        )

        if "error" in scrape_result:
            return MarkdownResponse(
                success=False, url=url, method=method,
                error=scrape_result["error"],
                conversion_time=time.time() - start_time,
            )

        # Convert to Markdown
        conversion_result = markdown_converter.convert_webpage_to_markdown(
            scrape_result=scrape_result,
            extract_main_content=extract_main_content,
            include_metadata=include_metadata,
            custom_options=custom_options,
            embed_images=embed_images,
            embed_options=embed_options,
        )

        duration_ms = elapsed_ms(start_time)

        if conversion_result.get("success"):
            metrics_collector.record_request(
                url, True, duration_ms, f"markdown_{method}"
            )

            return MarkdownResponse(
                success=True, url=url, method=f"markdown_{method}",
                markdown_content=conversion_result.get(
                    "markdown_content", conversion_result.get("markdown", "")
                ),
                metadata=conversion_result.get("metadata", {}),
                word_count=conversion_result.get("word_count", 0),
                images_embedded=conversion_result.get("images_embedded", 0),
                conversion_time=duration_ms / 1000.0,
            )
        else:
            error_msg = record_error(
                Exception(conversion_result.get("error", "Markdown conversion failed")),
                url, f"markdown_{method}", duration_ms,
            )
            return MarkdownResponse(
                success=False, url=url, method=f"markdown_{method}",
                error=error_msg, conversion_time=duration_ms,
            )

    except Exception as e:
        duration_ms = elapsed_ms(start_time) if "start_time" in dir() else 0
        error_msg = record_error(e, url, f"markdown_{method}", duration_ms)
        return MarkdownResponse(
            success=False, url=url, method=f"markdown_{method}",
            error=error_msg, conversion_time=duration_ms,
        )


@app.tool()
@timing_decorator
async def batch_convert_webpages_to_markdown(
    urls: Annotated[
        List[str],
        Field(
            ...,
            description="要批量转换为 Markdown 的 URL 列表，每个 URL 必须包含协议前缀，支持并发处理以提高效率",
        ),
    ],
    method: Annotated[
        str,
        Field(
            default="auto",
            description="""统一的抓取方法：
                "auto"（智能选择最佳方法）、
                "simple"（轻量级 HTTP 请求）、
                "scrapy"（适合大批量抓取）、
                "selenium"（支持 JavaScript 动态页面）""",
        ),
    ],
    extract_main_content: Annotated[
        bool,
        Field(
            default=True,
            description="是否统一提取主要内容区域，过滤掉导航、广告、页脚等非核心内容，获得更纯净的 Markdown 文档",
        ),
    ],
    include_metadata: Annotated[
        bool,
        Field(
            default=True,
            description="是否在每个转换结果中包含页面元数据，包含标题、URL、字数、处理时间等信息",
        ),
    ],
    custom_options: Annotated[
        Optional[Dict[str, Any]],
        Field(
            default=None,
            description="""统一的 markitdown 自定义选项，应用于所有 URL。支持 HTML 标签处理、格式化选项等。
                示例：{"strip": ["nav", "footer"], "convert": ["article"]}""",
        ),
    ],
    embed_images: Annotated[
        bool,
        Field(
            default=False,
            description="是否在所有页面中嵌入图片作为数据 URI，默认值：False",
        ),
    ],
    embed_options: Annotated[
        Optional[Dict[str, Any]],
        Field(
            default=None,
            description="""统一的图片嵌入选项配置，应用于所有 URL。
                示例：{"max_bytes_per_image": 100000}""",
        ),
    ],
) -> BatchMarkdownResponse:
    """
    Scrape multiple webpages and convert them to Markdown format.

    This tool provides batch processing for converting multiple webpages to Markdown.
    It processes all URLs concurrently for better performance.

    Features:
    - Concurrent processing of multiple URLs
    - Consistent formatting across all converted pages
    - Detailed summary statistics
    - Error handling for individual failures
    - Same conversion options as single page tool

    Returns:
        BatchMarkdownResponse object containing success status, batch conversion results, summary statistics,
        and individual page conversion details with error handling.
    """
    try:
        # Validate inputs
        if not urls:
            return BatchMarkdownResponse(
                success=False, total_urls=0, successful_count=0,
                failed_count=0, results=[], total_conversion_time=0,
            )

        for url in urls:
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                return BatchMarkdownResponse(
                    success=False, total_urls=0, successful_count=0,
                    failed_count=0, results=[], total_conversion_time=0,
                )

        if method not in ["auto", "simple", "scrapy", "selenium"]:
            return BatchMarkdownResponse(
                success=False, total_urls=0, successful_count=0,
                failed_count=0, results=[], total_conversion_time=0,
            )

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
            embed_images=embed_images,
            embed_options=embed_options,
        )

        duration_ms = elapsed_ms(start_time)

        # Record metrics for each URL
        for i, url in enumerate(urls):
            result = (
                conversion_result["results"][i]
                if i < len(conversion_result["results"])
                else {"success": False}
            )
            success = result.get("success", False)
            metrics_collector.record_request(
                url, success, duration_ms // len(urls), f"batch_markdown_{method}",
            )

        # Convert the conversion results to MarkdownResponse objects
        markdown_responses = []
        for i, result in enumerate(conversion_result.get("results", [])):
            url_item = urls[i] if i < len(urls) else ""
            markdown_responses.append(
                MarkdownResponse(
                    success=result.get("success", False),
                    url=url_item,
                    method=f"markdown_{method}",
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

        return BatchMarkdownResponse(
            success=conversion_result.get("success", False),
            total_urls=len(urls),
            successful_count=successful_count,
            failed_count=failed_count,
            results=markdown_responses,
            total_word_count=total_word_count,
            total_conversion_time=duration_ms / 1000.0,
        )

    except Exception as e:
        duration_ms = elapsed_ms(start_time) if "start_time" in dir() else 0
        logger.error(f"Error in batch Markdown conversion: {str(e)}")
        return BatchMarkdownResponse(
            success=False,
            total_urls=len(urls) if urls else 0,
            successful_count=0,
            failed_count=len(urls) if urls else 0,
            results=[],
            total_word_count=0,
            total_conversion_time=duration_ms / 1000.0,
        )
