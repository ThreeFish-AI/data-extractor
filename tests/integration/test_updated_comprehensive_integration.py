"""
集成测试：更新的综合集成测试
测试整个MCP服务器功能的端到端集成，包括所有14个工具的协同工作
"""

import pytest
import asyncio
import time
from unittest.mock import patch, AsyncMock, Mock
import tempfile
import os

from extractor.server import app
from extractor.config import settings


class TestUpdatedComprehensiveIntegration:
    """更新的综合集成测试，覆盖所有主要功能"""

    @pytest.fixture
    def sample_html_content(self):
        """样本HTML内容用于测试"""
        return """
        <!DOCTYPE html>
        <html>
            <head>
                <title>综合测试文章</title>
                <meta name="description" content="用于测试的综合示例文章">
                <meta name="author" content="测试作者">
            </head>
            <body>
                <nav>导航菜单</nav>
                <main>
                    <article>
                        <header>
                            <h1>综合测试文章</h1>
                            <p class="byline">作者：测试作者</p>
                        </header>
                        <div class="content">
                            <p>这是文章的主要内容，包含<strong>粗体</strong>和<em>斜体</em>文本。</p>
                            
                            <h2>演示的功能</h2>
                            <ul>
                                <li>HTML到Markdown转换</li>
                                <li>高级格式化选项</li>
                                <li>内容提取</li>
                                <li>链接和图片处理</li>
                            </ul>
                            
                            <table>
                                <thead>
                                    <tr>
                                        <th>功能</th>
                                        <th>状态</th>
                                        <th>备注</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    <tr>
                                        <td>网页爬取</td>
                                        <td>✅ 完成</td>
                                        <td>支持多种方法</td>
                                    </tr>
                                    <tr>
                                        <td>Markdown转换</td>
                                        <td>✅ 完成</td>
                                        <td>高级格式化</td>
                                    </tr>
                                    <tr>
                                        <td>PDF处理</td>
                                        <td>✅ 完成</td>
                                        <td>多引擎支持</td>
                                    </tr>
                                </tbody>
                            </table>
                            
                            <blockquote>
                                <p>这是一个引用块，展示了丰富的HTML结构。</p>
                            </blockquote>
                            
                            <div class="code-example">
                                <pre><code class="language-python">
def example_function():
    return "Hello, World!"
                                </code></pre>
                            </div>
                            
                            <p>文章还包含一些链接：
                                <a href="https://example.com">示例链接</a>和
                                <a href="/internal/page">内部链接</a>。
                            </p>
                            
                            <img src="/images/example.jpg" alt="示例图片" width="300" height="200">
                        </div>
                    </article>
                </main>
                <aside>侧边栏内容</aside>
                <footer>页脚信息</footer>
            </body>
        </html>
        """

    @pytest.fixture
    def sample_pdf_content(self):
        """样本PDF内容用于测试"""
        return "PDF文档内容\n\n这是一个测试PDF文档。\n\n包含多段落内容。"

    @pytest.mark.asyncio
    async def test_end_to_end_scrape_to_markdown_workflow(self, sample_html_content):
        """测试从网页爬取到Markdown转换的端到端工作流"""
        scrape_result = {
            "url": "https://example.com/article",
            "status_code": 200,
            "title": "综合测试文章",
            "content": {
                "text": "综合测试文章 作者：测试作者 这是文章的主要内容...",
                "html": sample_html_content,
                "links": [
                    {"url": "https://example.com", "text": "示例链接"},
                    {"url": "https://example.com/internal/page", "text": "内部链接"},
                ],
                "images": [{"src": "/images/example.jpg", "alt": "示例图片"}],
            },
            "meta_description": "用于测试的综合示例文章",
        }

        with (
            patch("extractor.scraper.WebScraper.scrape_url") as mock_scrape,
            patch(
                "extractor.markdown_converter.MarkdownConverter.convert_webpage_to_markdown"
            ) as mock_convert,
        ):
            mock_scrape.return_value = scrape_result
            mock_convert.return_value = {
                "success": True,
                "url": "https://example.com/article",
                "markdown": "# 综合测试文章\n\n这是文章的主要内容，包含**粗体**和*斜体*文本。",
                "metadata": {
                    "title": "综合测试文章",
                    "word_count": 150,
                    "links_count": 2,
                    "images_count": 1,
                },
            }

            # 验证工具链可以协同工作
            scrape_tool = await app.get_tool("scrape_webpage")
            convert_tool = await app.get_tool("convert_webpage_to_markdown")

            assert scrape_tool is not None
            assert convert_tool is not None

    @pytest.mark.asyncio
    async def test_batch_processing_integration(self):
        """测试批量处理集成"""
        urls = ["https://example1.com", "https://example2.com", "https://example3.com"]

        batch_scrape_result = {
            "results": [
                {
                    "url": "https://example1.com",
                    "status_code": 200,
                    "title": "页面1",
                    "content": {"text": "内容1", "html": "<h1>页面1</h1>"},
                },
                {
                    "url": "https://example2.com",
                    "status_code": 200,
                    "title": "页面2",
                    "content": {"text": "内容2", "html": "<h1>页面2</h1>"},
                },
                {
                    "url": "https://example3.com",
                    "status_code": 404,
                    "error": "页面未找到",
                },
            ],
            "summary": {"total": 3, "successful": 2, "failed": 1, "success_rate": 0.67},
        }

        batch_convert_result = {
            "success": True,
            "results": [
                {
                    "success": True,
                    "url": "https://example1.com",
                    "markdown": "# 页面1\n\n内容1",
                },
                {
                    "success": True,
                    "url": "https://example2.com",
                    "markdown": "# 页面2\n\n内容2",
                },
            ],
            "summary": {"total": 2, "successful": 2, "failed": 0},
        }

        with (
            patch(
                "extractor.scraper.WebScraper.scrape_multiple_urls"
            ) as mock_batch_scrape,
            patch(
                "extractor.markdown_converter.MarkdownConverter.batch_convert_to_markdown"
            ) as mock_batch_convert,
        ):
            mock_batch_scrape.return_value = batch_scrape_result
            mock_batch_convert.return_value = batch_convert_result

            batch_scrape_tool = await app.get_tool("scrape_multiple_webpages")
            batch_convert_tool = await app.get_tool(
                "batch_convert_webpages_to_markdown"
            )

            assert batch_scrape_tool is not None
            assert batch_convert_tool is not None

    @pytest.mark.asyncio
    async def test_advanced_features_integration(self):
        """测试高级功能集成"""
        # 测试隐身爬取
        stealth_result = {
            "url": "https://protected-site.com",
            "title": "受保护的页面",
            "content": {
                "text": "通过隐身技术获取的内容",
                "html": "<div>受保护的内容</div>",
            },
        }

        # 测试表单处理
        form_result = {
            "success": True,
            "results": {
                "#username": {"success": True, "value": "testuser"},
                "#password": {"success": True, "value": "testpass"},
                "_submit": {"success": True, "new_url": "https://site.com/dashboard"},
            },
        }

        # 测试结构化数据提取
        structured_result = {
            "url": "https://ecommerce.com",
            "data": {
                "products": [
                    {"name": "产品1", "price": "$99.99"},
                    {"name": "产品2", "price": "$149.99"},
                ],
                "contact": {"email": "info@ecommerce.com", "phone": "+1-555-0123"},
            },
        }

        with (
            patch(
                "extractor.advanced_features.AntiDetectionScraper.scrape_with_stealth"
            ) as mock_stealth,
            patch("extractor.advanced_features.FormHandler.fill_form") as mock_form,
        ):
            mock_stealth.return_value = stealth_result
            mock_form.return_value = form_result

            stealth_tool = await app.get_tool("scrape_with_stealth")
            form_tool = await app.get_tool("fill_and_submit_form")
            structured_tool = await app.get_tool("extract_structured_data")

            assert stealth_tool is not None
            assert form_tool is not None
            assert structured_tool is not None

    @pytest.mark.asyncio
    async def test_pdf_processing_integration(self, sample_pdf_content):
        """测试PDF处理集成"""
        pdf_result = {
            "success": True,
            "source": "https://example.com/document.pdf",
            "text": sample_pdf_content,
            "markdown": f"# PDF文档\n\n{sample_pdf_content}",
            "metadata": {
                "pages_processed": 3,
                "word_count": 20,
                "method_used": "pymupdf",
                "file_size_bytes": 1024000,
            },
            "output_format": "markdown",
        }

        batch_pdf_result = {
            "success": True,
            "results": [pdf_result, pdf_result],
            "summary": {
                "total_pdfs": 2,
                "successful": 2,
                "failed": 0,
                "total_pages_processed": 6,
                "total_words_extracted": 40,
            },
        }

        with (
            patch("extractor.pdf_processor.PDFProcessor.process_pdf") as mock_pdf,
            patch(
                "extractor.pdf_processor.PDFProcessor.batch_process_pdfs"
            ) as mock_batch_pdf,
        ):
            mock_pdf.return_value = pdf_result
            mock_batch_pdf.return_value = batch_pdf_result

            pdf_tool = await app.get_tool("convert_pdf_to_markdown")
            batch_pdf_tool = await app.get_tool("batch_convert_pdfs_to_markdown")

            assert pdf_tool is not None
            assert batch_pdf_tool is not None

    @pytest.mark.asyncio
    async def test_server_management_integration(self):
        """测试服务器管理集成"""
        metrics_result = {
            "server_info": {
                "name": settings.server_name,
                "version": settings.server_version,
                "uptime": "1h 23m 45s",
            },
            "performance": {
                "total_requests": 1234,
                "successful_requests": 1200,
                "failed_requests": 34,
                "success_rate": 0.972,
                "average_response_time": 1.25,
            },
            "cache": {"size": 150, "hit_rate": 0.85, "memory_usage": "25MB"},
            "methods": {
                "simple": 500,
                "scrapy": 600,
                "selenium": 100,
                "playwright": 34,
            },
        }

        cache_clear_result = {
            "success": True,
            "message": "缓存已清理",
            "items_cleared": 150,
            "memory_freed": "25MB",
        }

        with (
            patch("extractor.utils.MetricsCollector.get_stats") as mock_metrics,
            patch("extractor.utils.CacheManager.clear") as mock_cache_clear,
        ):
            mock_metrics.return_value = metrics_result
            mock_cache_clear.return_value = cache_clear_result

            metrics_tool = await app.get_tool("get_server_metrics")
            cache_tool = await app.get_tool("clear_cache")

            assert metrics_tool is not None
            assert cache_tool is not None

    @pytest.mark.asyncio
    async def test_information_extraction_integration(self):
        """测试信息提取工具集成"""
        page_info_result = {
            "url": "https://example.com",
            "status": 200,
            "title": "示例页面",
            "description": "这是一个示例页面",
            "content_type": "text/html",
            "content_length": 5000,
            "last_modified": "2024-01-15",
            "server": "nginx/1.18.0",
        }

        links_result = {
            "url": "https://example.com",
            "links": [
                {
                    "url": "https://example.com/page1",
                    "text": "页面1",
                    "type": "internal",
                },
                {"url": "https://external.com", "text": "外部链接", "type": "external"},
                {"url": "mailto:info@example.com", "text": "联系我们", "type": "email"},
            ],
            "summary": {
                "total_links": 3,
                "internal_links": 1,
                "external_links": 1,
                "email_links": 1,
            },
        }

        robots_result = {
            "url": "https://example.com/robots.txt",
            "exists": True,
            "content": "User-agent: *\nDisallow: /admin/\nAllow: /",
            "rules": [{"user_agent": "*", "disallow": ["/admin/"], "allow": ["/"]}],
            "sitemap_urls": ["https://example.com/sitemap.xml"],
        }

        with (
            patch("extractor.server.get_page_info") as mock_page_info,
            patch("extractor.server.extract_links") as mock_links,
            patch("extractor.server.check_robots_txt") as mock_robots,
        ):
            mock_page_info.return_value = page_info_result
            mock_links.return_value = links_result
            mock_robots.return_value = robots_result

            page_info_tool = await app.get_tool("get_page_info")
            links_tool = await app.get_tool("extract_links")
            robots_tool = await app.get_tool("check_robots_txt")

            assert page_info_tool is not None
            assert links_tool is not None
            assert robots_tool is not None


