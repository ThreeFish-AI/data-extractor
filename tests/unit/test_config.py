"""
单元测试：配置管理模块
测试 negentropy.perceives.config 模块的配置加载、验证和使用
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
from pydantic import ValidationError

from negentropy.perceives import __version__
from negentropy.perceives.config import (
    NegentropyPerceivesSettings,
    _PROJECT_ROOT,
    _resolve_env_files,
    describe_config_sources,
    settings,
)


class TestNegentropyPerceivesSettings:
    """测试配置设置类"""

    def test_default_settings(self):
        """测试默认配置值"""
        config = NegentropyPerceivesSettings()

        # 测试默认值（考虑环境变量覆盖）
        assert config.server_name == "negentropy-perceives"
        assert config.server_version == __version__
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
            "NEGENTROPY_PERCEIVES_SERVER_NAME": "Custom Server",
            "NEGENTROPY_PERCEIVES_ENABLE_JAVASCRIPT": "true",
            "NEGENTROPY_PERCEIVES_CONCURRENT_REQUESTS": "32",
            "NEGENTROPY_PERCEIVES_REQUEST_TIMEOUT": "60.0",
            "NEGENTROPY_PERCEIVES_RATE_LIMIT_REQUESTS_PER_MINUTE": "120",
            "NEGENTROPY_PERCEIVES_MAX_RETRIES": "5",
            "NEGENTROPY_PERCEIVES_BROWSER_HEADLESS": "false",
        }

        with patch.dict(os.environ, env_vars):
            config = NegentropyPerceivesSettings()

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
                os.environ, {"NEGENTROPY_PERCEIVES_ENABLE_JAVASCRIPT": env_value}
            ):
                config = NegentropyPerceivesSettings()
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
            config = NegentropyPerceivesSettings(**config_data)
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
                NegentropyPerceivesSettings(**config_data)

    def test_proxy_configuration(self):
        """测试代理配置"""
        # 无代理配置
        config = NegentropyPerceivesSettings(use_proxy=False)
        assert config.use_proxy is False
        assert config.proxy_url is None

        # 有代理配置
        proxy_url = "http://proxy.example.com:8080"
        config = NegentropyPerceivesSettings(use_proxy=True, proxy_url=proxy_url)
        assert config.use_proxy is True
        assert config.proxy_url == proxy_url

    def test_user_agent_configuration(self):
        """测试User-Agent配置"""
        # 随机User-Agent
        config = NegentropyPerceivesSettings(use_random_user_agent=True)
        assert config.use_random_user_agent is True
        assert config.default_user_agent is not None

        # 固定User-Agent
        custom_ua = "Custom Bot 1.0"
        config = NegentropyPerceivesSettings(
            use_random_user_agent=False, default_user_agent=custom_ua
        )
        assert config.use_random_user_agent is False
        assert config.default_user_agent == custom_ua

    def test_cache_configuration(self):
        """测试缓存配置"""
        config = NegentropyPerceivesSettings(
            enable_caching=True, cache_ttl_hours=48, cache_max_size=200
        )

        assert config.enable_caching is True
        assert config.cache_ttl_hours == 48
        assert config.cache_max_size == 200

    def test_logging_configuration(self):
        """测试日志配置"""
        config = NegentropyPerceivesSettings(
            log_level="DEBUG", log_requests=True, log_responses=False
        )

        assert config.log_level == "DEBUG"
        assert config.log_requests is True
        assert config.log_responses is False

    def test_browser_configuration(self):
        """测试浏览器配置"""
        config = NegentropyPerceivesSettings(
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
        assert isinstance(settings, NegentropyPerceivesSettings)
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

    @patch.dict(os.environ, {"NEGENTROPY_PERCEIVES_SERVER_NAME": "Test Server"})
    def test_settings_environment_override(self):
        """测试环境变量覆盖设置"""
        # 重新导入以获取新的设置
        from importlib import reload

        import negentropy.perceives.config

        reload(negentropy.perceives.config)

        assert negentropy.perceives.config.settings.server_name == "Test Server"


class TestConfigurationValidation:
    """测试配置验证逻辑"""

    def test_timeout_validation(self):
        """测试超时配置验证"""
        # 有效超时配置
        valid_timeouts = [0.1, 1.0, 30.0, 300.0]
        for timeout in valid_timeouts:
            config = NegentropyPerceivesSettings(
                request_timeout=timeout, browser_timeout=int(timeout)
            )
            assert config.request_timeout == timeout

        # 无效超时配置
        with pytest.raises(ValidationError):
            NegentropyPerceivesSettings(request_timeout=-1.0)

        with pytest.raises(ValidationError):
            NegentropyPerceivesSettings(browser_timeout=-1)

    def test_concurrency_validation(self):
        """测试并发配置验证"""
        # 有效并发配置
        valid_values = [1, 8, 16, 32, 64]
        for value in valid_values:
            config = NegentropyPerceivesSettings(concurrent_requests=value)
            assert config.concurrent_requests == value

        # 无效并发配置
        invalid_values = [0, -1, -10]
        for value in invalid_values:
            with pytest.raises(ValidationError):
                NegentropyPerceivesSettings(concurrent_requests=value)

    def test_rate_limit_validation(self):
        """测试速率限制配置验证"""
        # 有效速率限制
        valid_rates = [1, 60, 120, 1000]
        for rate in valid_rates:
            config = NegentropyPerceivesSettings(rate_limit_requests_per_minute=rate)
            assert config.rate_limit_requests_per_minute == rate

        # 无效速率限制
        with pytest.raises(ValidationError):
            NegentropyPerceivesSettings(rate_limit_requests_per_minute=-1)

    def test_retry_configuration_validation(self):
        """测试重试配置验证"""
        # 有效重试配置
        config = NegentropyPerceivesSettings(max_retries=5, retry_delay=2.0)
        assert config.max_retries == 5
        assert config.retry_delay == 2.0

        # 边界情况
        config = NegentropyPerceivesSettings(max_retries=0)  # 0次重试应该有效
        assert config.max_retries == 0

        # 无效重试配置
        with pytest.raises(ValidationError):
            NegentropyPerceivesSettings(max_retries=-1)

        with pytest.raises(ValidationError):
            NegentropyPerceivesSettings(retry_delay=-1.0)


class TestConfigurationIntegration:
    """测试配置集成和实际使用"""

    def test_scrapy_settings_generation(self):
        """测试Scrapy设置生成"""
        config = NegentropyPerceivesSettings(
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
        config = NegentropyPerceivesSettings(
            browser_timeout=45, browser_headless=True, browser_window_size="1366x768"
        )

        # 验证浏览器配置的有效性
        assert config.browser_timeout > 0
        assert isinstance(config.browser_headless, bool)
        assert "x" in config.browser_window_size  # 窗口尺寸格式

    def test_proxy_settings_integration(self):
        """测试代理设置集成"""
        config = NegentropyPerceivesSettings(
            use_proxy=True, proxy_url="http://proxy.example.com:8080"
        )

        if config.use_proxy:
            assert config.proxy_url is not None
            assert config.proxy_url.startswith("http")

    def test_cache_settings_integration(self):
        """测试缓存设置集成"""
        config = NegentropyPerceivesSettings(
            enable_caching=True, cache_ttl_hours=12, cache_max_size=150
        )

        if config.enable_caching:
            assert config.cache_ttl_hours > 0
            assert config.cache_max_size > 0

    def test_logging_settings_integration(self):
        """测试日志设置集成"""
        valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

        for level in valid_log_levels:
            config = NegentropyPerceivesSettings(
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
            "NEGENTROPY_PERCEIVES_SERVER_NAME",
            "NEGENTROPY_PERCEIVES_ENABLE_JAVASCRIPT",
            "NEGENTROPY_PERCEIVES_CONCURRENT_REQUESTS",
        ]

        with patch.dict(os.environ, {}, clear=True):
            config = NegentropyPerceivesSettings()
            # 应该使用默认值
            assert config.server_name == "negentropy-perceives"
            assert config.enable_javascript is False
            assert config.concurrent_requests == 16

    def test_invalid_environment_variable_types(self):
        """测试无效环境变量类型处理"""
        invalid_env_vars = {
            "NEGENTROPY_PERCEIVES_CONCURRENT_REQUESTS": "not-a-number",
            "NEGENTROPY_PERCEIVES_REQUEST_TIMEOUT": "invalid-float",
            "NEGENTROPY_PERCEIVES_ENABLE_JAVASCRIPT": "maybe",
        }

        with patch.dict(os.environ, invalid_env_vars):
            # 应该处理无效值并使用默认值或抛出异常
            with pytest.raises((ValidationError, ValueError)):
                NegentropyPerceivesSettings()

    def test_extreme_configuration_values(self):
        """测试极端配置值"""
        # 最小值
        config = NegentropyPerceivesSettings(
            concurrent_requests=1,
            request_timeout=0.1,
            rate_limit_requests_per_minute=1,
            max_retries=0,
            retry_delay=0.1,
        )
        assert config is not None

        # 大值（但合理）
        config = NegentropyPerceivesSettings(
            concurrent_requests=1000,
            request_timeout=3600.0,
            rate_limit_requests_per_minute=10000,
            max_retries=100,
            retry_delay=60.0,
        )
        assert config is not None


class TestEnvFileResolution:
    """测试 .env 文件路径解析逻辑"""

    def test_resolve_env_files_includes_project_root(self):
        """验证项目根目录 .env 路径在返回元组中"""
        result = _resolve_env_files()
        # 项目根目录下有 pyproject.toml，应包含项目根 .env
        project_env = _PROJECT_ROOT / ".env"
        assert project_env in result

    def test_resolve_env_files_includes_cwd_fallback(self):
        """验证 CWD .env 始终在返回元组中"""
        result = _resolve_env_files()
        assert ".env" in result

    def test_resolve_env_files_with_explicit_override(self):
        """验证 NEGENTROPY_PERCEIVES_ENV_FILE 追加到末尾（最高优先级）"""
        with patch.dict(
            os.environ, {"NEGENTROPY_PERCEIVES_ENV_FILE": "/tmp/custom.env"}
        ):
            result = _resolve_env_files()
            assert Path("/tmp/custom.env") in result
            # 显式指定的文件应在元组末尾（最高优先级）
            assert result[-1] == Path("/tmp/custom.env")

    def test_resolve_env_files_without_explicit_override(self):
        """验证无显式覆盖时不包含额外路径"""
        with patch.dict(os.environ, {}, clear=False):
            # 确保 NEGENTROPY_PERCEIVES_ENV_FILE 不存在
            os.environ.pop("NEGENTROPY_PERCEIVES_ENV_FILE", None)
            result = _resolve_env_files()
            # 不应包含额外路径（仅项目根 + CWD）
            assert len(result) <= 2

    def test_resolve_env_files_without_project_root(self):
        """当项目根不存在 pyproject.toml 时，仅包含 CWD 条目"""
        with patch.object(Path, "is_file", return_value=False):
            result = _resolve_env_files()
            assert ".env" in result

    def test_env_file_loading_via_explicit_path(self):
        """端到端验证：通过 NEGENTROPY_PERCEIVES_ENV_FILE 加载配置"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".env", delete=False
        ) as f:
            f.write("NEGENTROPY_PERCEIVES_HTTP_PORT=9999\n")
            f.write("NEGENTROPY_PERCEIVES_SERVER_NAME=test-from-env-file\n")
            tmp_path = f.name

        try:
            with patch.dict(
                os.environ, {"NEGENTROPY_PERCEIVES_ENV_FILE": tmp_path}
            ):
                config = NegentropyPerceivesSettings(
                    _env_file=tmp_path,
                )
                assert config.http_port == 9999
                assert config.server_name == "test-from-env-file"
        finally:
            os.unlink(tmp_path)


