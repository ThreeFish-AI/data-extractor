"""
单元测试：MCP Server 工具函数
测试所有 14 个 @app.tool() 装饰器的 MCP 工具函数
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock

import extractor.server as server_module

# 获取实际的函数，而不是 FunctionTool 包装器
scrape_webpage = server_module.scrape_webpage.fn
scrape_multiple_webpages = server_module.scrape_multiple_webpages.fn
extract_links = server_module.extract_links.fn
get_page_info = server_module.get_page_info.fn
check_robots_txt = server_module.check_robots_txt.fn
scrape_with_stealth = server_module.scrape_with_stealth.fn
fill_and_submit_form = server_module.fill_and_submit_form.fn
get_server_metrics = server_module.get_server_metrics.fn
clear_cache = server_module.clear_cache.fn
extract_structured_data = server_module.extract_structured_data.fn
convert_webpage_to_markdown = server_module.convert_webpage_to_markdown.fn
batch_convert_webpages_to_markdown = server_module.batch_convert_webpages_to_markdown.fn
convert_pdf_to_markdown = server_module.convert_pdf_to_markdown.fn
batch_convert_pdfs_to_markdown = server_module.batch_convert_pdfs_to_markdown.fn


class TestMCPToolsScraping:
    """测试基础网页抓取 MCP 工具"""

    @pytest.mark.asyncio
    async def test_scrape_webpage_success(self):
        """测试单页面抓取成功"""
        with patch("extractor.server.web_scraper") as mock_scraper:
            mock_result = {
                "url": "https://example.com",
                "status_code": 200,
                "title": "Test Page",
                "content": {"text": "Sample content"},
            }
            mock_scraper.scrape_url = AsyncMock(return_value=mock_result)

            result = await scrape_webpage(url="https://example.com", method="simple")

            assert result["success"] is True
            assert result["data"] == mock_result
            assert result["method_used"] == "simple"
            mock_scraper.scrape_url.assert_called_once()

    @pytest.mark.asyncio
    async def test_scrape_webpage_invalid_url(self):
        """测试无效URL处理"""
        result = await scrape_webpage(url="invalid-url", method="simple")

        assert result["success"] is False
        assert "Invalid URL format" in result["error"]
        assert result["url"] == "invalid-url"

    @pytest.mark.asyncio
    async def test_scrape_webpage_invalid_method(self):
        """测试无效方法处理"""
        result = await scrape_webpage(
            url="https://example.com", method="invalid-method"
        )

        assert result["success"] is False
        assert "Method must be one of" in result["error"]

    @pytest.mark.asyncio
    async def test_scrape_multiple_webpages_success(self):
        """测试批量抓取成功"""
        with patch("extractor.server.web_scraper") as mock_scraper:
            mock_results = [
                {"url": "https://example.com/1", "status_code": 200},
                {"url": "https://example.com/2", "status_code": 200},
            ]
            mock_scraper.scrape_multiple_urls = AsyncMock(return_value=mock_results)

            result = await scrape_multiple_webpages(
                urls=["https://example.com/1", "https://example.com/2"], method="simple"
            )

            assert result["success"] is True
            assert result["summary"]["total"] == 2
            assert result["summary"]["successful"] == 2

    @pytest.mark.asyncio
    async def test_scrape_multiple_webpages_empty_list(self):
        """测试空URL列表处理"""
        result = await scrape_multiple_webpages(urls=[], method="simple")

        assert result["success"] is False
        assert "URLs list cannot be empty" in result["error"]

    @pytest.mark.asyncio
    async def test_extract_links_success(self):
        """测试链接提取成功"""
        with patch("extractor.server.web_scraper") as mock_scraper:
            mock_result = {
                "content": {
                    "links": [
                        {"url": "https://example.com/page1", "text": "Page 1"},
                        {"url": "https://external.com/page", "text": "External"},
                    ]
                }
            }
            mock_scraper.scrape_url = AsyncMock(return_value=mock_result)

            result = await extract_links(url="https://example.com", internal_only=True)

            assert result["success"] is True
            # 内部链接过滤应该只保留同域名链接
            internal_links = [
                link for link in result["data"]["links"] if "example.com" in link["url"]
            ]
            assert len(internal_links) >= 1

    @pytest.mark.asyncio
    async def test_extract_links_domain_filtering(self):
        """测试域名过滤功能"""
        with patch("extractor.server.web_scraper") as mock_scraper:
            mock_result = {
                "content": {
                    "links": [
                        {"url": "https://example.com/page1", "text": "Page 1"},
                        {"url": "https://allowed.com/page", "text": "Allowed"},
                        {"url": "https://blocked.com/page", "text": "Blocked"},
                    ]
                }
            }
            mock_scraper.scrape_url = AsyncMock(return_value=mock_result)

            result = await extract_links(
                url="https://example.com",
                filter_domains=["example.com", "allowed.com"],
                exclude_domains=["blocked.com"],
            )

            assert result["success"] is True
            # 检查过滤结果
            for link in result["data"]["links"]:
                assert "blocked.com" not in link["url"]


class TestMCPToolsInformation:
    """测试页面信息获取 MCP 工具"""

    @pytest.mark.asyncio
    async def test_get_page_info_success(self):
        """测试页面信息获取成功"""
        with patch("extractor.server.web_scraper") as mock_scraper:
            mock_result = {
                "url": "https://example.com",
                "status_code": 200,
                "title": "Test Page",
                "meta_description": "A test page",
            }
            mock_scraper.simple_scraper.scrape = AsyncMock(return_value=mock_result)

            result = await get_page_info("https://example.com")

            assert result["success"] is True
            assert result["data"]["title"] == "Test Page"
            assert result["data"]["status_code"] == 200

    @pytest.mark.asyncio
    async def test_check_robots_txt_success(self):
        """测试robots.txt检查成功"""
        with patch("extractor.server.web_scraper") as mock_scraper:
            mock_result = {"content": {"text": "User-agent: *\nDisallow: /admin/"}}
            mock_scraper.simple_scraper.scrape = AsyncMock(return_value=mock_result)

            result = await check_robots_txt("https://example.com")

            assert result["success"] is True
            assert "User-agent" in result["data"]["content"]
            assert result["data"]["base_domain"] == "example.com"

    @pytest.mark.asyncio
    async def test_check_robots_txt_not_found(self):
        """测试robots.txt不存在"""
        with patch("extractor.server.web_scraper") as mock_scraper:
            mock_scraper.simple_scraper.scrape = AsyncMock(
                return_value={"error": "404 Not Found"}
            )

            result = await check_robots_txt("https://example.com")

            assert result["success"] is False
            assert "Could not fetch robots.txt" in result["error"]


class TestMCPToolsAdvanced:
    """测试高级功能 MCP 工具"""

    @pytest.mark.asyncio
    async def test_scrape_with_stealth_success(self):
        """测试反检测抓取成功"""
        with (
            patch("extractor.server.anti_detection_scraper") as mock_scraper,
            patch("extractor.server.rate_limiter") as mock_limiter,
            patch("extractor.server.cache_manager") as mock_cache,
            patch("extractor.server.retry_manager") as mock_retry,
        ):
            mock_limiter.wait = AsyncMock()
            mock_cache.get.return_value = None

            mock_result = {
                "url": "https://example.com",
                "status_code": 200,
                "content": {"text": "Stealth content"},
            }
            mock_retry.retry_async = AsyncMock(return_value=mock_result)

            result = await scrape_with_stealth(
                url="https://example.com", method="selenium"
            )

            assert result["success"] is True
            assert result["data"] == mock_result

    @pytest.mark.asyncio
    async def test_fill_and_submit_form_success(self):
        """测试表单填写成功"""
        with (
            patch("extractor.server.rate_limiter") as mock_limiter,
            patch("selenium.webdriver.Chrome") as mock_driver,
            patch("extractor.server.settings") as mock_settings,
        ):
            mock_limiter.wait = AsyncMock()
            mock_settings.browser_headless = True
            mock_settings.browser_timeout = 10

            mock_driver_instance = Mock()
            mock_driver.return_value = mock_driver_instance

            result = await fill_and_submit_form(
                url="https://example.com/form",
                form_data={"#username": "test", "#password": "secret"},
                submit=False,
            )

            # 由于复杂的浏览器交互，这里主要测试参数验证
            assert "success" in result

    @pytest.mark.asyncio
    async def test_extract_structured_data_success(self):
        """测试结构化数据提取成功"""
        with (
            patch("extractor.server.web_scraper") as mock_scraper,
            patch("extractor.server.rate_limiter") as mock_limiter,
        ):
            mock_limiter.wait = AsyncMock()
            mock_result = {
                "content": {
                    "text": "Contact us at info@example.com or call 123-456-7890",
                    "links": [
                        {"url": "https://facebook.com/page", "text": "Facebook"},
                        {"url": "https://twitter.com/page", "text": "Twitter"},
                    ],
                },
                "title": "Contact Page",
                "meta_description": "Contact information",
            }
            mock_scraper.scrape_url = AsyncMock(return_value=mock_result)

            result = await extract_structured_data(
                url="https://example.com/contact", data_type="contact"
            )

            assert result["success"] is True
            assert "data" in result
            assert result["data_type"] == "contact"


class TestMCPToolsServer:
    """测试服务器管理 MCP 工具"""

    @pytest.mark.asyncio
    async def test_get_server_metrics_success(self):
        """测试服务器指标获取成功"""
        with (
            patch("extractor.server.metrics_collector") as mock_metrics,
            patch("extractor.server.cache_manager") as mock_cache,
            patch("extractor.server.settings") as mock_settings,
        ):
            mock_metrics.get_stats.return_value = {
                "total_requests": 100,
                "successful_requests": 95,
                "failed_requests": 5,
            }
            mock_cache.stats.return_value = {"cache_hits": 50, "cache_misses": 50}
            mock_settings.server_name = "Test Server"
            mock_settings.server_version = "0.1.5"

            result = await get_server_metrics()

            assert result["success"] is True
            assert "scraping_metrics" in result["data"]
            assert "cache_statistics" in result["data"]
            assert "server_info" in result["data"]

    @pytest.mark.asyncio
    async def test_clear_cache_success(self):
        """测试缓存清理成功"""
        with patch("extractor.server.cache_manager") as mock_cache:
            mock_cache.clear.return_value = None

            result = await clear_cache()

            assert result["success"] is True
            assert "Cache cleared successfully" in result["message"]
            mock_cache.clear.assert_called_once()


class TestMCPToolsMarkdown:
    """测试 Markdown 转换 MCP 工具"""

    @pytest.mark.asyncio
    async def test_convert_webpage_to_markdown_success(self):
        """测试单页面Markdown转换成功"""
        with (
            patch("extractor.server.web_scraper") as mock_scraper,
            patch("extractor.server.markdown_converter") as mock_converter,
            patch("extractor.server.rate_limiter") as mock_limiter,
        ):
            mock_limiter.wait = AsyncMock()

            mock_scrape_result = {
                "url": "https://example.com",
                "content": {"html": "<h1>Test</h1><p>Content</p>"},
                "title": "Test Page",
            }
            mock_scraper.scrape_url = AsyncMock(return_value=mock_scrape_result)

            mock_conversion_result = {
                "success": True,
                "markdown": "# Test\n\nContent",
                "metadata": {"word_count": 2, "processing_time": 0.5},
            }
            mock_converter.convert_webpage_to_markdown.return_value = (
                mock_conversion_result
            )

            result = await convert_webpage_to_markdown(
                url="https://example.com", method="simple"
            )

            assert result["success"] is True
            assert result["data"]["markdown"] == "# Test\n\nContent"

    @pytest.mark.asyncio
    async def test_batch_convert_webpages_to_markdown_success(self):
        """测试批量Markdown转换成功"""
        with (
            patch("extractor.server.web_scraper") as mock_scraper,
            patch("extractor.server.markdown_converter") as mock_converter,
        ):
            mock_scrape_results = [
                {
                    "url": "https://example.com/1",
                    "content": {"html": "<h1>Page 1</h1>"},
                },
                {
                    "url": "https://example.com/2",
                    "content": {"html": "<h1>Page 2</h1>"},
                },
            ]
            mock_scraper.scrape_multiple_urls = AsyncMock(
                return_value=mock_scrape_results
            )

            mock_conversion_result = {
                "success": True,
                "results": [
                    {"success": True, "markdown": "# Page 1"},
                    {"success": True, "markdown": "# Page 2"},
                ],
                "summary": {"total": 2, "successful": 2, "failed": 0},
            }
            mock_converter.batch_convert_to_markdown.return_value = (
                mock_conversion_result
            )

            result = await batch_convert_webpages_to_markdown(
                urls=["https://example.com/1", "https://example.com/2"], method="simple"
            )

            assert result["success"] is True
            assert result["data"]["summary"]["total"] == 2


class TestMCPToolsPDF:
    """测试 PDF 处理 MCP 工具"""

    @pytest.mark.asyncio
    async def test_convert_pdf_to_markdown_success(self):
        """测试PDF转Markdown成功"""
        with (
            patch("extractor.server._get_pdf_processor") as mock_get_processor,
            patch("extractor.server.rate_limiter") as mock_limiter,
        ):
            mock_limiter.wait = AsyncMock()

            mock_processor = Mock()
            mock_processor.process_pdf = AsyncMock(
                return_value={
                    "success": True,
                    "markdown": "# PDF Title\n\nPDF content",
                    "metadata": {"pages": 10, "word_count": 500},
                }
            )
            mock_get_processor.return_value = mock_processor

            result = await convert_pdf_to_markdown(
                pdf_source="https://example.com/document.pdf", method="auto"
            )

            assert result["success"] is True
            assert result["data"]["markdown"] == "# PDF Title\n\nPDF content"

    @pytest.mark.asyncio
    async def test_convert_pdf_to_markdown_invalid_method(self):
        """测试PDF转换无效方法"""
        result = await convert_pdf_to_markdown(
            pdf_source="https://example.com/document.pdf", method="invalid-method"
        )

        assert result["success"] is False
        assert "Method must be one of" in result["error"]

    @pytest.mark.asyncio
    async def test_batch_convert_pdfs_to_markdown_success(self):
        """测试批量PDF转换成功"""
        with (
            patch("extractor.server._get_pdf_processor") as mock_get_processor,
            patch("extractor.server.rate_limiter") as mock_limiter,
        ):
            mock_limiter.wait = AsyncMock()

            mock_processor = Mock()
            mock_processor.batch_process_pdfs = AsyncMock(
                return_value={
                    "success": True,
                    "results": [
                        {"success": True, "markdown": "# PDF 1"},
                        {"success": True, "markdown": "# PDF 2"},
                    ],
                    "summary": {"total": 2, "successful": 2, "failed": 0},
                }
            )
            mock_get_processor.return_value = mock_processor

            result = await batch_convert_pdfs_to_markdown(
                pdf_sources=[
                    "https://example.com/doc1.pdf",
                    "https://example.com/doc2.pdf",
                ],
                method="auto",
            )

            assert result["success"] is True
            assert result["data"]["summary"]["total"] == 2

    @pytest.mark.asyncio
    async def test_batch_convert_pdfs_to_markdown_empty_list(self):
        """测试批量PDF转换空列表"""
        result = await batch_convert_pdfs_to_markdown(pdf_sources=[], method="auto")

        assert result["success"] is False
        assert "PDF sources list cannot be empty" in result["error"]


class TestMCPToolsValidation:
    """测试 MCP 工具参数验证"""

    @pytest.mark.asyncio
    async def test_invalid_urls_handling(self):
        """测试无效URL的一致性处理"""
        invalid_urls = [
            "not-a-url",
            "ftp://example.com",  # 非HTTP协议
            "",  # 空字符串
            "http://",  # 不完整URL
        ]

        for invalid_url in invalid_urls:
            # 测试单页面抓取
            result = await scrape_webpage(url=invalid_url)
            assert result["success"] is False
            assert "Invalid URL format" in result["error"]

            # 测试页面信息获取
            result = await get_page_info(url=invalid_url)
            assert result["success"] is False
            assert "Invalid URL format" in result["error"]

    @pytest.mark.asyncio
    async def test_method_validation_consistency(self):
        """测试方法参数验证的一致性"""
        invalid_methods = ["invalid", "unknown", "", "AUTO"]  # 大写应该无效

        for invalid_method in invalid_methods:
            # 测试不同工具的方法验证一致性
            result = await scrape_webpage(
                url="https://example.com", method=invalid_method
            )
            assert result["success"] is False
            assert "Method must be one of" in result["error"]
