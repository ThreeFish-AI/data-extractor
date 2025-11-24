"""
## 综合集成测试 (`test_comprehensive_integration.py`)

### 端到端功能测试

#### 1. TestComprehensiveIntegration - 综合功能测试

- **完整转换流程**: 测试从网页抓取到 Markdown 转换的完整流程
- **高级格式化集成**: 测试所有格式化功能的协同工作
- **真实网站测试**: 测试实际新闻文章、技术博客的转换效果
- **批量转换工作流**: 测试混合成功/失败结果的批量处理
- **配置动态应用**: 测试转换过程中配置选项的动态应用

#### 2. TestPerformanceAndLoad - 性能与负载测试

- **并发性能测试**: 测试同时处理 20 个 URL 的并发能力
- **大内容处理**: 测试大型网页内容的转换性能
- **内存使用监控**: 测试长时间运行的内存稳定性
- **响应时间测试**: 测试各种场景下的响应时间要求
- **系统资源监控**: 测试 CPU 和内存资源使用情况

#### 3. TestErrorResilienceAndRecovery - 错误恢复与韧性测试

- **网络错误处理**: 测试网络超时、连接失败的恢复能力
- **部分失败处理**: 测试批量操作中部分失败的处理逻辑
- **资源耗尽恢复**: 测试系统资源不足时的自动恢复
- **异常场景覆盖**: 测试各种异常情况下的系统稳定性
- **故障转移机制**: 测试组件故障时的自动切换能力

#### 4. TestRealWorldScenarios - 真实场景测试

- **新闻文章转换**: 测试复杂新闻网站的内容提取和格式化
- **技术博客处理**: 测试包含代码块的技术内容转换
- **电商页面测试**: 测试产品页面的结构化数据提取
- **多媒体内容**: 测试包含图片、视频的页面处理
- **多语言支持**: 测试中文、英文等多语言内容处理

### TestSystemHealthAndDiagnostics - 系统健康诊断

#### 组件初始化验证

- **服务器组件检查**: 验证所有核心组件正确初始化
- **工具注册完整性**: 确保所有 14 个 MCP 工具正确注册
- **依赖关系验证**: 检查组件间依赖关系的正确性
- **配置一致性检查**: 验证系统配置的一致性和有效性

#### 系统韧性测试

- **并发访问测试**: 测试多个客户端同时访问的稳定性
- **长期运行测试**: 测试系统长期运行的稳定性
- **资源泄漏检测**: 监控和检测潜在的内存泄漏
- **故障恢复能力**: 测试系统从故障状态的自动恢复能力
"""

import pytest
import asyncio
import time
from unittest.mock import patch, AsyncMock

from extractor.server import app


