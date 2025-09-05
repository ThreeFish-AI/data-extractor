"""Core scraping functionality using Scrapy and additional web drivers."""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from urllib.parse import urljoin

import scrapy
from scrapy.crawler import CrawlerRunner
from scrapy.utils.log import configure_logging
from scrapy.http import Response
from bs4 import BeautifulSoup
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from fake_useragent import UserAgent

from .config import settings

logger = logging.getLogger(__name__)


class WebScrapingSpider(scrapy.Spider):
    """Custom Scrapy spider for web scraping."""

    name = "web_scraper"

    def __init__(
        self, url: str, extract_config: Optional[Dict[str, Any]] = None, *args, **kwargs
    ) -> None:
        super().__init__(*args, **kwargs)
        self.start_urls = [url]
        self.extract_config = extract_config or {}
        self.results: List[Dict[str, Any]] = []

    def parse(self, response: Response) -> Dict[str, Any]:
        """Parse the response and extract data based on configuration."""
        result = {
            "url": response.url,
            "status_code": response.status,
            "title": response.css("title::text").get(),
            "meta_description": response.css(
                "meta[name='description']::attr(content)"
            ).get(),
            "content": {},
        }

        # Extract based on configuration
        if self.extract_config:
            for key, selector_config in self.extract_config.items():
                if isinstance(selector_config, str):
                    # Simple CSS selector
                    result["content"][key] = response.css(selector_config).getall()
                elif isinstance(selector_config, dict):
                    # Complex selector configuration
                    selector_type = selector_config.get("type", "css")
                    selector = selector_config.get("selector")
                    attr = selector_config.get("attr")
                    multiple = selector_config.get("multiple", False)

                    if selector_type == "css":
                        elements = response.css(selector)
                    elif selector_type == "xpath":
                        elements = response.xpath(selector)
                    else:
                        continue

                    if attr:
                        if attr == "text":
                            extracted = (
                                elements.css("::text").getall()
                                if multiple
                                else elements.css("::text").get()
                            )
                        else:
                            extracted = (
                                elements.css(f"::{attr}").getall()
                                if multiple
                                else elements.css(f"::{attr}").get()
                            )
                    else:
                        extracted = elements.getall() if multiple else elements.get()

                    result["content"][key] = extracted
        else:
            # Default extraction: get all text content
            result["content"]["text"] = " ".join(response.css("body *::text").getall())
            result["content"]["links"] = [
                {"url": urljoin(response.url, link), "text": text}
                for link, text in zip(
                    response.css("a::attr(href)").getall(),
                    response.css("a::text").getall(),
                )
            ]
            result["content"]["images"] = [
                {"src": urljoin(response.url, src), "alt": alt}
                for src, alt in zip(
                    response.css("img::attr(src)").getall(),
                    response.css("img::attr(alt)").getall(),
                )
            ]

        self.results.append(result)
        yield result


