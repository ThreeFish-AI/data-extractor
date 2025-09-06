"""Configuration settings for the Data Extractor MCP Server."""

from typing import Dict, Any, Optional
from pydantic import Field
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
    server_name: str = Field(default="data-extractor")
    server_version: str = Field(default_factory=_get_dynamic_version)

    # Data Extractor settings
    concurrent_requests: int = Field(default=16)
    download_delay: float = Field(default=1.0)
    randomize_download_delay: bool = Field(default=True)
    autothrottle_enabled: bool = Field(default=True)
    autothrottle_start_delay: float = Field(default=1.0)
    autothrottle_max_delay: float = Field(default=60.0)
    autothrottle_target_concurrency: float = Field(default=1.0)

    # Browser settings
    enable_javascript: bool = Field(default=False)
    browser_headless: bool = Field(default=True)
    browser_timeout: int = Field(default=30)

    # User agent settings
    use_random_user_agent: bool = Field(default=True)
    default_user_agent: str = Field(
        default="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )

    # Proxy settings
    use_proxy: bool = Field(default=False)
    proxy_url: Optional[str] = Field(default=None)

    # Request settings
    max_retries: int = Field(default=3)
    request_timeout: int = Field(default=30)

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",  # Allow extra environment variables
        "env_prefix": "DATA_EXTRACTOR_",  # Automatically map env vars with this prefix
    }

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


# 创建设置实例，并动态设置版本号（如果没有环境变量覆盖的话）
settings = DataExtractorSettings()
if not hasattr(settings, "_version_set"):
    # 如果没有从环境变量读取到版本号，使用动态版本
    dynamic_version = _get_dynamic_version()
    if settings.server_version != dynamic_version:
        # 重新创建实例以使用正确的版本号
        import os

        if "DATA_EXTRACTOR_SERVER_VERSION" not in os.environ:
            os.environ["DATA_EXTRACTOR_SERVER_VERSION"] = dynamic_version
            settings = DataExtractorSettings()
    setattr(settings, "_version_set", True)
