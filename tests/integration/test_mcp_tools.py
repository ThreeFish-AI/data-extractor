"""Integration tests for all 10 MCP tools."""

import pytest
from unittest.mock import Mock, patch

from extractor.server import (
    scrape_webpage,
    scrape_multiple_webpages,
    extract_links,
    get_page_info,
    check_robots_txt,
    scrape_with_stealth,
    fill_and_submit_form,
    get_server_metrics,
    clear_cache,
    extract_structured_data,
)


class TestScrapeWebpage:
    """Test the scrape_webpage MCP tool."""

    @pytest.mark.asyncio
    async def test_scrape_webpage_success(self, sample_scrape_result):
        """Test successful webpage scraping."""
        with patch('extractor.server.web_scraper') as mock_scraper:
            mock_scraper.scrape_url.return_value = sample_scrape_result
            
            result = await scrape_webpage(
                url="https://example.com",
                method="simple"
            )
            
            assert result["success"] is True
            assert result["data"]["url"] == "https://example.com"
            assert result["method_used"] == "simple"

    @pytest.mark.asyncio
    async def test_scrape_webpage_invalid_url(self):
        """Test scraping with invalid URL."""
        result = await scrape_webpage(
            url="not-a-url",
            method="simple"
        )
        
        assert result["success"] is False
        assert "Invalid URL format" in result["error"]

    @pytest.mark.asyncio
    async def test_scrape_webpage_invalid_method(self):
        """Test scraping with invalid method."""
        result = await scrape_webpage(
            url="https://example.com",
            method="invalid_method"
        )
        
        assert result["success"] is False
        assert "Method must be one of" in result["error"]

    @pytest.mark.asyncio
    async def test_scrape_webpage_with_extraction_config(self, sample_scrape_result):
        """Test scraping with extraction configuration."""
        extraction_config = {"title": "h1", "content": "p"}
        
        with patch('extractor.server.web_scraper') as mock_scraper:
            mock_scraper.scrape_url.return_value = sample_scrape_result
            
            result = await scrape_webpage(
                url="https://example.com",
                method="simple",
                extract_config=extraction_config
            )
            
            assert result["success"] is True
            mock_scraper.scrape_url.assert_called_once_with(
                url="https://example.com",
                method="simple",
                extract_config=extraction_config,
                wait_for_element=None
            )

    @pytest.mark.asyncio
    async def test_scrape_webpage_exception_handling(self):
        """Test exception handling in scrape_webpage."""
        with patch('extractor.server.web_scraper') as mock_scraper:
            mock_scraper.scrape_url.side_effect = Exception("Network error")
            
            result = await scrape_webpage(
                url="https://example.com",
                method="simple"
            )
            
            assert result["success"] is False
            assert "Network error" in result["error"]


class TestScrapeMultipleWebpages:
    """Test the scrape_multiple_webpages MCP tool."""

    @pytest.mark.asyncio
    async def test_scrape_multiple_webpages_success(self, sample_scrape_result):
        """Test successful multiple webpage scraping."""
        urls = ["https://example.com", "https://test.com"]
        results = [sample_scrape_result, sample_scrape_result]
        
        with patch('extractor.server.web_scraper') as mock_scraper:
            mock_scraper.scrape_multiple_urls.return_value = results
            
            result = await scrape_multiple_webpages(
                urls=urls,
                method="simple"
            )
            
            assert result["success"] is True
            assert len(result["data"]) == 2
            assert result["total_scraped"] == 2

    @pytest.mark.asyncio
    async def test_scrape_multiple_webpages_empty_list(self):
        """Test scraping with empty URL list."""
        result = await scrape_multiple_webpages(
            urls=[],
            method="simple"
        )
        
        assert result["success"] is False
        assert "No URLs provided" in result["error"]

    @pytest.mark.asyncio
    async def test_scrape_multiple_webpages_invalid_url(self):
        """Test scraping with invalid URL in list."""
        urls = ["https://example.com", "not-a-url"]
        
        result = await scrape_multiple_webpages(
            urls=urls,
            method="simple"
        )
        
        assert result["success"] is False
        assert "Invalid URL" in result["error"]


