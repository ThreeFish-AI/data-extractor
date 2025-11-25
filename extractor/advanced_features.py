"""Advanced scraping features including anti-detection and form handling."""

import asyncio
import random
from typing import Dict, Any, Optional
from urllib.parse import urljoin
import logging

from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from fake_useragent import UserAgent
import undetected_chromedriver as uc
from playwright.async_api import async_playwright

from .config import settings

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
        options = ChromeOptions()

        if settings.browser_headless:
            options.add_argument("--headless")

        # Anti-detection options
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-plugins")
        options.add_argument("--disable-images")
        options.add_argument("--disable-javascript")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--start-maximized")

        # Randomize user agent
        if settings.use_random_user_agent:
            options.add_argument(f"--user-agent={self.ua.random}")

        # Additional stealth options
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)
        options.add_argument("--disable-blink-features=AutomationControlled")

        # Proxy support
        if settings.use_proxy and settings.proxy_url:
            options.add_argument(f"--proxy-server={settings.proxy_url}")

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
            for key, config in extract_config.items():
                try:
                    if isinstance(config, str):
                        elements = self.driver.find_elements(By.CSS_SELECTOR, config)
                        result["content"][key] = [elem.text for elem in elements]
                    elif isinstance(config, dict):
                        selector = config.get("selector")
                        attr = config.get("attr")
                        multiple = config.get("multiple", False)

                        if multiple:
                            elements = self.driver.find_elements(
                                By.CSS_SELECTOR, selector
                            )
                            if attr == "text":
                                extracted = [elem.text for elem in elements]
                            elif attr:
                                extracted = [
                                    elem.get_attribute(attr) for elem in elements
                                ]
                            else:
                                extracted = [
                                    elem.get_attribute("outerHTML") for elem in elements
                                ]
                        else:
                            try:
                                element = self.driver.find_element(
                                    By.CSS_SELECTOR, selector
                                )
                                if attr == "text":
                                    extracted = element.text
                                elif attr:
                                    extracted = element.get_attribute(attr)
                                else:
                                    extracted = element.get_attribute("outerHTML")
                            except Exception:
                                extracted = None

                        result["content"][key] = extracted
                except Exception as e:
                    logger.warning(f"Failed to extract {key}: {str(e)}")
                    result["content"][key] = None
        else:
            # Default extraction
            result["content"]["text"] = soup.get_text(strip=True)
            result["content"]["links"] = [
                {
                    "url": urljoin(self.driver.current_url, str(a.get("href", ""))),
                    "text": a.get_text(strip=True),
                }
                for a in soup.find_all("a", href=True)
                if hasattr(a, "get")
            ]

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
            for key, config in extract_config.items():
                try:
                    if isinstance(config, str):
                        elements = await self.page.query_selector_all(config)
                        texts = []
                        for element in elements:
                            text = await element.text_content()
                            texts.append(text)
                        result["content"][key] = texts
                    elif isinstance(config, dict):
                        selector = config.get("selector")
                        attr = config.get("attr")
                        multiple = config.get("multiple", False)

                        if multiple:
                            elements = await self.page.query_selector_all(selector)
                            extracted = []
                            for element in elements:
                                if attr == "text":
                                    value = await element.text_content()
                                elif attr:
                                    value = await element.get_attribute(attr)
                                else:
                                    value = await element.inner_html()
                                extracted.append(value)
                        else:
                            element = await self.page.query_selector(selector)
                            if element:
                                if attr == "text":
                                    extracted = await element.text_content()
                                elif attr:
                                    extracted = await element.get_attribute(attr)
                                else:
                                    extracted = await element.inner_html()
                            else:
                                extracted = None

                        result["content"][key] = extracted
                except Exception as e:
                    logger.warning(f"Failed to extract {key}: {str(e)}")
                    result["content"][key] = None
        else:
            # Default extraction
            result["content"]["text"] = await self.page.text_content("body")

            # Extract links
            links = []
            link_elements = await self.page.query_selector_all("a[href]")
            for link_elem in link_elements:
                href = await link_elem.get_attribute("href")
                text = await link_elem.text_content()
                if href:
                    links.append(
                        {
                            "url": urljoin(self.page.url, href),
                            "text": text.strip() if text else "",
                        }
                    )
            result["content"]["links"] = links

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


