"""FastMCP application entry point for Negentropy Perceives."""

import logging
from pathlib import Path
import sys

from ..config import describe_config_sources, settings
from .._logging import build_uvicorn_log_config, setup_logging

logger = logging.getLogger(__name__)


def _active_cli_name() -> str:
    """Return the current CLI executable name for user-facing diagnostics."""
    argv0 = sys.argv[0] if sys.argv else "negentropy-perceives"
    return Path(argv0).name or "negentropy-perceives"


def main() -> None:
    """Run the MCP server."""
    # ── 步骤 1：初始化日志体系（必须在导入 tools 之前） ──
    setup_logging(settings.log_level)

    # ── 步骤 2：延迟导入 tools（触发 @app.tool 注册，此时 logger 已就绪） ──
    from ..tools import app  # noqa: E402

    cli_name = _active_cli_name()
    logger.info("Starting %s v%s", settings.server_name, settings.server_version)
    logger.info("CLI entrypoint: %s", cli_name)
    logger.info("Transport mode: %s", settings.transport_mode)
    logger.info(
        "JavaScript support: %s",
        "Enabled" if settings.enable_javascript else "Disabled",
    )
    logger.info(
        "Random User-Agent: %s",
        "Enabled" if settings.use_random_user_agent else "Disabled",
    )
    logger.info("Proxy: %s", "Enabled" if settings.use_proxy else "Disabled")
    logger.info(
        "Resolved settings: server_name=%s, host=%s, port=%s, path=%s",
        settings.server_name,
        settings.http_host,
        settings.http_port,
        settings.http_path,
    )
    logger.info("Config sources: %s", describe_config_sources())

    if settings.transport_mode in ["http", "sse"]:
        transport_type = "HTTP" if settings.transport_mode == "http" else "SSE"
        binding_host = settings.http_host
        binding_port = settings.http_port
        binding_path = settings.http_path

        if binding_host == "0.0.0.0":  # nosec B104
            logger.info(
                "Starting %s server on %s:%s", transport_type, binding_host, binding_port
            )
            logger.info(
                "Local endpoint: http://localhost:%s%s", binding_port, binding_path
            )
            logger.info(
                "Network endpoint: http://%s:%s%s",
                binding_host,
                binding_port,
                binding_path,
            )
        else:
            logger.info(
                "Starting %s server on %s:%s", transport_type, binding_host, binding_port
            )
            endpoint_url = f"http://{binding_host}:{binding_port}{binding_path}"
            logger.info("%s endpoint: %s", transport_type, endpoint_url)

        logger.info("CORS origins: %s", settings.http_cors_origins)

        # ── 步骤 3：构建 Uvicorn 日志配置并启动 ──
        uvicorn_log_config = build_uvicorn_log_config(settings.log_level)

        app.run(
            transport=settings.transport_mode,
            host=binding_host,
            port=binding_port,
            path=binding_path,
            uvicorn_config={"log_config": uvicorn_log_config},
        )
    else:
        logger.info("Starting STDIO server")
        app.run()


if __name__ == "__main__":
    main()
