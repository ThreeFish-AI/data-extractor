"""Negentropy Perceives MCP Server 配置管理模块。

基于 pydantic-settings 的分层配置系统，按优先级从高到低：
1. 环境变量（NEGENTROPY_PERCEIVES_ 前缀）
2. .env 文件（项目根目录 → CWD → 显式指定）
3. 字段默认值
"""

import os
from pathlib import Path
from typing import Any, Dict, Optional, Union

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings

from . import __version__

# ---------------------------------------------------------------------------
# .env 文件路径解析
# ---------------------------------------------------------------------------

# 项目根目录（与 __init__.py 中版本检测使用相同的定位策略）
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent


def _resolve_env_files() -> tuple[Path | str, ...]:
    """计算 .env 文件搜索路径。

    pydantic-settings 按顺序加载列表中的文件，后者覆盖前者。
    优先级（后者覆盖前者）：
    1. 项目根目录 .env（通过 pyproject.toml 哨兵文件检测）
    2. CWD .env（pydantic-settings 原生行为）
    3. NEGENTROPY_PERCEIVES_ENV_FILE 显式指定（最高优先级）

    不存在的文件由 pydantic-settings 静默跳过。
    """
    candidates: list[Path | str] = []

    # 项目根目录（仅当 pyproject.toml 存在时才视为有效项目根）
    if (_PROJECT_ROOT / "pyproject.toml").is_file():
        candidates.append(_PROJECT_ROOT / ".env")

    # CWD 回退（保持 pydantic-settings 原生行为）
    candidates.append(".env")

    # 显式覆盖（最高优先级）
    explicit = os.environ.get("NEGENTROPY_PERCEIVES_ENV_FILE")
    if explicit:
        candidates.append(Path(explicit))

    return tuple(candidates)


def describe_config_sources() -> str:
    """报告 .env 文件加载情况，用于启动诊断。"""
    found: list[str] = []
    for ef in _resolve_env_files():
        p = Path(ef) if Path(ef).is_absolute() else Path.cwd() / ef
        if p.is_file():
            found.append(str(p))
    if found:
        return f"Loaded: {', '.join(found)}"
    return "No .env files loaded (using env vars and defaults)"


# ---------------------------------------------------------------------------
# 配置模型
# ---------------------------------------------------------------------------