class ScrapyWrapper:
    """Wrapper for Scrapy functionality."""

    def __init__(self) -> None:
        self.configure_logging()
        self.runner = None

    def configure_logging(self) -> None:
        """Configure Scrapy logging."""
        configure_logging(install_root_handler=False)
        logging.getLogger("scrapy").setLevel(logging.WARNING)

    async def scrape(
        self, url: str, extract_config: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Scrape a URL using Scrapy."""
        try:
            self.runner = CrawlerRunner(settings.get_scrapy_settings())

            spider_instance = WebScrapingSpider(url=url, extract_config=extract_config)
            deferred = self.runner.crawl(spider_instance)
            deferred.addBoth(lambda _: None)  # Ignore result

            # Wait for the spider to complete
            while not deferred.called:
                await asyncio.sleep(0.1)

            return spider_instance.results

        except Exception as e:
            logger.error(f"Scrapy scraping failed for {url}: {str(e)}")
            return []


class SeleniumScraper:
    """Selenium-based scraper for JavaScript-heavy sites."""

    def __init__(self) -> None:
        self.driver = None
        self.ua = UserAgent() if settings.use_random_user_agent else None

    def _get_driver(self) -> webdriver.Chrome:
        """Get configured Chrome driver."""
        options = ChromeOptions()

        if settings.browser_headless:
            options.add_argument("--headless")

        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")

        if settings.use_random_user_agent and self.ua:
            options.add_argument(f"--user-agent={self.ua.random}")
        else:
            options.add_argument(f"--user-agent={settings.default_user_agent}")

        if settings.use_proxy and settings.proxy_url:
            options.add_argument(f"--proxy-server={settings.proxy_url}")

        return webdriver.Chrome(options=options)

    async def scrape(
        self,
        url: str,
        wait_for_element: Optional[str] = None,
        extract_config: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Scrape a URL using Selenium."""
        try:
            self.driver = self._get_driver()
            self.driver.get(url)

            # Wait for specific element if specified
            if wait_for_element:
                try:
                    WebDriverWait(self.driver, settings.browser_timeout).until(
                        EC.presence_of_element_located(
                            (By.CSS_SELECTOR, wait_for_element)
                        )
                    )
                except TimeoutException:
                    logger.warning(f"Timeout waiting for element: {wait_for_element}")

            # Extract page content
            page_source = self.driver.page_source
            soup = BeautifulSoup(page_source, "html.parser")

            result = {
                "url": self.driver.current_url,
                "title": self.driver.title,
                "meta_description": None,
                "content": {},
            }

            # Get meta description
            meta_desc = soup.find("meta", attrs={"name": "description"})
            if meta_desc and hasattr(meta_desc, "get"):
                result["meta_description"] = meta_desc.get("content")

            # Extract based on configuration
            if extract_config:
                for key, selector_config in extract_config.items():
                    try:
                        if isinstance(selector_config, str):
                            # Simple CSS selector
                            elements = self.driver.find_elements(
                                By.CSS_SELECTOR, selector_config
                            )
                            result["content"][key] = [elem.text for elem in elements]
                        elif isinstance(selector_config, dict):
                            # Complex selector configuration
                            selector = selector_config.get("selector")
                            attr = selector_config.get("attr")
                            multiple = selector_config.get("multiple", False)

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
                                        elem.get_attribute("outerHTML")
                                        for elem in elements
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
                        "url": urljoin(url, str(a.get("href", ""))),
                        "text": a.get_text(strip=True),
                    }
                    for a in soup.find_all("a", href=True)
                    if hasattr(a, "get")
                ]
                result["content"]["images"] = [
                    {
                        "src": urljoin(url, str(img.get("src", ""))),
                        "alt": str(img.get("alt", "")),
                    }
                    for img in soup.find_all("img", src=True)
                    if hasattr(img, "get")
                ]

            return result

        except Exception as e:
            logger.error(f"Selenium scraping failed for {url}: {str(e)}")
            return {"error": str(e), "url": url}
        finally:
            if self.driver:
                self.driver.quit()


