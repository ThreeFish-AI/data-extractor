"""Configuration settings for the Scrapy MCP Server."""

import os
from typing import Dict, Any, Optional
from pydantic import BaseSettings, Field


class ScrapyMCPSettings(BaseSettings):
    """Settings for the Scrapy MCP Server."""
    
    # Server settings
    server_name: str = Field(default="scrapy-mcp-server", env="SCRAPY_MCP_SERVER_NAME")
    server_version: str = Field(default="0.1.0", env="SCRAPY_MCP_SERVER_VERSION")
    
    # Scrapy settings
    scrapy_concurrent_requests: int = Field(default=16, env="SCRAPY_CONCURRENT_REQUESTS")
    scrapy_download_delay: float = Field(default=1.0, env="SCRAPY_DOWNLOAD_DELAY")
    scrapy_randomize_download_delay: bool = Field(default=True, env="SCRAPY_RANDOMIZE_DOWNLOAD_DELAY")
    scrapy_autothrottle_enabled: bool = Field(default=True, env="SCRAPY_AUTOTHROTTLE_ENABLED")
    scrapy_autothrottle_start_delay: float = Field(default=1.0, env="SCRAPY_AUTOTHROTTLE_START_DELAY")
    scrapy_autothrottle_max_delay: float = Field(default=60.0, env="SCRAPY_AUTOTHROTTLE_MAX_DELAY")
    scrapy_autothrottle_target_concurrency: float = Field(default=1.0, env="SCRAPY_AUTOTHROTTLE_TARGET_CONCURRENCY")
    
    # Browser settings
    enable_javascript: bool = Field(default=False, env="SCRAPY_MCP_ENABLE_JAVASCRIPT")
    browser_headless: bool = Field(default=True, env="SCRAPY_MCP_BROWSER_HEADLESS")
    browser_timeout: int = Field(default=30, env="SCRAPY_MCP_BROWSER_TIMEOUT")
    
    # User agent settings
    use_random_user_agent: bool = Field(default=True, env="SCRAPY_MCP_USE_RANDOM_USER_AGENT")
    default_user_agent: str = Field(
        default="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        env="SCRAPY_MCP_DEFAULT_USER_AGENT"
    )
    
    # Proxy settings
    use_proxy: bool = Field(default=False, env="SCRAPY_MCP_USE_PROXY")
    proxy_url: Optional[str] = Field(default=None, env="SCRAPY_MCP_PROXY_URL")
    
    # Request settings
    max_retries: int = Field(default=3, env="SCRAPY_MCP_MAX_RETRIES")
    request_timeout: int = Field(default=30, env="SCRAPY_MCP_REQUEST_TIMEOUT")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
    
    def get_scrapy_settings(self) -> Dict[str, Any]:
        """Get Scrapy-specific settings as a dictionary."""
        return {
            "CONCURRENT_REQUESTS": self.scrapy_concurrent_requests,
            "DOWNLOAD_DELAY": self.scrapy_download_delay,
            "RANDOMIZE_DOWNLOAD_DELAY": self.scrapy_randomize_download_delay,
            "AUTOTHROTTLE_ENABLED": self.scrapy_autothrottle_enabled,
            "AUTOTHROTTLE_START_DELAY": self.scrapy_autothrottle_start_delay,
            "AUTOTHROTTLE_MAX_DELAY": self.scrapy_autothrottle_max_delay,
            "AUTOTHROTTLE_TARGET_CONCURRENCY": self.scrapy_autothrottle_target_concurrency,
            "RETRY_TIMES": self.max_retries,
            "DOWNLOAD_TIMEOUT": self.request_timeout,
            "USER_AGENT": self.default_user_agent,
        }


settings = ScrapyMCPSettings()