"""
单元测试：配置管理模块
测试 extractor.config 模块的配置加载、验证和使用
"""

import pytest
import os
from unittest.mock import patch, Mock
from pydantic import ValidationError

from extractor.config import DataExtractorSettings, settings


class TestDataExtractorSettings:
    """测试配置设置类"""

    def test_default_settings(self):
        """测试默认配置值"""
        config = DataExtractorSettings()

        # 测试默认值
        assert config.server_name == "Data Extractor"
        assert config.server_version == "0.1.4"
        assert config.enable_javascript is False
        assert config.concurrent_requests == 16
        assert config.request_timeout == 30.0
        assert config.rate_limit_requests_per_minute == 60
        assert config.max_retries == 3
        assert config.retry_delay == 1.0
        assert config.cache_ttl_hours == 24
        assert config.browser_timeout == 30
        assert config.browser_headless is True

    def test_environment_variable_loading(self):
        """测试环境变量加载"""
        env_vars = {
            "DATA_EXTRACTOR_SERVER_NAME": "Custom Server",
            "DATA_EXTRACTOR_ENABLE_JAVASCRIPT": "true",
            "DATA_EXTRACTOR_CONCURRENT_REQUESTS": "32",
            "DATA_EXTRACTOR_REQUEST_TIMEOUT": "60.0",
            "DATA_EXTRACTOR_RATE_LIMIT_REQUESTS_PER_MINUTE": "120",
            "DATA_EXTRACTOR_MAX_RETRIES": "5",
            "DATA_EXTRACTOR_BROWSER_HEADLESS": "false",
        }

        with patch.dict(os.environ, env_vars):
            config = DataExtractorSettings()

            assert config.server_name == "Custom Server"
            assert config.enable_javascript is True
            assert config.concurrent_requests == 32
            assert config.request_timeout == 60.0
            assert config.rate_limit_requests_per_minute == 120
            assert config.max_retries == 5
            assert config.browser_headless is False

    def test_boolean_environment_variables(self):
        """测试布尔型环境变量的解析"""
        # 测试各种布尔值表示
        boolean_test_cases = [
            ("true", True),
            ("True", True),
            ("TRUE", True),
            ("1", True),
            ("yes", True),
            ("false", False),
            ("False", False),
            ("FALSE", False),
            ("0", False),
            ("no", False),
        ]

        for env_value, expected_value in boolean_test_cases:
            with patch.dict(
                os.environ, {"DATA_EXTRACTOR_ENABLE_JAVASCRIPT": env_value}
            ):
                config = DataExtractorSettings()
                assert config.enable_javascript is expected_value, (
                    f"Failed for {env_value}"
                )

    def test_numeric_validation(self):
        """测试数值型配置的验证"""
        # 测试有效的数值
        valid_configs = [
            {"concurrent_requests": 1},
            {"concurrent_requests": 100},
            {"request_timeout": 0.1},
            {"request_timeout": 300.0},
            {"rate_limit_requests_per_minute": 1},
            {"max_retries": 0},
            {"max_retries": 10},
        ]

        for config_data in valid_configs:
            config = DataExtractorSettings(**config_data)
            assert config is not None

        # 测试无效的数值
        invalid_configs = [
            {"concurrent_requests": 0},  # 必须大于0
            {"concurrent_requests": -1},  # 不能为负数
            {"request_timeout": -1.0},  # 不能为负数
            {"rate_limit_requests_per_minute": -1},  # 不能为负数
            {"max_retries": -1},  # 不能为负数
        ]

        for config_data in invalid_configs:
            with pytest.raises(ValidationError):
                DataExtractorSettings(**config_data)

    def test_proxy_configuration(self):
        """测试代理配置"""
        # 无代理配置
        config = DataExtractorSettings(use_proxy=False)
        assert config.use_proxy is False
        assert config.proxy_url is None

        # 有代理配置
        proxy_url = "http://proxy.example.com:8080"
        config = DataExtractorSettings(use_proxy=True, proxy_url=proxy_url)
        assert config.use_proxy is True
        assert config.proxy_url == proxy_url

    def test_user_agent_configuration(self):
        """测试User-Agent配置"""
        # 随机User-Agent
        config = DataExtractorSettings(use_random_user_agent=True)
        assert config.use_random_user_agent is True
        assert config.default_user_agent is not None

        # 固定User-Agent
        custom_ua = "Custom Bot 1.0"
        config = DataExtractorSettings(
            use_random_user_agent=False, default_user_agent=custom_ua
        )
        assert config.use_random_user_agent is False
        assert config.default_user_agent == custom_ua

    def test_cache_configuration(self):
        """测试缓存配置"""
        config = DataExtractorSettings(
            enable_caching=True, cache_ttl_hours=48, cache_max_size=200
        )

        assert config.enable_caching is True
        assert config.cache_ttl_hours == 48
        assert config.cache_max_size == 200

    def test_logging_configuration(self):
        """测试日志配置"""
        config = DataExtractorSettings(
            log_level="DEBUG", log_requests=True, log_responses=False
        )

        assert config.log_level == "DEBUG"
        assert config.log_requests is True
        assert config.log_responses is False

    def test_browser_configuration(self):
        """测试浏览器配置"""
        config = DataExtractorSettings(
            browser_timeout=60, browser_headless=False, browser_window_size="1920x1080"
        )

        assert config.browser_timeout == 60
        assert config.browser_headless is False
        assert config.browser_window_size == "1920x1080"