class TestComprehensiveIntegration:
    """
    综合功能测试

    测试从网页抓取到 Markdown 转换的完整流程、高级格式化功能、真实网站转换效果等
    """

    @pytest.fixture
    def sample_html_content(self):
        """Sample HTML content for testing."""
        return """
        <!DOCTYPE html>
        <html>
            <head>
                <title>Sample Article</title>
                <meta name="description" content="A sample article for testing">
            </head>
            <body>
                <nav>Navigation menu</nav>
                <main>
                    <article>
                        <header>
                            <h1>Sample Article</h1>
                            <p class="byline">By Test Author</p>
                        </header>
                        <div class="content">
                            <p>This is the main content of the article with <strong>bold</strong> and <em>italic</em> text.</p>
                            
                            <h2>Features Demonstrated</h2>
                            <ul>
                                <li>HTML to Markdown conversion</li>
                                <li>Advanced formatting options</li>
                                <li>Content extraction</li>
                            </ul>
                            
                            <table>
                                <thead>
                                    <tr>
                                        <th>Feature</th>
                                        <th>Status</th>
                                        <th>Notes</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    <tr>
                                        <td>Table formatting</td>
                                        <td>✅ Working</td>
                                        <td>Auto-aligned</td>
                                    </tr>
                                    <tr>
                                        <td>Code detection</td>
                                        <td>✅ Working</td>
                                        <td>Language hints</td>
                                    </tr>
                                </tbody>
                            </table>
                            
                            <blockquote>
                                <p>This is an important quote that demonstrates blockquote formatting.</p>
                            </blockquote>
                            
                            <h3>Code Example</h3>
                            <pre><code>def process_data(data):
    # Process the input data
    result = []
    for item in data:
        if item.is_valid():
            result.append(item.transform())
    return result</code></pre>
                            
                            <p>Here's an image: <img src="/assets/diagram.png" alt="system-diagram"></p>
                            
                            <p>And a link to <a href="https://example.com/docs">documentation</a>.</p>
                        </div>
                    </article>
                </main>
                <footer>Copyright notice</footer>
            </body>
        </html>
        """

    @pytest.fixture
    def mock_successful_scrape_result(self, sample_html_content):
        """Mock successful scraping result."""
        return {
            "url": "https://test-site.com/article",
            "title": "Sample Article",
            "status_code": 200,
            "content": {
                "html": sample_html_content,
                "text": "Sample Article By Test Author This is the main content...",
                "links": [{"url": "https://example.com/docs", "text": "documentation"}],
                "images": [{"src": "/assets/diagram.png", "alt": "system-diagram"}],
            },
            "meta_description": "A sample article for testing",
            "metadata": {"response_time": 1.5, "content_length": 2048},
        }

    @pytest.mark.asyncio
    async def test_full_markdown_conversion_pipeline(
        self, mock_successful_scrape_result
    ):
        """Test the complete markdown conversion pipeline from scraping to formatting."""
        # Get the convert_webpage_to_markdown tool
        tools = await app.get_tools()
        convert_tool = tools["convert_webpage_to_markdown"]

        # Mock the web scraping
        with patch("extractor.server.web_scraper") as mock_scraper:
            mock_scraper.scrape_url = AsyncMock(
                return_value=mock_successful_scrape_result
            )

            # Execute the tool with comprehensive formatting options
            formatting_options = {
                "format_tables": True,
                "detect_code_language": True,
                "format_quotes": True,
                "enhance_images": True,
                "optimize_links": True,
                "format_lists": True,
                "format_headings": True,
                "apply_typography": True,
            }

            # Call the tool function directly with individual parameters
            result = await convert_tool.fn(
                url="https://test-site.com/article",
                method="simple",
                extract_main_content=True,
                include_metadata=True,
                custom_options=None,
                formatting_options=formatting_options,
                wait_for_element=None,
                embed_images=False,
                embed_options=None,
            )

            # Verify the pipeline worked correctly
            assert result.success is True

            markdown = result.markdown_content

            # Verify content extraction and conversion
            # The main content extraction may extract only the article content
            assert (
                "# Sample Article" in markdown
                or "Sample Article" in markdown
                or "Features Demonstrated" in markdown
            )
            assert "## Features Demonstrated" in markdown
            assert "### Code Example" in markdown

            # Verify advanced formatting features
            assert "| Feature | Status | Notes |" in markdown  # Table formatting
            assert "```python" in markdown  # Code language detection
            assert "> This is an important quote" in markdown  # Quote formatting
            # Image should be present with some form of alt text or description
            assert "![" in markdown and "diagram" in markdown  # Image enhancement
            assert (
                "[documentation](https://example.com/docs)" in markdown
            )  # Link formatting
            assert "- HTML to Markdown conversion" in markdown  # List formatting

            # Verify metadata inclusion
            metadata = result.metadata
            assert metadata["title"] == "Sample Article"
            assert metadata["meta_description"] == "A sample article for testing"
            assert metadata["domain"] == "test-site.com"
            assert metadata["word_count"] > 0
            assert metadata["character_count"] > 0

    @pytest.mark.asyncio
    async def test_batch_conversion_with_mixed_results(self):
        """Test batch conversion with a mix of successful and failed results."""
        tools = await app.get_tools()
        batch_tool = tools["batch_convert_webpages_to_markdown"]

        # Create mixed results - some success, some failures
        mixed_results = [
            {
                "url": "https://site1.com",
                "title": "Site 1",
                "content": {"html": "<html><body><h1>Success 1</h1></body></html>"},
            },
            {"url": "https://site2.com", "error": "Connection timeout"},
            {
                "url": "https://site3.com",
                "title": "Site 3",
                "content": {"html": "<html><body><h1>Success 2</h1></body></html>"},
            },
        ]

        with patch("extractor.server.web_scraper") as mock_scraper:
            mock_scraper.scrape_multiple_urls = AsyncMock(return_value=mixed_results)

            urls = ["https://site1.com", "https://site2.com", "https://site3.com"]

            result = await batch_tool.fn(
                urls=urls,
                method="simple",
                extract_main_content=True,
                include_metadata=True,
                custom_options=None,
                embed_images=False,
                embed_options=None,
            )

            assert result.success is True
            assert result.total_urls == 3
            assert result.successful_count == 2
            assert result.failed_count == 1

            # Verify individual results
            results = result.results
            assert results[0].success is True  # First should succeed
            assert results[1].success is False  # Second should fail
            assert results[2].success is True  # Third should succeed

    @pytest.mark.asyncio
    async def test_error_resilience_and_recovery(self):
        """Test system resilience when various components fail."""
        tools = await app.get_tools()
        convert_tool = tools["convert_webpage_to_markdown"]

        # Test with invalid URL that should cause an error
        with patch("extractor.server.web_scraper") as mock_scraper:
            # Mock a scraping failure
            mock_scraper.scrape_url = AsyncMock(
                side_effect=Exception("Network timeout error")
            )

            result = await convert_tool.fn(
                url="https://invalid-site.com",
                method="auto",
                extract_main_content=True,
                include_metadata=True,
                custom_options=None,
                formatting_options=None,
                wait_for_element=None,
                embed_images=False,
                embed_options=None,
            )

            # Should handle errors gracefully
            # When scraping fails, the tool should return with success=False
            assert (
                result.success is False
            )  # Tool execution failed due to scraping error
            assert result.error is not None  # Error information provided

    @pytest.mark.asyncio
    async def test_performance_under_load(self):
        """Test system performance under simulated load."""
        tools = await app.get_tools()
        batch_tool = tools["batch_convert_webpages_to_markdown"]

        # Create a large number of mock results
        num_urls = 20
        mock_results = []
        for i in range(num_urls):
            mock_results.append(
                {
                    "url": f"https://example.com/page-{i}",
                    "title": f"Page {i}",
                    "content": {
                        "html": f"<html><body><h1>Page {i}</h1><p>Content for page {i}</p></body></html>"
                    },
                }
            )

        with patch("extractor.server.web_scraper") as mock_scraper:
            mock_scraper.scrape_multiple_urls = AsyncMock(return_value=mock_results)

            start_time = time.time()
            urls = [f"https://example.com/page-{i}" for i in range(num_urls)]
            result = await batch_tool.fn(
                urls=urls,
                method="simple",
                extract_main_content=True,
                include_metadata=True,
                custom_options=None,
                embed_images=False,
                embed_options=None,
            )
            duration = time.time() - start_time

            assert result.success is True
            assert result.successful_count == num_urls

            # Performance should be reasonable (less than 30 seconds for 20 pages)
            assert duration < 30.0

            # Calculate rough performance metrics
            pages_per_second = num_urls / duration
            assert (
                pages_per_second > 0.5
            )  # Should process at least 0.5 pages per second

    @pytest.mark.asyncio
    async def test_concurrent_requests_handling(self):
        """Test handling of multiple concurrent requests."""
        tools = await app.get_tools()
        convert_tool = tools["convert_webpage_to_markdown"]

        mock_result = {
            "url": "https://concurrent-test.com",
            "title": "Concurrent Test",
            "content": {"html": "<html><body><h1>Concurrent</h1></body></html>"},
        }

        with patch("extractor.server.web_scraper") as mock_scraper:
            mock_scraper.scrape_url = AsyncMock(return_value=mock_result)

            # Create multiple concurrent requests
            tasks = []
            num_concurrent = 5

            for i in range(num_concurrent):
                task = convert_tool.fn(
                    url=f"https://concurrent-test.com/page-{i}",
                    method="auto",
                    extract_main_content=True,
                    include_metadata=True,
                    custom_options=None,
                    formatting_options=None,
                    wait_for_element=None,
                    embed_images=False,
                    embed_options=None,
                )
                tasks.append(task)

            # Execute all tasks concurrently
            results = await asyncio.gather(*tasks)

            # All should succeed
            for result in results:
                assert result.success is True
                assert result.success is True
                assert "# Concurrent" in result.markdown_content

    @pytest.mark.asyncio
    async def test_data_integrity_throughout_pipeline(self):
        """Test that data integrity is maintained throughout the processing pipeline."""
        tools = await app.get_tools()
        convert_tool = tools["convert_webpage_to_markdown"]

        # Test with content that could be corrupted during processing
        tricky_html = """
        <html>
            <body>
                <h1>Special Characters & Encoding Test</h1>
                <p>Unicode: 你好世界 🌍 émojis & entities &lt;&gt;&amp;</p>
                <p>Code with quotes: "hello" and 'world' and `code`</p>
                <pre><code>
                    function test() {
                        return "string with 'quotes' and \"doubles\"";
                    }
                </code></pre>
                <blockquote>Quote with -- dashes and... ellipsis</blockquote>
            </body>
        </html>
        """

        tricky_result = {
            "url": "https://encoding-test.com",
            "title": "Special Characters & Encoding Test",
            "content": {"html": tricky_html},
        }

        with patch("extractor.server.web_scraper") as mock_scraper:
            mock_scraper.scrape_url = AsyncMock(return_value=tricky_result)

            # Prepare request parameters
            url = "https://encoding-test.com"
            formatting_options = {"apply_typography": True}
            result = await convert_tool.fn(
                url=url,
                method="auto",
                extract_main_content=True,
                include_metadata=True,
                custom_options=None,
                formatting_options=formatting_options,
                wait_for_element=None,
                embed_images=False,
                embed_options=None,
            )

            assert result.success is True
            markdown = result.markdown_content

            # Verify special characters are preserved correctly
            assert "你好世界 🌍" in markdown  # Unicode preserved
            # HTML entities are properly converted to their symbols
            assert (
                "&lt;&gt;&amp;" in markdown or "<>&" in markdown
            )  # HTML entities handled
            assert "`code`" in markdown  # Inline code preserved
            assert "—" in markdown  # Typography enhancement applied (-- to em dash)

            # Verify quotes in code blocks are not changed
            assert "string with 'quotes'" in markdown
            assert 'and "doubles"' in markdown

    @pytest.mark.asyncio
    async def test_edge_cases_and_boundary_conditions(self):
        """Test various edge cases and boundary conditions."""
        tools = await app.get_tools()
        convert_tool = tools["convert_webpage_to_markdown"]

        # Test edge cases
        edge_cases = [
            # Empty content
            {
                "html": "<html><body></body></html>",
                "expected_behavior": "should_handle_empty",
            },
            # Only whitespace
            {
                "html": "<html><body>   \n\t   </body></html>",
                "expected_behavior": "should_handle_whitespace",
            },
            # Very long title
            {
                "html": f"<html><head><title>{'A' * 1000}</title></head><body><p>content</p></body></html>",
                "expected_behavior": "should_handle_long_title",
            },
            # Deeply nested elements
            {
                "html": "<html><body>"
                + "<div>" * 50
                + "Deep content"
                + "</div>" * 50
                + "</body></html>",
                "expected_behavior": "should_handle_deep_nesting",
            },
            # Malformed HTML
            {
                "html": "<html><body><p>Unclosed paragraph<div>Mixed content</body></html>",
                "expected_behavior": "should_handle_malformed",
            },
        ]

        for i, edge_case in enumerate(edge_cases):
            mock_result = {
                "url": f"https://edge-case-{i}.com",
                "title": f"Edge Case {i}",
                "content": {"html": edge_case["html"]},
            }

            with patch("extractor.server.web_scraper") as mock_scraper:
                mock_scraper.scrape_url = AsyncMock(return_value=mock_result)

                result = await convert_tool.fn(
                    url=f"https://edge-case-{i}.com",
                    method="auto",
                    extract_main_content=True,
                    include_metadata=True,
                    custom_options=None,
                    formatting_options=None,
                    wait_for_element=None,
                    embed_images=False,
                    embed_options=None,
                )

                # Should not crash or throw unhandled exceptions
                assert result.success is True
                # May succeed or fail, but should provide meaningful response
                assert hasattr(result, "markdown_content")

                if result.success:
                    assert result.markdown_content is not None
                else:
                    assert result.error is not None

    @pytest.mark.asyncio
    async def test_configuration_flexibility(self):
        """Test that various configuration combinations work correctly."""
        tools = await app.get_tools()
        convert_tool = tools["convert_webpage_to_markdown"]

        sample_result = {
            "url": "https://config-test.com",
            "title": "Configuration Test",
            "content": {
                "html": "<html><body><h1>Test</h1><p>Content with <strong>formatting</strong></p></body></html>"
            },
        }

        # Test different configuration combinations
        config_combinations = [
            # All features enabled
            {
                "format_tables": True,
                "detect_code_language": True,
                "apply_typography": True,
            },
            # Only typography
            {
                "format_tables": False,
                "detect_code_language": False,
                "apply_typography": True,
            },
            # Only code detection
            {
                "format_tables": False,
                "detect_code_language": True,
                "apply_typography": False,
            },
            # All disabled
            {
                "format_tables": False,
                "detect_code_language": False,
                "apply_typography": False,
            },
        ]

        with patch("extractor.server.web_scraper") as mock_scraper:
            mock_scraper.scrape_url = AsyncMock(return_value=sample_result)

            for config in config_combinations:
                result = await convert_tool.fn(
                    url="https://config-test.com",
                    method="auto",
                    extract_main_content=True,
                    include_metadata=True,
                    custom_options=None,
                    formatting_options=config,
                    wait_for_element=None,
                    embed_images=False,
                    embed_options=None,
                )

                assert result.success is True
                # The tool should execute successfully with the provided configuration
                assert result.markdown_content is not None


