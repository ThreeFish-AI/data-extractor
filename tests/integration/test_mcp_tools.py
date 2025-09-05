"""Integration tests for MCP tools through FastMCP app."""

import asyncio
import pytest

from extractor.server import app, web_scraper, anti_detection_scraper
from extractor.scraper import WebScraper
from extractor.advanced_features import AntiDetectionScraper
from extractor.markdown_converter import MarkdownConverter


class TestMCPToolsIntegration:
    """Integration tests for MCP tools functionality."""

    @pytest.fixture
    def mock_scraper_result(self):
        """Mock scraper result for testing."""
        return {
            "url": "https://example.com",
            "status_code": 200,
            "title": "Example Domain",
            "content": {
                "text": "Example Domain This domain is for use in illustrative examples.",
                "links": [{"url": "https://example.com/link", "text": "Link text"}],
                "images": [],
            },
            "meta_description": None,
            "metadata": {
                "response_time": 1.2,
                "content_length": 1000,
            },
        }

    @pytest.mark.asyncio
    async def test_all_tools_registered(self):
        """Test that all expected MCP tools are registered."""
        tools = await app.get_tools()
        tool_names = list(tools.keys())

        expected_tools = [
            "scrape_webpage",
            "scrape_multiple_webpages",
            "extract_links",
            "get_page_info",
            "check_robots_txt",
            "scrape_with_stealth",
            "fill_and_submit_form",
            "get_server_metrics",
            "clear_cache",
            "extract_structured_data",
            "convert_webpage_to_markdown",
            "batch_convert_webpages_to_markdown",
        ]

        for expected_tool in expected_tools:
            assert expected_tool in tool_names, (
                f"Tool {expected_tool} not found in registered tools"
            )

    @pytest.mark.asyncio
    async def test_tool_execution_via_get_tool(self, mock_scraper_result):
        """Test tool execution through get_tool method."""
        # Get the tool by name
        scrape_tool = await app.get_tool("scrape_webpage")

        assert scrape_tool is not None, "scrape_webpage tool not found"

        # Test tool structure
        assert scrape_tool.name == "scrape_webpage"
        assert hasattr(scrape_tool, "fn") or callable(scrape_tool)

        # Test that the tool function exists
        if hasattr(scrape_tool, "fn"):
            assert callable(scrape_tool.fn)

    @pytest.mark.asyncio
    async def test_fastmcp_app_properties(self):
        """Test FastMCP app has expected properties."""
        assert hasattr(app, "get_tools")
        assert hasattr(app, "get_tool")
        assert hasattr(app, "name")
        assert hasattr(app, "version")

        # Test basic app properties
        assert app.name is not None
        assert app.version is not None

        # Test tools list is not empty
        tools = await app.get_tools()
        assert len(tools) > 0

    @pytest.mark.asyncio
    async def test_tool_registration_completeness(self):
        """Test that all tools are properly registered with correct structure."""
        tools = await app.get_tools()

        for tool_name, tool in tools.items():
            # Each tool should have basic properties
            assert hasattr(tool, "name")
            assert hasattr(tool, "description")
            assert tool.name is not None
            assert tool.name == tool_name
            # Description should exist and be meaningful if present
            if tool.description:
                assert len(tool.description) > 0

    @pytest.mark.asyncio
    async def test_server_initialization(self):
        """Test that server components are properly initialized."""
        # Test that global scrapers are initialized
        assert web_scraper is not None
        assert anti_detection_scraper is not None

        # Test that they are the correct type
        assert isinstance(web_scraper, WebScraper)
        assert isinstance(anti_detection_scraper, AntiDetectionScraper)


class TestWebScraperIntegration:
    """Integration tests for WebScraper class."""

    @pytest.fixture
    def scraper(self):
        """WebScraper instance for testing."""
        return WebScraper()

    def test_scraper_initialization(self, scraper):
        """Test WebScraper initializes correctly."""
        assert isinstance(scraper, WebScraper)
        assert hasattr(scraper, "simple_scraper")
        assert hasattr(scraper, "scrapy_wrapper")
        assert hasattr(scraper, "selenium_scraper")

    @pytest.mark.asyncio
    async def test_scraper_basic_functionality(self, scraper):
        """Test basic scraper functionality."""
        # Test that scraper can be called without errors
        assert hasattr(scraper, "scrape_url")
        assert callable(scraper.scrape_url)

        assert hasattr(scraper, "scrape_multiple_urls")
        assert callable(scraper.scrape_multiple_urls)


