"""Configuration settings for the Data Extractor MCP Server."""

from typing import Dict, Any, Optional, Union
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


# 动态从 pyproject.toml 读取版本号
def _get_dynamic_version():
    """从 pyproject.toml 动态读取版本号"""
    from pathlib import Path

    try:
        current_file = Path(__file__).resolve()
        project_root = (
            current_file.parent.parent
        )  # config.py -> extractor -> project_root
        pyproject_path = project_root / "pyproject.toml"

        if pyproject_path.exists():
            with open(pyproject_path, "r", encoding="utf-8") as f:
                content = f.read()
                for line in content.splitlines():
                    line = line.strip()
                    if line.startswith('version = "') and line.endswith('"'):
                        return line.split('"')[1]
    except Exception:
        pass
    return "0.0.0"


class DataExtractorSettings(BaseSettings):
    """Settings for the Data Extractor MCP Server."""

    # Server settings
    server_name: str = Field(default="Data Extractor")
    server_version: str = Field(default_factory=_get_dynamic_version)

    # Data Extractor settings
    concurrent_requests: int = Field(default=16, gt=0)
    download_delay: float = Field(default=1.0, ge=0.0)
    randomize_download_delay: bool = Field(default=True)
    autothrottle_enabled: bool = Field(default=True)
    autothrottle_start_delay: float = Field(default=1.0, ge=0.0)
    autothrottle_max_delay: float = Field(default=60.0, ge=0.0)
    autothrottle_target_concurrency: float = Field(default=1.0, ge=0.0)

    # Rate limiting settings
    rate_limit_requests_per_minute: int = Field(default=60, ge=1)

    # Retry settings
    max_retries: int = Field(default=3, ge=0)
    retry_delay: float = Field(default=1.0, ge=0.0)

    # Cache settings
    enable_caching: bool = Field(default=True)
    cache_ttl_hours: int = Field(default=24, gt=0)
    cache_max_size: Optional[int] = Field(default=None)

    # Logging settings
    log_level: str = Field(default="INFO")
    log_requests: Optional[bool] = Field(default=None)
    log_responses: Optional[bool] = Field(default=None)

    # Browser settings
    enable_javascript: bool = Field(default=False)
    browser_headless: bool = Field(default=True)
    browser_timeout: int = Field(default=30, ge=0)
    browser_window_size: Union[str, tuple] = Field(default="1920x1080")

    # User agent settings
    use_random_user_agent: bool = Field(default=True)
    default_user_agent: str = Field(
        default="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )

    # Proxy settings
    use_proxy: bool = Field(default=False)
    proxy_url: Optional[str] = Field(default=None)

    # Request settings
    request_timeout: float = Field(default=30.0, gt=0.0)

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",  # Allow extra environment variables
        "env_prefix": "DATA_EXTRACTOR_",  # Automatically map env vars with this prefix
        "env_ignore_empty": True,  # Ignore empty environment variables
        "frozen": True,  # Make instances immutable
    }

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v):
        """Validate log level is one of the standard logging levels."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"log_level must be one of: {valid_levels}")
        return v.upper()

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


# 创建全局设置实例
settings = DataExtractorSettings()
