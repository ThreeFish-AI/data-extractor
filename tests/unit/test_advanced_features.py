"""
单元测试：高级功能模块
测试 extractor.advanced_features 模块的反检测爬虫和表单处理功能
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock, MagicMock

from extractor.advanced_features import AntiDetectionScraper, FormHandler


class TestAntiDetectionScraper:
    """测试反检测爬虫主要功能"""

    def setup_method(self):
        """测试前准备"""
        self.scraper = AntiDetectionScraper()

    def teardown_method(self):
        """测试后清理"""
        # 确保清理资源
        try:
            asyncio.create_task(self.scraper.cleanup())
        except Exception:
            pass

    def test_scraper_initialization(self):
        """测试爬虫初始化"""
        assert self.scraper is not None
        assert hasattr(self.scraper, "scrape_with_stealth")
        assert hasattr(self.scraper, "ua")
        assert self.scraper.driver is None
        assert self.scraper.page is None
        assert self.scraper.browser is None
        assert self.scraper.context is None
        assert self.scraper.playwright is None

    @pytest.mark.asyncio
    async def test_invalid_stealth_method(self):
        """测试无效的隐身方法"""
        result = await self.scraper.scrape_with_stealth(
            "https://example.com", method="invalid_method"
        )

        assert "error" in result
        assert "Unknown stealth method" in result["error"]
        assert result["url"] == "https://example.com"

    @pytest.mark.asyncio
    async def test_scraping_exception_handling(self):
        """测试爬取异常处理"""
        with patch.object(self.scraper, "_scrape_with_selenium_stealth") as mock_scrape:
            mock_scrape.side_effect = Exception("Network error")

            result = await self.scraper.scrape_with_stealth(
                "https://example.com", method="selenium"
            )

            assert "error" in result
            assert "Network error" in result["error"]

    @pytest.mark.asyncio
    async def test_cleanup_called_after_scraping(self):
        """测试爬取后调用清理"""
        with (
            patch.object(self.scraper, "_scrape_with_selenium_stealth") as mock_scrape,
            patch.object(self.scraper, "cleanup") as mock_cleanup,
        ):
            mock_scrape.return_value = {"title": "Test", "content": {}}

            await self.scraper.scrape_with_stealth(
                "https://example.com", method="selenium"
            )

            mock_cleanup.assert_called_once()


class TestSeleniumStealth:
    """测试Selenium隐身功能"""

    def setup_method(self):
        """测试前准备"""
        self.scraper = AntiDetectionScraper()

    def teardown_method(self):
        """测试后清理"""
        try:
            asyncio.create_task(self.scraper.cleanup())
        except Exception:
            pass

    @patch("extractor.advanced_features.uc.Chrome")
    @patch("selenium.webdriver.support.ui.WebDriverWait")
    @patch.object(AntiDetectionScraper, "_scroll_page_selenium")
    @patch.object(AntiDetectionScraper, "_simulate_human_behavior_selenium")
    @patch.object(AntiDetectionScraper, "_extract_data_selenium")
    @patch("asyncio.sleep")
    @pytest.mark.asyncio
    async def test_selenium_stealth_scraping_success(
        self,
        mock_sleep,
        mock_extract,
        mock_simulate,
        mock_scroll,
        mock_wait,
        mock_chrome,
    ):
        """测试Selenium隐身爬取成功"""
        # 模拟Chrome驱动器
        mock_driver = Mock()
        mock_driver.current_url = "https://example.com/final"
        mock_chrome.return_value = mock_driver

        # 模拟数据提取
        mock_extract.return_value = {
            "title": "Test Page",
            "content": {"text": "Test content"},
            "meta_description": "Test description",
        }

        result = await self.scraper._scrape_with_selenium_stealth(
            "https://example.com",
            extract_config=None,
            wait_for_element=None,
            scroll_page=False,
        )

        assert result["title"] == "Test Page"
        assert result["url"] == "https://example.com/final"
        assert result["content"]["text"] == "Test content"

        # 验证调用了必要的方法
        mock_driver.get.assert_called_once_with("https://example.com")
        mock_simulate.assert_called_once()
        mock_extract.assert_called_once()
        # scroll_page=False，所以不应该调用滚动
        mock_scroll.assert_not_called()

    @patch("extractor.advanced_features.uc.Chrome")
    @patch("selenium.webdriver.support.ui.WebDriverWait")
    @patch.object(AntiDetectionScraper, "_scroll_page_selenium")
    @patch("asyncio.sleep")
    @pytest.mark.asyncio
    async def test_selenium_stealth_with_scroll(
        self, mock_sleep, mock_scroll, mock_wait, mock_chrome
    ):
        """测试Selenium隐身爬取带滚动"""
        mock_driver = Mock()
        mock_driver.current_url = "https://example.com"
        mock_chrome.return_value = mock_driver

        with (
            patch.object(self.scraper, "_extract_data_selenium") as mock_extract,
            patch.object(self.scraper, "_simulate_human_behavior_selenium"),
        ):
            mock_extract.return_value = {"title": "Test", "content": {}}

            await self.scraper._scrape_with_selenium_stealth(
                "https://example.com",
                extract_config=None,
                wait_for_element=None,
                scroll_page=True,
            )

            mock_scroll.assert_called_once()

    @patch("extractor.advanced_features.uc.Chrome")
    @patch("selenium.webdriver.support.ui.WebDriverWait")
    @patch("selenium.webdriver.support.expected_conditions.presence_of_element_located")
    @patch("asyncio.sleep")
    @pytest.mark.asyncio
    async def test_selenium_wait_for_element(
        self, mock_sleep, mock_presence, mock_wait, mock_chrome
    ):
        """测试Selenium等待特定元素"""
        mock_driver = Mock()
        mock_chrome.return_value = mock_driver
        mock_wait_instance = Mock()
        mock_wait.return_value = mock_wait_instance

        with (
            patch.object(self.scraper, "_extract_data_selenium") as mock_extract,
            patch.object(self.scraper, "_simulate_human_behavior_selenium"),
        ):
            mock_extract.return_value = {"title": "Test", "content": {}}

            await self.scraper._scrape_with_selenium_stealth(
                "https://example.com",
                extract_config=None,
                wait_for_element=".loading-spinner",
                scroll_page=False,
            )

            mock_wait_instance.until.assert_called_once()

    @patch("extractor.advanced_features.random.randint")
    @patch("extractor.advanced_features.random.uniform")
    @patch("asyncio.sleep")
    @pytest.mark.asyncio
    async def test_selenium_page_scrolling(
        self, mock_sleep, mock_uniform, mock_randint
    ):
        """测试Selenium页面滚动"""
        # 模拟随机值
        mock_randint.return_value = 300
        mock_uniform.return_value = 1.0

        # 模拟驱动器
        mock_driver = Mock()
        mock_driver.execute_script.side_effect = [
            1000,
            1000,
            1200,
            1200,
        ]  # scrollHeight变化
        self.scraper.driver = mock_driver

        await self.scraper._scroll_page_selenium()

        # 验证滚动调用
        assert mock_driver.execute_script.call_count >= 2
        mock_sleep.assert_called()

    @patch("selenium.webdriver.common.action_chains.ActionChains")
    @patch("extractor.advanced_features.random.randint")
    @patch("extractor.advanced_features.random.uniform")
    @patch("asyncio.sleep")
    @pytest.mark.asyncio
    async def test_selenium_human_behavior_simulation(
        self, mock_sleep, mock_uniform, mock_randint, mock_action_chains
    ):
        """测试Selenium人类行为模拟"""
        mock_randint.side_effect = [3, 100, 200, 300, 400, 500, 600]  # 次数和坐标
        mock_uniform.return_value = 1.0

        mock_driver = Mock()
        mock_actions = Mock()
        mock_action_chains.return_value = mock_actions
        self.scraper.driver = mock_driver

        await self.scraper._simulate_human_behavior_selenium()

        mock_action_chains.assert_called_once_with(mock_driver)
        mock_actions.perform.assert_called_once()
        mock_sleep.assert_called()


class TestPlaywrightStealth:
    """测试Playwright隐身功能"""

    def setup_method(self):
        """测试前准备"""
        self.scraper = AntiDetectionScraper()

    def teardown_method(self):
        """测试后清理"""
        try:
            asyncio.create_task(self.scraper.cleanup())
        except Exception:
            pass

    @patch.object(AntiDetectionScraper, "_setup_playwright_browser")
    @patch.object(AntiDetectionScraper, "_scroll_page_playwright")
    @patch.object(AntiDetectionScraper, "_simulate_human_behavior_playwright")
    @patch.object(AntiDetectionScraper, "_extract_data_playwright")
    @patch("asyncio.sleep")
    @pytest.mark.asyncio
    async def test_playwright_stealth_scraping_success(
        self, mock_sleep, mock_extract, mock_simulate, mock_scroll, mock_setup
    ):
        """测试Playwright隐身爬取成功"""
        # 模拟页面
        mock_page = AsyncMock()
        mock_page.url = "https://example.com/final"
        mock_page.goto = AsyncMock()
        self.scraper.page = mock_page

        # 模拟数据提取
        mock_extract.return_value = {
            "title": "Test Page",
            "content": {"text": "Test content"},
        }

        result = await self.scraper._scrape_with_playwright_stealth(
            "https://example.com",
            extract_config=None,
            wait_for_element=None,
            scroll_page=False,
        )

        assert result["title"] == "Test Page"
        assert result["url"] == "https://example.com/final"

        mock_setup.assert_called_once()
        mock_page.goto.assert_called_once()
        mock_simulate.assert_called_once()
        mock_extract.assert_called_once()
        mock_scroll.assert_not_called()

    @patch.object(AntiDetectionScraper, "_setup_playwright_browser")
    @patch("asyncio.sleep")
    @pytest.mark.asyncio
    async def test_playwright_wait_for_element(self, mock_sleep, mock_setup):
        """测试Playwright等待特定元素"""
        mock_page = AsyncMock()
        mock_page.goto = AsyncMock()
        mock_page.wait_for_selector = AsyncMock()
        self.scraper.page = mock_page

        with (
            patch.object(self.scraper, "_extract_data_playwright") as mock_extract,
            patch.object(self.scraper, "_simulate_human_behavior_playwright"),
        ):
            mock_extract.return_value = {"title": "Test", "content": {}}

            await self.scraper._scrape_with_playwright_stealth(
                "https://example.com",
                extract_config=None,
                wait_for_element=".content",
                scroll_page=False,
            )

            mock_page.wait_for_selector.assert_called_once()

    @pytest.mark.asyncio
    async def test_playwright_page_scrolling(self):
        """测试Playwright页面滚动"""
        mock_page = AsyncMock()
        mock_page.evaluate = AsyncMock()
        self.scraper.page = mock_page

        await self.scraper._scroll_page_playwright()

        mock_page.evaluate.assert_called_once()
        # 验证传递的JavaScript代码包含滚动逻辑
        js_code = mock_page.evaluate.call_args[0][0]
        assert "scrollBy" in js_code
        assert "Promise" in js_code

    @patch("extractor.advanced_features.random.randint")
    @patch("extractor.advanced_features.random.uniform")
    @patch("asyncio.sleep")
    @pytest.mark.asyncio
    async def test_playwright_human_behavior_simulation(
        self, mock_sleep, mock_uniform, mock_randint
    ):
        """测试Playwright人类行为模拟"""
        mock_randint.side_effect = [3, 100, 200, 300, 400, 500, 600]
        mock_uniform.return_value = 0.5

        mock_page = AsyncMock()
        mock_mouse = AsyncMock()
        mock_page.mouse = mock_mouse
        self.scraper.page = mock_page

        await self.scraper._simulate_human_behavior_playwright()

        # 验证鼠标移动被调用
        assert mock_mouse.move.call_count > 0
        mock_sleep.assert_called()


class TestDataExtraction:
    """测试数据提取功能"""

    def setup_method(self):
        """测试前准备"""
        self.scraper = AntiDetectionScraper()

    def teardown_method(self):
        """测试后清理"""
        try:
            asyncio.create_task(self.scraper.cleanup())
        except Exception:
            pass

    @patch("bs4.BeautifulSoup")
    @pytest.mark.asyncio
    async def test_selenium_data_extraction_default(self, mock_beautifulsoup):
        """测试Selenium默认数据提取"""
        # 模拟驱动器
        mock_driver = Mock()
        mock_driver.title = "Test Page"
        mock_driver.current_url = "https://example.com"
        mock_driver.page_source = "<html><body><h1>Test</h1></body></html>"

        # 模拟meta描述元素
        mock_meta_element = Mock()
        mock_meta_element.get_attribute.return_value = "Test description"
        mock_driver.find_element.return_value = mock_meta_element

        # 模拟BeautifulSoup
        mock_soup = Mock()
        mock_soup.get_text.return_value = "Test content"
        mock_soup.find_all.return_value = []
        mock_beautifulsoup.return_value = mock_soup

        self.scraper.driver = mock_driver

        result = await self.scraper._extract_data_selenium(extract_config=None)

        assert result["title"] == "Test Page"
        assert result["meta_description"] == "Test description"
        assert result["content"]["text"] == "Test content"
        assert result["content"]["links"] == []

    @patch("bs4.BeautifulSoup")
    @pytest.mark.asyncio
    async def test_selenium_data_extraction_with_config(self, mock_beautifulsoup):
        """测试Selenium配置化数据提取"""
        mock_driver = Mock()
        mock_driver.title = "Test Page"
        mock_driver.current_url = "https://example.com"
        mock_driver.page_source = "<html></html>"

        # 模拟meta描述不存在
        from selenium.common.exceptions import NoSuchElementException

        mock_driver.find_element.side_effect = NoSuchElementException()

        # 模拟元素查找
        mock_element = Mock()
        mock_element.text = "Extracted text"
        mock_element.get_attribute.return_value = "href_value"
        mock_driver.find_elements.return_value = [mock_element]

        mock_beautifulsoup.return_value = Mock()
        self.scraper.driver = mock_driver

        extract_config = {
            "titles": "h1",
            "link": {"selector": "a", "attr": "href", "multiple": False},
        }

        result = await self.scraper._extract_data_selenium(extract_config)

        assert result["title"] == "Test Page"
        assert result["meta_description"] is None
        assert result["content"]["titles"] == ["Extracted text"]
        assert result["content"]["link"] == "href_value"

    @pytest.mark.asyncio
    async def test_playwright_data_extraction_default(self):
        """测试Playwright默认数据提取"""
        mock_page = AsyncMock()
        mock_page.title.return_value = "Test Page"
        mock_page.url = "https://example.com"
        mock_page.get_attribute.return_value = "Test description"
        mock_page.text_content.return_value = "Test content"
        mock_page.query_selector_all.return_value = []

        self.scraper.page = mock_page

        result = await self.scraper._extract_data_playwright(extract_config=None)

        assert result["title"] == "Test Page"
        assert result["meta_description"] == "Test description"
        assert result["content"]["text"] == "Test content"
        assert result["content"]["links"] == []

    @pytest.mark.asyncio
    async def test_playwright_data_extraction_with_config(self):
        """测试Playwright配置化数据提取"""
        mock_page = AsyncMock()
        mock_page.title.return_value = "Test Page"
        mock_page.get_attribute.return_value = None  # 无meta描述

        # 模拟元素
        mock_element = AsyncMock()
        mock_element.text_content.return_value = "Extracted text"
        mock_element.get_attribute.return_value = "href_value"

        mock_page.query_selector_all.return_value = [mock_element]
        mock_page.query_selector.return_value = mock_element

        self.scraper.page = mock_page

        extract_config = {
            "titles": "h1",
            "link": {"selector": "a", "attr": "href", "multiple": False},
        }

        result = await self.scraper._extract_data_playwright(extract_config)

        assert result["title"] == "Test Page"
        assert result["meta_description"] is None
        assert result["content"]["titles"] == ["Extracted text"]
        assert result["content"]["link"] == "href_value"


class TestResourceCleanup:
    """测试资源清理"""

    @pytest.mark.asyncio
    async def test_cleanup_selenium_driver(self):
        """测试清理Selenium驱动器"""
        scraper = AntiDetectionScraper()

        # 模拟驱动器
        mock_driver = Mock()
        scraper.driver = mock_driver

        await scraper.cleanup()

        mock_driver.quit.assert_called_once()
        assert scraper.driver is None

    @pytest.mark.asyncio
    async def test_cleanup_playwright_resources(self):
        """测试清理Playwright资源"""
        scraper = AntiDetectionScraper()

        # 模拟Playwright资源
        mock_page = AsyncMock()
        mock_context = AsyncMock()
        mock_browser = AsyncMock()
        mock_playwright = AsyncMock()

        scraper.page = mock_page
        scraper.context = mock_context
        scraper.browser = mock_browser
        scraper.playwright = mock_playwright

        await scraper.cleanup()

        mock_page.close.assert_called_once()
        mock_context.close.assert_called_once()
        mock_browser.close.assert_called_once()
        mock_playwright.stop.assert_called_once()

        assert scraper.page is None
        assert scraper.context is None
        assert scraper.browser is None
        assert scraper.playwright is None

    @pytest.mark.asyncio
    async def test_cleanup_with_none_resources(self):
        """测试清理空资源"""
        scraper = AntiDetectionScraper()

        # 所有资源都是None，应该正常执行
        await scraper.cleanup()

        # 不应该抛出异常
        assert True


class TestFormHandler:
    """测试表单处理器"""

    def test_form_handler_initialization_selenium(self):
        """测试表单处理器初始化（Selenium）"""
        mock_driver = Mock()
        # Selenium驱动器没有fill方法
        delattr(mock_driver, "fill") if hasattr(mock_driver, "fill") else None

        handler = FormHandler(mock_driver)

        assert handler.driver_or_page == mock_driver
        assert handler.is_playwright is False

    def test_form_handler_initialization_playwright(self):
        """测试表单处理器初始化（Playwright）"""
        mock_page = Mock()
        mock_page.fill = Mock()  # Playwright页面有fill方法

        handler = FormHandler(mock_page)

        assert handler.driver_or_page == mock_page
        assert handler.is_playwright is True

    @pytest.mark.asyncio
    async def test_form_filling_success(self):
        """测试表单填充成功"""
        mock_driver = Mock()
        handler = FormHandler(mock_driver)
        handler.is_playwright = False

        with (
            patch.object(handler, "_fill_field") as mock_fill_field,
            patch.object(handler, "_submit_form") as mock_submit,
        ):
            mock_fill_field.return_value = {"success": True, "value": "test"}
            mock_submit.return_value = {
                "success": True,
                "new_url": "https://example.com",
            }

            form_data = {"#username": "testuser", "#password": "testpass"}
            result = await handler.fill_form(
                form_data, submit=True, submit_button_selector="#submit"
            )

            assert result["success"] is True
            assert len(result["results"]) == 3  # 2 fields + submit
            mock_fill_field.assert_any_call("#username", "testuser")
            mock_fill_field.assert_any_call("#password", "testpass")
            mock_submit.assert_called_once_with("#submit")

    @pytest.mark.asyncio
    async def test_form_filling_error(self):
        """测试表单填充错误"""
        mock_driver = Mock()
        handler = FormHandler(mock_driver)

        with patch.object(handler, "_fill_field") as mock_fill_field:
            mock_fill_field.side_effect = Exception("Fill error")

            result = await handler.fill_form({"#field": "value"})

            assert result["success"] is False
            assert "Fill error" in result["error"]


class TestSeleniumFormHandling:
    """测试Selenium表单处理"""

    @patch("selenium.webdriver.support.ui.Select")
    @pytest.mark.asyncio
    async def test_selenium_fill_select_field(self, mock_select):
        """测试Selenium填充选择框"""
        mock_driver = Mock()
        mock_element = Mock()
        mock_element.tag_name = "select"
        mock_driver.find_element.return_value = mock_element

        mock_select_instance = Mock()
        mock_select.return_value = mock_select_instance

        handler = FormHandler(mock_driver)

        # 测试按可见文本选择
        result = await handler._fill_field_selenium("#select", "Option 1")

        assert result["success"] is True
        assert result["value"] == "Option 1"
        mock_select_instance.select_by_visible_text.assert_called_once_with("Option 1")

    @pytest.mark.asyncio
    async def test_selenium_fill_checkbox(self):
        """测试Selenium填充复选框"""
        mock_driver = Mock()
        mock_element = Mock()
        mock_element.tag_name = "input"
        mock_element.get_attribute.return_value = "checkbox"
        mock_element.is_selected.return_value = False
        mock_driver.find_element.return_value = mock_element

        handler = FormHandler(mock_driver)

        result = await handler._fill_field_selenium("#checkbox", True)

        assert result["success"] is True
        assert result["value"] is True
        mock_element.click.assert_called_once()

    @pytest.mark.asyncio
    async def test_selenium_fill_text_input(self):
        """测试Selenium填充文本输入"""
        mock_driver = Mock()
        mock_element = Mock()
        mock_element.tag_name = "input"
        mock_element.get_attribute.return_value = "text"
        mock_driver.find_element.return_value = mock_element

        handler = FormHandler(mock_driver)

        result = await handler._fill_field_selenium("#text", "test value")

        assert result["success"] is True
        assert result["value"] == "test value"
        mock_element.clear.assert_called_once()
        mock_element.send_keys.assert_called_once_with("test value")

    @pytest.mark.asyncio
    async def test_selenium_submit_form_with_button(self):
        """测试Selenium提交表单（指定按钮）"""
        mock_driver = Mock()
        mock_driver.current_url = "https://example.com/success"
        mock_button = Mock()
        mock_driver.find_element.return_value = mock_button

        handler = FormHandler(mock_driver)

        with patch("asyncio.sleep"):
            result = await handler._submit_form_selenium("#submit-btn")

        assert result["success"] is True
        assert result["new_url"] == "https://example.com/success"
        mock_button.click.assert_called_once()


class TestPlaywrightFormHandling:
    """测试Playwright表单处理"""

    @pytest.mark.asyncio
    async def test_playwright_fill_select_field(self):
        """测试Playwright填充选择框"""
        mock_page = AsyncMock()
        mock_element = AsyncMock()
        mock_element.evaluate.return_value = "select"
        mock_element.get_attribute.return_value = None
        mock_page.query_selector.return_value = mock_element

        handler = FormHandler(mock_page)
        handler.is_playwright = True

        result = await handler._fill_field_playwright("#select", "Option 1")

        assert result["success"] is True
        assert result["value"] == "Option 1"
        mock_element.select_option.assert_called_once_with(label="Option 1")

    @pytest.mark.asyncio
    async def test_playwright_fill_checkbox(self):
        """测试Playwright填充复选框"""
        mock_page = AsyncMock()
        mock_element = AsyncMock()
        mock_element.evaluate.return_value = "input"
        mock_element.get_attribute.return_value = "checkbox"
        mock_element.is_checked.return_value = False
        mock_page.query_selector.return_value = mock_element

        handler = FormHandler(mock_page)
        handler.is_playwright = True

        result = await handler._fill_field_playwright("#checkbox", True)

        assert result["success"] is True
        assert result["value"] is True
        mock_element.check.assert_called_once()

    @pytest.mark.asyncio
    async def test_playwright_fill_text_input(self):
        """测试Playwright填充文本输入"""
        mock_page = AsyncMock()
        mock_element = AsyncMock()
        mock_element.evaluate.return_value = "input"
        mock_element.get_attribute.return_value = "text"
        mock_page.query_selector.return_value = mock_element

        handler = FormHandler(mock_page)
        handler.is_playwright = True

        result = await handler._fill_field_playwright("#text", "test value")

        assert result["success"] is True
        assert result["value"] == "test value"
        mock_element.fill.assert_called_once_with("test value")

    @pytest.mark.asyncio
    async def test_playwright_fill_element_not_found(self):
        """测试Playwright元素未找到"""
        mock_page = AsyncMock()
        mock_page.query_selector.return_value = None

        handler = FormHandler(mock_page)
        handler.is_playwright = True

        result = await handler._fill_field_playwright("#nonexistent", "value")

        assert result["success"] is False
        assert result["error"] == "Element not found"

    @pytest.mark.asyncio
    async def test_playwright_submit_form_with_button(self):
        """测试Playwright提交表单（指定按钮）"""
        mock_page = AsyncMock()
        mock_page.url = "https://example.com/success"
        mock_page.wait_for_load_state = AsyncMock()

        handler = FormHandler(mock_page)
        handler.is_playwright = True

        result = await handler._submit_form_playwright("#submit-btn")

        assert result["success"] is True
        assert result["new_url"] == "https://example.com/success"
        mock_page.click.assert_called_once_with("#submit-btn")

    @pytest.mark.asyncio
    async def test_playwright_submit_form_auto_find(self):
        """测试Playwright自动查找提交按钮"""
        mock_page = AsyncMock()
        mock_page.url = "https://example.com/success"
        mock_page.click.side_effect = [
            Exception("Not found"),
            None,
        ]  # 第一个失败，第二个成功
        mock_page.wait_for_load_state = AsyncMock()

        handler = FormHandler(mock_page)
        handler.is_playwright = True

        result = await handler._submit_form_playwright()

        assert result["success"] is True
        # 应该尝试多个选择器
        assert mock_page.click.call_count >= 2


class TestFormHandlingErrorCases:
    """测试表单处理错误情况"""

    @pytest.mark.asyncio
    async def test_selenium_field_not_found(self):
        """测试Selenium字段未找到"""
        mock_driver = Mock()
        from selenium.common.exceptions import NoSuchElementException

        mock_driver.find_element.side_effect = NoSuchElementException(
            "Element not found"
        )

        handler = FormHandler(mock_driver)

        result = await handler._fill_field_selenium("#nonexistent", "value")

        assert result["success"] is False
        assert "Element not found" in result["error"]

    @pytest.mark.asyncio
    async def test_playwright_field_error(self):
        """测试Playwright字段操作错误"""
        mock_page = AsyncMock()
        mock_element = AsyncMock()
        mock_element.evaluate.side_effect = Exception("Evaluation error")
        mock_page.query_selector.return_value = mock_element

        handler = FormHandler(mock_page)
        handler.is_playwright = True

        result = await handler._fill_field_playwright("#field", "value")

        assert result["success"] is False
        assert "Evaluation error" in result["error"]

    @pytest.mark.asyncio
    async def test_selenium_submit_no_button_found(self):
        """测试Selenium提交时找不到按钮"""
        mock_driver = Mock()
        mock_driver.current_url = "https://example.com"
        from selenium.common.exceptions import NoSuchElementException

        mock_driver.find_element.side_effect = NoSuchElementException(
            "Button not found"
        )

        # 模拟找到表单并提交
        mock_form = Mock()
        mock_driver.find_element.side_effect = [
            NoSuchElementException("Submit button not found"),
            NoSuchElementException("Another button not found"),
            mock_form,  # 最后找到表单
        ]

        handler = FormHandler(mock_driver)

        with patch("asyncio.sleep"):
            result = await handler._submit_form_selenium()

        # 应该尝试直接提交表单
        assert mock_driver.find_element.call_count > 1