class TestDescribeConfigSources:
    """测试启动诊断信息"""

    def test_describe_config_sources_no_env_files(self):
        """无 .env 文件时返回默认提示"""
        with patch.object(Path, "is_file", return_value=False):
            result = describe_config_sources()
            assert "No .env files loaded" in result

    def test_describe_config_sources_returns_string(self):
        """诊断信息始终返回字符串"""
        result = describe_config_sources()
        assert isinstance(result, str)
        assert len(result) > 0


# ============================================================
# MinerU 引擎配置字段验证
# ============================================================
class TestMinerUConfigFields:
    """测试 MinerU 引擎相关配置字段。"""

    def test_mineru_enabled_default(self):
        """MinerU 引擎默认禁用。"""
        config = NegentropyPerceivesSettings()
        assert config.mineru_enabled is False

    def test_mineru_enabled_env_override(self):
        """环境变量 NEGENTROPY_PERCEIVES_MINERU_ENABLED=true 应启用 MinerU。"""
        with patch.dict(
            os.environ, {"NEGENTROPY_PERCEIVES_MINERU_ENABLED": "true"}
        ):
            config = NegentropyPerceivesSettings()
            assert config.mineru_enabled is True

    def test_mineru_device_default(self):
        """MinerU 推理设备默认为 auto。"""
        config = NegentropyPerceivesSettings()
        assert config.mineru_device == "auto"

    def test_mineru_device_valid_values(self):
        """MinerU 推理设备合法值。"""
        for device in ("auto", "cpu", "mlx", "cuda"):
            config = NegentropyPerceivesSettings(mineru_device=device)
            assert config.mineru_device == device

    def test_mineru_device_env_override(self):
        """环境变量覆盖 MinerU 推理设备。"""
        with patch.dict(
            os.environ, {"NEGENTROPY_PERCEIVES_MINERU_DEVICE": "mlx"}
        ):
            config = NegentropyPerceivesSettings()
            assert config.mineru_device == "mlx"

    def test_mineru_backend_default(self):
        """MinerU 后端默认为 auto。"""
        config = NegentropyPerceivesSettings()
        assert config.mineru_backend == "auto"

    def test_mineru_backend_valid_values(self):
        """MinerU 后端合法值。"""
        for backend in ("auto", "pipeline", "vlm"):
            config = NegentropyPerceivesSettings(mineru_backend=backend)
            assert config.mineru_backend == backend

    def test_mineru_backend_env_override(self):
        """环境变量覆盖 MinerU 后端。"""
        with patch.dict(
            os.environ, {"NEGENTROPY_PERCEIVES_MINERU_BACKEND": "pipeline"}
        ):
            config = NegentropyPerceivesSettings()
            assert config.mineru_backend == "pipeline"


