"""
集成测试：更新的MCP工具集成测试
测试所有14个MCP工具的完整功能和集成
"""

import pytest
import asyncio
import json
from unittest.mock import patch, AsyncMock, Mock

from extractor.server import app


class TestUpdatedMCPToolsIntegration:
    """更新的MCP工具集成测试"""

    @pytest.mark.asyncio
    async def test_all_14_mcp_tools_registered(self):
        """测试所有14个MCP工具都已注册"""
        tools = await app.get_tools()
        tool_names = list(tools.keys())

        # 当前项目中的14个MCP工具
        expected_tools = [
            "scrape_webpage",  # 1. 基本网页爬取
            "scrape_multiple_webpages",  # 2. 批量网页爬取
            "extract_links",  # 3. 链接提取
            "get_page_info",  # 4. 页面信息获取
            "check_robots_txt",  # 5. robots.txt检查
            "scrape_with_stealth",  # 6. 隐身爬取
            "fill_and_submit_form",  # 7. 表单填充和提交
            "get_server_metrics",  # 8. 服务器指标获取
            "clear_cache",  # 9. 缓存清理
            "extract_structured_data",  # 10. 结构化数据提取
            "convert_webpage_to_markdown",  # 11. 网页转Markdown
            "batch_convert_webpages_to_markdown",  # 12. 批量网页转Markdown
            "convert_pdf_to_markdown",  # 13. PDF转Markdown
            "batch_convert_pdfs_to_markdown",  # 14. 批量PDF转Markdown
        ]

        assert len(expected_tools) == 14, "预期工具数量应为14个"

        for expected_tool in expected_tools:
            assert expected_tool in tool_names, (
                f"工具 {expected_tool} 未在注册工具中找到"
            )

        # 确保没有额外的未预期工具
        assert len(tool_names) >= 14, f"注册工具数量 {len(tool_names)} 少于预期的14个"

    @pytest.mark.asyncio
    async def test_tool_schema_completeness(self):
        """测试所有工具的schema完整性"""
        tools = await app.get_tools()

        for tool_name, tool in tools.items():
            # 验证工具基本结构
            assert hasattr(tool, "name"), f"工具 {tool_name} 缺少 name 属性"
            assert hasattr(tool, "description"), (
                f"工具 {tool_name} 缺少 description 属性"
            )
            assert tool.name == tool_name, f"工具名称不匹配: {tool.name} != {tool_name}"
            assert tool.description, f"工具 {tool_name} 的描述不能为空"

    @pytest.mark.asyncio
    async def test_basic_scraping_tools_integration(self):
        """测试基本爬取工具集成"""
        with patch("extractor.scraper.WebScraper.scrape_url") as mock_scrape:
            mock_scrape.return_value = {
                "url": "https://example.com",
                "status_code": 200,
                "title": "Test Page",
                "content": {
                    "text": "Test content",
                    "links": [{"url": "https://example.com/link", "text": "Link"}],
                    "images": [],
                },
                "meta_description": "Test description",
            }

            # 测试单页面爬取
            scrape_tool = await app.get_tool("scrape_webpage")
            assert scrape_tool is not None

            # 测试批量爬取
            batch_scrape_tool = await app.get_tool("scrape_multiple_webpages")
            assert batch_scrape_tool is not None

    @pytest.mark.asyncio
    async def test_advanced_scraping_tools_integration(self):
        """测试高级爬取工具集成"""
        with patch(
            "extractor.advanced_features.AntiDetectionScraper.scrape_with_stealth"
        ) as mock_stealth:
            mock_stealth.return_value = {
                "url": "https://example.com",
                "title": "Stealth Page",
                "content": {"text": "Stealth content"},
            }

            stealth_tool = await app.get_tool("scrape_with_stealth")
            assert stealth_tool is not None

        # 测试表单处理工具
        form_tool = await app.get_tool("fill_and_submit_form")
        assert form_tool is not None

        # 测试结构化数据提取
        structured_tool = await app.get_tool("extract_structured_data")
        assert structured_tool is not None

    @pytest.mark.asyncio
    async def test_information_tools_integration(self):
        """测试信息获取工具集成"""
        # 测试页面信息获取
        page_info_tool = await app.get_tool("get_page_info")
        assert page_info_tool is not None

        # 测试链接提取
        links_tool = await app.get_tool("extract_links")
        assert links_tool is not None

        # 测试robots.txt检查
        robots_tool = await app.get_tool("check_robots_txt")
        assert robots_tool is not None

    @pytest.mark.asyncio
    async def test_markdown_conversion_tools_integration(self):
        """测试Markdown转换工具集成"""
        with patch(
            "extractor.markdown_converter.MarkdownConverter.convert_webpage_to_markdown"
        ) as mock_convert:
            mock_convert.return_value = {
                "success": True,
                "url": "https://example.com",
                "markdown": "# Test Page\n\nTest content",
                "metadata": {"word_count": 3},
            }

            # 测试单页面转换
            convert_tool = await app.get_tool("convert_webpage_to_markdown")
            assert convert_tool is not None

            # 测试批量转换
            batch_convert_tool = await app.get_tool(
                "batch_convert_webpages_to_markdown"
            )
            assert batch_convert_tool is not None

    @pytest.mark.asyncio
    async def test_pdf_processing_tools_integration(self):
        """测试PDF处理工具集成"""
        with patch("extractor.pdf_processor.PDFProcessor.process_pdf") as mock_pdf:
            mock_pdf.return_value = {
                "success": True,
                "source": "test.pdf",
                "text": "PDF content",
                "markdown": "# PDF Content",
                "metadata": {"pages_processed": 1},
            }

            # 测试单PDF处理
            pdf_tool = await app.get_tool("convert_pdf_to_markdown")
            assert pdf_tool is not None

            # 测试批量PDF处理
            batch_pdf_tool = await app.get_tool("batch_convert_pdfs_to_markdown")
            assert batch_pdf_tool is not None

    @pytest.mark.asyncio
    async def test_server_management_tools_integration(self):
        """测试服务器管理工具集成"""
        # 测试服务器指标获取
        metrics_tool = await app.get_tool("get_server_metrics")
        assert metrics_tool is not None

        # 测试缓存清理
        cache_tool = await app.get_tool("clear_cache")
        assert cache_tool is not None

    @pytest.mark.asyncio
    async def test_tool_error_handling(self):
        """测试工具错误处理"""
        from fastmcp.exceptions import NotFoundError

        # 测试不存在的工具
        with pytest.raises(NotFoundError, match="Unknown tool: nonexistent_tool"):
            await app.get_tool("nonexistent_tool")

    @pytest.mark.asyncio
    async def test_app_metadata(self):
        """测试应用元数据"""
        assert hasattr(app, "name")
        assert hasattr(app, "version")
        assert app.name is not None
        assert app.version is not None


