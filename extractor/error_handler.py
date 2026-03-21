"""Centralized error handling for scraping operations."""

import logging
from datetime import datetime
from typing import Any, Dict

logger = logging.getLogger(__name__)


class ErrorHandler:
    """Centralized error handling."""

    @staticmethod
    def handle_scraping_error(e: Exception, url: str, method: str) -> Dict[str, Any]:
        """Handle scraping errors and return standardized error response."""
        error_type = type(e).__name__
        error_message = str(e)

        logger.error(
            f"Scraping error for {url} using {method}: {error_type}: {error_message}"
        )

        # Categorize common errors
        if "timeout" in error_message.lower():
            category = "timeout"
            user_message = (
                "Request timed out. The website might be slow or unavailable."
            )
        elif "connection" in error_message.lower():
            category = "connection"
            user_message = (
                "Connection failed. Please check the URL and your internet connection."
            )
        elif "404" in error_message:
            category = "not_found"
            user_message = "Page not found (404). Please verify the URL is correct."
        elif "403" in error_message:
            category = "forbidden"
            user_message = (
                "Access forbidden (403). The website might be blocking scraping."
            )
        elif "cloudflare" in error_message.lower():
            category = "anti_bot"
            user_message = "Anti-bot protection detected. Try using stealth mode or a different method."
        else:
            category = "unknown"
            user_message = "An unexpected error occurred while scraping."

        return {
            "success": False,
            "error": {
                "type": error_type,
                "message": error_message,
                "category": category,
                "user_message": user_message,
                "url": url,
                "method": method,
                "timestamp": datetime.now().isoformat(),
            },
        }