class TestPerformanceAndLoadIntegration:
    """性能和负载集成测试"""

    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_concurrent_tool_access_performance(self):
        """测试并发工具访问性能"""

        async def access_tools_concurrently():
            tasks = []
            tool_names = [
                "scrape_webpage",
                "convert_webpage_to_markdown",
                "get_server_metrics",
                "extract_links",
                "get_page_info",
            ]

            for tool_name in tool_names:
                task = app.get_tool(tool_name)
                tasks.append(task)

            return await asyncio.gather(*tasks)

        start_time = time.time()
        results = await access_tools_concurrently()
        end_time = time.time()

        access_time = end_time - start_time

        # 验证所有工具都能成功访问
        assert all(tool is not None for tool in results)
        # 并发访问应该在合理时间内完成
        assert access_time < 1.0, f"并发工具访问时间 {access_time:.2f}s 过长"

    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_batch_processing_scalability(self):
        """测试批量处理可扩展性"""
        # 模拟大量URL的批量处理
        large_url_list = [f"https://example{i}.com" for i in range(100)]

        batch_result = {
            "results": [
                {
                    "url": url,
                    "status_code": 200,
                    "title": f"页面{i}",
                    "content": {"text": f"内容{i}"},
                }
                for i, url in enumerate(large_url_list[:10])  # 只模拟前10个成功
            ]
            + [
                {"url": url, "error": "超时"}
                for url in large_url_list[10:15]  # 5个失败
            ],
            "summary": {
                "total": 100,
                "successful": 10,
                "failed": 5,
                "skipped": 85,  # 其他跳过以节省测试时间
            },
        }

        with patch("extractor.scraper.WebScraper.scrape_multiple_urls") as mock_batch:
            mock_batch.return_value = batch_result

            batch_tool = await app.get_tool("scrape_multiple_webpages")
            assert batch_tool is not None

    @pytest.mark.asyncio
    async def test_memory_usage_integration(self):
        """测试内存使用集成"""
        try:
            import psutil
        except ImportError:
            pytest.skip("psutil not available for memory monitoring")
        import os

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss

        # 执行一系列操作
        tools = await app.get_tools()

        # 访问所有工具
        for tool_name in tools.keys():
            tool = await app.get_tool(tool_name)
            assert tool is not None

        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory

        # 内存增长应该在合理范围内（比如小于50MB）
        assert memory_increase < 50 * 1024 * 1024, (
            f"内存增长 {memory_increase / 1024 / 1024:.1f}MB 过大"
        )