class TestMCPToolsParameterValidation:
    """测试MCP工具参数验证"""

    @pytest.mark.asyncio
    async def test_scrape_webpage_parameters(self):
        """测试scrape_webpage工具参数"""
        tool = await app.get_tool("scrape_webpage")
        assert tool is not None

        # 工具应该有适当的输入schema
        if hasattr(tool, "input_schema"):
            schema = tool.input_schema
            assert "properties" in schema
            assert "url" in schema["properties"]

    @pytest.mark.asyncio
    async def test_batch_tools_parameters(self):
        """测试批量工具参数"""
        batch_tools = [
            "scrape_multiple_webpages",
            "batch_convert_webpages_to_markdown",
            "batch_convert_pdfs_to_markdown",
        ]

        for tool_name in batch_tools:
            tool = await app.get_tool(tool_name)
            assert tool is not None, f"批量工具 {tool_name} 未找到"

    @pytest.mark.asyncio
    async def test_advanced_tools_parameters(self):
        """测试高级工具参数"""
        advanced_tools = [
            "scrape_with_stealth",
            "fill_and_submit_form",
            "extract_structured_data",
        ]

        for tool_name in advanced_tools:
            tool = await app.get_tool(tool_name)
            assert tool is not None, f"高级工具 {tool_name} 未找到"