# ============================================================
# Marker 引擎配置字段验证
# ============================================================
class TestMarkerConfigFields:
    """测试 Marker 引擎相关配置字段。"""

    def test_marker_enabled_default(self):
        """Marker 引擎默认禁用。"""
        config = NegentropyPerceivesSettings()
        assert config.marker_enabled is False

    def test_marker_enabled_env_override(self):
        """环境变量覆盖 Marker 启用状态。"""
        with patch.dict(
            os.environ, {"NEGENTROPY_PERCEIVES_MARKER_ENABLED": "true"}
        ):
            config = NegentropyPerceivesSettings()
            assert config.marker_enabled is True

    def test_marker_llm_enhanced_default(self):
        """Marker LLM 增强模式默认禁用。"""
        config = NegentropyPerceivesSettings()
        assert config.marker_llm_enhanced is False

    def test_marker_llm_enhanced_config(self):
        """Marker LLM 增强模式配置。"""
        config = NegentropyPerceivesSettings(
            marker_llm_enhanced=True,
            marker_license_acknowledged=True,
        )
        assert config.marker_llm_enhanced is True
        assert config.marker_license_acknowledged is True

    def test_marker_llm_enhanced_env_override(self):
        """环境变量覆盖 Marker LLM 增强模式。"""
        with patch.dict(
            os.environ,
            {
                "NEGENTROPY_PERCEIVES_MARKER_LLM_ENHANCED": "true",
                "NEGENTROPY_PERCEIVES_MARKER_LICENSE_ACKNOWLEDGED": "true",
            },
        ):
            config = NegentropyPerceivesSettings()
            assert config.marker_llm_enhanced is True
            assert config.marker_license_acknowledged is True

    def test_marker_license_acknowledged_default(self):
        """Marker GPL-3.0 许可证确认默认不确认。"""
        config = NegentropyPerceivesSettings()
        assert config.marker_license_acknowledged is False

    def test_marker_license_acknowledged_env_override(self):
        """环境变量覆盖 Marker 许可证确认。"""
        with patch.dict(
            os.environ,
            {"NEGENTROPY_PERCEIVES_MARKER_LICENSE_ACKNOWLEDGED": "true"},
        ):
            config = NegentropyPerceivesSettings()
            assert config.marker_license_acknowledged is True