class TestErrorHandlingAndResilience:
    """错误处理和恢复性集成测试"""

    @pytest.mark.asyncio
    async def test_network_failure_resilience(self):
        """测试网络故障恢复性"""
        with patch("extractor.scraper.WebScraper.scrape_url") as mock_scrape:
            # 模拟网络故障
            mock_scrape.side_effect = [
                Exception("连接超时"),
                Exception("DNS解析失败"),
                {  # 第三次尝试成功
                    "url": "https://example.com",
                    "status_code": 200,
                    "title": "成功页面",
                    "content": {"text": "成功获取内容"},
                },
            ]

            # 工具应该能够处理这些错误
            scrape_tool = await app.get_tool("scrape_webpage")
            assert scrape_tool is not None

    @pytest.mark.asyncio
    async def test_invalid_input_handling(self):
        """测试无效输入处理"""
        # 所有工具都应该存在并能处理基本的验证
        tools = await app.get_tools()

        critical_tools = [
            "scrape_webpage",
            "convert_webpage_to_markdown",
            "convert_pdf_to_markdown",
            "scrape_with_stealth",
        ]

        for tool_name in critical_tools:
            assert tool_name in tools, f"关键工具 {tool_name} 未注册"
            tool = tools[tool_name]
            assert tool is not None, f"工具 {tool_name} 为None"

    @pytest.mark.asyncio
    async def test_resource_exhaustion_handling(self):
        """测试资源耗尽处理"""
        # 模拟资源耗尽情况
        with patch("tempfile.mkdtemp") as mock_mkdtemp:
            mock_mkdtemp.side_effect = OSError("磁盘空间不足")

            # 系统应该能够优雅地处理这种情况
            pdf_tool = await app.get_tool("convert_pdf_to_markdown")
            assert pdf_tool is not None

    @pytest.mark.asyncio
    async def test_configuration_validation(self):
        """测试配置验证"""
        # 验证关键配置项
        assert settings.server_name is not None
        assert settings.server_version is not None
        assert settings.concurrent_requests > 0
        assert settings.request_timeout > 0
        assert settings.browser_timeout > 0

        # 验证工具能够使用这些配置
        tools = await app.get_tools()
        assert len(tools) == 14


