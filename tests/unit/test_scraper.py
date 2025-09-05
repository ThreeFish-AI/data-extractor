"""Unit tests for WebScraper core functionality."""

import pytest
from unittest.mock import patch
from bs4 import BeautifulSoup

from extractor.scraper import WebScraper


class TestBasicScraping:
    """Test basic scraping functionality."""

    def test_html_parsing(self, sample_html):
        """Test HTML parsing with BeautifulSoup."""
        soup = BeautifulSoup(sample_html, 'html.parser')
        
        title = soup.find('title')
        assert title.get_text() == "Test Page"
        
        links = soup.find_all('a')
        assert len(links) >= 1
        assert links[0].get('href') == "https://example.com"

    def test_css_selector_extraction(self, sample_html):
        """Test CSS selector based extraction."""
        soup = BeautifulSoup(sample_html, 'html.parser')
        
        # Test simple selector
        heading = soup.select_one('h1')
        assert heading.get_text() == "Test Heading"
        
        # Test multiple elements
        paragraphs = soup.select('.content p')
        assert len(paragraphs) == 2
        
        # Test attribute extraction
        link_href = soup.select_one('a')['href']
        assert link_href == "https://example.com"


class TestWebScraper:
    """Test the WebScraper main class."""

    @pytest.fixture
    def scraper(self, test_config):
        """WebScraper instance with test config."""
        return WebScraper()

    def test_scraper_initialization(self, scraper):
        """Test WebScraper initializes correctly."""
        assert scraper is not None
        assert hasattr(scraper, 'scrapy_wrapper')
        assert hasattr(scraper, 'selenium_scraper')
        assert hasattr(scraper, 'simple_scraper')

    @pytest.mark.asyncio
    async def test_scrape_url_simple_method(self, scraper, mock_http_response):
        """Test scraping with simple HTTP method."""
        with patch('requests.get') as mock_get:
            mock_get.return_value = mock_http_response
            
            result = await scraper.scrape_url(
                "https://example.com",
                method="simple"
            )
            
            assert result["url"] == "https://example.com"
            assert result["status_code"] == 200
            assert "Mock Content" in result["content"]

    @pytest.mark.asyncio
    async def test_scrape_url_with_extraction(self, scraper, mock_http_response, sample_extraction_config):
        """Test scraping with data extraction."""
        with patch('requests.get') as mock_get:
            mock_get.return_value = mock_http_response
            
            result = await scraper.scrape_url(
                "https://example.com",
                method="simple",
                extract_config={"title": "title"}
            )
            
            assert result["extracted_data"]["title"] == "Mock Page"

    @pytest.mark.asyncio
    async def test_scrape_multiple_urls(self, scraper, mock_http_response):
        """Test scraping multiple URLs."""
        with patch('requests.get') as mock_get:
            mock_get.return_value = mock_http_response
            
            urls = ["https://example.com", "https://test.com"]
            results = await scraper.scrape_multiple_urls(urls, method="simple")
            
            assert len(results) == 2
            assert all(r["status_code"] == 200 for r in results)

    @pytest.mark.asyncio
    async def test_scrape_url_error_handling(self, scraper):
        """Test error handling during scraping."""
        with patch('requests.get') as mock_get:
            mock_get.side_effect = Exception("Network error")
            
            result = await scraper.scrape_url("https://example.com", method="simple")
            
            assert "error" in result
            assert "Network error" in result["error"]

    def test_extract_page_metadata(self, scraper, mock_http_response):
        """Test page metadata extraction."""
        metadata = scraper._extract_page_metadata(mock_http_response, start_time=0, end_time=1.5)
        
        assert metadata["content_length"] > 0
        assert metadata["response_time"] == 1.5
        assert metadata["final_url"] == "https://example.com"
        assert metadata["content_type"] == "text/html"

    @pytest.mark.asyncio
    async def test_scrapy_method_mock(self, scraper):
        """Test Scrapy method execution (mocked)."""
        with patch.object(scraper, '_run_scrapy_spider') as mock_spider:
            mock_spider.return_value = [{"url": "https://example.com", "content": "test"}]
            
            result = await scraper._scrape_with_scrapy("https://example.com")
            
            assert result["url"] == "https://example.com"
            assert result["content"] == "test"