"""反检测抓取模块，提供基于 Selenium 和 Playwright 的隐身抓取能力。"""

import asyncio
import random
from typing import Dict, Any, Optional
import logging

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from fake_useragent import UserAgent
import undetected_chromedriver as uc
from playwright.async_api import async_playwright

from .browser_utils import build_chrome_options
from .config import settings
from .content_extraction import (
    extract_default_content,
    extract_default_content_playwright,
    extract_with_playwright_config,
    extract_with_selenium_config,
)

logger = logging.getLogger(__name__)


class AntiDetectionScraper:
    """Advanced scraper with anti-detection capabilities."""

    def __init__(self) -> None:
        self.ua = UserAgent()
        self.driver = None
        self.page = None
        self.browser = None
        self.context = None
        self.playwright = None

    async def _get_undetected_chrome_driver(self) -> webdriver.Chrome:
        """Get undetected Chrome driver for anti-bot detection."""
        user_agent = self.ua.random if settings.use_random_user_agent else None
        options = build_chrome_options(
            headless=settings.browser_headless,
            stealth=True,
            user_agent=user_agent,
        )

        # Use undetected-chromedriver
        driver = uc.Chrome(options=options)

        # Execute stealth scripts
        driver.execute_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )

        return driver

    async def _setup_playwright_browser(self) -> None:
        """Setup Playwright browser for advanced scraping."""
        self.playwright = await async_playwright().start()

        # Launch browser with stealth settings
        self.browser = await self.playwright.chromium.launch(
            headless=settings.browser_headless,
            args=[
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--disable-extensions",
                "--window-size=1920,1080",
            ],
        )

        # Create context with randomized settings
        context_options = {
            "viewport": {"width": 1920, "height": 1080},
            "user_agent": self.ua.random
            if settings.use_random_user_agent
            else settings.default_user_agent,
        }

        if settings.use_proxy and settings.proxy_url:
            context_options["proxy"] = {"server": settings.proxy_url}

        self.context = await self.browser.new_context(**context_options)

        # Add stealth scripts
        await self.context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
            });

            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5],
            });

            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en'],
            });
        """)

        self.page = await self.context.new_page()

    async def scrape_with_stealth(
        self,
        url: str,
        method: str = "selenium",
        extract_config: Optional[Dict[str, Any]] = None,
        wait_for_element: Optional[str] = None,
        scroll_page: bool = False,
    ) -> Dict[str, Any]:
        """
        Scrape using stealth techniques to avoid detection.

        Args:
            url: URL to scrape
            method: "selenium" or "playwright"
            extract_config: Data extraction configuration
            wait_for_element: Element to wait for
            scroll_page: Whether to scroll the page to load dynamic content
        """
        try:
            if method == "selenium":
                return await self._scrape_with_selenium_stealth(
                    url, extract_config, wait_for_element, scroll_page
                )
            elif method == "playwright":
                return await self._scrape_with_playwright_stealth(
                    url, extract_config, wait_for_element, scroll_page
                )
            else:
                raise ValueError(f"Unknown stealth method: {method}")

        except Exception as e:
            logger.error(f"Stealth scraping failed for {url}: {str(e)}")
            return {"error": str(e), "url": url}

        finally:
            await self.cleanup()

    async def _scrape_with_selenium_stealth(
        self,
        url: str,
        extract_config: Optional[Dict[str, Any]],
        wait_for_element: Optional[str],
        scroll_page: bool,
    ) -> Dict[str, Any]:
        """Scrape using Selenium with stealth techniques."""
        self.driver = await self._get_undetected_chrome_driver()

        # Random delay before navigation
        await asyncio.sleep(random.uniform(1, 3))  # nosec B311

        self.driver.get(url)

        # Wait for page load
        await asyncio.sleep(random.uniform(2, 4))  # nosec B311

        # Wait for specific element if specified
        if wait_for_element:
            try:
                WebDriverWait(self.driver, settings.browser_timeout).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, wait_for_element))
                )
            except TimeoutException:
                logger.warning(f"Timeout waiting for element: {wait_for_element}")

        # Scroll page to load dynamic content
        if scroll_page:
            await self._scroll_page_selenium()

        # Human-like mouse movements
        await self._simulate_human_behavior_selenium()

        # Extract data
        result = await self._extract_data_selenium(extract_config)
        result["url"] = self.driver.current_url

        return result

    async def _scrape_with_playwright_stealth(
        self,
        url: str,
        extract_config: Optional[Dict[str, Any]],
        wait_for_element: Optional[str],
        scroll_page: bool,
    ) -> Dict[str, Any]:
        """Scrape using Playwright with stealth techniques."""
        await self._setup_playwright_browser()

        # Random delay before navigation
        await asyncio.sleep(random.uniform(1, 3))  # nosec B311

        # Navigate with random timeout
        await self.page.goto(url, timeout=60000, wait_until="domcontentloaded")

        # Wait for specific element if specified
        if wait_for_element:
            try:
                await self.page.wait_for_selector(
                    wait_for_element, timeout=settings.browser_timeout * 1000
                )
            except Exception:
                logger.warning(f"Timeout waiting for element: {wait_for_element}")

        # Scroll page to load dynamic content
        if scroll_page:
            await self._scroll_page_playwright()

        # Human-like interactions
        await self._simulate_human_behavior_playwright()

        # Extract data
        result = await self._extract_data_playwright(extract_config)
        result["url"] = self.page.url

        return result

    async def _scroll_page_selenium(self) -> None:
        """Scroll page naturally to trigger dynamic content loading."""
        total_height = self.driver.execute_script("return document.body.scrollHeight")
        current_height = 0

        while current_height < total_height:
            # Scroll down by a random amount
            scroll_amount = random.randint(200, 600)  # nosec B311
            self.driver.execute_script(f"window.scrollBy(0, {scroll_amount});")

            # Random delay between scrolls
            await asyncio.sleep(random.uniform(0.5, 2.0))  # nosec B311

            current_height += scroll_amount

            # Check if page height changed (lazy loading)
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            if new_height > total_height:
                total_height = new_height

    async def _scroll_page_playwright(self) -> None:
        """Scroll page naturally using Playwright."""
        await self.page.evaluate("""
            new Promise((resolve) => {
                let totalHeight = 0;
                const distance = 100;
                const timer = setInterval(() => {
                    const scrollHeight = document.body.scrollHeight;
                    window.scrollBy(0, distance);
                    totalHeight += distance;

                    if(totalHeight >= scrollHeight){
                        clearInterval(timer);
                        resolve();
                    }
                }, 100);
            })
        """)

    async def _simulate_human_behavior_selenium(self) -> None:
        """Simulate human-like behavior to avoid detection."""
        try:
            # Random mouse movements
            actions = ActionChains(self.driver)

            # Move mouse to random positions
            for _ in range(random.randint(2, 5)):  # nosec B311
                x = random.randint(100, 800)  # nosec B311
                y = random.randint(100, 600)  # nosec B311
                actions.move_by_offset(x, y)
                await asyncio.sleep(random.uniform(0.1, 0.5))  # nosec B311

            actions.perform()

            # Random delays
            await asyncio.sleep(random.uniform(1, 3))  # nosec B311

        except Exception as e:
            logger.debug(f"Error simulating human behavior: {str(e)}")

    async def _simulate_human_behavior_playwright(self) -> None:
        """Simulate human-like behavior using Playwright."""
        try:
            # Random mouse movements
            for _ in range(random.randint(2, 4)):  # nosec B311
                x = random.randint(100, 800)  # nosec B311
                y = random.randint(100, 600)  # nosec B311
                await self.page.mouse.move(x, y)
                await asyncio.sleep(random.uniform(0.1, 0.5))  # nosec B311

            # Random delays
            await asyncio.sleep(random.uniform(1, 2))  # nosec B311

        except Exception as e:
            logger.debug(f"Error simulating human behavior: {str(e)}")

    async def _extract_data_selenium(
        self, extract_config: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Extract data using Selenium."""
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(self.driver.page_source, "html.parser")

        result = {"title": self.driver.title, "content": {}}

        # Get meta description
        try:
            meta_desc = self.driver.find_element(
                By.CSS_SELECTOR, "meta[name='description']"
            )
            result["meta_description"] = meta_desc.get_attribute("content")
        except NoSuchElementException:
            result["meta_description"] = None

        if extract_config:
            result["content"] = extract_with_selenium_config(
                self.driver, extract_config
            )
        else:
            default = extract_default_content(soup, self.driver.current_url)
            result["content"]["text"] = default["text"]
            result["content"]["links"] = default["links"]

        return result

    async def _extract_data_playwright(
        self, extract_config: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Extract data using Playwright."""
        result = {"title": await self.page.title(), "content": {}}

        # Get meta description
        try:
            meta_desc = await self.page.get_attribute(
                "meta[name='description']", "content"
            )
            result["meta_description"] = meta_desc
        except Exception:
            result["meta_description"] = None

        if extract_config:
            result["content"] = await extract_with_playwright_config(
                self.page, extract_config
            )
        else:
            default = await extract_default_content_playwright(self.page)
            result["content"]["text"] = default["text"]
            result["content"]["links"] = default["links"]

        return result

    async def cleanup(self) -> None:
        """Clean up resources."""
        if self.driver:
            self.driver.quit()
            self.driver = None

        if self.page:
            await self.page.close()
            self.page = None

        if self.context:
            await self.context.close()
            self.context = None

        if self.browser:
            await self.browser.close()
            self.browser = None

        if self.playwright:
            await self.playwright.stop()
            self.playwright = None
