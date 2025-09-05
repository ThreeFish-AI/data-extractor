"""Simplified unit tests for WebScraper core functionality."""

import pytest
from bs4 import BeautifulSoup

from extractor.scraper import WebScraper


class TestBasicScraping:
    """Test basic scraping functionality."""

    def test_html_parsing(self, sample_html):
        """Test HTML parsing with BeautifulSoup."""
        soup = BeautifulSoup(sample_html, "html.parser")

        title = soup.find("title")
        assert title.get_text() == "Test Page"

        links = soup.find_all("a")
        assert len(links) >= 1
        assert links[0].get("href") == "https://example.com"

    def test_css_selector_extraction(self, sample_html):
        """Test CSS selector based extraction."""
        soup = BeautifulSoup(sample_html, "html.parser")

        # Test simple selector
        heading = soup.select_one("h1")
        assert heading.get_text() == "Test Heading"

        # Test multiple elements
        paragraphs = soup.select(".content p")
        assert len(paragraphs) == 2

        # Test attribute extraction
        link_href = soup.select_one("a")["href"]
        assert link_href == "https://example.com"


class TestWebScraperBasic:
    """Test basic WebScraper functionality."""

    @pytest.fixture
    def scraper(self):
        """WebScraper instance."""
        return WebScraper()

    def test_scraper_initialization(self, scraper):
        """Test WebScraper initializes correctly."""
        assert scraper is not None
        assert hasattr(scraper, "scrapy_wrapper")
        assert hasattr(scraper, "selenium_scraper")
        assert hasattr(scraper, "simple_scraper")

    def test_scrape_url_method_exists(self, scraper):
        """Test scrape_url method exists."""
        # Test that the method exists
        assert hasattr(scraper, "scrape_url")
        assert callable(getattr(scraper, "scrape_url"))

    @pytest.mark.asyncio
    async def test_scrape_multiple_urls_method_exists(self, scraper):
        """Test scrape_multiple_urls method exists."""
        # Test that the method exists
        assert hasattr(scraper, "scrape_multiple_urls")
        assert callable(getattr(scraper, "scrape_multiple_urls"))


class TestHTMLExtraction:
    """Test HTML content extraction."""

    def test_title_extraction(self, sample_html):
        """Test title extraction from HTML."""
        soup = BeautifulSoup(sample_html, "html.parser")
        title = soup.find("title")
        assert title is not None
        assert title.get_text().strip() == "Test Page"

    def test_link_extraction(self, sample_html):
        """Test link extraction from HTML."""
        soup = BeautifulSoup(sample_html, "html.parser")
        links = soup.find_all("a")
        assert len(links) > 0

        # Test first link
        first_link = links[0]
        assert first_link.get("href") == "https://example.com"
        assert first_link.get_text() == "Test Link"

    def test_form_detection(self, sample_html):
        """Test form detection in HTML."""
        soup = BeautifulSoup(sample_html, "html.parser")
        forms = soup.find_all("form")
        assert len(forms) > 0

        # Test form has inputs
        form = forms[0]
        inputs = form.find_all("input")
        assert len(inputs) >= 2  # username and password

    def test_list_extraction(self, sample_html):
        """Test list item extraction."""
        soup = BeautifulSoup(sample_html, "html.parser")
        list_items = soup.select(".list li")
        assert len(list_items) == 3

        item_texts = [item.get_text() for item in list_items]
        assert "Item 1" in item_texts
        assert "Item 2" in item_texts
        assert "Item 3" in item_texts