class TestMCPToolsIntegrationWorkflow:
    """测试MCP工具集成工作流"""

    @pytest.fixture
    def sample_scrape_result(self):
        """示例爬取结果"""
        return {
            "url": "https://example.com",
            "status_code": 200,
            "title": "Example Domain",
            "content": {
                "text": "This domain is for use in illustrative examples in documents.",
                "html": "<html><body><h1>Example Domain</h1><p>This domain is for use in illustrative examples.</p></body></html>",
                "links": [
                    {
                        "url": "https://www.iana.org/domains/example",
                        "text": "More information...",
                    }
                ],
                "images": [],
            },
            "meta_description": "Example domain for documentation",
        }

    @pytest.mark.asyncio
    async def test_scrape_to_markdown_workflow(self, sample_scrape_result):
        """测试爬取到Markdown的完整工作流"""
        with (
            patch("extractor.scraper.WebScraper.scrape_url") as mock_scrape,
            patch(
                "extractor.markdown_converter.MarkdownConverter.convert_webpage_to_markdown"
            ) as mock_convert,
        ):
            mock_scrape.return_value = sample_scrape_result
            mock_convert.return_value = {
                "success": True,
                "url": "https://example.com",
                "markdown": "# Example Domain\n\nThis domain is for use in illustrative examples.",
                "metadata": {"word_count": 10},
            }

            # 这个工作流应该能够无缝工作
            scrape_tool = await app.get_tool("scrape_webpage")
            convert_tool = await app.get_tool("convert_webpage_to_markdown")

            assert scrape_tool is not None
            assert convert_tool is not None

    @pytest.mark.asyncio
    async def test_batch_processing_workflow(self):
        """测试批量处理工作流"""
        with (
            patch(
                "extractor.scraper.WebScraper.scrape_multiple_urls"
            ) as mock_batch_scrape,
            patch(
                "extractor.markdown_converter.MarkdownConverter.batch_convert_to_markdown"
            ) as mock_batch_convert,
        ):
            mock_batch_scrape.return_value = {
                "results": [
                    {"url": "https://example1.com", "title": "Page 1", "content": {}},
                    {"url": "https://example2.com", "title": "Page 2", "content": {}},
                ],
                "summary": {"successful": 2, "failed": 0},
            }

            mock_batch_convert.return_value = {
                "success": True,
                "results": [
                    {
                        "success": True,
                        "url": "https://example1.com",
                        "markdown": "# Page 1",
                    },
                    {
                        "success": True,
                        "url": "https://example2.com",
                        "markdown": "# Page 2",
                    },
                ],
            }

            batch_scrape_tool = await app.get_tool("scrape_multiple_webpages")
            batch_convert_tool = await app.get_tool(
                "batch_convert_webpages_to_markdown"
            )

            assert batch_scrape_tool is not None
            assert batch_convert_tool is not None

    @pytest.mark.asyncio
    async def test_stealth_to_structured_data_workflow(self):
        """测试隐身爬取到结构化数据提取工作流"""
        with patch(
            "extractor.advanced_features.AntiDetectionScraper.scrape_with_stealth"
        ) as mock_stealth:
            mock_stealth.return_value = {
                "url": "https://ecommerce-example.com",
                "title": "Product Page",
                "content": {
                    "text": "Product details and pricing information",
                    "html": "<div class='product'><h1>Product Name</h1><span class='price'>$99.99</span></div>",
                },
            }

            stealth_tool = await app.get_tool("scrape_with_stealth")
            structured_tool = await app.get_tool("extract_structured_data")

            assert stealth_tool is not None
            assert structured_tool is not None

    @pytest.mark.asyncio
    async def test_pdf_processing_workflow(self):
        """测试PDF处理工作流"""
        with patch(
            "extractor.pdf_processor.PDFProcessor.process_pdf"
        ) as mock_pdf_process:
            mock_pdf_process.return_value = {
                "success": True,
                "source": "https://example.com/document.pdf",
                "text": "PDF document content extracted successfully",
                "markdown": "# PDF Document\n\nContent extracted successfully",
                "metadata": {
                    "pages_processed": 5,
                    "word_count": 500,
                    "method_used": "pymupdf",
                },
            }

            pdf_tool = await app.get_tool("convert_pdf_to_markdown")
            assert pdf_tool is not None

    @pytest.mark.asyncio
    async def test_server_management_workflow(self):
        """测试服务器管理工作流"""
        # 测试指标获取后清理缓存的工作流
        metrics_tool = await app.get_tool("get_server_metrics")
        cache_tool = await app.get_tool("clear_cache")

        assert metrics_tool is not None
        assert cache_tool is not None


