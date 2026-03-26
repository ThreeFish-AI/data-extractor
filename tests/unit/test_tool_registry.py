"""
单元测试：tools/_registry.py 公共辅助函数
测试 validate_url, validate_page_range, record_error, elapsed_ms, ToolTimer
"""

import time
from unittest.mock import patch


from extractor.tools._registry import (
    elapsed_ms,
    record_error,
    ToolTimer,
    validate_page_range,
    validate_url,
)


class TestValidateUrl:
    """测试 URL 验证辅助函数"""

    def test_valid_http_url(self):
        assert validate_url("http://example.com") is None

    def test_valid_https_url(self):
        assert validate_url("https://example.com/path?q=1") is None

    def test_missing_scheme(self):
        assert validate_url("example.com") is not None

    def test_missing_netloc(self):
        assert validate_url("http://") is not None

    def test_empty_string(self):
        assert validate_url("") is not None

    def test_relative_path(self):
        assert validate_url("/path/to/page") is not None


class TestValidatePageRange:
    """测试页码范围验证辅助函数"""

    def test_none_returns_none(self):
        result, error = validate_page_range(None)
        assert result is None
        assert error is None

    def test_empty_list_returns_none(self):
        result, error = validate_page_range([])
        assert result is None
        assert error is None

    def test_valid_range(self):
        result, error = validate_page_range([0, 10])
        assert result == (0, 10)
        assert error is None

    def test_wrong_length(self):
        result, error = validate_page_range([1])
        assert result is None
        assert "exactly 2 elements" in error

    def test_three_elements(self):
        result, error = validate_page_range([1, 2, 3])
        assert result is None
        assert "exactly 2 elements" in error

    def test_negative_start(self):
        result, error = validate_page_range([-1, 5])
        assert result is None
        assert "non-negative" in error

    def test_negative_end(self):
        result, error = validate_page_range([0, -1])
        assert result is None
        assert "non-negative" in error

    def test_start_equals_end(self):
        result, error = validate_page_range([5, 5])
        assert result is None
        assert "less than" in error

    def test_start_greater_than_end(self):
        result, error = validate_page_range([10, 5])
        assert result is None
        assert "less than" in error


class TestRecordError:
    """测试错误记录辅助函数"""

    def test_returns_user_message(self):
        with patch("extractor.tools._registry.metrics_collector") as mock_metrics:
            msg = record_error(
                ValueError("test error"), "https://example.com", "simple", 100
            )
            assert isinstance(msg, str)
            assert len(msg) > 0
            mock_metrics.record_request.assert_called_once()

    def test_records_metrics(self):
        with patch("extractor.tools._registry.metrics_collector") as mock_metrics:
            record_error(
                TimeoutError("timeout"), "https://example.com", "selenium", 5000
            )
            mock_metrics.record_request.assert_called_once_with(
                "https://example.com", False, 5000, "selenium", "timeout"
            )

    def test_categorize_timeout(self):
        """timeout 关键字归类为 timeout。"""
        with patch("extractor.tools._registry.metrics_collector") as mock_metrics:
            msg = record_error(
                Exception("Request timeout"), "https://example.com", "simple", 100
            )
            assert msg == "Request timeout"
            mock_metrics.record_request.assert_called_once_with(
                "https://example.com", False, 100, "simple", "timeout"
            )

    def test_categorize_connection(self):
        """connection 关键字归类为 connection。"""
        with patch("extractor.tools._registry.metrics_collector") as mock_metrics:
            msg = record_error(
                Exception("Connection refused"), "https://example.com", "simple", 100
            )
            assert msg == "Connection refused"
            mock_metrics.record_request.assert_called_once_with(
                "https://example.com", False, 100, "simple", "connection"
            )

    def test_categorize_not_found(self):
        """404 归类为 not_found。"""
        with patch("extractor.tools._registry.metrics_collector") as mock_metrics:
            msg = record_error(
                Exception("HTTP 404"), "https://example.com", "simple", 100
            )
            assert msg == "HTTP 404"
            mock_metrics.record_request.assert_called_once_with(
                "https://example.com", False, 100, "simple", "not_found"
            )

    def test_categorize_forbidden(self):
        """403 归类为 forbidden。"""
        with patch("extractor.tools._registry.metrics_collector") as mock_metrics:
            msg = record_error(
                Exception("HTTP 403"), "https://example.com", "simple", 100
            )
            assert msg == "HTTP 403"
            mock_metrics.record_request.assert_called_once_with(
                "https://example.com", False, 100, "simple", "forbidden"
            )

    def test_categorize_anti_bot(self):
        """cloudflare 关键字归类为 anti_bot。"""
        with patch("extractor.tools._registry.metrics_collector") as mock_metrics:
            msg = record_error(
                Exception("Cloudflare challenge"), "https://example.com", "simple", 100
            )
            assert msg == "Cloudflare challenge"
            mock_metrics.record_request.assert_called_once_with(
                "https://example.com", False, 100, "simple", "anti_bot"
            )

    def test_categorize_unknown(self):
        """无法匹配的错误归类为 unknown。"""
        with patch("extractor.tools._registry.metrics_collector") as mock_metrics:
            msg = record_error(
                Exception("Some random error"), "https://example.com", "simple", 100
            )
            assert msg == "Some random error"
            mock_metrics.record_request.assert_called_once_with(
                "https://example.com", False, 100, "simple", "unknown"
            )

    def test_logs_error(self):
        """record_error 应记录错误日志。"""
        with patch("extractor.tools._registry.metrics_collector"):
            with patch("extractor.tools._registry.logger") as mock_logger:
                record_error(
                    Exception("test error"), "https://example.com", "simple", 100
                )
                mock_logger.error.assert_called_once()


