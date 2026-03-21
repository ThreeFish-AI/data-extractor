"""反检测抓取 (anti_detection) 单元测试。"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock

from extractor.anti_detection import AntiDetectionScraper


class TestAntiDetectionScraperInit:
    """AntiDetectionScraper 初始化测试。"""

    def test_init_attributes(self):
        """初始化属性校验。"""
        scraper = AntiDetectionScraper()
        assert scraper.driver is None
        assert scraper.page is None
        assert scraper.browser is None
        assert scraper.context is None
        assert scraper.playwright is None
        assert scraper.ua is not None

    def test_init_user_agent(self):
        """UserAgent 实例可用。"""
        scraper = AntiDetectionScraper()
        # UserAgent 实例应该有 random 属性
        assert hasattr(scraper.ua, "random")


class TestAntiDetectionScraperStealth:
    """AntiDetectionScraper 隐身抓取测试。"""

    @pytest.mark.asyncio
    async def test_invalid_stealth_method(self):
        """无效隐身方法返回错误。"""
        scraper = AntiDetectionScraper()
        result = await scraper.scrape_with_stealth(
            url="https://example.com", method="invalid_method"
        )
        assert "error" in result

    @pytest.mark.asyncio
    async def test_selenium_stealth_method_called(self):
        """Selenium 隐身方法被正确调用。"""
        scraper = AntiDetectionScraper()
        with patch.object(
            scraper,
            "_scrape_with_selenium_stealth",
            new_callable=AsyncMock,
            return_value={"title": "Test", "content": {}},
        ) as mock_method, patch.object(
            scraper, "cleanup", new_callable=AsyncMock
        ):
            result = await scraper.scrape_with_stealth(
                url="https://example.com", method="selenium"
            )
            mock_method.assert_called_once()
            assert result["title"] == "Test"

    @pytest.mark.asyncio
    async def test_playwright_stealth_method_called(self):
        """Playwright 隐身方法被正确调用。"""
        scraper = AntiDetectionScraper()
        with patch.object(
            scraper,
            "_scrape_with_playwright_stealth",
            new_callable=AsyncMock,
            return_value={"title": "Test", "content": {}},
        ) as mock_method, patch.object(
            scraper, "cleanup", new_callable=AsyncMock
        ):
            result = await scraper.scrape_with_stealth(
                url="https://example.com", method="playwright"
            )
            mock_method.assert_called_once()

    @pytest.mark.asyncio
    async def test_cleanup_called_on_success(self):
        """成功执行后清理资源。"""
        scraper = AntiDetectionScraper()
        with patch.object(
            scraper,
            "_scrape_with_selenium_stealth",
            new_callable=AsyncMock,
            return_value={"title": "Test", "content": {}},
        ), patch.object(scraper, "cleanup", new_callable=AsyncMock) as mock_cleanup:
            await scraper.scrape_with_stealth(url="https://example.com")
            mock_cleanup.assert_called_once()

    @pytest.mark.asyncio
    async def test_cleanup_called_on_error(self):
        """异常时仍然清理资源。"""
        scraper = AntiDetectionScraper()
        with patch.object(
            scraper,
            "_scrape_with_selenium_stealth",
            new_callable=AsyncMock,
            side_effect=Exception("test error"),
        ), patch.object(scraper, "cleanup", new_callable=AsyncMock) as mock_cleanup:
            result = await scraper.scrape_with_stealth(url="https://example.com")
            mock_cleanup.assert_called_once()
            assert "error" in result


class TestAntiDetectionScraperCleanup:
    """AntiDetectionScraper 资源清理测试。"""

    @pytest.mark.asyncio
    async def test_cleanup_driver(self):
        """清理 Selenium driver。"""
        scraper = AntiDetectionScraper()
        mock_driver = MagicMock()
        scraper.driver = mock_driver

        await scraper.cleanup()

        mock_driver.quit.assert_called_once()
        assert scraper.driver is None

    @pytest.mark.asyncio
    async def test_cleanup_playwright(self):
        """清理 Playwright 资源。"""
        scraper = AntiDetectionScraper()
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
    async def test_cleanup_no_resources(self):
        """无资源时清理不报错。"""
        scraper = AntiDetectionScraper()
        await scraper.cleanup()  # 不应抛出异常


class TestImportCompatibility:
    """导入兼容性测试。"""

    def test_import_from_anti_detection(self):
        """直接从 anti_detection 模块导入。"""
        from extractor.anti_detection import AntiDetectionScraper

        assert AntiDetectionScraper is not None

    def test_import_from_advanced_features_shim(self):
        """通过 advanced_features 垫片导入。"""
        from extractor.advanced_features import AntiDetectionScraper

        assert AntiDetectionScraper is not None
