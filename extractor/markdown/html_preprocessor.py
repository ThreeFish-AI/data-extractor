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
    """Fallback HTML conversion when MarkItDown fails.

    Preserves table structures by converting them to markdown before
    stripping HTML tags.
    """
    try:
        soup = BeautifulSoup(html_content, "html.parser")

        # Remove unwanted elements
        for tag in soup.find_all(["script", "style", "nav", "header", "footer"]):
            tag.decompose()

        # Convert <table> elements to markdown BEFORE stripping HTML
        for table_tag in soup.find_all("table"):
            md_table = _html_table_to_markdown(table_tag)
            if md_table:
                table_tag.replace_with(f"\n\n{md_table}\n\n")

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


def _html_table_to_markdown(table_tag) -> Optional[str]:
    """Convert a BeautifulSoup <table> element to markdown table format.

    Args:
        table_tag: BeautifulSoup Tag for <table>

    Returns:
        Markdown table string, or None if table has no meaningful content
    """
    try:
        rows = []
        for tr in table_tag.find_all("tr"):
            cells = []
            for cell in tr.find_all(["th", "td"]):
                cell_text = cell.get_text(strip=True).replace("|", "\\|")
                cells.append(cell_text)
            if cells:
                rows.append(cells)

        if len(rows) < 2:
            return None

        # Normalize column count
        max_cols = max(len(row) for row in rows)
        for row in rows:
            while len(row) < max_cols:
                row.append("")

        # Build markdown
        md_lines = []
        # Header row
        md_lines.append("| " + " | ".join(rows[0]) + " |")
        # Separator
        md_lines.append("| " + " | ".join(["---"] * max_cols) + " |")
        # Data rows
        for row in rows[1:]:
            md_lines.append("| " + " | ".join(row) + " |")

        return "\n".join(md_lines)

    except Exception:
        return None


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


def _match_image_to_paragraph(paragraph: str, img_alt: str) -> bool:
    """Check if an image is contextually related to a paragraph via alt text."""
    if not img_alt or not paragraph:
        return False
    # Normalize for comparison
    alt_lower = img_alt.lower().strip()
    para_lower = paragraph.lower()
    # Skip generic alt texts
    if alt_lower in ("", "image", "img", "photo", "picture", "icon", "logo"):
        return False
    return alt_lower in para_lower


def build_html_from_text(text_content: str, title: str, content_data: Dict) -> str:
    """Build basic HTML structure from text content.

    Images are distributed proportionally among paragraphs to approximate
    the original document layout, rather than being appended at the end.
    """
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

        images = content_data.get("images", [])[:20]
        num_images = len(images)
        num_paragraphs = len(paragraphs)

        # First pass: try to match images to paragraphs by alt text
        alt_matched: dict = {}  # img_index -> paragraph_index
        matched_img_indices: set = set()
        if images and paragraphs:
            for img_idx, img in enumerate(images):
                img_alt = img.get("alt", "")
                for para_idx, paragraph in enumerate(paragraphs):
                    if _match_image_to_paragraph(paragraph, img_alt):
                        alt_matched[img_idx] = para_idx
                        matched_img_indices.add(img_idx)
                        break

        # Second pass: distribute remaining images proportionally
        unmatched_images = [i for i in range(num_images) if i not in matched_img_indices]
        proportional: dict = {}  # paragraph_index -> [img_indices]
        if unmatched_images and num_paragraphs > 0:
            for seq, img_idx in enumerate(unmatched_images):
                # Distribute evenly: place after paragraph at proportional position
                para_idx = min(
                    (seq + 1) * num_paragraphs // (len(unmatched_images) + 1),
                    num_paragraphs - 1,
                )
                proportional.setdefault(para_idx, []).append(img_idx)

        # Build a combined schedule: paragraph_index -> [img_indices to place after]
        placement: dict = {}
        for img_idx, para_idx in alt_matched.items():
            placement.setdefault(para_idx, []).append(img_idx)
        for para_idx, img_indices in proportional.items():
            placement.setdefault(para_idx, []).extend(img_indices)

        # Emit paragraphs with interleaved images
        for i, paragraph in enumerate(paragraphs):
            if paragraph:
                html_parts.append(f"<p>{paragraph}</p>")
            # Place images scheduled for after this paragraph
            if i in placement:
                for img_idx in placement[i]:
                    img = images[img_idx]
                    img_src = img.get("src", "")
                    img_alt = img.get("alt", "")
                    html_parts.append(f"<img src='{img_src}' alt='{img_alt}'>")

        # Handle edge case: images without any paragraphs
        if images and not paragraphs:
            for img in images:
                img_src = img.get("src", "")
                img_alt = img.get("alt", "")
                html_parts.append(f"<img src='{img_src}' alt='{img_alt}'>")

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

        html_parts.append("</body></html>")
        return "\n".join(html_parts)

    except Exception as e:
        logger.warning(f"Error building HTML from text: {str(e)}")
        return f"<html><body><p>{text_content}</p></body></html>"
