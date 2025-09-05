"""Unit tests for advanced features (anti-detection and form handling)."""

import pytest
from unittest.mock import Mock, AsyncMock, patch

from extractor.advanced_features import AntiDetectionScraper, FormHandler


class TestAntiDetectionScraper:
    """Test the AntiDetectionScraper class."""

    @pytest.fixture
    def scraper(self, test_config):
        """AntiDetectionScraper instance with test config."""
        return AntiDetectionScraper(config=test_config)

    def test_scraper_initialization(self, scraper, test_config):
        """Test AntiDetectionScraper initializes correctly."""
        assert scraper.config == test_config

    @pytest.mark.asyncio
    async def test_scrape_with_stealth_undetected_chrome(self, scraper):
        """Test stealth scraping with undetected Chrome."""
        mock_driver = Mock()
        mock_driver.page_source = "<html><body>Stealth content</body></html>"
        mock_driver.current_url = "https://example.com"

        with patch("undetected_chromedriver.Chrome") as mock_chrome:
            mock_chrome.return_value = mock_driver

            result = await scraper.scrape_with_stealth(
                "https://example.com", method="undetected_chrome"
            )

            assert result["url"] == "https://example.com"
            assert "Stealth content" in result["content"]
            assert result["method"] == "undetected_chrome"

    @pytest.mark.asyncio
    async def test_scrape_with_stealth_playwright(self, scraper):
        """Test stealth scraping with Playwright."""
        mock_page = AsyncMock()
        mock_page.content.return_value = "<html><body>Playwright content</body></html>"
        mock_page.url = "https://example.com"

        mock_context = AsyncMock()
        mock_context.new_page.return_value = mock_page

        mock_browser = AsyncMock()
        mock_browser.new_context.return_value = mock_context

        with patch("playwright.async_api.async_playwright") as mock_playwright:
            mock_playwright_instance = AsyncMock()
            mock_playwright_instance.chromium.launch.return_value = mock_browser
            mock_playwright.return_value.__aenter__.return_value = (
                mock_playwright_instance
            )

            result = await scraper.scrape_with_stealth(
                "https://example.com", method="playwright"
            )

            assert result["url"] == "https://example.com"
            assert "Playwright content" in result["content"]
            assert result["method"] == "playwright"

    @pytest.mark.asyncio
    async def test_scrape_with_stealth_error_handling(self, scraper):
        """Test error handling in stealth scraping."""
        with patch("undetected_chromedriver.Chrome") as mock_chrome:
            mock_chrome.side_effect = Exception("Browser launch failed")

            result = await scraper.scrape_with_stealth(
                "https://example.com", method="undetected_chrome"
            )

            assert "error" in result
            assert "Browser launch failed" in result["error"]

    def test_get_stealth_headers(self, scraper):
        """Test stealth headers generation."""
        headers = scraper._get_stealth_headers()

        assert "User-Agent" in headers
        assert "Accept" in headers
        assert "Accept-Language" in headers
        assert "Accept-Encoding" in headers

    @pytest.mark.asyncio
    async def test_simulate_human_behavior(self, scraper):
        """Test human behavior simulation."""
        mock_driver = Mock()

        # Test that the method completes without error
        await scraper._simulate_human_behavior(mock_driver)

        # Verify some interactions occurred (scroll, random delays)
        assert mock_driver.execute_script.called

    def test_apply_stealth_settings_chrome(self, scraper):
        """Test Chrome stealth settings application."""
        mock_driver = Mock()

        scraper._apply_stealth_settings(mock_driver, "undetected_chrome")

        # Verify stealth scripts were executed
        assert mock_driver.execute_cdp_cmd.called

    def test_apply_stealth_settings_playwright(self, scraper):
        """Test Playwright stealth settings application."""
        mock_page = Mock()

        scraper._apply_stealth_settings(mock_page, "playwright")

        # Verify stealth methods were called
        assert mock_page.add_init_script.called