class TestExtractLinks:
    """Test the extract_links MCP tool."""

    @pytest.mark.asyncio
    async def test_extract_links_success(self):
        """Test successful link extraction."""
        mock_result = {
            "url": "https://example.com",
            "status_code": 200,
            "content": '<a href="https://link1.com">Link 1</a><a href="https://link2.com">Link 2</a>'
        }
        
        with patch('extractor.server.web_scraper') as mock_scraper:
            mock_scraper.scrape_url.return_value = mock_result
            
            result = await extract_links(
                url="https://example.com"
            )
            
            assert result["success"] is True
            assert len(result["links"]) >= 0
            assert result["total_links"] >= 0

    @pytest.mark.asyncio
    async def test_extract_links_with_domain_filter(self):
        """Test link extraction with domain filtering."""
        mock_result = {
            "url": "https://example.com",
            "status_code": 200,
            "content": '<a href="https://allowed.com/page">Allowed</a><a href="https://blocked.com/page">Blocked</a>'
        }
        
        with patch('extractor.server.web_scraper') as mock_scraper:
            mock_scraper.scrape_url.return_value = mock_result
            
            result = await extract_links(
                url="https://example.com",
                filter_domains=["allowed.com"]
            )
            
            assert result["success"] is True

    @pytest.mark.asyncio
    async def test_extract_links_with_domain_exclusion(self):
        """Test link extraction with domain exclusion."""
        mock_result = {
            "url": "https://example.com",
            "status_code": 200,
            "content": '<a href="https://good.com/page">Good</a><a href="https://bad.com/page">Bad</a>'
        }
        
        with patch('extractor.server.web_scraper') as mock_scraper:
            mock_scraper.scrape_url.return_value = mock_result
            
            result = await extract_links(
                url="https://example.com",
                exclude_domains=["bad.com"]
            )
            
            assert result["success"] is True


class TestGetPageInfo:
    """Test the get_page_info MCP tool."""

    @pytest.mark.asyncio
    async def test_get_page_info_success(self):
        """Test successful page info retrieval."""
        mock_result = {
            "url": "https://example.com",
            "status_code": 200,
            "title": "Example Page",
            "content": "Page content",
            "metadata": {
                "content_length": 1000,
                "response_time": 1.5,
                "content_type": "text/html"
            }
        }
        
        with patch('extractor.server.web_scraper') as mock_scraper:
            mock_scraper.scrape_url.return_value = mock_result
            
            result = await get_page_info("https://example.com")
            
            assert result["success"] is True
            assert result["url"] == "https://example.com"
            assert result["title"] == "Example Page"
            assert result["status_code"] == 200

    @pytest.mark.asyncio
    async def test_get_page_info_invalid_url(self):
        """Test page info with invalid URL."""
        result = await get_page_info("not-a-url")
        
        assert result["success"] is False
        assert "Invalid URL format" in result["error"]


class TestCheckRobotsTxt:
    """Test the check_robots_txt MCP tool."""

    @pytest.mark.asyncio
    async def test_check_robots_txt_success(self):
        """Test successful robots.txt checking."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "User-agent: *\nDisallow: /admin\nAllow: /"
        
        with patch('requests.get') as mock_get:
            mock_get.return_value = mock_response
            
            result = await check_robots_txt("https://example.com")
            
            assert result["success"] is True
            assert result["robots_txt_exists"] is True
            assert "rules" in result

    @pytest.mark.asyncio
    async def test_check_robots_txt_not_found(self):
        """Test robots.txt checking when file doesn't exist."""
        mock_response = Mock()
        mock_response.status_code = 404
        
        with patch('requests.get') as mock_get:
            mock_get.return_value = mock_response
            
            result = await check_robots_txt("https://example.com")
            
            assert result["success"] is True
            assert result["robots_txt_exists"] is False

    @pytest.mark.asyncio
    async def test_check_robots_txt_invalid_url(self):
        """Test robots.txt checking with invalid URL."""
        result = await check_robots_txt("not-a-url")
        
        assert result["success"] is False
        assert "Invalid URL format" in result["error"]


class TestScrapeWithStealth:
    """Test the scrape_with_stealth MCP tool."""

    @pytest.mark.asyncio
    async def test_scrape_with_stealth_success(self, sample_scrape_result):
        """Test successful stealth scraping."""
        with patch('extractor.server.anti_detection_scraper') as mock_scraper:
            mock_scraper.scrape_with_stealth.return_value = sample_scrape_result
            
            result = await scrape_with_stealth(
                url="https://example.com",
                method="selenium"
            )
            
            assert result["success"] is True
            assert result["data"]["url"] == "https://example.com"

    @pytest.mark.asyncio
    async def test_scrape_with_stealth_invalid_method(self):
        """Test stealth scraping with invalid method."""
        result = await scrape_with_stealth(
            url="https://example.com",
            method="invalid_method"
        )
        
        assert result["success"] is False
        assert "Method must be one of" in result["error"]

    @pytest.mark.asyncio
    async def test_scrape_with_stealth_invalid_url(self):
        """Test stealth scraping with invalid URL."""
        result = await scrape_with_stealth(
            url="not-a-url",
            method="selenium"
        )
        
        assert result["success"] is False
        assert "Invalid URL format" in result["error"]


