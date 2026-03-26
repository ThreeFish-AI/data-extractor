"""Utility MCP tools: robots.txt checking."""

import logging
from urllib.parse import urlparse

from ..schemas import RobotsResponse
from ._registry import app, validate_url, web_scraper

logger = logging.getLogger(__name__)


@app.tool()
async def check_robots_txt(
    url: str,
) -> RobotsResponse:
    """
    Check the robots.txt file for a domain to understand crawling permissions.

    This tool helps ensure ethical scraping by checking the robots.txt file
    of a website to see what crawling rules are in place.

    Returns:
        RobotsResponse object containing success status, robots.txt content, base domain, and content availability.
        Helps determine crawling permissions and restrictions for the specified domain.
    """
    try:
        # Validate inputs
        url_error = validate_url(url)
        if url_error:
            raise ValueError(url_error)

        logger.info(f"Checking robots.txt for: {url}")

        # Parse URL to get base domain
        parsed = urlparse(url)
        robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"

        # Scrape robots.txt
        result = await web_scraper.http_scraper.scrape(robots_url, extract_config={})

        if "error" in result:
            return RobotsResponse(
                success=False,
                url=url,
                robots_txt_url=robots_url,
                is_allowed=False,
                user_agent="*",
                error=f"Could not fetch robots.txt: {result['error']}",
            )

        robots_content = result.get("content", {}).get("text", "")

        return RobotsResponse(
            success=True,
            url=url,
            robots_txt_url=robots_url,
            robots_content=robots_content,
            is_allowed=True,  # Basic check, could be enhanced
            user_agent="*",
        )

    except Exception as e:
        logger.error(f"Error checking robots.txt for {url}: {str(e)}")
        return RobotsResponse(
            success=False,
            url=url,
            robots_txt_url="",
            is_allowed=False,
            user_agent="*",
            error=str(e),
        )
