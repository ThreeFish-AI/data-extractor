"""MCP tools package. Importing triggers @app.tool() registration."""

from ._registry import (  # noqa: F401
    app,
    web_scraper,
    anti_detection_scraper,
    markdown_converter,
    create_pdf_processor,
)

# Import tool modules to trigger @app.tool() decorator registration
from . import scraping  # noqa: F401
from . import stealth  # noqa: F401
from . import extraction  # noqa: F401
from . import form  # noqa: F401
from . import markdown  # noqa: F401
from . import pdf  # noqa: F401
