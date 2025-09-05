"""Markdown conversion utilities for HTML content."""

import logging
import re
from typing import Dict, Any, List, Optional
from urllib.parse import urljoin, urlparse

from markdownify import markdownify as md
from bs4 import BeautifulSoup, Comment

logger = logging.getLogger(__name__)


class MarkdownConverter:
    """Convert HTML content to Markdown format."""

    def __init__(self):
        """Initialize the Markdown converter."""
        self.default_options = {
            "heading_style": "ATX",  # Use # style headings
            "bullets": "-",  # Use - for bullet points
            "emphasis_mark": "*",  # Use * for emphasis
            "strong_mark": "**",  # Use ** for strong
            "link_style": "INLINE",  # Use inline links [text](url)
            "autolinks": True,  # Convert plain URLs to links
            "wrap": False,  # Disable wrapping
        }

        # Advanced formatting options
        self.formatting_options = {
            "format_tables": True,  # Enable table formatting
            "detect_code_language": True,  # Auto-detect code language
            "format_quotes": True,  # Improve blockquote formatting
            "enhance_images": True,  # Improve image alt text
            "optimize_links": True,  # Optimize link formatting
            "format_lists": True,  # Improve list formatting
            "format_headings": True,  # Add proper heading spacing
            "apply_typography": True,  # Apply typography fixes (smart quotes, em dashes)
            "smart_quotes": True,  # Enable smart quotes
            "em_dashes": True,  # Convert double hyphens to em dashes
            "fix_spacing": True,  # Fix spacing issues
        }

    def preprocess_html(self, html_content: str, base_url: Optional[str] = None) -> str:
        """
        Preprocess HTML content before Markdown conversion.

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

            # Remove unwanted elements
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
                re.compile(
                    r".*(ad|advertisement|sidebar|nav|menu|footer|header).*", re.I
                )
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
                    if hasattr(link, "get"):
                        href = link.get("href", "")
                        if isinstance(href, str) and not href.startswith(
                            ("http://", "https://")
                        ):
                            link["href"] = urljoin(base_url, href)

                # Convert relative image sources
                for img in soup.find_all("img", src=True):
                    if hasattr(img, "get"):
                        src = img.get("src", "")
                        if isinstance(src, str) and not src.startswith(
                            ("http://", "https://")
                        ):
                            img["src"] = urljoin(base_url, src)

            # Clean up empty paragraphs and divs
            for tag in soup.find_all(["p", "div"]):
                if not tag.get_text(strip=True) and not tag.find_all(
                    ["img", "video", "audio"]
                ):
                    tag.decompose()

            return str(soup)

        except Exception as e:
            logger.warning(f"Error preprocessing HTML: {str(e)}")
            return html_content

    def html_to_markdown(
        self,
        html_content: str,
        base_url: Optional[str] = None,
        custom_options: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Convert HTML content to Markdown.

        Args:
            html_content: HTML content to convert
            base_url: Base URL for resolving relative URLs
            custom_options: Custom options for markdownify

        Returns:
            Markdown formatted content
        """
        try:
            # Use custom options if provided, otherwise use defaults
            options = self.default_options.copy()
            if custom_options:
                options.update(custom_options)

            # Preprocess HTML
            processed_html = self.preprocess_html(html_content, base_url)

            # Convert to Markdown
            markdown_content = md(processed_html, **options)

            # Post-process Markdown
            markdown_content = self.postprocess_markdown(markdown_content)

            return markdown_content

        except Exception as e:
            logger.error(f"Error converting HTML to Markdown: {str(e)}")
            return f"Error converting content: {str(e)}"

    def postprocess_markdown(self, markdown_content: str) -> str:
        """
        Post-process Markdown content with advanced formatting features.

        Args:
            markdown_content: Raw Markdown content

        Returns:
            Enhanced and cleaned up Markdown content
        """
        try:
            # Apply advanced formatting features based on configuration
            if self.formatting_options.get("format_tables", True):
                markdown_content = self._format_tables(markdown_content)

            if self.formatting_options.get("detect_code_language", True):
                markdown_content = self._format_code_blocks(markdown_content)

            if self.formatting_options.get("format_quotes", True):
                markdown_content = self._format_quotes(markdown_content)

            if self.formatting_options.get("enhance_images", True):
                markdown_content = self._format_images(markdown_content)

            if self.formatting_options.get("optimize_links", True):
                markdown_content = self._format_links(markdown_content)

            if self.formatting_options.get("format_lists", True):
                markdown_content = self._format_lists(markdown_content)

            if self.formatting_options.get("format_headings", True):
                markdown_content = self._format_headings(markdown_content)

            if self.formatting_options.get("apply_typography", True):
                markdown_content = self._apply_typography_fixes(markdown_content)

            # Basic cleanup (existing functionality)
            markdown_content = self._basic_cleanup(markdown_content)

            return markdown_content

        except Exception as e:
            logger.warning(f"Error post-processing Markdown: {str(e)}")
            return markdown_content

    def _format_tables(self, markdown_content: str) -> str:
        """Format and align Markdown tables."""
        try:
            lines = markdown_content.split("\n")
            formatted_lines = []

            for i, line in enumerate(lines):
                if (
                    "|" in line
                    and line.strip().startswith("|")
                    and line.strip().endswith("|")
                ):
                    # This looks like a table row
                    cells = [
                        cell.strip() for cell in line.split("|")[1:-1]
                    ]  # Remove empty first/last elements

                    # Check if next line is a separator (header separator)
                    if i + 1 < len(lines) and re.match(
                        r"^\s*\|[\s\-:]+\|\s*$", lines[i + 1]
                    ):
                        # This is a header row, format it
                        formatted_line = "| " + " | ".join(cells) + " |"
                        formatted_lines.append(formatted_line)
                    elif re.match(r"^\s*\|[\s\-:]+\|\s*$", line):
                        # This is a separator row, format it
                        separator_cells = []
                        for cell in cells:
                            if ":" in cell:
                                if cell.startswith(":") and cell.endswith(":"):
                                    separator_cells.append(":---:")  # Center aligned
                                elif cell.endswith(":"):
                                    separator_cells.append("---:")  # Right aligned
                                else:
                                    separator_cells.append(":---")  # Left aligned
                            else:
                                separator_cells.append("---")  # Default alignment
                        formatted_line = "| " + " | ".join(separator_cells) + " |"
                        formatted_lines.append(formatted_line)
                    else:
                        # Regular table row
                        formatted_line = "| " + " | ".join(cells) + " |"
                        formatted_lines.append(formatted_line)
                else:
                    formatted_lines.append(line)

            return "\n".join(formatted_lines)
        except Exception as e:
            logger.warning(f"Error formatting tables: {str(e)}")
            return markdown_content

    def _format_code_blocks(self, markdown_content: str) -> str:
        """Enhance code block formatting with language detection."""
        try:
            # Detect common code patterns and add language hints
            code_patterns = {
                r"(?m)^```\s*\n(.*?function\s+\w+.*?)^```": r"```javascript\n\1```",
                r"(?m)^```\s*\n(.*?def\s+\w+.*?)^```": r"```python\n\1```",
                r"(?m)^```\s*\n(.*?class\s+\w+.*?)^```": r"```python\n\1```",
                r"(?m)^```\s*\n(.*?import\s+.*?)^```": r"```python\n\1```",
                r"(?m)^```\s*\n(.*?<\?php.*?)^```": r"```php\n\1```",
                r"(?m)^```\s*\n(.*?<html.*?)^```": r"```html\n\1```",
                r"(?m)^```\s*\n(.*?<!DOCTYPE.*?)^```": r"```html\n\1```",
                r"(?m)^```\s*\n(.*?SELECT\s+.*?)^```": r"```sql\n\1```",
                r'(?m)^```\s*\n(.*?\{.*?".*?".*?\}.*?)^```': r"```json\n\1```",
            }

            for pattern, replacement in code_patterns.items():
                markdown_content = re.sub(
                    pattern,
                    replacement,
                    markdown_content,
                    flags=re.DOTALL | re.IGNORECASE,
                )

            # Ensure code blocks are properly separated
            markdown_content = re.sub(
                r"(```[a-z]*\n.*?\n```)", r"\n\1\n", markdown_content, flags=re.DOTALL
            )

            return markdown_content
        except Exception as e:
            logger.warning(f"Error formatting code blocks: {str(e)}")
            return markdown_content

    def _format_quotes(self, markdown_content: str) -> str:
        """Improve blockquote formatting."""
        try:
            # Ensure blockquotes are properly formatted
            markdown_content = re.sub(
                r"^>\s*(.+)$", r"> \1", markdown_content, flags=re.MULTILINE
            )

            # Add spacing around blockquotes
            markdown_content = re.sub(
                r"(^>.+$)", r"\n\1\n", markdown_content, flags=re.MULTILINE
            )

            return markdown_content
        except Exception as e:
            logger.warning(f"Error formatting quotes: {str(e)}")
            return markdown_content

    def _format_images(self, markdown_content: str) -> str:
        """Enhance image formatting with better alt text and titles."""
        try:
            # Improve image alt text when it's missing or poor
            def improve_image_alt(match):
                alt_text = match.group(1)
                image_url = match.group(2)

                if not alt_text or alt_text in ["", "image", "img", "photo", "picture"]:
                    # Try to generate better alt text from URL
                    import os

                    filename = os.path.basename(image_url).split(".")[0]
                    alt_text = filename.replace("-", " ").replace("_", " ").title()

                return f"![{alt_text}]({image_url})"

            markdown_content = re.sub(
                r"!\[(.*?)\]\((.*?)\)", improve_image_alt, markdown_content
            )

            # Add proper spacing around images
            markdown_content = re.sub(r"(!\[.*?\]\(.*?\))", r"\n\1\n", markdown_content)

            return markdown_content
        except Exception as e:
            logger.warning(f"Error formatting images: {str(e)}")
            return markdown_content

    def _format_links(self, markdown_content: str) -> str:
        """Optimize link formatting and reference links."""
        try:
            # Convert inline links to reference links for better readability (optional)
            # For now, just ensure proper spacing and formatting

            # Fix link formatting issues
            markdown_content = re.sub(
                r"\[([^\]]+)\]\s*\(\s*([^\s\)]+)\s*\)", r"[\1](\2)", markdown_content
            )

            # Ensure links don't break across lines improperly
            markdown_content = re.sub(
                r"\[([^\]]+)\]\s*\n\s*\(([^\)]+)\)", r"[\1](\2)", markdown_content
            )

            return markdown_content
        except Exception as e:
            logger.warning(f"Error formatting links: {str(e)}")
            return markdown_content

    def _format_lists(self, markdown_content: str) -> str:
        """Improve list formatting and nesting."""
        try:
            lines = markdown_content.split("\n")
            formatted_lines = []

            for line in lines:
                # Ensure consistent list marker spacing
                line = re.sub(r"^(\s*)([-\*\+])\s*(.+)$", r"\1\2 \3", line)

                # Ensure consistent numbered list formatting
                line = re.sub(r"^(\s*)(\d+)\.?\s*(.+)$", r"\1\2. \3", line)

                formatted_lines.append(line)

            # Clean up empty list items
            markdown_content = "\n".join(formatted_lines)
            markdown_content = re.sub(r"\n[-*+]\s*\n", "\n", markdown_content)

            # Ensure proper spacing around lists
            markdown_content = re.sub(
                r"(^[-*+\d]+\.?\s+.+$)", r"\n\1", markdown_content, flags=re.MULTILINE
            )

            return markdown_content
        except Exception as e:
            logger.warning(f"Error formatting lists: {str(e)}")
            return markdown_content

    def _format_headings(self, markdown_content: str) -> str:
        """Improve heading formatting and hierarchy."""
        try:
            lines = markdown_content.split("\n")
            formatted_lines = []

            for i, line in enumerate(lines):
                if re.match(r"^#{1,6}\s", line):
                    # Ensure proper heading spacing
                    heading = line.strip()

                    # Add spacing before headings (except if first line or after another heading)
                    if i > 0 and not re.match(r"^#{1,6}\s", lines[i - 1]):
                        formatted_lines.append("")  # Add blank line before heading

                    formatted_lines.append(heading)

                    # Add spacing after headings
                    if i < len(lines) - 1 and lines[i + 1].strip() != "":
                        formatted_lines.append("")  # Add blank line after heading
                else:
                    # Always append non-heading lines (including empty lines for proper spacing)
                    formatted_lines.append(line)

            return "\n".join(formatted_lines)
        except Exception as e:
            logger.warning(f"Error formatting headings: {str(e)}")
            return markdown_content

    def _apply_typography_fixes(self, markdown_content: str) -> str:
        """Apply typography improvements like smart quotes, em dashes, etc."""
        try:
            # Convert double hyphens to em dashes
            markdown_content = re.sub(r"(?<!\-)\-\-(?!\-)", "—", markdown_content)

            # Convert straight quotes to smart quotes (be careful in code blocks)
            def replace_quotes(match):
                text = match.group(0)
                # Don't replace quotes in code blocks or inline code
                if "`" in text or text.startswith("    "):
                    return text

                # Simple smart quote replacement
                text = re.sub(r'"([^"]*)"', r'"\1"', text)
                text = re.sub(r"'([^']*)'", r"'\1'", text)
                return text

            # Apply smart quotes to paragraphs, avoiding code
            markdown_content = re.sub(
                r"^(?![ ]*```|[ ]*`|[ ]{4})(.+)$",
                replace_quotes,
                markdown_content,
                flags=re.MULTILINE,
            )

            # Fix multiple spaces
            markdown_content = re.sub(r" {2,}", " ", markdown_content)

            # Fix spacing around punctuation
            markdown_content = re.sub(r"\s+([.!?:;,])", r"\1", markdown_content)
            markdown_content = re.sub(r"([.!?])\s*([A-Z])", r"\1 \2", markdown_content)

            return markdown_content
        except Exception as e:
            logger.warning(f"Error applying typography fixes: {str(e)}")
            return markdown_content

    def _basic_cleanup(self, markdown_content: str) -> str:
        """Apply basic cleanup operations (original postprocessing logic)."""
        try:
            # Remove excessive blank lines (more than 2 consecutive)
            markdown_content = re.sub(r"\n{3,}", "\n\n", markdown_content)

            # Clean up excessive spaces
            lines = []
            for line in markdown_content.split("\n"):
                # Remove trailing spaces but preserve intentional line breaks
                cleaned_line = line.rstrip()
                lines.append(cleaned_line)

            markdown_content = "\n".join(lines)

            # Remove leading/trailing whitespace
            markdown_content = markdown_content.strip()

            return markdown_content

        except Exception as e:
            logger.warning(f"Error in basic cleanup: {str(e)}")
            return markdown_content

    def extract_content_area(self, html_content: str) -> str:
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
                    # Take the first match that has substantial content
                    for element in elements:
                        text_length = len(element.get_text(strip=True))
                        if text_length > 200:  # Minimum content length
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

    def convert_webpage_to_markdown(
        self,
        scrape_result: Dict[str, Any],
        extract_main_content: bool = True,
        include_metadata: bool = True,
        custom_options: Optional[Dict[str, Any]] = None,
        formatting_options: Optional[Dict[str, bool]] = None,
    ) -> Dict[str, Any]:
        """
        Convert a scraped webpage result to Markdown format.

        Args:
            scrape_result: Result from web scraping
            extract_main_content: Whether to extract main content area
            include_metadata: Whether to include page metadata
            custom_options: Custom options for markdownify
            formatting_options: Advanced formatting options (overrides defaults)

        Returns:
            Dictionary with Markdown content and metadata
        """
        try:
            if "error" in scrape_result:
                return {
                    "success": False,
                    "error": scrape_result["error"],
                    "url": scrape_result.get("url"),
                }

            url = scrape_result.get("url", "")
            title = scrape_result.get("title", "")
            content_data = scrape_result.get("content", {})

            # Get HTML content - try different sources
            html_content = None
            if "html" in content_data:
                html_content = content_data["html"]
            elif "text" in content_data and content_data["text"]:
                # If we only have text, try to reconstruct basic HTML structure
                text_content = content_data["text"]
                links = content_data.get("links", [])
                images = content_data.get("images", [])

                # Build basic HTML structure
                html_parts = ["<html><head>"]
                if title:
                    html_parts.append(f"<title>{title}</title>")
                html_parts.append("</head><body>")

                # Add main text content
                html_parts.append(f"<div class='main-content'>{text_content}</div>")

                # Add links if available
                if links:
                    html_parts.append("<div class='links'>")
                    for link in links[:50]:  # Limit to first 50 links
                        link_url = link.get("url", "")
                        link_text = link.get("text", link_url)
                        html_parts.append(f"<a href='{link_url}'>{link_text}</a><br>")
                    html_parts.append("</div>")

                # Add images if available
                if images:
                    html_parts.append("<div class='images'>")
                    for img in images[:20]:  # Limit to first 20 images
                        img_src = img.get("src", "")
                        img_alt = img.get("alt", "")
                        html_parts.append(f"<img src='{img_src}' alt='{img_alt}'>")
                    html_parts.append("</div>")

                html_parts.append("</body></html>")
                html_content = "\n".join(html_parts)
            else:
                return {
                    "success": False,
                    "error": "No content found in scrape result",
                    "url": url,
                }

            # Extract main content area if requested
            if extract_main_content:
                html_content = self.extract_content_area(html_content)

            # Update formatting options if provided
            original_formatting_options = None
            if formatting_options:
                original_formatting_options = self.formatting_options.copy()
                self.formatting_options.update(formatting_options)

            try:
                # Convert to Markdown
                markdown_content = self.html_to_markdown(
                    html_content, url, custom_options
                )
            finally:
                # Restore original formatting options
                if original_formatting_options:
                    self.formatting_options = original_formatting_options

            # Prepare result
            result = {
                "success": True,
                "url": url,
                "markdown": markdown_content,
                "conversion_options": {
                    "extract_main_content": extract_main_content,
                    "include_metadata": include_metadata,
                    "custom_options": custom_options or {},
                    "formatting_options": formatting_options or {},
                },
            }

            # Include metadata if requested
            if include_metadata:
                metadata = {
                    "title": title,
                    "meta_description": scrape_result.get("meta_description"),
                    "word_count": len(markdown_content.split()),
                    "character_count": len(markdown_content),
                    "domain": urlparse(url).netloc if url else None,
                }

                # Add links and images count if available
                if "links" in content_data:
                    metadata["links_count"] = len(content_data["links"])
                if "images" in content_data:
                    metadata["images_count"] = len(content_data["images"])

                result["metadata"] = metadata

            return result

        except Exception as e:
            logger.error(f"Error converting webpage to Markdown: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "url": scrape_result.get("url", ""),
            }

    def batch_convert_to_markdown(
        self,
        scrape_results: List[Dict[str, Any]],
        extract_main_content: bool = True,
        include_metadata: bool = True,
        custom_options: Optional[Dict[str, Any]] = None,
        formatting_options: Optional[Dict[str, bool]] = None,
    ) -> Dict[str, Any]:
        """
        Convert multiple scraped webpage results to Markdown format.

        Args:
            scrape_results: List of scraping results
            extract_main_content: Whether to extract main content area
            include_metadata: Whether to include page metadata
            custom_options: Custom options for markdownify
            formatting_options: Advanced formatting options (overrides defaults)

        Returns:
            Dictionary with converted results and summary
        """
        try:
            converted_results = []
            successful_conversions = 0
            failed_conversions = 0

            for scrape_result in scrape_results:
                conversion_result = self.convert_webpage_to_markdown(
                    scrape_result,
                    extract_main_content,
                    include_metadata,
                    custom_options,
                    formatting_options,
                )

                if conversion_result.get("success"):
                    successful_conversions += 1
                else:
                    failed_conversions += 1

                converted_results.append(conversion_result)

            return {
                "success": True,
                "results": converted_results,
                "summary": {
                    "total": len(scrape_results),
                    "successful": successful_conversions,
                    "failed": failed_conversions,
                    "success_rate": successful_conversions
                    / max(1, len(scrape_results)),
                },
                "conversion_options": {
                    "extract_main_content": extract_main_content,
                    "include_metadata": include_metadata,
                    "custom_options": custom_options or {},
                },
            }

        except Exception as e:
            logger.error(f"Error in batch Markdown conversion: {str(e)}")
            return {"success": False, "error": str(e), "results": []}
