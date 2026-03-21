"""MCP tools package. Importing triggers @app.tool() registration."""

from ._registry import (  # noqa: F401
    app,
    web_scraper,
    anti_detection_scraper,
    markdown_converter,
    _get_pdf_processor,
)

# Import tool modules to trigger @app.tool() decorator registration
from . import scraping  # noqa: F401
from . import utility  # noqa: F401
from . import form  # noqa: F401
from . import markdown  # noqa: F401
from . import pdf  # noqa: F401
from . import service  # noqa: F401
