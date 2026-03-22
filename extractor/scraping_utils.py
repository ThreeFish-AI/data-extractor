"""共享抓取工具函数：BeautifulSoup / Selenium 通用数据提取。"""

import logging
from typing import Any, Dict
from urllib.parse import urljoin

from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


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