class NegentropyPerceivesSettings(BaseSettings):
    """Negentropy Perceives MCP Server 配置。"""

    # ── 服务标识 ──────────────────────────────────────────────
    server_name: str = Field(
        default="negentropy-perceives", description="MCP 服务器标识名称"
    )
    server_version: str = Field(
        default=__version__, description="版本号（从 pyproject.toml 自动获取）"
    )

    # ── 传输层 ────────────────────────────────────────────────
    transport_mode: str = Field(
        default="http", description="MCP 传输协议模式：stdio / http / sse"
    )
    http_host: str = Field(default="localhost", description="HTTP 服务器绑定主机")
    http_port: int = Field(default=8081, description="HTTP 服务器监听端口")
    http_path: str = Field(default="/mcp", description="HTTP 端点路径")
    http_cors_origins: Optional[str] = Field(
        default="*", description="CORS 来源白名单（null 禁用）"
    )

    # ── 抓取引擎 ──────────────────────────────────────────────
    concurrent_requests: int = Field(default=16, gt=0, description="并发请求上限")
    download_delay: float = Field(default=1.0, ge=0.0, description="下载间隔（秒）")
    randomize_download_delay: bool = Field(default=True, description="随机化下载间隔")
    autothrottle_enabled: bool = Field(default=True, description="启用自动节流")
    autothrottle_start_delay: float = Field(
        default=1.0, ge=0.0, description="自动节流初始延迟（秒）"
    )
    autothrottle_max_delay: float = Field(
        default=60.0, ge=0.0, description="自动节流最大延迟（秒）"
    )
    autothrottle_target_concurrency: float = Field(
        default=1.0, ge=0.0, description="自动节流目标并发度"
    )

    # ── 速率限制 ──────────────────────────────────────────────
    rate_limit_requests_per_minute: int = Field(
        default=60, ge=1, description="每分钟请求频率上限"
    )

    # ── 重试策略 ──────────────────────────────────────────────
    max_retries: int = Field(default=3, ge=0, description="失败重试最大次数")
    retry_delay: float = Field(default=1.0, ge=0.0, description="重试间隔（秒）")

    # ── 缓存系统 ──────────────────────────────────────────────
    enable_caching: bool = Field(default=True, description="启用响应缓存")
    cache_ttl_hours: int = Field(default=24, gt=0, description="缓存生存时间（小时）")
    cache_max_size: Optional[int] = Field(
        default=None, description="缓存最大条目数（null 不限）"
    )

    # ── 日志系统 ──────────────────────────────────────────────
    log_level: str = Field(
        default="INFO",
        description="日志级别：DEBUG / INFO / WARNING / ERROR / CRITICAL",
    )
    log_requests: Optional[bool] = Field(default=None, description="记录请求详情")
    log_responses: Optional[bool] = Field(default=None, description="记录响应详情")

    # ── 浏览器引擎 ────────────────────────────────────────────
    enable_javascript: bool = Field(default=False, description="启用 JavaScript 执行")
    browser_headless: bool = Field(default=True, description="无头浏览器模式")
    browser_timeout: int = Field(default=30, ge=0, description="浏览器操作超时（秒）")
    browser_window_size: Union[str, tuple] = Field(
        default="1920x1080", description="浏览器窗口尺寸"
    )

    # ── 用户代理 ──────────────────────────────────────────────
    use_random_user_agent: bool = Field(
        default=True, description="启用随机 User-Agent 轮换"
    )
    default_user_agent: str = Field(
        default="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        description="默认 User-Agent 字符串",
    )

    # ── 代理服务 ──────────────────────────────────────────────
    use_proxy: bool = Field(default=False, description="启用代理服务器")
    proxy_url: Optional[str] = Field(
        default=None, description="代理服务器 URL（启用代理时必填）"
    )

    # ── 请求设置 ──────────────────────────────────────────────
    request_timeout: float = Field(
        default=30.0, gt=0.0, description="HTTP 请求超时（秒）"
    )

    # ── LLM 编排 ──────────────────────────────────────────────
    llm_api_key: Optional[str] = Field(
        default=None, description="LLM API Key（ZhipuAI）"
    )
    llm_model: str = Field(
        default="zhipu/glm-5-plus-250414",
        description="LiteLLM 模型标识（如 zhipu/glm-5-plus-250414）",
    )
    llm_temperature: float = Field(
        default=0.1, ge=0.0, le=2.0, description="LLM 温度参数"
    )
    llm_max_tokens: int = Field(default=4096, gt=0, description="LLM 最大输出 token")
    llm_timeout: float = Field(default=60.0, gt=0.0, description="LLM API 超时（秒）")
    llm_max_retries: int = Field(default=2, ge=0, description="LLM API 重试次数")

    # ── 硬件加速 ──────────────────────────────────────────────
    accelerator_device: str = Field(
        default="auto",
        description="推理设备：auto / cpu / cuda (NVIDIA) / mps (Apple Silicon) / xpu (Intel)",
    )
    accelerator_num_threads: int = Field(default=4, ge=1, description="CPU 推理线程数")

    # ── Docling PDF 引擎 ──────────────────────────────────────
    docling_enabled: bool = Field(
        default=False,
        description="启用 Docling 作为可选 PDF 提取引擎（需安装 docling 可选依赖）",
    )
    docling_ocr_enabled: bool = Field(default=True, description="为扫描版 PDF 启用 OCR")
    docling_table_extraction_enabled: bool = Field(
        default=True, description="启用 Docling 高级表格提取"
    )
    docling_formula_extraction_enabled: bool = Field(
        default=True, description="启用 Docling 数学公式提取"
    )

    model_config = {
        "env_file": _resolve_env_files(),
        "env_file_encoding": "utf-8",
        "extra": "ignore",
        "env_prefix": "NEGENTROPY_PERCEIVES_",
        "env_ignore_empty": True,
        "frozen": True,
    }

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v):
        """Validate log level is one of the standard logging levels."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"log_level must be one of: {valid_levels}")
        return v.upper()

    @field_validator("transport_mode")
    @classmethod
    def validate_transport_mode(cls, v):
        """Validate transport mode is one of the supported modes."""
        valid_modes = ["stdio", "http", "sse"]
        if v.lower() not in valid_modes:
            raise ValueError(f"transport_mode must be one of: {valid_modes}")
        return v.lower()

    @field_validator("accelerator_device")
    @classmethod
    def validate_accelerator_device(cls, v):
        """Validate accelerator device is one of the supported devices."""
        valid_devices = ["auto", "cpu", "cuda", "mps", "xpu"]
        if v.lower() not in valid_devices:
            raise ValueError(f"accelerator_device must be one of: {valid_devices}")
        return v.lower()

    def get_scrapy_settings(self) -> Dict[str, Any]:
        """Get Scrapy-specific settings as a dictionary."""
        return {
            "CONCURRENT_REQUESTS": self.concurrent_requests,
            "DOWNLOAD_DELAY": self.download_delay,
            "RANDOMIZE_DOWNLOAD_DELAY": self.randomize_download_delay,
            "AUTOTHROTTLE_ENABLED": self.autothrottle_enabled,
            "AUTOTHROTTLE_START_DELAY": self.autothrottle_start_delay,
            "AUTOTHROTTLE_MAX_DELAY": self.autothrottle_max_delay,
            "AUTOTHROTTLE_TARGET_CONCURRENCY": self.autothrottle_target_concurrency,
            "RETRY_TIMES": self.max_retries,
            "DOWNLOAD_TIMEOUT": self.request_timeout,
            "USER_AGENT": self.default_user_agent,
        }

    def get_docling_settings(self) -> Dict[str, Any]:
        """Get Docling-specific settings as a dictionary.

        Returns settings compatible with Docling's AcceleratorOptions and
        pipeline configuration.

        Example:
            >>> settings.get_docling_settings()
            {'device': 'auto', 'num_threads': 4, 'enable_ocr': True, ...}
        """
        return {
            "device": self.accelerator_device,
            "num_threads": self.accelerator_num_threads,
            "enable_ocr": self.docling_ocr_enabled,
            "enable_table_extraction": self.docling_table_extraction_enabled,
            "enable_formula_extraction": self.docling_formula_extraction_enabled,
        }


# 创建全局设置实例
settings = NegentropyPerceivesSettings()
