"""浏览器配置工具 (browser_utils) 单元测试。"""

import pytest
from unittest.mock import AsyncMock, Mock, patch

from extractor.browser_utils import build_chrome_options, playwright_session, selenium_session


class TestBuildChromeOptions:
    """build_chrome_options 函数测试。"""

    def test_default_options(self):
        """默认选项包含基础稳定性参数。"""
        options = build_chrome_options()
        args = options.arguments

        assert "--headless" in args
        assert "--no-sandbox" in args
        assert "--disable-dev-shm-usage" in args
        assert "--disable-gpu" in args
        assert "--window-size=1920,1080" in args

    def test_headless_disabled(self):
        """禁用无头模式。"""
        options = build_chrome_options(headless=False)
        assert "--headless" not in options.arguments

    def test_headless_enabled(self):
        """启用无头模式。"""
        options = build_chrome_options(headless=True)
        assert "--headless" in options.arguments

    def test_stealth_mode(self):
        """反检测模式包含额外选项。"""
        options = build_chrome_options(stealth=True)
        args = options.arguments

        assert "--disable-extensions" in args
        assert "--disable-plugins" in args
        assert "--disable-images" in args
        assert "--disable-javascript" not in args  # 禁用 JS 与反检测语义矛盾
        assert "--start-maximized" in args
        assert "--disable-blink-features=AutomationControlled" in args

        # 验证 experimental options
        exp_opts = options.experimental_options
        assert exp_opts.get("excludeSwitches") == ["enable-automation"]
        assert exp_opts.get("useAutomationExtension") is False

    def test_non_stealth_mode(self):
        """非反检测模式不包含反检测选项。"""
        options = build_chrome_options(stealth=False)
        args = options.arguments

        assert "--disable-extensions" not in args
        assert "--disable-plugins" not in args
        assert "--disable-images" not in args

    def test_custom_user_agent(self):
        """自定义 User-Agent。"""
        ua = "Mozilla/5.0 Custom Agent"
        options = build_chrome_options(user_agent=ua)
        args = options.arguments

        matching = [a for a in args if f"--user-agent={ua}" in a]
        assert len(matching) == 1

    def test_default_user_agent(self):
        """未指定 User-Agent 时使用配置默认值。"""
        options = build_chrome_options()
        args = options.arguments

        ua_args = [a for a in args if "--user-agent=" in a]
        assert len(ua_args) == 1

    def test_custom_proxy(self):
        """自定义代理配置。"""
        proxy = "http://proxy.example.com:8080"
        options = build_chrome_options(proxy_url=proxy)
        args = options.arguments

        assert f"--proxy-server={proxy}" in args

    def test_stealth_with_custom_user_agent(self):
        """反检测模式 + 自定义 User-Agent 组合。"""
        ua = "StealthAgent/1.0"
        options = build_chrome_options(stealth=True, user_agent=ua)
        args = options.arguments

        assert "--disable-extensions" in args
        matching = [a for a in args if f"--user-agent={ua}" in a]
        assert len(matching) == 1

    def test_all_options_combined(self):
        """所有选项组合。"""
        options = build_chrome_options(
            headless=False,
            stealth=True,
            user_agent="TestBot/1.0",
            proxy_url="http://localhost:3128",
        )
        args = options.arguments

        assert "--headless" not in args
        assert "--disable-extensions" in args
        assert any("--user-agent=TestBot/1.0" in a for a in args)
        assert "--proxy-server=http://localhost:3128" in args


class TestSeleniumSession:
    """selenium_session 上下文管理器测试（步骤 7 新增）。"""

    @patch("selenium.webdriver.Chrome")
    def test_yields_driver_and_quits(self, mock_chrome_cls):
        """上下文管理器应 yield driver 并在退出时调用 quit()。"""
        mock_driver = Mock()
        mock_chrome_cls.return_value = mock_driver

        with selenium_session("https://example.com") as driver:
            assert driver is mock_driver
            mock_driver.get.assert_called_once_with("https://example.com")

        mock_driver.quit.assert_called_once()

    @patch("selenium.webdriver.support.ui.WebDriverWait")
    @patch("selenium.webdriver.Chrome")
    def test_waits_for_element(self, mock_chrome_cls, mock_wait_cls):
        """指定 wait_for_element 时应使用 WebDriverWait。"""
        mock_driver = Mock()
        mock_chrome_cls.return_value = mock_driver
        mock_wait_instance = Mock()
        mock_wait_cls.return_value = mock_wait_instance

        with selenium_session("https://example.com", wait_for_element=".content") as driver:
            assert driver is mock_driver

        mock_wait_cls.assert_called_once()
        mock_driver.quit.assert_called_once()

    @patch("selenium.webdriver.Chrome")
    def test_quits_on_exception(self, mock_chrome_cls):
        """即使内部抛异常也应调用 quit()。"""
        mock_driver = Mock()
        mock_chrome_cls.return_value = mock_driver

        with pytest.raises(RuntimeError):
            with selenium_session("https://example.com"):
                raise RuntimeError("test")

        mock_driver.quit.assert_called_once()


class TestPlaywrightSession:
    """playwright_session 上下文管理器测试（步骤 7 新增）。"""

    @staticmethod
    def _setup_playwright_mocks():
        """创建 Playwright mock 链：async_playwright().start() -> pw."""
        mock_page = AsyncMock()
        mock_context = AsyncMock()
        mock_context.new_page.return_value = mock_page
        mock_browser = AsyncMock()
        mock_browser.new_context.return_value = mock_context
        mock_pw = AsyncMock()
        mock_pw.chromium.launch.return_value = mock_browser
        # async_playwright() returns sync object, .start() is async
        mock_instance = Mock()
        mock_instance.start = AsyncMock(return_value=mock_pw)
        return mock_instance, mock_pw, mock_browser, mock_page

    @pytest.mark.asyncio
    async def test_yields_page_and_closes(self):
        """上下文管理器应 yield page 并在退出时关闭资源。"""
        mock_instance, mock_pw, mock_browser, mock_page = self._setup_playwright_mocks()

        with patch("playwright.async_api.async_playwright", return_value=mock_instance):
            async with playwright_session("https://example.com") as page:
                assert page is mock_page
                mock_page.goto.assert_called_once()

            mock_browser.close.assert_called_once()
            mock_pw.stop.assert_called_once()

    @pytest.mark.asyncio
    async def test_waits_for_selector(self):
        """指定 wait_for_element 时应调用 wait_for_selector。"""
        mock_instance, mock_pw, mock_browser, mock_page = self._setup_playwright_mocks()

        with patch("playwright.async_api.async_playwright", return_value=mock_instance):
            async with playwright_session("https://example.com", wait_for_element="#app"):
                pass

            mock_page.wait_for_selector.assert_called_once()

    @pytest.mark.asyncio
    async def test_closes_on_exception(self):
        """即使内部抛异常也应关闭资源。"""
        mock_instance, mock_pw, mock_browser, mock_page = self._setup_playwright_mocks()

        with patch("playwright.async_api.async_playwright", return_value=mock_instance):
            with pytest.raises(RuntimeError):
                async with playwright_session("https://example.com"):
                    raise RuntimeError("test")

            mock_browser.close.assert_called_once()
            mock_pw.stop.assert_called_once()