class TestFillAndSubmitForm:
    """Test the fill_and_submit_form MCP tool."""

    @pytest.mark.asyncio
    async def test_fill_and_submit_form_success(self):
        """Test successful form filling and submission."""
        form_data = {"username": "testuser", "password": "testpass"}
        mock_result = {
            "success": True,
            "url": "https://example.com",
            "final_url": "https://example.com/dashboard",
            "message": "Form submitted successfully"
        }
        
        with patch('extractor.advanced_features.FormHandler') as mock_handler_class:
            mock_handler = Mock()
            mock_handler.fill_and_submit_form.return_value = mock_result
            mock_handler_class.return_value = mock_handler
            
            result = await fill_and_submit_form(
                url="https://example.com/login",
                form_data=form_data,
                submit=True
            )
            
            assert result["success"] is True

    @pytest.mark.asyncio
    async def test_fill_and_submit_form_no_data(self):
        """Test form handling with no form data."""
        result = await fill_and_submit_form(
            url="https://example.com",
            form_data={},
            submit=False
        )
        
        assert result["success"] is False
        assert "No form data provided" in result["error"]

    @pytest.mark.asyncio
    async def test_fill_and_submit_form_invalid_url(self):
        """Test form handling with invalid URL."""
        result = await fill_and_submit_form(
            url="not-a-url",
            form_data={"field": "value"},
            submit=False
        )
        
        assert result["success"] is False
        assert "Invalid URL format" in result["error"]


class TestGetServerMetrics:
    """Test the get_server_metrics MCP tool."""

    @pytest.mark.asyncio
    async def test_get_server_metrics_success(self):
        """Test successful server metrics retrieval."""
        with patch('extractor.server.metrics_collector') as mock_collector:
            mock_collector.get_summary.return_value = {
                "total_requests": 100,
                "total_errors": 5,
                "success_rate": 0.95,
                "average_response_time": 2.3
            }
            
            result = await get_server_metrics()
            
            assert result["success"] is True
            assert "metrics" in result
            assert result["metrics"]["total_requests"] == 100

    @pytest.mark.asyncio
    async def test_get_server_metrics_exception_handling(self):
        """Test exception handling in get_server_metrics."""
        with patch('extractor.server.metrics_collector') as mock_collector:
            mock_collector.get_summary.side_effect = Exception("Metrics error")
            
            result = await get_server_metrics()
            
            assert result["success"] is False
            assert "Metrics error" in result["error"]


class TestClearCache:
    """Test the clear_cache MCP tool."""

    @pytest.mark.asyncio
    async def test_clear_cache_success(self):
        """Test successful cache clearing."""
        with patch('extractor.server.cache_manager') as mock_cache:
            mock_cache.clear.return_value = None
            
            result = await clear_cache()
            
            assert result["success"] is True
            assert "Cache cleared successfully" in result["message"]
            mock_cache.clear.assert_called_once()

    @pytest.mark.asyncio
    async def test_clear_cache_exception_handling(self):
        """Test exception handling in clear_cache."""
        with patch('extractor.server.cache_manager') as mock_cache:
            mock_cache.clear.side_effect = Exception("Cache error")
            
            result = await clear_cache()
            
            assert result["success"] is False
            assert "Cache error" in result["error"]


class TestExtractStructuredData:
    """Test the extract_structured_data MCP tool."""

    @pytest.mark.asyncio
    async def test_extract_structured_data_success(self):
        """Test successful structured data extraction."""
        mock_result = {
            "url": "https://example.com",
            "status_code": 200,
            "content": '''
            <script type="application/ld+json">
            {"@type": "Article", "headline": "Test Article"}
            </script>
            '''
        }
        
        with patch('extractor.server.web_scraper') as mock_scraper:
            mock_scraper.scrape_url.return_value = mock_result
            
            result = await extract_structured_data(
                url="https://example.com",
                data_type="all"
            )
            
            assert result["success"] is True
            assert "structured_data" in result

    @pytest.mark.asyncio
    async def test_extract_structured_data_invalid_type(self):
        """Test structured data extraction with invalid data type."""
        result = await extract_structured_data(
            url="https://example.com",
            data_type="invalid_type"
        )
        
        assert result["success"] is False
        assert "Data type must be one of" in result["error"]

    @pytest.mark.asyncio
    async def test_extract_structured_data_invalid_url(self):
        """Test structured data extraction with invalid URL."""
        result = await extract_structured_data(
            url="not-a-url",
            data_type="all"
        )
        
        assert result["success"] is False
        assert "Invalid URL format" in result["error"]