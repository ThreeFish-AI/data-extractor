"""Integration tests for MCP tools through FastMCP app."""

import pytest
from unittest.mock import patch, AsyncMock

from extractor.server import app, web_scraper, anti_detection_scraper
from extractor.scraper import WebScraper
from extractor.advanced_features import AntiDetectionScraper


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
        ]

        for expected_tool in expected_tools:
            assert expected_tool in tool_names, (
                f"Tool {expected_tool} not found in registered tools"
            )

    @pytest.mark.asyncio
    async def test_tool_execution_via_get_tool(self, mock_scraper_result):
        """Test tool execution through get_tool method."""
        # Mock the web_scraper.scrape_url method
        with patch.object(
            web_scraper, "scrape_url", new_callable=AsyncMock
        ) as mock_scrape:
            mock_scrape.return_value = mock_scraper_result

            # Get the tool by name
            scrape_tool = await app.get_tool("scrape_webpage")

            assert scrape_tool is not None, "scrape_webpage tool not found"

            # Test tool execution via the tool handler
            # FunctionTool has 'fn' attribute and 'run' method
            assert hasattr(scrape_tool, "fn") or hasattr(scrape_tool, "run")
            assert scrape_tool.name == "scrape_webpage"

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
            assert tool.description is not None
            assert len(tool.description) > 0
            assert tool.name == tool_name

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