class TestGlobalSettings:
    """测试全局设置实例"""

    def test_global_settings_instance(self):
        """测试全局settings实例"""
        assert settings is not None
        assert isinstance(settings, DataExtractorSettings)
        assert settings.server_name is not None
        assert settings.server_version is not None

    def test_settings_immutability(self):
        """测试设置的不可变性（一旦创建就固定）"""
        original_name = settings.server_name

        # 不应该能直接修改settings
        with pytest.raises(ValidationError):
            settings.server_name = "Modified Name"

        # 验证值没有被修改
        assert settings.server_name == original_name

    @patch.dict(os.environ, {"DATA_EXTRACTOR_SERVER_NAME": "Test Server"})
    def test_settings_environment_override(self):
        """测试环境变量覆盖设置"""
        # 重新导入以获取新的设置
        from importlib import reload
        import extractor.config

        reload(extractor.config)

        assert extractor.config.settings.server_name == "Test Server"


class TestConfigurationValidation:
    """测试配置验证逻辑"""

    def test_timeout_validation(self):
        """测试超时配置验证"""
        # 有效超时配置
        valid_timeouts = [0.1, 1.0, 30.0, 300.0]
        for timeout in valid_timeouts:
            config = DataExtractorSettings(
                request_timeout=timeout, browser_timeout=int(timeout)
            )
            assert config.request_timeout == timeout

        # 无效超时配置
        with pytest.raises(ValidationError):
            DataExtractorSettings(request_timeout=-1.0)

        with pytest.raises(ValidationError):
            DataExtractorSettings(browser_timeout=-1)

    def test_concurrency_validation(self):
        """测试并发配置验证"""
        # 有效并发配置
        valid_values = [1, 8, 16, 32, 64]
        for value in valid_values:
            config = DataExtractorSettings(concurrent_requests=value)
            assert config.concurrent_requests == value

        # 无效并发配置
        invalid_values = [0, -1, -10]
        for value in invalid_values:
            with pytest.raises(ValidationError):
                DataExtractorSettings(concurrent_requests=value)

    def test_rate_limit_validation(self):
        """测试速率限制配置验证"""
        # 有效速率限制
        valid_rates = [1, 60, 120, 1000]
        for rate in valid_rates:
            config = DataExtractorSettings(rate_limit_requests_per_minute=rate)
            assert config.rate_limit_requests_per_minute == rate

        # 无效速率限制
        with pytest.raises(ValidationError):
            DataExtractorSettings(rate_limit_requests_per_minute=-1)

    def test_retry_configuration_validation(self):
        """测试重试配置验证"""
        # 有效重试配置
        config = DataExtractorSettings(max_retries=5, retry_delay=2.0)
        assert config.max_retries == 5
        assert config.retry_delay == 2.0

        # 边界情况
        config = DataExtractorSettings(max_retries=0)  # 0次重试应该有效
        assert config.max_retries == 0

        # 无效重试配置
        with pytest.raises(ValidationError):
            DataExtractorSettings(max_retries=-1)

        with pytest.raises(ValidationError):
            DataExtractorSettings(retry_delay=-1.0)


