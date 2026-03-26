"""FastMCP Server entry point and backward-compatible re-exports."""

from .config import settings

# Re-export from tools package for backward compatibility
from .tools import app
from .tools import web_scraper as web_scraper
from .tools import anti_detection_scraper as anti_detection_scraper
from .tools import markdown_converter as markdown_converter
from .tools import create_pdf_processor as create_pdf_processor
from .tools.scraping import scrape_webpage, scrape_multiple_webpages  # noqa: F401
from .tools.stealth import scrape_with_stealth  # noqa: F401
from .tools.extraction import extract_links, get_page_info, extract_structured_data, check_robots_txt  # noqa: F401
from .tools.form import fill_and_submit_form  # noqa: F401
from .tools.markdown import convert_webpage_to_markdown as convert_webpage_to_markdown
from .tools.markdown import (
    batch_convert_webpages_to_markdown as batch_convert_webpages_to_markdown,
)
from .tools.pdf import convert_pdf_to_markdown, batch_convert_pdfs_to_markdown  # noqa: F401
from .tools.service import get_server_metrics, clear_cache  # noqa: F401


def main() -> None:
    """Run the MCP server."""
    print(f"Starting {settings.server_name} v{settings.server_version}")
    print(f"Transport mode: {settings.transport_mode}")
    print(
        f"JavaScript support: {'Enabled' if settings.enable_javascript else 'Disabled'}"
    )
    print(
        f"Random User-Agent: {'Enabled' if settings.use_random_user_agent else 'Disabled'}"
    )
    print(f"Proxy: {'Enabled' if settings.use_proxy else 'Disabled'}")

    if settings.transport_mode in ["http", "sse"]:
        transport_type = "HTTP" if settings.transport_mode == "http" else "SSE"
        binding_host = settings.http_host
        binding_port = settings.http_port
        binding_path = settings.http_path

        # Determine the actual endpoint URL for user-friendly display
        if binding_host == "0.0.0.0":  # nosec B104
            # For 0.0.0.0 binding, show both localhost and actual binding
            print(f"Starting {transport_type} server on {binding_host}:{binding_port}")
            print(f"Local endpoint: http://localhost:{binding_port}{binding_path}")
            print(
                f"Network endpoint: http://{binding_host}:{binding_port}{binding_path}"
            )
        else:
            print(f"Starting {transport_type} server on {binding_host}:{binding_port}")
            endpoint_url = f"http://{binding_host}:{binding_port}{binding_path}"
            print(f"{transport_type} endpoint: {endpoint_url}")

        print(f"CORS origins: {settings.http_cors_origins}")

        # Run with appropriate transport
        app.run(
            transport=settings.transport_mode,
            host=binding_host,
            port=binding_port,
            path=binding_path,
        )
    else:
        # Default STDIO transport mode
        print("Starting STDIO server")
        app.run()


if __name__ == "__main__":
    main()
