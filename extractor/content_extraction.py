"""统一内容提取模块：BeautifulSoup / Selenium / Playwright 三引擎数据提取。"""

import logging
from typing import Any, Dict
from urllib.parse import urljoin

from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# BeautifulSoup 提取
# ---------------------------------------------------------------------------


def extract_default_content(soup: BeautifulSoup, base_url: str) -> Dict[str, Any]:
    """从 BeautifulSoup 解析树中提取默认内容（text / links / images）。

    Args:
        soup: 已解析的 BeautifulSoup 对象
        base_url: 用于拼接相对 URL 的基础地址

    Returns:
        包含 text、links、images 键的字典
    """
    text = soup.get_text(strip=True)

    links = [
        {
            "url": urljoin(base_url, str(a.get("href", ""))),
            "text": a.get_text(strip=True),
        }
        for a in soup.find_all("a", href=True)
        if hasattr(a, "get")
    ]

    images = [
        {
            "src": urljoin(base_url, str(img.get("src", ""))),
            "alt": str(img.get("alt", "")),
        }
        for img in soup.find_all("img", src=True)
        if hasattr(img, "get")
    ]

    return {"text": text, "links": links, "images": images}


def extract_with_bs4_config(
    soup: BeautifulSoup, extract_config: Dict[str, Any]
) -> Dict[str, Any]:
    """使用 BeautifulSoup 按 extract_config 提取数据。

    Args:
        soup: 已解析的 BeautifulSoup 对象
        extract_config: 提取配置字典，键为目标名，值为选择器字符串或配置字典

    Returns:
        键值对字典，键为 extract_config 中的目标名
    """
    content: Dict[str, Any] = {}

    for key, selector_config in extract_config.items():
        try:
            if isinstance(selector_config, str):
                # Simple CSS selector
                elements = soup.select(selector_config)
                content[key] = [elem.get_text(strip=True) for elem in elements]
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
                        extracted = [elem.get_text(strip=True) for elem in elements]
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

                content[key] = extracted
        except Exception as e:
            logger.warning(f"Failed to extract {key}: {str(e)}")
            content[key] = None

    return content


# ---------------------------------------------------------------------------
# Selenium 提取
# ---------------------------------------------------------------------------


def extract_with_selenium_config(
    driver, extract_config: Dict[str, Any]
) -> Dict[str, Any]:
    """使用 Selenium driver 按 extract_config 提取数据。

    Args:
        driver: Selenium WebDriver 实例
        extract_config: 提取配置字典，键为目标名，值为选择器字符串或配置字典

    Returns:
        键值对字典，键为 extract_config 中的目标名
    """
    from selenium.webdriver.common.by import By

    content: Dict[str, Any] = {}

    for key, config in extract_config.items():
        try:
            if isinstance(config, str):
                elements = driver.find_elements(By.CSS_SELECTOR, config)
                content[key] = [elem.text for elem in elements]
            elif isinstance(config, dict):
                selector = config.get("selector")
                attr = config.get("attr")
                multiple = config.get("multiple", False)

                if multiple:
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    if attr == "text":
                        extracted = [elem.text for elem in elements]
                    elif attr:
                        extracted = [elem.get_attribute(attr) for elem in elements]
                    else:
                        extracted = [
                            elem.get_attribute("outerHTML") for elem in elements
                        ]
                else:
                    try:
                        element = driver.find_element(By.CSS_SELECTOR, selector)
                        if attr == "text":
                            extracted = element.text
                        elif attr:
                            extracted = element.get_attribute(attr)
                        else:
                            extracted = element.get_attribute("outerHTML")
                    except Exception:
                        extracted = None

                content[key] = extracted
        except Exception as e:
            logger.warning(f"Failed to extract {key}: {str(e)}")
            content[key] = None

    return content


# ---------------------------------------------------------------------------
# Playwright 提取
# ---------------------------------------------------------------------------


async def extract_with_playwright_config(
    page, extract_config: Dict[str, Any]
) -> Dict[str, Any]:
    """使用 Playwright page 按 extract_config 提取数据。

    Args:
        page: Playwright Page 实例
        extract_config: 提取配置字典，键为目标名，值为选择器字符串或配置字典

    Returns:
        键值对字典，键为 extract_config 中的目标名
    """
    content: Dict[str, Any] = {}

    for key, config in extract_config.items():
        try:
            if isinstance(config, str):
                elements = await page.query_selector_all(config)
                texts = []
                for element in elements:
                    text = await element.text_content()
                    texts.append(text)
                content[key] = texts
            elif isinstance(config, dict):
                selector = config.get("selector")
                attr = config.get("attr")
                multiple = config.get("multiple", False)

                if multiple:
                    elements = await page.query_selector_all(selector)
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
                    element = await page.query_selector(selector)
                    if element:
                        if attr == "text":
                            extracted = await element.text_content()
                        elif attr:
                            extracted = await element.get_attribute(attr)
                        else:
                            extracted = await element.inner_html()
                    else:
                        extracted = None

                content[key] = extracted
        except Exception as e:
            logger.warning(f"Failed to extract {key}: {str(e)}")
            content[key] = None

    return content


async def extract_default_content_playwright(
    page, base_url: str | None = None
) -> Dict[str, Any]:
    """从 Playwright page 提取默认内容（text / links）。

    Args:
        page: Playwright Page 实例
        base_url: 用于拼接相对 URL 的基础地址（默认使用 page.url）

    Returns:
        包含 text、links 键的字典
    """
    if base_url is None:
        base_url = page.url

    text = await page.text_content("body")

    links = []
    link_elements = await page.query_selector_all("a[href]")
    for link_elem in link_elements:
        href = await link_elem.get_attribute("href")
        link_text = await link_elem.text_content()
        if href:
            links.append(
                {
                    "url": urljoin(base_url, href),
                    "text": link_text.strip() if link_text else "",
                }
            )

    return {"text": text, "links": links}