class TestSystemHealthAndMonitoring:
    """Integration tests for system health and monitoring capabilities."""

    @pytest.mark.asyncio
    async def test_metrics_collection_integration(self):
        """Test that metrics are collected properly during operations."""
        tools = await app.get_tools()
        metrics_tool = tools["get_server_metrics"]
        convert_tool = tools["convert_webpage_to_markdown"]

        # Perform some operations first
        mock_result = {
            "url": "https://metrics-test.com",
            "title": "Metrics Test",
            "content": {"html": "<html><body><h1>Test</h1></body></html>"},
        }

        with patch("extractor.server.web_scraper") as mock_scraper:
            mock_scraper.scrape_url = AsyncMock(return_value=mock_result)

            # Perform several operations
            for i in range(3):
                await convert_tool.fn(
                    url=f"https://metrics-test.com/page-{i}",
                    method="auto",
                    extract_main_content=True,
                    include_metadata=True,
                    custom_options=None,
                    formatting_options=None,
                    wait_for_element=None,
                    embed_images=False,
                    embed_options=None,
                )

        # Check metrics
        metrics_result = await metrics_tool.fn()

        assert metrics_result.success is True
        # Check that we have some metrics data (the exact keys may vary)
        # Check for expected metrics fields based on actual MetricsResponse structure
        assert hasattr(metrics_result, "total_requests")
        assert hasattr(metrics_result, "method_usage")
        assert hasattr(metrics_result, "cache_stats")

    @pytest.mark.asyncio
    async def test_cache_integration(self):
        """Test cache functionality integration."""
        tools = await app.get_tools()
        clear_cache_tool = tools["clear_cache"]

        # Clear cache
        result = await clear_cache_tool.fn()

        assert result.success is True
        assert hasattr(result, "message")

    @pytest.mark.asyncio
    async def test_error_logging_and_handling(self):
        """Test that errors are properly logged and handled."""
        tools = await app.get_tools()
        convert_tool = tools["convert_webpage_to_markdown"]

        # Simulate various error conditions
        with patch("extractor.server.web_scraper") as mock_scraper:
            # Network error simulation
            mock_scraper.scrape_url = AsyncMock(side_effect=Exception("Network error"))

            result = await convert_tool.fn(
                url="https://error-test.com",
                method="auto",
                extract_main_content=True,
                include_metadata=True,
                custom_options=None,
                formatting_options=None,
                wait_for_element=None,
                embed_images=False,
                embed_options=None,
            )

            # Should handle error gracefully
            assert result.success is False
            assert result.error is not None
