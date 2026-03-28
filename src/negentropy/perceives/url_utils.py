"""URL 校验与规范化工具。"""

from urllib.parse import urlparse


class URLValidator:
    """校验与规范化 URL。"""

    @staticmethod
    def is_valid_url(url: str) -> bool:
        """检查 URL 是否有效。"""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except Exception:
            return False

    @staticmethod
    def normalize_url(url: str) -> str:
        """规范化 URL 格式。"""
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
        """从 URL 中提取域名。"""
        return urlparse(url).netloc
