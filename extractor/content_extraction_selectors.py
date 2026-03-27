"""按后端划分的选择器提取实现。"""

import logging
from typing import Any, Dict

from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


def extract_with_bs4_config(
    soup: BeautifulSoup, extract_config: Dict[str, Any]
) -> Dict[str, Any]:
    """使用 BeautifulSoup 按 extract_config 提取数据。"""
    content: Dict[str, Any] = {}

    for key, selector_config in extract_config.items():
        try:
            if isinstance(selector_config, str):
                elements = soup.select(selector_config)
                content[key] = [elem.get_text(strip=True) for elem in elements]
                continue

            if not isinstance(selector_config, dict):
                content[key] = None
                continue

            content[key] = _extract_bs4_selector_value(soup, selector_config)
        except Exception as e:
            logger.warning("Failed to extract %s: %s", key, e)
            content[key] = None

    return content


def _extract_bs4_selector_value(
    soup: BeautifulSoup, selector_config: Dict[str, Any]
) -> Any:
    selector = selector_config.get("selector")
    attr = selector_config.get("attr")
    multiple = selector_config.get("multiple", False)
    elements = soup.select(selector) if selector else []

    if multiple:
        return _extract_bs4_multiple(elements, attr)

    element = elements[0] if elements else None
    if element is None:
        return None
    if attr == "text":
        return element.get_text(strip=True)
    if attr and hasattr(element, "get"):
        return element.get(attr, "")
    return str(element)


def _extract_bs4_multiple(elements: list, attr: Any) -> list:
    if attr == "text":
        return [elem.get_text(strip=True) for elem in elements]
    if attr:
        return [elem.get(attr, "") for elem in elements if hasattr(elem, "get")]
    return [str(elem) for elem in elements]


def extract_with_selenium_config(driver, extract_config: Dict[str, Any]) -> Dict[str, Any]:
    """使用 Selenium driver 按 extract_config 提取数据。"""
    from selenium.webdriver.common.by import By

    content: Dict[str, Any] = {}

    for key, selector_config in extract_config.items():
        try:
            if isinstance(selector_config, str):
                elements = driver.find_elements(By.CSS_SELECTOR, selector_config)
                content[key] = [elem.text for elem in elements]
                continue

            if not isinstance(selector_config, dict):
                content[key] = None
                continue

            content[key] = _extract_selenium_selector_value(driver, selector_config)
        except Exception as e:
            logger.warning("Failed to extract %s: %s", key, e)
            content[key] = None

    return content


def _extract_selenium_selector_value(driver, selector_config: Dict[str, Any]) -> Any:
    from selenium.webdriver.common.by import By

    selector = selector_config.get("selector")
    attr = selector_config.get("attr")
    multiple = selector_config.get("multiple", False)

    if multiple:
        elements = driver.find_elements(By.CSS_SELECTOR, selector)
        return _extract_selenium_multiple(elements, attr)

    try:
        element = driver.find_element(By.CSS_SELECTOR, selector)
    except Exception:
        return None

    if attr == "text":
        return element.text
    if attr:
        return element.get_attribute(attr)
    return element.get_attribute("outerHTML")


def _extract_selenium_multiple(elements: list, attr: Any) -> list:
    if attr == "text":
        return [elem.text for elem in elements]
    if attr:
        return [elem.get_attribute(attr) for elem in elements]
    return [elem.get_attribute("outerHTML") for elem in elements]


async def extract_with_playwright_config(
    page, extract_config: Dict[str, Any]
) -> Dict[str, Any]:
    """使用 Playwright page 按 extract_config 提取数据。"""
    content: Dict[str, Any] = {}

    for key, selector_config in extract_config.items():
        try:
            if isinstance(selector_config, str):
                elements = await page.query_selector_all(selector_config)
                content[key] = [await element.text_content() for element in elements]
                continue

            if not isinstance(selector_config, dict):
                content[key] = None
                continue

            content[key] = await _extract_playwright_selector_value(
                page, selector_config
            )
        except Exception as e:
            logger.warning("Failed to extract %s: %s", key, e)
            content[key] = None

    return content


async def _extract_playwright_selector_value(page, selector_config: Dict[str, Any]) -> Any:
    selector = selector_config.get("selector")
    attr = selector_config.get("attr")
    multiple = selector_config.get("multiple", False)

    if multiple:
        elements = await page.query_selector_all(selector)
        return await _extract_playwright_multiple(elements, attr)

    element = await page.query_selector(selector)
    if not element:
        return None
    if attr == "text":
        return await element.text_content()
    if attr:
        return await element.get_attribute(attr)
    return await element.inner_html()


async def _extract_playwright_multiple(elements: list, attr: Any) -> list:
    extracted = []
    for element in elements:
        if attr == "text":
            value = await element.text_content()
        elif attr:
            value = await element.get_attribute(attr)
        else:
            value = await element.inner_html()
        extracted.append(value)
    return extracted
