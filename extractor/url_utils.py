"""URL validation and normalization."""

from urllib.parse import urlparse


class URLValidator:
    """Validate and normalize URLs."""

    @staticmethod
    def is_valid_url(url: str) -> bool:
        """Check if URL is valid."""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except Exception:
            return False

    @staticmethod
    def normalize_url(url: str) -> str:
        """Normalize URL format."""
        if not url.startswith(("http://", "https://")):
            url = "https://" + url

        parsed = urlparse(url)
        # Remove fragment and normalize
        normalized = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        if parsed.query:
            normalized += f"?{parsed.query}"

        return normalized

    @staticmethod
    def extract_domain(url: str) -> str:
        """Extract domain from URL."""
        return urlparse(url).netloc