class TestConfigurationIntegration:
    """测试配置集成和实际使用"""

    def test_scrapy_settings_generation(self):
        """测试Scrapy设置生成"""
        config = DataExtractorSettings(
            concurrent_requests=32,
            request_timeout=60.0,
            use_random_user_agent=True,
            default_user_agent="Custom Bot",
        )

        # 验证配置可以用于Scrapy设置
        assert config.concurrent_requests > 0
        assert config.request_timeout > 0
        assert config.default_user_agent is not None

    def test_browser_settings_generation(self):
        """测试浏览器设置生成"""
        config = DataExtractorSettings(
            browser_timeout=45, browser_headless=True, browser_window_size="1366x768"
        )

        # 验证浏览器配置的有效性
        assert config.browser_timeout > 0
        assert isinstance(config.browser_headless, bool)
        assert "x" in config.browser_window_size  # 窗口尺寸格式

    def test_proxy_settings_integration(self):
        """测试代理设置集成"""
        config = DataExtractorSettings(
            use_proxy=True, proxy_url="http://proxy.example.com:8080"
        )

        if config.use_proxy:
            assert config.proxy_url is not None
            assert config.proxy_url.startswith("http")

    def test_cache_settings_integration(self):
        """测试缓存设置集成"""
        config = DataExtractorSettings(
            enable_caching=True, cache_ttl_hours=12, cache_max_size=150
        )

        if config.enable_caching:
            assert config.cache_ttl_hours > 0
            assert config.cache_max_size > 0

    def test_logging_settings_integration(self):
        """测试日志设置集成"""
        valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

        for level in valid_log_levels:
            config = DataExtractorSettings(
                log_level=level, log_requests=True, log_responses=True
            )
            assert config.log_level == level
            assert isinstance(config.log_requests, bool)
            assert isinstance(config.log_responses, bool)


class TestConfigurationEdgeCases:
    """测试配置边界情况和异常处理"""

    def test_missing_environment_variables(self):
        """测试环境变量缺失时的处理"""
        # 清空相关环境变量
        env_vars_to_clear = [
            "DATA_EXTRACTOR_SERVER_NAME",
            "DATA_EXTRACTOR_ENABLE_JAVASCRIPT",
            "DATA_EXTRACTOR_CONCURRENT_REQUESTS",
        ]

        with patch.dict(os.environ, {}, clear=True):
            config = DataExtractorSettings()
            # 应该使用默认值
            assert config.server_name == "Data Extractor"
            assert config.enable_javascript is False
            assert config.concurrent_requests == 16

    def test_invalid_environment_variable_types(self):
        """测试无效环境变量类型处理"""
        invalid_env_vars = {
            "DATA_EXTRACTOR_CONCURRENT_REQUESTS": "not-a-number",
            "DATA_EXTRACTOR_REQUEST_TIMEOUT": "invalid-float",
            "DATA_EXTRACTOR_ENABLE_JAVASCRIPT": "maybe",
        }

        with patch.dict(os.environ, invalid_env_vars):
            # 应该处理无效值并使用默认值或抛出异常
            with pytest.raises((ValidationError, ValueError)):
                DataExtractorSettings()

    def test_extreme_configuration_values(self):
        """测试极端配置值"""
        # 最小值
        config = DataExtractorSettings(
            concurrent_requests=1,
            request_timeout=0.1,
            rate_limit_requests_per_minute=1,
            max_retries=0,
            retry_delay=0.1,
        )
        assert config is not None

        # 大值（但合理）
        config = DataExtractorSettings(
            concurrent_requests=1000,
            request_timeout=3600.0,
            rate_limit_requests_per_minute=10000,
            max_retries=100,
            retry_delay=60.0,
        )
        assert config is not None