class FormHandler:
    """Handle form interactions and submissions."""

    def __init__(self, driver_or_page: Any) -> None:
        self.driver_or_page = driver_or_page
        # Simple check for Playwright page
        self.is_playwright = hasattr(driver_or_page, "fill")

    async def fill_form(
        self,
        form_data: Dict[str, Any],
        submit: bool = False,
        submit_button_selector: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Fill and optionally submit a form.

        Args:
            form_data: Dict mapping field selectors to values
            submit: Whether to submit the form
            submit_button_selector: Selector for submit button (if not using default)
        """
        try:
            results = {}

            for field_selector, value in form_data.items():
                field_result = await self._fill_field(field_selector, value)
                results[field_selector] = field_result

            if submit:
                submit_result = await self._submit_form(submit_button_selector)
                results["_submit"] = submit_result

            return {"success": True, "results": results}

        except Exception as e:
            logger.error(f"Error filling form: {str(e)}")
            return {"success": False, "error": str(e)}

    async def _fill_field(self, selector: str, value: Any) -> Dict[str, Any]:
        """Fill a single form field."""
        try:
            if self.is_playwright:
                return await self._fill_field_playwright(selector, value)
            else:
                return await self._fill_field_selenium(selector, value)

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _fill_field_selenium(self, selector: str, value: Any) -> Dict[str, Any]:
        """Fill field using Selenium."""
        try:
            element = self.driver_or_page.find_element(By.CSS_SELECTOR, selector)
            tag_name = element.tag_name.lower()
            input_type = element.get_attribute("type")

            if tag_name == "select":
                # Handle select dropdown
                select = Select(element)
                if isinstance(value, int):
                    select.select_by_index(value)
                elif str(value).isdigit():
                    select.select_by_value(str(value))
                else:
                    select.select_by_visible_text(str(value))

            elif input_type in ["checkbox", "radio"]:
                # Handle checkbox/radio
                if value and not element.is_selected():
                    element.click()
                elif not value and element.is_selected():
                    element.click()

            elif input_type == "file":
                # Handle file upload
                element.send_keys(str(value))

            else:
                # Handle text inputs
                element.clear()
                element.send_keys(str(value))

            return {"success": True, "value": value}

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _fill_field_playwright(self, selector: str, value: Any) -> Dict[str, Any]:
        """Fill field using Playwright."""
        try:
            element = await self.driver_or_page.query_selector(selector)
            if not element:
                return {"success": False, "error": "Element not found"}

            tag_name = await element.evaluate("el => el.tagName.toLowerCase()")
            input_type = await element.get_attribute("type")

            if tag_name == "select":
                # Handle select dropdown
                if isinstance(value, int):
                    await element.select_option(index=value)
                else:
                    await element.select_option(label=str(value))

            elif input_type in ["checkbox", "radio"]:
                # Handle checkbox/radio
                is_checked = await element.is_checked()
                if value and not is_checked:
                    await element.check()
                elif not value and is_checked:
                    await element.uncheck()

            elif input_type == "file":
                # Handle file upload
                await element.set_input_files(str(value))

            else:
                # Handle text inputs
                await element.fill(str(value))

            return {"success": True, "value": value}

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _submit_form(
        self, submit_button_selector: Optional[str] = None
    ) -> Dict[str, Any]:
        """Submit the form."""
        try:
            if self.is_playwright:
                return await self._submit_form_playwright(submit_button_selector)
            else:
                return await self._submit_form_selenium(submit_button_selector)

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _submit_form_selenium(
        self, submit_button_selector: Optional[str] = None
    ) -> Dict[str, Any]:
        """Submit form using Selenium."""
        try:
            if submit_button_selector:
                # Use specific submit button
                submit_button = self.driver_or_page.find_element(
                    By.CSS_SELECTOR, submit_button_selector
                )
                submit_button.click()
            else:
                # Try to find submit button automatically
                submit_selectors = [
                    "input[type='submit']",
                    "button[type='submit']",
                    "button:contains('Submit')",
                    "input[value*='Submit']",
                    "button:contains('Send')",
                ]

                for selector in submit_selectors:
                    try:
                        if "contains" in selector:
                            # Use XPath for text content
                            xpath = "//button[contains(text(), 'Submit')] | //button[contains(text(), 'Send')]"
                            submit_button = self.driver_or_page.find_element(
                                By.XPATH, xpath
                            )
                        else:
                            submit_button = self.driver_or_page.find_element(
                                By.CSS_SELECTOR, selector
                            )

                        submit_button.click()
                        break
                    except NoSuchElementException:
                        continue
                else:
                    # If no submit button found, try submitting the form directly
                    form = self.driver_or_page.find_element(By.TAG_NAME, "form")
                    form.submit()

            # Wait for page to load after submission
            await asyncio.sleep(2)

            return {"success": True, "new_url": self.driver_or_page.current_url}

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _submit_form_playwright(
        self, submit_button_selector: Optional[str] = None
    ) -> Dict[str, Any]:
        """Submit form using Playwright."""
        try:
            if submit_button_selector:
                # Use specific submit button
                await self.driver_or_page.click(submit_button_selector)
            else:
                # Try to find submit button automatically
                submit_selectors = [
                    "input[type='submit']",
                    "button[type='submit']",
                    "text=Submit",
                    "text=Send",
                ]

                for selector in submit_selectors:
                    try:
                        await self.driver_or_page.click(selector)
                        break
                    except Exception:  # nosec B112
                        # Continue trying next submit button selector
                        continue
                else:
                    # If no submit button found, press Enter on the form
                    await self.driver_or_page.keyboard.press("Enter")

            # Wait for navigation or response
            try:
                await self.driver_or_page.wait_for_load_state(
                    "networkidle", timeout=10000
                )
            except Exception:  # nosec B110
                # Ignore timeout or navigation errors - form might submit without page load
                pass

            return {"success": True, "new_url": self.driver_or_page.url}

        except Exception as e:
            return {"success": False, "error": str(e)}