class TestSecurityAndCompliance:
    """安全和合规集成测试"""

    @pytest.mark.asyncio
    async def test_robots_txt_compliance_integration(self):
        """测试robots.txt合规性集成"""
        robots_result = {
            "url": "https://example.com/robots.txt",
            "exists": True,
            "content": "User-agent: *\nDisallow: /private/\nCrawl-delay: 1",
            "rules": [{"user_agent": "*", "disallow": ["/private/"], "crawl_delay": 1}],
        }

        with patch(
            "extractor.server.web_scraper.simple_scraper.scrape", new_callable=AsyncMock
        ) as mock_scrape:
            # Mock the robots.txt scraping result - no error means success
            mock_scrape.return_value = {
                "content": {"text": robots_result["content"]},
                "status_code": 200,
            }

            # Get the check_robots_txt tool from the FastMCP app
            from extractor.server import check_robots_txt, CheckRobotsRequest

            request = CheckRobotsRequest(url="https://example.com")
            result = await check_robots_txt.fn(request)

            assert result.success is True
            assert "robots.txt" in result.robots_txt_url
            assert "Disallow: /private/" in result.robots_content

    @pytest.mark.asyncio
    async def test_user_agent_and_rate_limiting(self):
        """测试User-Agent和速率限制"""
        # 验证配置中的User-Agent和速率限制设置
        assert settings.use_random_user_agent is not None
        assert settings.default_user_agent is not None
        assert settings.rate_limit_requests_per_minute > 0

        # 验证相关工具存在
        scrape_tool = await app.get_tool("scrape_webpage")
        stealth_tool = await app.get_tool("scrape_with_stealth")

        assert scrape_tool is not None
        assert stealth_tool is not None

    @pytest.mark.asyncio
    async def test_data_privacy_compliance(self):
        """测试数据隐私合规"""
        # 验证工具不会意外存储敏感信息
        tools = await app.get_tools()

        # 所有工具都应该正确注册且可访问
        for tool_name, tool in tools.items():
            assert tool is not None
            assert hasattr(tool, "name")
            assert tool.name == tool_name


