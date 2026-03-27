"""统一内容提取导出：兼容保留原入口，内部按职责拆分。"""

from typing import Any, Dict, Optional

from bs4 import BeautifulSoup

from .content_extraction_pages import (
    extract_default_content as _extract_default_content,
    extract_default_content_playwright as _extract_default_content_playwright,
    extract_page_data_playwright as _extract_page_data_playwright,
)
from .content_extraction_selectors import (
    extract_with_bs4_config,
    extract_with_playwright_config,
    extract_with_selenium_config,
)


def extract_default_content(soup: BeautifulSoup, base_url: str) -> Dict[str, Any]:
    """兼容导出默认内容提取。"""
    return _extract_default_content(soup, base_url)


async def extract_default_content_playwright(
    page, base_url: str | None = None
) -> Dict[str, Any]:
    """兼容导出 Playwright 默认内容提取。"""
    return await _extract_default_content_playwright(page, base_url)


def extract_page_data_selenium(
    driver, extract_config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """兼容保留 Selenium 整页提取门面，便于测试 patch 模块级依赖。"""
    from selenium.common.exceptions import NoSuchElementException
    from selenium.webdriver.common.by import By

    soup = BeautifulSoup(driver.page_source, "html.parser")
    result: Dict[str, Any] = {"title": driver.title, "content": {}}

    try:
        meta_elem = driver.find_element(By.CSS_SELECTOR, "meta[name='description']")
        result["meta_description"] = meta_elem.get_attribute("content")
    except NoSuchElementException:
        result["meta_description"] = None

    if extract_config:
        result["content"] = extract_with_selenium_config(driver, extract_config)
    else:
        default = extract_default_content(soup, driver.current_url)
        result["content"] = {
            "text": default["text"],
            "links": default["links"],
        }

    return result


async def extract_page_data_playwright(
    page, extract_config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """兼容导出 Playwright 整页提取门面。"""
    if extract_config:
        result: Dict[str, Any] = {"title": await page.title(), "content": {}}
        try:
            result["meta_description"] = await page.get_attribute(
                "meta[name='description']",
                "content",
            )
        except Exception:
            result["meta_description"] = None
        result["content"] = await extract_with_playwright_config(page, extract_config)
        return result

    return await _extract_page_data_playwright(page, extract_config)

__all__ = [
    "extract_default_content",
    "extract_with_bs4_config",
    "extract_with_selenium_config",
    "extract_with_playwright_config",
    "extract_default_content_playwright",
    "extract_page_data_selenium",
    "extract_page_data_playwright",
    "BeautifulSoup",
]
