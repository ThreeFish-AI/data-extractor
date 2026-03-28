"""集中式日志配置。进程级单次初始化，由 apps/app.py 入口调用。"""

import logging
import logging.config
from typing import Any

# 统一格式常量（与 pyproject.toml [tool.pytest.ini_options] log_cli_format 风格对齐）
LOG_FORMAT = "%(asctime)s [%(levelname)-8s] %(name)s: %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# 高 verbosity 第三方 logger 的默认静音级别
_THIRD_PARTY_OVERRIDES: dict[str, str] = {
    "docling": "WARNING",
    "docling.pipeline": "WARNING",
    "docling.document_converter": "WARNING",
    "docling.datamodel": "WARNING",
    "urllib3": "WARNING",
    "httpcore": "WARNING",
    "httpx": "WARNING",
    "selenium": "WARNING",
    "undetected_chromedriver": "WARNING",
    "scrapy": "WARNING",
    "playwright": "WARNING",
}


def setup_logging(log_level: str = "INFO") -> None:
    """配置进程日志体系。

    - 设置 root logger 的级别与格式
    - 将所有日志输出到 stderr（避免 STDIO 传输模式下污染 MCP 协议流）
    - 压制高 verbosity 第三方库的日志级别

    Args:
        log_level: 应用日志级别（来自 settings.log_level）
    """
    level = getattr(logging, log_level.upper(), logging.INFO)

    config: dict[str, Any] = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {
                "format": LOG_FORMAT,
                "datefmt": LOG_DATE_FORMAT,
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "standard",
                "stream": "ext://sys.stderr",
            },
        },
        "root": {
            "level": level,
            "handlers": ["console"],
        },
    }

    logging.config.dictConfig(config)

    # 压制第三方库噪音
    for logger_name, override_level in _THIRD_PARTY_OVERRIDES.items():
        effective_level = getattr(logging, override_level, logging.WARNING)
        logging.getLogger(logger_name).setLevel(effective_level)


def build_uvicorn_log_config(log_level: str = "INFO") -> dict[str, Any]:
    """构建 Uvicorn 的 log_config 字典，使 access/error 日志格式与应用统一。

    通过 ``app.run(uvicorn_config={"log_config": ...})`` 传入 FastMCP。

    Args:
        log_level: 日志级别字符串

    Returns:
        Uvicorn LOGGING_CONFIG 兼容的字典
    """
    upper_level = log_level.upper()
    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": LOG_FORMAT,
                "datefmt": LOG_DATE_FORMAT,
            },
            "access": {
                "format": LOG_FORMAT,
                "datefmt": LOG_DATE_FORMAT,
            },
        },
        "handlers": {
            "default": {
                "class": "logging.StreamHandler",
                "formatter": "default",
                "stream": "ext://sys.stderr",
            },
            "access": {
                "class": "logging.StreamHandler",
                "formatter": "access",
                "stream": "ext://sys.stderr",
            },
        },
        "loggers": {
            "uvicorn": {
                "handlers": ["default"],
                "level": upper_level,
                "propagate": False,
            },
            "uvicorn.error": {
                "handlers": ["default"],
                "level": upper_level,
                "propagate": False,
            },
            "uvicorn.access": {
                "handlers": ["access"],
                "level": upper_level,
                "propagate": False,
            },
        },
    }