class TestElapsedMs:
    """测试耗时计算辅助函数"""

    def test_returns_int(self):
        start = time.time()
        result = elapsed_ms(start)
        assert isinstance(result, int)

    def test_positive_duration(self):
        start = time.time() - 0.1  # 100ms ago
        result = elapsed_ms(start)
        assert result >= 90  # Allow some tolerance


class TestToolTimer:
    """测试 ToolTimer 统一计时与指标辅助类"""

    def test_init_stores_url_and_method(self):
        """初始化保存 url 和 method。"""
        timer = ToolTimer("https://example.com", "stealth_selenium")
        assert timer.url == "https://example.com"
        assert timer.method == "stealth_selenium"
        assert timer.duration_ms == 0

    def test_elapsed_returns_positive(self):
        """elapsed() 返回正整数毫秒值。"""
        timer = ToolTimer("https://example.com", "simple")
        ms = timer.elapsed()
        assert isinstance(ms, int)
        assert ms >= 0
        assert timer.duration_ms == ms

    def test_record_success_records_metrics(self):
        """record_success() 记录成功指标并返回 duration_ms。"""
        with patch("extractor.tools._registry.metrics_collector") as mock_metrics:
            timer = ToolTimer("https://example.com", "markdown_auto")
            ms = timer.record_success()
            assert isinstance(ms, int)
            assert ms >= 0
            mock_metrics.record_request.assert_called_once_with(
                "https://example.com", True, ms, "markdown_auto"
            )

    def test_record_failure_records_metrics_and_returns_message(self):
        """record_failure() 记录失败指标并返回用户友好错误信息。"""
        with patch("extractor.tools._registry.metrics_collector") as mock_metrics:
            timer = ToolTimer("https://example.com", "pdf_pymupdf")
            error = ValueError("test error")
            msg = timer.record_failure(error)
            assert isinstance(msg, str)
            assert len(msg) > 0
            mock_metrics.record_request.assert_called_once()

    def test_url_can_be_updated(self):
        """url 属性可以在创建后更新（如 URL 规范化场景）。"""
        timer = ToolTimer("https://example.com", "stealth_selenium")
        timer.url = "https://example.com/"
        assert timer.url == "https://example.com/"
