"""HTML 预处理模块：清理、内容区域提取、URL 归一化。"""

import logging
import re
from typing import Dict, Optional

from bs4 import BeautifulSoup, Comment
from urllib.parse import urljoin

logger = logging.getLogger(__name__)


def preprocess_html(html_content: str, base_url: Optional[str] = None) -> str:
    """
    Preprocess HTML content before MarkItDown conversion.

    Args:
        html_content: Raw HTML content
        base_url: Base URL for resolving relative URLs

    Returns:
        Preprocessed HTML content
    """
    try:
        soup = BeautifulSoup(html_content, "html.parser")

        # Remove comments
        comments = soup.find_all(string=lambda text: isinstance(text, Comment))
        for comment in comments:
            comment.extract()

        # Remove unwanted elements that typically don't contain main content
        unwanted_tags = [
            "script",
            "style",
            "nav",
            "header",
            "footer",
            "aside",
            "advertisement",
            "ads",
        ]
        for tag in unwanted_tags:
            for element in soup.find_all(tag):
                element.decompose()

        # Remove elements with specific classes/ids commonly used for ads/navigation
        unwanted_patterns = [
            re.compile(r".*(ad|advertisement|sidebar|nav|menu|footer|header).*", re.I)
        ]

        for pattern in unwanted_patterns:
            for element in soup.find_all(class_=pattern):
                element.decompose()
            for element in soup.find_all(id=pattern):
                element.decompose()

        # Convert relative URLs to absolute if base_url is provided
        if base_url:
            # Convert relative links
            for link in soup.find_all("a", href=True):
                href = link.get("href", "")
                if isinstance(href, str) and not href.startswith(
                    ("http://", "https://")
                ):
                    link["href"] = urljoin(base_url, href)

            # Convert relative image sources
            for img in soup.find_all("img", src=True):
                src = img.get("src", "")
                if isinstance(src, str) and not src.startswith(("http://", "https://")):
                    img["src"] = urljoin(base_url, src)

        return str(soup)

    except Exception as e:
        logger.warning(f"Error preprocessing HTML: {str(e)}")
        return html_content


def extract_content_area(html_content: str) -> str:
    """
    Extract the main content area from HTML, removing navigation, ads, etc.

    Args:
        html_content: HTML content

    Returns:
        HTML content with main content area only
    """
    try:
        soup = BeautifulSoup(html_content, "html.parser")

        # Try to find main content area using common selectors
        content_selectors = [
            "main",
            '[role="main"]',
            "article",
            ".content",
            ".post",
            ".entry",
            ".article",
            "#content",
            "#main",
            ".main-content",
            ".post-content",
            ".entry-content",
            ".article-content",
        ]

        main_content = None
        for selector in content_selectors:
            elements = soup.select(selector)
            if elements:
                for element in elements:
                    text_length = len(element.get_text(strip=True))
                    if text_length > 10:
                        main_content = element
                        break
                if main_content:
                    break

        # If no main content area found, use the body
        if not main_content:
            main_content = soup.find("body") or soup

        return str(main_content)

    except Exception as e:
        logger.warning(f"Error extracting content area: {str(e)}")
        return html_content


def fallback_html_conversion(html_content: str) -> str:
    """Fallback HTML conversion when MarkItDown fails."""
    try:
        soup = BeautifulSoup(html_content, "html.parser")

        # Remove unwanted elements
        for tag in soup.find_all(["script", "style", "nav", "header", "footer"]):
            tag.decompose()

        # Simple conversion logic
        text_content = soup.get_text()

        # Basic markdown formatting
        lines = text_content.split("\n")
        markdown_lines = []

        for line in lines:
            line = line.strip()
            if line:
                markdown_lines.append(line)

        return "\n\n".join(markdown_lines)

    except Exception as e:
        logger.warning(f"Fallback conversion failed: {str(e)}")
        return f"Conversion failed: {str(e)}"


def _heuristic_split_paragraphs(text: str) -> list:
    """Split text into paragraphs using heuristics when double-newlines are absent."""
    lines = text.split("\n")
    paragraphs = []
    current = []

    for i, line in enumerate(lines):
        stripped = line.strip()
        if not stripped:
            # Empty line = explicit paragraph break
            if current:
                paragraphs.append(" ".join(current))
                current = []
            continue

        current.append(stripped)

        # Check if this line ends a paragraph
        if i < len(lines) - 1:
            next_stripped = lines[i + 1].strip()
            if next_stripped and stripped[-1] in ".?!:" and next_stripped[0].isupper():
                paragraphs.append(" ".join(current))
                current = []

    if current:
        paragraphs.append(" ".join(current))

    return paragraphs if len(paragraphs) > 1 else [text.strip()]


def build_html_from_text(text_content: str, title: str, content_data: Dict) -> str:
    """Build basic HTML structure from text content."""
    try:
        html_parts = ["<html><head>"]
        if title:
            html_parts.append(f"<title>{title}</title>")
        html_parts.append("</head><body>")

        # Add main text content
        html_parts.append("<div class='main-content'>")

        # Split text into paragraphs
        paragraphs = [p.strip() for p in text_content.split("\n\n") if p.strip()]

        # Fallback: if text has no double-newlines, use heuristics
        if len(paragraphs) <= 1 and len(text_content) > 200:
            paragraphs = _heuristic_split_paragraphs(text_content)

        for paragraph in paragraphs:
            if paragraph:
                html_parts.append(f"<p>{paragraph}</p>")

        html_parts.append("</div>")

        # Add links if available
        links = content_data.get("links", [])
        if links:
            html_parts.append("<div class='links'>")
            for link in links[:50]:
                link_url = link.get("url", "")
                link_text = link.get("text", link_url)
                html_parts.append(f"<a href='{link_url}'>{link_text}</a><br>")
            html_parts.append("</div>")

        # Add images if available
        images = content_data.get("images", [])
        if images:
            html_parts.append("<div class='images'>")
            for img in images[:20]:
                img_src = img.get("src", "")
                img_alt = img.get("alt", "")
                html_parts.append(f"<img src='{img_src}' alt='{img_alt}'>")
            html_parts.append("</div>")

        html_parts.append("</body></html>")
        return "\n".join(html_parts)

    except Exception as e:
        logger.warning(f"Error building HTML from text: {str(e)}")
        return f"<html><body><p>{text_content}</p></body></html>"