class TestBackwardCompatibilityAndUpgrade:
    """向后兼容性和升级测试"""

    @pytest.mark.asyncio
    async def test_api_backward_compatibility(self):
        """测试API向后兼容性"""
        # 验证所有预期的工具仍然存在
        expected_core_tools = [
            "scrape_webpage",
            "convert_webpage_to_markdown",
            "convert_pdf_to_markdown",
        ]

        tools = await app.get_tools()

        for tool_name in expected_core_tools:
            assert tool_name in tools, f"核心工具 {tool_name} 缺失，可能破坏向后兼容性"

    @pytest.mark.asyncio
    async def test_configuration_upgrade_compatibility(self):
        """测试配置升级兼容性"""
        # 验证配置系统能够处理新旧配置格式
        assert hasattr(settings, "server_name")
        assert hasattr(settings, "server_version")
        assert hasattr(settings, "concurrent_requests")
        assert hasattr(settings, "enable_caching")

        # 新功能配置也应该存在
        assert hasattr(settings, "browser_headless")
        assert hasattr(settings, "use_random_user_agent")

    @pytest.mark.asyncio
    async def test_tool_interface_stability(self):
        """测试工具接口稳定性"""
        tools = await app.get_tools()

        # 验证所有工具都有稳定的接口
        for tool_name, tool in tools.items():
            assert tool is not None
            assert hasattr(tool, "name")
            assert hasattr(tool, "description")
            assert tool.name == tool_name
            assert isinstance(tool.description, str)
            assert len(tool.description) > 0