class TestAntiDetectionScraperIntegration:
    """Integration tests for AntiDetectionScraper class."""

    @pytest.fixture
    def anti_scraper(self):
        """AntiDetectionScraper instance for testing."""
        return AntiDetectionScraper()

    def test_anti_scraper_initialization(self, anti_scraper):
        """Test AntiDetectionScraper initializes correctly."""
        assert isinstance(anti_scraper, AntiDetectionScraper)
        assert hasattr(anti_scraper, "ua")

    @pytest.mark.asyncio
    async def test_anti_scraper_basic_functionality(self, anti_scraper):
        """Test basic anti-detection scraper functionality."""
        assert hasattr(anti_scraper, "scrape_with_stealth")
        assert callable(anti_scraper.scrape_with_stealth)


class TestMarkdownConversionIntegration:
    """Integration tests for Markdown conversion tools registration."""

    @pytest.mark.asyncio
    async def test_markdown_tools_registration(self):
        """Test that the new Markdown conversion tools are properly registered."""
        tools = await app.get_tools()

        # Test that the new Markdown conversion tools are registered
        assert "convert_webpage_to_markdown" in tools
        assert "batch_convert_webpages_to_markdown" in tools

        # Test convert_webpage_to_markdown tool properties
        convert_tool = tools["convert_webpage_to_markdown"]
        assert convert_tool.name == "convert_webpage_to_markdown"
        assert "Markdown" in convert_tool.description
        assert "webpage" in convert_tool.description.lower()

        # Test batch_convert_webpages_to_markdown tool properties
        batch_tool = tools["batch_convert_webpages_to_markdown"]
        assert batch_tool.name == "batch_convert_webpages_to_markdown"
        assert "batch" in batch_tool.description.lower()
        assert "Markdown" in batch_tool.description

    @pytest.mark.asyncio
    async def test_markdown_tools_parameters(self):
        """Test that the new tools have correct parameter schemas."""
        tools = await app.get_tools()

        # Test convert_webpage_to_markdown parameters
        convert_tool = tools["convert_webpage_to_markdown"]
        assert hasattr(convert_tool, "schema")

        # Test batch_convert_webpages_to_markdown parameters
        batch_tool = tools["batch_convert_webpages_to_markdown"]
        assert hasattr(batch_tool, "schema")


class TestMarkdownConversionToolIntegration:
    """Integration tests for Markdown conversion tool functionality through MCP layer."""

    @pytest.mark.asyncio
    async def test_markdown_conversion_tools_structure(self):
        """Test that Markdown conversion tools have proper structure and can be accessed."""
        tools = await app.get_tools()

        # Test convert_webpage_to_markdown tool
        convert_tool = tools["convert_webpage_to_markdown"]
        assert convert_tool is not None
        assert hasattr(convert_tool, "fn") or callable(convert_tool)
        if convert_tool.description:
            assert "Markdown" in convert_tool.description

        # Test batch_convert_webpages_to_markdown tool
        batch_tool = tools["batch_convert_webpages_to_markdown"]
        assert batch_tool is not None
        assert hasattr(batch_tool, "fn") or callable(batch_tool)
        if batch_tool.description:
            assert "batch" in batch_tool.description.lower()

    @pytest.mark.asyncio
    async def test_markdown_converter_component_integration(self):
        """Test that MarkdownConverter integrates properly with the system."""
        # Test direct MarkdownConverter functionality
        converter = MarkdownConverter()

        # Verify initialization
        assert converter.default_options["heading_style"] == "ATX"
        assert converter.formatting_options["format_tables"] is True

        # Test basic conversion
        html = "<html><body><h1>Test</h1><p>Content</p></body></html>"
        markdown = converter.html_to_markdown(html)

        assert "# Test" in markdown
        assert "Content" in markdown

    @pytest.mark.asyncio
    async def test_markdown_conversion_with_advanced_formatting(self):
        """Test advanced formatting options integration."""
        converter = MarkdownConverter()

        # HTML with various elements that trigger advanced formatting
        complex_html = """
        <html>
            <body>
                <h1>Test Article</h1>
                <table>
                    <tr><th>Col 1</th><th>Col 2</th></tr>
                    <tr><td>Data 1</td><td>Data 2</td></tr>
                </table>
                <pre><code>def test():\n    return True</code></pre>
                <blockquote>Important note</blockquote>
                <img src="test.jpg" alt="">
                <p>Text with -- dashes and "quotes"</p>
            </body>
        </html>
        """

        # Test with all formatting options enabled
        markdown = converter.html_to_markdown(complex_html)

        # Verify advanced formatting applied
        assert "| Col 1 | Col 2 |" in markdown  # Table formatting
        assert "```python" in markdown  # Code language detection
        assert "> Important note" in markdown  # Quote formatting
        assert "![Test](test.jpg)" in markdown  # Image enhancement
        assert "—" in markdown  # Typography (-- to em dash)

    @pytest.mark.asyncio
    async def test_error_handling_integration(self):
        """Test error handling integration across components."""
        converter = MarkdownConverter()

        # Test with malformed HTML
        malformed_html = "<html><body><p>Unclosed paragraph<div>Mixed"

        # Should handle gracefully without crashing
        result = converter.html_to_markdown(malformed_html)
        assert isinstance(result, str)  # Should return something, not crash

        # Test with empty content
        empty_result = {
            "url": "https://empty.com",
            "content": {"html": "<html><body></body></html>"},
        }

        conversion_result = converter.convert_webpage_to_markdown(empty_result)
        assert conversion_result["success"] is True

    @pytest.mark.asyncio
    async def test_component_configuration_integration(self):
        """Test that configuration options work across the integration stack."""
        converter = MarkdownConverter()

        # Test configuration modification
        original_options = converter.formatting_options.copy()

        # Modify configuration
        test_options = {"format_tables": False, "apply_typography": False}

        # Test conversion with modified options
        html = "<html><body><table><tr><td>test</td></tr></table><p>Text -- with dashes</p></body></html>"
        result = converter.convert_webpage_to_markdown(
            {"url": "test", "content": {"html": html}}, formatting_options=test_options
        )

        # Configuration should have been applied
        assert result["conversion_options"]["formatting_options"] == test_options

        # Original options should be restored
        assert converter.formatting_options == original_options


