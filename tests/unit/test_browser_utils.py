"""浏览器配置工具 (browser_utils) 单元测试。"""

import pytest

from extractor.browser_utils import build_chrome_options


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
