"""
共享抓取工具函数单元测试。

覆盖 `extract_default_content` 和 `extract_with_selenium_config` 两个共享函数。
"""

import pytest
from unittest.mock import Mock, MagicMock
from bs4 import BeautifulSoup

from extractor.scraping_utils import extract_default_content, extract_with_selenium_config


class TestExtractDefaultContent:
    """测试 BeautifulSoup 默认内容提取。"""

    def test_extracts_text(self):
        """测试文本提取"""
        html = "<html><body><p>Hello World</p></body></html>"
        soup = BeautifulSoup(html, "html.parser")
        result = extract_default_content(soup, "https://example.com")

        assert "Hello World" in result["text"]

    def test_extracts_links(self):
        """测试链接提取"""
        html = '<html><body><a href="/page1">Link 1</a><a href="https://other.com">Link 2</a></body></html>'
        soup = BeautifulSoup(html, "html.parser")
        result = extract_default_content(soup, "https://example.com")

        assert len(result["links"]) == 2
        assert result["links"][0]["url"] == "https://example.com/page1"
        assert result["links"][0]["text"] == "Link 1"
        assert result["links"][1]["url"] == "https://other.com"

    def test_extracts_images(self):
        """测试图片提取"""
        html = '<html><body><img src="/img/logo.png" alt="Logo" /></body></html>'
        soup = BeautifulSoup(html, "html.parser")
        result = extract_default_content(soup, "https://example.com")

        assert len(result["images"]) == 1
        assert result["images"][0]["src"] == "https://example.com/img/logo.png"
        assert result["images"][0]["alt"] == "Logo"

    def test_empty_html(self):
        """测试空 HTML"""
        soup = BeautifulSoup("<html><body></body></html>", "html.parser")
        result = extract_default_content(soup, "https://example.com")

        assert result["text"] == ""
        assert result["links"] == []
        assert result["images"] == []

    def test_relative_url_resolution(self):
        """测试相对 URL 拼接"""
        html = '<html><body><a href="../page">Link</a><img src="images/photo.jpg" alt="Photo" /></body></html>'
        soup = BeautifulSoup(html, "html.parser")
        result = extract_default_content(soup, "https://example.com/dir/")

        assert result["links"][0]["url"] == "https://example.com/page"
        assert result["images"][0]["src"] == "https://example.com/dir/images/photo.jpg"


class TestExtractWithSeleniumConfig:
    """测试 Selenium 配置化提取。"""

    def _make_driver(self, elements_map=None):
        """创建 mock driver。"""
        driver = MagicMock()

        def find_elements(by, selector):
            if elements_map and selector in elements_map:
                return elements_map[selector]
            return []

        def find_element(by, selector):
            if elements_map and selector in elements_map:
                items = elements_map[selector]
                if items:
                    return items[0]
            raise Exception("Element not found")

        driver.find_elements = find_elements
        driver.find_element = find_element
        return driver

    def test_simple_string_selector(self):
        """测试简单字符串选择器"""
        elem = Mock()
        elem.text = "Hello"
        driver = self._make_driver({".title": [elem]})

        result = extract_with_selenium_config(driver, {"title": ".title"})

        assert result["title"] == ["Hello"]

    def test_dict_config_multiple_text(self):
        """测试字典配置 - 多元素文本提取"""
        elems = [Mock(text="A"), Mock(text="B")]
        driver = self._make_driver({".items": elems})

        config = {
            "items": {
                "selector": ".items",
                "attr": "text",
                "multiple": True,
            }
        }
        result = extract_with_selenium_config(driver, config)

        assert result["items"] == ["A", "B"]

    def test_dict_config_single_attr(self):
        """测试字典配置 - 单元素属性提取"""
        elem = Mock()
        elem.get_attribute = Mock(return_value="https://example.com")
        driver = self._make_driver({"a.link": [elem]})

        config = {
            "link": {
                "selector": "a.link",
                "attr": "href",
                "multiple": False,
            }
        }
        result = extract_with_selenium_config(driver, config)

        assert result["link"] == "https://example.com"

    def test_element_not_found(self):
        """测试元素未找到时返回 None"""
        driver = self._make_driver({})

        config = {
            "missing": {
                "selector": ".nonexistent",
                "attr": "text",
                "multiple": False,
            }
        }
        result = extract_with_selenium_config(driver, config)

        assert result["missing"] is None

    def test_extraction_error_handling(self):
        """测试提取出错时的容错处理"""
        driver = MagicMock()
        driver.find_elements = Mock(side_effect=Exception("Driver error"))

        result = extract_with_selenium_config(driver, {"data": ".selector"})

        assert result["data"] is None