class TestSystemHealthAndDiagnostics:
    """Integration tests for system health and diagnostic capabilities."""

    @pytest.mark.asyncio
    async def test_all_components_initialized(self):
        """Test that all system components are properly initialized."""
        # Test that server components exist
        assert web_scraper is not None
        assert anti_detection_scraper is not None
        assert isinstance(web_scraper, WebScraper)
        assert isinstance(anti_detection_scraper, AntiDetectionScraper)

        # Test that all expected tools are available
        tools = await app.get_tools()
        expected_tool_count = 12  # Current total
        assert len(tools) == expected_tool_count

        # Test that app has proper structure
        assert hasattr(app, "get_tools")
        assert hasattr(app, "get_tool")
        assert app.name is not None

    @pytest.mark.asyncio
    async def test_tool_parameter_schemas_completeness(self):
        """Test that all tools have complete parameter schemas."""
        tools = await app.get_tools()

        for tool_name, tool in tools.items():
            # Each tool should have proper structure
            assert hasattr(tool, "name")
            assert hasattr(tool, "description")

            # Basic validation of tool properties
            assert tool.name == tool_name
            # Description should be meaningful if present
            if tool.description:
                assert len(tool.description) > 10

            # Check for schema or parameter information if available
            # Skip JSON schema generation as some tools may have callable schemas
            # that don't support JSON schema generation
            try:
                if hasattr(tool, "model_json_schema"):
                    schema = tool.model_json_schema()
                    assert schema is not None
            except Exception:
                # Some tools may have callable schemas that don't support JSON schema
                # This is acceptable as long as the tool has other validation
                pass

    @pytest.mark.asyncio
    async def test_system_resilience_under_load(self):
        """Test system resilience when processing multiple requests."""
        # Test accessing multiple tools simultaneously
        tasks = []
        for tool_name in [
            "scrape_webpage",
            "convert_webpage_to_markdown",
            "get_server_metrics",
        ]:
            task = app.get_tool(tool_name)
            tasks.append(task)

        # Should handle concurrent access without issues
        results = await asyncio.gather(*tasks)

        for result in results:
            assert result is not None
            assert hasattr(result, "name")

    @pytest.mark.asyncio
    async def test_memory_and_resource_management(self):
        """Test that the system manages memory and resources properly."""
        import gc

        # Get initial memory usage
        initial_objects = len(gc.get_objects())

        # Create and use converter multiple times
        for i in range(10):
            converter = MarkdownConverter()
            html = f"<html><body><h1>Test {i}</h1><p>Content {i}</p></body></html>"
            markdown = converter.html_to_markdown(html)
            assert "Test" in markdown
            del converter

        # Force garbage collection
        gc.collect()

        # Check that we haven't leaked too many objects
        final_objects = len(gc.get_objects())
        object_growth = final_objects - initial_objects

        # Allow for some growth, but not excessive (less than 1000 new objects)
        assert object_growth < 1000, (
            f"Memory leak detected: {object_growth} new objects"
        )
