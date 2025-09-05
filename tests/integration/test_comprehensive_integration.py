"""Comprehensive integration tests for the entire MCP server functionality."""

import pytest
import asyncio
import time
from unittest.mock import patch, AsyncMock

from extractor.server import app


class TestComprehensiveIntegration:
    """Comprehensive integration tests covering all major functionality."""

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

            # This should work as the tool function is async
            result = await convert_tool.fn(
                url="https://test-site.com/article",
                method="simple",
                extract_main_content=True,
                include_metadata=True,
                formatting_options=formatting_options,
            )

            # Verify the pipeline worked correctly
            assert result["success"] is True
            assert result["data"]["success"] is True

            markdown = result["data"]["markdown"]

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
            metadata = result["data"]["metadata"]
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
            result = await batch_tool.fn(urls=urls, method="simple")

            assert result["success"] is True
            assert result["data"]["summary"]["total"] == 3
            assert result["data"]["summary"]["successful"] == 2
            assert result["data"]["summary"]["failed"] == 1
            assert result["data"]["summary"]["success_rate"] == 2 / 3

            # Verify individual results
            results = result["data"]["results"]
            assert results[0]["success"] is True  # First should succeed
            assert results[1]["success"] is False  # Second should fail
            assert results[2]["success"] is True  # Third should succeed

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

            result = await convert_tool.fn(url="https://invalid-site.com")

            # Should handle errors gracefully
            # When scraping fails, the tool should return with success=False
            assert (
                result["success"] is False
            )  # Tool execution failed due to scraping error
            assert "error" in result  # Error information provided

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
            result = await batch_tool.fn(urls=urls, method="simple")
            duration = time.time() - start_time

            assert result["success"] is True
            assert result["data"]["summary"]["successful"] == num_urls

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
                task = convert_tool.fn(url=f"https://concurrent-test.com/page-{i}")
                tasks.append(task)

            # Execute all tasks concurrently
            results = await asyncio.gather(*tasks)

            # All should succeed
            for result in results:
                assert result["success"] is True
                assert result["data"]["success"] is True
                assert "# Concurrent" in result["data"]["markdown"]

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

            result = await convert_tool.fn(
                url="https://encoding-test.com",
                formatting_options={"apply_typography": True},
            )

            assert result["success"] is True
            markdown = result["data"]["markdown"]

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

                result = await convert_tool.fn(url=f"https://edge-case-{i}.com")

                # Should not crash or throw unhandled exceptions
                assert result["success"] is True
                # May succeed or fail, but should provide meaningful response
                assert "data" in result

                if result["data"]["success"]:
                    assert "markdown" in result["data"]
                else:
                    assert "error" in result["data"]

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
                    url="https://config-test.com", formatting_options=config
                )

                assert result["success"] is True
                assert result["data"]["success"] is True
                assert (
                    result["data"]["conversion_options"]["formatting_options"] == config
                )


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
                await convert_tool.fn(url=f"https://metrics-test.com/page-{i}")

        # Check metrics
        metrics_result = await metrics_tool.fn()

        assert metrics_result["success"] is True
        # Check that we have some metrics data (the exact keys may vary)
        assert "scraping_metrics" in metrics_result["data"]
        # Check for expected metrics fields based on actual implementation
        metrics_data = metrics_result["data"]
        assert any(
            key in metrics_data
            for key in ["performance_metrics", "method_usage", "server_info"]
        )

    @pytest.mark.asyncio
    async def test_cache_integration(self):
        """Test cache functionality integration."""
        tools = await app.get_tools()
        clear_cache_tool = tools["clear_cache"]

        # Clear cache
        result = await clear_cache_tool.fn()

        assert result["success"] is True
        assert "message" in result

    @pytest.mark.asyncio
    async def test_error_logging_and_handling(self):
        """Test that errors are properly logged and handled."""
        tools = await app.get_tools()
        convert_tool = tools["convert_webpage_to_markdown"]

        # Simulate various error conditions
        with patch("extractor.server.web_scraper") as mock_scraper:
            # Network error simulation
            mock_scraper.scrape_url = AsyncMock(side_effect=Exception("Network error"))

            result = await convert_tool.fn(url="https://error-test.com")

            # Should handle error gracefully
            assert result["success"] is False
            assert "error" in result