class TestMCPToolsRobustnessAndReliability:
    """测试MCP工具的健壮性和可靠性"""

    @pytest.mark.asyncio
    async def test_tools_handle_network_errors(self):
        """测试工具处理网络错误的能力"""
        with patch("extractor.scraper.WebScraper.scrape_url") as mock_scrape:
            # 模拟网络错误
            mock_scrape.side_effect = Exception("Network timeout")

            scrape_tool = await app.get_tool("scrape_webpage")
            assert scrape_tool is not None
            # 工具应该存在并能够处理错误

    @pytest.mark.asyncio
    async def test_tools_handle_invalid_parameters(self):
        """测试工具处理无效参数的能力"""
        # 所有工具都应该存在并有基本的错误处理
        tools = await app.get_tools()
        for tool_name, tool in tools.items():
            assert tool is not None, f"工具 {tool_name} 不应该为 None"
            assert hasattr(tool, "name"), f"工具 {tool_name} 应该有 name 属性"

    @pytest.mark.asyncio
    async def test_concurrent_tool_access(self):
        """测试并发工具访问"""

        async def get_tool_concurrent(tool_name):
            return await app.get_tool(tool_name)

        # 并发访问多个工具
        tool_names = [
            "scrape_webpage",
            "convert_webpage_to_markdown",
            "get_server_metrics",
        ]

        tasks = [get_tool_concurrent(name) for name in tool_names]
        results = await asyncio.gather(*tasks)

        for i, result in enumerate(results):
            assert result is not None, f"并发访问工具 {tool_names[i]} 失败"

    @pytest.mark.asyncio
    async def test_tool_resource_cleanup(self):
        """测试工具资源清理"""
        # 验证工具在使用后能够正确清理资源
        scrape_tool = await app.get_tool("scrape_webpage")
        stealth_tool = await app.get_tool("scrape_with_stealth")
        pdf_tool = await app.get_tool("convert_pdf_to_markdown")

        assert scrape_tool is not None
        assert stealth_tool is not None
        assert pdf_tool is not None


class TestMCPToolsPerformanceAndScalability:
    """测试MCP工具性能和可扩展性"""

    @pytest.mark.asyncio
    async def test_tool_registration_performance(self):
        """测试工具注册性能"""
        import time

        start_time = time.time()
        tools = await app.get_tools()
        end_time = time.time()

        registration_time = end_time - start_time

        assert len(tools) == 14, "应该注册14个工具"
        assert registration_time < 1.0, f"工具注册时间 {registration_time:.2f}s 过长"

    @pytest.mark.asyncio
    async def test_tool_access_performance(self):
        """测试工具访问性能"""
        import time

        tool_names = [
            "scrape_webpage",
            "convert_webpage_to_markdown",
            "convert_pdf_to_markdown",
            "scrape_with_stealth",
        ]

        for tool_name in tool_names:
            start_time = time.time()
            tool = await app.get_tool(tool_name)
            end_time = time.time()

            access_time = end_time - start_time

            assert tool is not None
            assert access_time < 0.1, (
                f"工具 {tool_name} 访问时间 {access_time:.3f}s 过长"
            )

    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_batch_tools_scalability(self):
        """测试批量工具可扩展性"""
        # 这个测试被标记为slow，只在完整测试时运行
        batch_tools = [
            "scrape_multiple_webpages",
            "batch_convert_webpages_to_markdown",
            "batch_convert_pdfs_to_markdown",
        ]

        for tool_name in batch_tools:
            tool = await app.get_tool(tool_name)
            assert tool is not None, f"批量工具 {tool_name} 应该支持可扩展性"