# ============================================================
# 多引擎配置集成验证
# ============================================================
class TestMultiEngineConfigIntegration:
    """测试多引擎配置集成验证。"""

    def test_all_engine_configs_default(self):
        """Docling、MinerU、Marker 默认值验证。"""
        config = NegentropyPerceivesSettings()
        # 各引擎默认禁用
        assert config.docling_enabled is False
        assert config.mineru_enabled is False
        assert config.marker_enabled is False

    def test_all_engine_configs_enabled(self):
        """各引擎可独立启用。"""
        config = NegentropyPerceivesSettings(
            docling_enabled=True,
            mineru_enabled=True,
            marker_enabled=True,
        )
        assert config.docling_enabled is True
        assert config.mineru_enabled is True
        assert config.marker_enabled is True

    def test_all_engine_configs_env_override(self):
        """环境变量可同时启用所有引擎。"""
        with patch.dict(
            os.environ,
            {
                "NEGENTROPY_PERCEIVES_DOCLING_ENABLED": "true",
                "NEGENTROPY_PERCEIVES_MINERU_ENABLED": "true",
                "NEGENTROPY_PERCEIVES_MARKER_ENABLED": "true",
            },
        ):
            config = NegentropyPerceivesSettings()
            assert config.docling_enabled is True
            assert config.mineru_enabled is True
            assert config.marker_enabled is True

    def test_get_docling_settings_returns_dict(self):
        """get_docling_settings() 应返回正确的 Docling 配置。"""
        config = NegentropyPerceivesSettings(
            docling_enabled=True,
            docling_ocr_enabled=False,
            docling_table_extraction_enabled=False,
            docling_formula_extraction_enabled=True,
            accelerator_device="mps",
            accelerator_num_threads=8,
            accelerator_ocr_batch_size=2,
            accelerator_layout_batch_size=10,
            accelerator_table_batch_size=15,
        )
        ds = config.get_docling_settings()
        assert ds["device"] == "mps"
        assert ds["num_threads"] == 8
        assert ds["enable_ocr"] is False
        assert ds["enable_table_extraction"] is False
        assert ds["enable_formula_extraction"] is True
        assert ds["ocr_batch_size"] == 2
        assert ds["layout_batch_size"] == 10
        assert ds["table_batch_size"] == 15