class SimpleScraper:
    """Simple HTTP-based scraper using requests."""

    def __init__(self) -> None:
        self.session = requests.Session()
        self.ua = UserAgent() if settings.use_random_user_agent else None
        self._configure_session()

    def _configure_session(self) -> None:
        """Configure the requests session."""
        if settings.use_random_user_agent and self.ua:
            self.session.headers.update({"User-Agent": self.ua.random})
        else:
            self.session.headers.update({"User-Agent": settings.default_user_agent})

        if settings.use_proxy and settings.proxy_url:
            self.session.proxies.update(
                {"http": settings.proxy_url, "https": settings.proxy_url}
            )

    async def scrape(
        self, url: str, extract_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Scrape a URL using requests."""
        try:
            response = self.session.get(url, timeout=settings.request_timeout)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, "html.parser")

            result = {
                "url": response.url,
                "status_code": response.status_code,
                "title": None,
                "meta_description": None,
                "content": {},
            }

            # Extract title
            title_tag = soup.find("title")
            if title_tag:
                result["title"] = title_tag.get_text(strip=True)

            # Extract meta description
            meta_desc = soup.find("meta", attrs={"name": "description"})
            if meta_desc and hasattr(meta_desc, "get"):
                result["meta_description"] = meta_desc.get("content")

            # Extract based on configuration
            if extract_config:
                for key, selector_config in extract_config.items():
                    try:
                        if isinstance(selector_config, str):
                            # Simple CSS selector
                            elements = soup.select(selector_config)
                            result["content"][key] = [
                                elem.get_text(strip=True) for elem in elements
                            ]
                        elif isinstance(selector_config, dict):
                            # Complex selector configuration
                            selector = selector_config.get("selector")
                            attr = selector_config.get("attr")
                            multiple = selector_config.get("multiple", False)

                            if selector:
                                elements = soup.select(selector)
                            else:
                                elements = []

                            if multiple:
                                if attr == "text":
                                    extracted = [
                                        elem.get_text(strip=True) for elem in elements
                                    ]
                                elif attr:
                                    extracted = [
                                        elem.get(attr, "")
                                        for elem in elements
                                        if hasattr(elem, "get")
                                    ]
                                else:
                                    extracted = [str(elem) for elem in elements]
                            else:
                                element = elements[0] if elements else None
                                if element:
                                    if attr == "text":
                                        extracted = element.get_text(strip=True)
                                    elif attr and hasattr(element, "get"):
                                        extracted = element.get(attr, "")
                                    else:
                                        extracted = str(element)
                                else:
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
                        "url": urljoin(url, str(a.get("href", ""))),
                        "text": a.get_text(strip=True),
                    }
                    for a in soup.find_all("a", href=True)
                    if hasattr(a, "get")
                ]
                result["content"]["images"] = [
                    {
                        "src": urljoin(url, str(img.get("src", ""))),
                        "alt": str(img.get("alt", "")),
                    }
                    for img in soup.find_all("img", src=True)
                    if hasattr(img, "get")
                ]

            return result

        except Exception as e:
            logger.error(f"Simple scraping failed for {url}: {str(e)}")
            return {"error": str(e), "url": url}


class WebScraper:
    """Main web scraper that chooses the appropriate scraping method."""

    def __init__(self) -> None:
        self.scrapy_wrapper = ScrapyWrapper()
        self.selenium_scraper = SeleniumScraper()
        self.simple_scraper = SimpleScraper()

    async def scrape_url(
        self,
        url: str,
        method: str = "auto",
        extract_config: Optional[Dict[str, Any]] = None,
        wait_for_element: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Scrape a URL using the specified method.

        Args:
            url: The URL to scrape
            method: Scraping method ("auto", "simple", "scrapy", "selenium")
            extract_config: Configuration for data extraction
            wait_for_element: CSS selector to wait for (Selenium only)

        Returns:
            Dict containing scraped data
        """

        if method == "auto":
            # Auto-detect best method based on URL and settings
            if settings.enable_javascript or wait_for_element:
                method = "selenium"
            else:
                method = "simple"

        logger.info(f"Scraping {url} using {method} method")

        try:
            if method == "simple":
                return await self.simple_scraper.scrape(url, extract_config)
            elif method == "scrapy":
                results = await self.scrapy_wrapper.scrape(url, extract_config)
                return results[0] if results else {"error": "No results", "url": url}
            elif method == "selenium":
                return await self.selenium_scraper.scrape(
                    url, wait_for_element, extract_config
                )
            else:
                raise ValueError(f"Unknown scraping method: {method}")

        except Exception as e:
            logger.error(f"Scraping failed for {url}: {str(e)}")
            return {"error": str(e), "url": url}

    async def scrape_multiple_urls(
        self,
        urls: List[str],
        method: str = "auto",
        extract_config: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Scrape multiple URLs concurrently."""
        tasks = [self.scrape_url(url, method, extract_config) for url in urls]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append({"error": str(result), "url": urls[i]})
            else:
                processed_results.append(result)

        return processed_results