class TestFormHandler:
    """Test the FormHandler class."""

    @pytest.fixture
    def form_handler(self, test_config):
        """FormHandler instance with test config."""
        return FormHandler(config=test_config)

    def test_form_handler_initialization(self, form_handler, test_config):
        """Test FormHandler initializes correctly."""
        assert form_handler.config == test_config

    @pytest.mark.asyncio
    async def test_fill_and_submit_form_basic(self, form_handler):
        """Test basic form filling and submission."""
        mock_driver = Mock()
        mock_element = Mock()
        mock_driver.find_element.return_value = mock_element

        form_data = {"username": "testuser", "password": "testpass"}

        with patch("selenium.webdriver.Chrome") as mock_chrome:
            mock_chrome.return_value = mock_driver

            result = await form_handler.fill_and_submit_form(
                "https://example.com",
                form_data,
                submit_button_selector="button[type=submit]",
            )

            assert result["success"] is True
            assert result["url"] == "https://example.com"

    @pytest.mark.asyncio
    async def test_fill_and_submit_form_with_wait(self, form_handler):
        """Test form submission with element waiting."""
        mock_driver = Mock()
        mock_element = Mock()
        mock_driver.find_element.return_value = mock_element

        form_data = {"email": "test@example.com"}

        with (
            patch("selenium.webdriver.Chrome") as mock_chrome,
            patch("selenium.webdriver.support.ui.WebDriverWait") as mock_wait,
        ):
            mock_chrome.return_value = mock_driver
            mock_wait.return_value.until.return_value = mock_element

            result = await form_handler.fill_and_submit_form(
                "https://example.com", form_data, wait_for_element=".success-message"
            )

            assert result["success"] is True

    @pytest.mark.asyncio
    async def test_fill_form_field_input(self, form_handler):
        """Test filling input form fields."""
        mock_driver = Mock()
        mock_element = Mock()
        mock_element.tag_name = "input"
        mock_element.get_attribute.return_value = "text"

        await form_handler._fill_form_field(
            mock_driver, "username", "testuser", mock_element
        )

        mock_element.clear.assert_called_once()
        mock_element.send_keys.assert_called_once_with("testuser")

    @pytest.mark.asyncio
    async def test_fill_form_field_select(self, form_handler):
        """Test filling select form fields."""
        mock_driver = Mock()
        mock_element = Mock()
        mock_element.tag_name = "select"

        mock_select = Mock()
        with patch("selenium.webdriver.support.ui.Select") as mock_select_class:
            mock_select_class.return_value = mock_select

            await form_handler._fill_form_field(
                mock_driver, "country", "US", mock_element
            )

            mock_select.select_by_visible_text.assert_called_once_with("US")

    @pytest.mark.asyncio
    async def test_fill_form_field_checkbox(self, form_handler):
        """Test filling checkbox form fields."""
        mock_driver = Mock()
        mock_element = Mock()
        mock_element.tag_name = "input"
        mock_element.get_attribute.return_value = "checkbox"
        mock_element.is_selected.return_value = False

        await form_handler._fill_form_field(mock_driver, "agree", True, mock_element)

        mock_element.click.assert_called_once()

    @pytest.mark.asyncio
    async def test_submit_form_by_button(self, form_handler):
        """Test form submission by button selector."""
        mock_driver = Mock()
        mock_button = Mock()
        mock_driver.find_element.return_value = mock_button

        await form_handler._submit_form(mock_driver, "button[type=submit]", None)

        mock_button.click.assert_called_once()

    @pytest.mark.asyncio
    async def test_submit_form_by_enter(self, form_handler):
        """Test form submission by Enter key."""
        from selenium.webdriver.common.keys import Keys

        mock_driver = Mock()
        mock_element = Mock()

        await form_handler._submit_form(mock_driver, None, mock_element)

        mock_element.send_keys.assert_called_once_with(Keys.RETURN)

    @pytest.mark.asyncio
    async def test_form_handling_error_recovery(self, form_handler):
        """Test error handling and recovery in form operations."""
        mock_driver = Mock()
        mock_driver.find_element.side_effect = Exception("Element not found")

        with patch("selenium.webdriver.Chrome") as mock_chrome:
            mock_chrome.return_value = mock_driver

            result = await form_handler.fill_and_submit_form(
                "https://example.com",
                {"username": "test"},
                submit_button_selector="button",
            )

            assert result["success"] is False
            assert "error" in result
            assert "Element not found" in result["error"]
