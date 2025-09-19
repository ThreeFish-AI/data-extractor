"""Markdown conversion utilities for various content types using MarkItDown."""

import logging
import re
import tempfile
import os
from typing import Dict, Any, List, Optional, Union
from urllib.parse import urljoin, urlparse
from pathlib import Path

try:
    from markitdown import MarkItDown
except ImportError:
    # Fallback for testing or if markitdown is not available
    MarkItDown = None

from bs4 import BeautifulSoup, Comment
import base64
import mimetypes
import requests

logger = logging.getLogger(__name__)


class MarkdownConverter:
    """Convert various content types to Markdown format using Microsoft's MarkItDown."""

    def __init__(
        self, enable_plugins: bool = False, llm_client=None, llm_model: str = None
    ):
        """
        Initialize the Markdown converter.

        Args:
            enable_plugins: Whether to enable MarkItDown plugins
            llm_client: Optional LLM client for enhanced image descriptions
            llm_model: LLM model to use (e.g., "gpt-4o")
        """
        if MarkItDown is None:
            raise ImportError(
                "MarkItDown is not available. Please install it with: pip install 'markitdown[all]'"
            )

        self.markitdown = MarkItDown(
            enable_plugins=enable_plugins, llm_client=llm_client, llm_model=llm_model
        )

        # Configuration options for different conversion scenarios
        self.default_options = {
            "extract_main_content": True,
            "preserve_structure": True,
            "clean_output": True,
            "include_links": True,
            "include_images": True,
        }

        # Advanced formatting options
        self.formatting_options = {
            "format_tables": True,
            "enhance_images": True,
            "optimize_links": True,
            "format_lists": True,
            "format_headings": True,
            "apply_typography": True,
            "smart_quotes": True,
            "em_dashes": True,
            "fix_spacing": True,
        }

    def html_to_markdown(
        self,
        html_content: str,
        base_url: Optional[str] = None,
        custom_options: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Convert HTML content to Markdown using MarkItDown.

        Args:
            html_content: HTML content to convert
            base_url: Base URL for resolving relative URLs
            custom_options: Custom options (maintained for compatibility)

        Returns:
            Markdown formatted content
        """
        try:
            # Preprocess HTML if needed
            processed_html = self.preprocess_html(html_content, base_url)

            # Create a temporary HTML file for MarkItDown to process
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".html", delete=False, encoding="utf-8"
            ) as temp_file:
                temp_file.write(processed_html)
                temp_file_path = temp_file.name

            try:
                # Convert using MarkItDown
                result = self.markitdown.convert(temp_file_path)
                markdown_content = result.text_content

                # Post-process the markdown for better formatting
                markdown_content = self.postprocess_markdown(markdown_content)

                return markdown_content

            finally:
                # Clean up temporary file
                try:
                    os.unlink(temp_file_path)
                except OSError:
                    pass

        except Exception as e:
            logger.error(f"Error converting HTML to Markdown with MarkItDown: {str(e)}")
            # Fallback to basic conversion if MarkItDown fails
            return self._fallback_html_conversion(html_content)

    def _fallback_html_conversion(self, html_content: str) -> str:
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

    def preprocess_html(self, html_content: str, base_url: Optional[str] = None) -> str:
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
                    href = link.get("href", "")
                    if isinstance(href, str) and not href.startswith(
                        ("http://", "https://")
                    ):
                        link["href"] = urljoin(base_url, href)

                # Convert relative image sources
                for img in soup.find_all("img", src=True):
                    src = img.get("src", "")
                    if isinstance(src, str) and not src.startswith(
                        ("http://", "https://")
                    ):
                        img["src"] = urljoin(base_url, src)

            return str(soup)

        except Exception as e:
            logger.warning(f"Error preprocessing HTML: {str(e)}")
            return html_content

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

            if self.formatting_options.get("enhance_images", True):
                markdown_content = self._format_images(markdown_content)

            if self.formatting_options.get("optimize_links", True):
                markdown_content = self._format_links(markdown_content)

            if self.formatting_options.get("format_lists", True):
                markdown_content = self._format_lists(markdown_content)

            if self.formatting_options.get("format_headings", True):
                markdown_content = self._format_headings(markdown_content)

            # Add code block and quote formatting
            markdown_content = self._format_code_blocks(markdown_content)
            markdown_content = self._format_quotes(markdown_content)

            if self.formatting_options.get("apply_typography", True):
                markdown_content = self._apply_typography_fixes(markdown_content)

            # Basic cleanup
            markdown_content = self._basic_cleanup(markdown_content)

            return markdown_content

        except Exception as e:
            logger.warning(f"Error post-processing Markdown: {str(e)}")
            return markdown_content

    def _embed_images_in_markdown(
        self,
        markdown_content: str,
        *,
        max_images: int = 50,
        max_bytes_per_image: int = 2_000_000,
        timeout_seconds: int = 10,
    ) -> Dict[str, Any]:
        """Embed remote images referenced in Markdown as data URIs."""
        try:
            pattern = re.compile(r"!\[(.*?)\]\((.*?)\)")

            embedded_count = 0
            attempted = 0
            skipped_large = 0
            skipped_errors = 0

            def replacer(match: re.Match) -> str:
                nonlocal embedded_count, attempted, skipped_large, skipped_errors
                if embedded_count >= max_images:
                    return match.group(0)

                alt_text = match.group(1)
                image_url = match.group(2)

                attempted += 1

                try:
                    resp = requests.get(image_url, timeout=timeout_seconds, stream=True)
                    resp.raise_for_status()

                    content_type = resp.headers.get("Content-Type", "")
                    if not content_type.startswith("image/"):
                        guessed, _ = mimetypes.guess_type(image_url)
                        if not (guessed and guessed.startswith("image/")):
                            return match.group(0)
                        content_type = guessed

                    # Guard by Content-Length if present
                    length_header = resp.headers.get("Content-Length")
                    if length_header is not None:
                        try:
                            content_length = int(length_header)
                            if content_length > max_bytes_per_image:
                                skipped_large += 1
                                return match.group(0)
                        except Exception:
                            pass

                    content = resp.content
                    if len(content) > max_bytes_per_image:
                        skipped_large += 1
                        return match.group(0)

                    b64 = base64.b64encode(content).decode("ascii")
                    data_uri = f"data:{content_type};base64,{b64}"
                    embedded_count += 1
                    return f"![{alt_text}]({data_uri})"
                except Exception:
                    skipped_errors += 1
                    return match.group(0)

            new_md = pattern.sub(replacer, markdown_content)

            return {
                "markdown": new_md,
                "stats": {
                    "attempted": attempted,
                    "embedded": embedded_count,
                    "skipped_large": skipped_large,
                    "skipped_errors": skipped_errors,
                    "max_images": max_images,
                    "max_bytes_per_image": max_bytes_per_image,
                },
            }
        except Exception as e:
            logger.warning(f"Error embedding images: {str(e)}")
            return {
                "markdown": markdown_content,
                "stats": {
                    "attempted": 0,
                    "embedded": 0,
                    "skipped_large": 0,
                    "skipped_errors": 1,
                },
            }

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
                    cells = [cell.strip() for cell in line.split("|")[1:-1]]

                    # Check if next line is a separator (header separator)
                    if i + 1 < len(lines) and re.match(
                        r"^\s*\|[\s\-:]+\|\s*$", lines[i + 1]
                    ):
                        # This is a header row
                        formatted_line = "| " + " | ".join(cells) + " |"
                        formatted_lines.append(formatted_line)
                    elif re.match(r"^\s*\|[\s\-:]+\|\s*$", line):
                        # This is a separator row
                        separator_cells = []
                        for cell in cells:
                            if ":" in cell:
                                if cell.startswith(":") and cell.endswith(":"):
                                    separator_cells.append(":---:")
                                elif cell.endswith(":"):
                                    separator_cells.append("---:")
                                else:
                                    separator_cells.append(":---")
                            else:
                                separator_cells.append("---")
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

    def _format_images(self, markdown_content: str) -> str:
        """Enhance image formatting with better alt text."""
        try:

            def improve_image_alt(match):
                alt_text = match.group(1)
                image_url = match.group(2)

                if not alt_text or alt_text in ["", "image", "img", "photo", "picture"]:
                    # Try to generate better alt text from URL
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
        """Optimize link formatting."""
        try:
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

    def _format_code_blocks(self, markdown_content: str) -> str:
        """Enhance code block formatting with language detection."""
        try:
            # Detect common code patterns and add language hints
            code_patterns = {
                r"(?m)^(\s*)```\s*\n((?:(?!```).)*?def\s+\w+(?:(?!```).)*?)^\1```": r"\1```python\n\2\1```",
                r"(?m)^(\s*)```\s*\n((?:(?!```).)*?function\s+\w+(?:(?!```).)*?)^\1```": r"\1```javascript\n\2\1```",
                r"(?m)^(\s*)```\s*\n((?:(?!```).)*?class\s+\w+(?:(?!```).)*?)^\1```": r"\1```python\n\2\1```",
                r"(?m)^(\s*)```\s*\n((?:(?!```).)*?import\s+(?:(?!```).)*?)^\1```": r"\1```python\n\2\1```",
                r"(?m)^(\s*)```\s*\n((?:(?!```).)*?<\?php(?:(?!```).)*?)^\1```": r"\1```php\n\2\1```",
                r"(?m)^(\s*)```\s*\n((?:(?!```).)*?<html(?:(?!```).)*?)^\1```": r"\1```html\n\2\1```",
                r"(?m)^(\s*)```\s*\n((?:(?!```).)*?SELECT\s+(?:(?!```).)*?)^\1```": r"\1```sql\n\2\1```",
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
                r"^(\s*)>\s*(.+)$", r"\1> \2", markdown_content, flags=re.MULTILINE
            )

            # Add spacing around blockquotes
            markdown_content = re.sub(
                r"(^>.+$)", r"\n\1\n", markdown_content, flags=re.MULTILINE
            )

            return markdown_content
        except Exception as e:
            logger.warning(f"Error formatting quotes: {str(e)}")
            return markdown_content

    def _split_text_into_paragraphs(self, text_content: str) -> list:
        """
        Split text content into paragraphs using various heuristics.

        Args:
            text_content: Raw text content

        Returns:
            List of paragraph strings
        """
        try:
            # Clean up text
            text = text_content.strip()

            # Step 1: Split by double newlines
            parts = text.split("\n\n")
            if len(parts) > 1:
                paragraphs = []
                for part in parts:
                    part = part.replace("\n", " ").strip()
                    if part:
                        paragraphs.extend(self._split_long_text(part))
                return paragraphs

            # Step 2: Split by sentence patterns
            sentence_pattern = r"([.!?])\s*\n+\s*([A-Z])"
            text_with_markers = re.sub(
                sentence_pattern, r"\1\n\nPARAGRAPH_SPLIT\n\n\2", text
            )

            if "PARAGRAPH_SPLIT" in text_with_markers:
                parts = text_with_markers.split("\n\nPARAGRAPH_SPLIT\n\n")
                paragraphs = []
                for part in parts:
                    part = part.replace("\n", " ").strip()
                    if part:
                        paragraphs.extend(self._split_long_text(part))
                return paragraphs

            # Step 3: Split by sentences with smart grouping
            return self._split_by_sentences(text)

        except Exception as e:
            logger.warning(f"Error splitting text into paragraphs: {str(e)}")
            return [text_content]

    def _split_long_text(self, text: str, max_length: int = 150) -> list:
        """Split text that's too long into smaller chunks."""
        if len(text) <= max_length:
            return [text]

        # Split by sentences first
        sentences = re.split(r"([.!?])\s+", text)

        paragraphs = []
        current_chunk = ""

        i = 0
        while i < len(sentences):
            sentence = sentences[i]
            ending = sentences[i + 1] if i + 1 < len(sentences) else ""
            full_sentence = sentence + ending

            if len(current_chunk + full_sentence) > max_length and current_chunk:
                paragraphs.append(current_chunk.strip())
                current_chunk = full_sentence
            else:
                current_chunk += full_sentence

            i += 2 if ending else 1

        if current_chunk:
            paragraphs.append(current_chunk.strip())

        return paragraphs

    def _split_by_sentences(self, text: str) -> list:
        """Split text by sentences with intelligent grouping."""
        # Split by sentence boundaries
        sentences = re.split(r"([.!?])\s+", text)

        paragraphs = []
        current_paragraph = ""

        i = 0
        while i < len(sentences):
            sentence = sentences[i]
            ending = sentences[i + 1] if i + 1 < len(sentences) else ""
            full_sentence = sentence + ending

            # Rules for paragraph boundaries
            should_break = False

            if current_paragraph:
                # Check length
                if len(current_paragraph) > 120:
                    should_break = True

                # Check for transition words
                transition_words = [
                    "However",
                    "Therefore",
                    "Furthermore",
                    "Moreover",
                    "Meanwhile",
                    "Additionally",
                    "In contrast",
                    "For example",
                ]

                for word in transition_words:
                    if full_sentence.strip().startswith(word + " "):
                        should_break = True
                        break

            if should_break and current_paragraph.strip():
                paragraphs.append(current_paragraph.strip())
                current_paragraph = full_sentence
            else:
                current_paragraph += full_sentence

            i += 2 if ending else 1

        if current_paragraph.strip():
            paragraphs.append(current_paragraph.strip())

        return paragraphs if len(paragraphs) > 1 else [text]

    def _format_lists(self, markdown_content: str) -> str:
        """Improve list formatting and nesting."""
        try:
            lines = markdown_content.split("\n")
            formatted_lines = []

            for line in lines:
                # Ensure consistent list marker spacing
                line = re.sub(r"^(\s*)([-\*\+])\s*(.+)$", r"\1- \3", line)

                # Ensure consistent numbered list formatting
                line = re.sub(r"^(\s*)(\d+)[\.\)]\s*(.+)$", r"\1\2. \3", line)

                formatted_lines.append(line)

            # Clean up empty list items
            markdown_content = "\n".join(formatted_lines)
            markdown_content = re.sub(r"\n[-*+]\s*\n(?=\n)", "\n", markdown_content)

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

                    # Add spacing before headings
                    if (
                        i > 0
                        and lines[i - 1].strip() != ""
                        and not re.match(r"^#{1,6}\s", lines[i - 1])
                    ):
                        formatted_lines.append("")

                    formatted_lines.append(heading)

                    # Add spacing after headings
                    if i < len(lines) - 1 and lines[i + 1].strip() != "":
                        formatted_lines.append("")
                else:
                    formatted_lines.append(line)

            return "\n".join(formatted_lines)
        except Exception as e:
            logger.warning(f"Error formatting headings: {str(e)}")
            return markdown_content

    def _apply_typography_fixes(self, markdown_content: str) -> str:
        """Apply typography improvements."""
        try:
            # Convert double hyphens to em dashes
            markdown_content = re.sub(r"(?<!\-)\-\-(?!\-)", "—", markdown_content)

            # Fix multiple spaces
            lines = markdown_content.split("\n")
            fixed_lines = []
            for line in lines:
                line = re.sub(r" {2,}", " ", line)
                fixed_lines.append(line)
            markdown_content = "\n".join(fixed_lines)

            # Fix spacing around punctuation
            markdown_content = re.sub(r"\s+([.!?:;,])", r"\1", markdown_content)
            markdown_content = re.sub(r"([.!?])\s*([A-Z])", r"\1 \2", markdown_content)

            return markdown_content
        except Exception as e:
            logger.warning(f"Error applying typography fixes: {str(e)}")
            return markdown_content

    def _basic_cleanup(self, markdown_content: str) -> str:
        """Apply basic cleanup operations."""
        try:
            # Clean up excessive spaces
            lines = []
            for line in markdown_content.split("\n"):
                cleaned_line = line.rstrip()
                lines.append(cleaned_line)

            markdown_content = "\n".join(lines)

            # Remove excessive blank lines
            markdown_content = re.sub(r"\n{3,}", "\n\n", markdown_content)

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

    def convert_pdf_to_markdown(
        self,
        pdf_source: Union[str, Path],
        page_range: Optional[List[int]] = None,
        output_format: str = "markdown",
        include_metadata: bool = True,
    ) -> Dict[str, Any]:
        """
        Convert PDF to Markdown using MarkItDown.

        Args:
            pdf_source: Path to PDF file or URL
            page_range: Optional page range [start, end]
            output_format: Output format ("markdown" or "text")
            include_metadata: Whether to include metadata

        Returns:
            Dictionary with conversion results
        """
        try:
            # Handle URL downloads
            temp_file_path = None
            if isinstance(pdf_source, str) and pdf_source.startswith(
                ("http://", "https://")
            ):
                # Download PDF from URL
                response = requests.get(pdf_source, timeout=30)
                response.raise_for_status()

                with tempfile.NamedTemporaryFile(
                    suffix=".pdf", delete=False
                ) as temp_file:
                    temp_file.write(response.content)
                    temp_file_path = temp_file.name
                    source_path = temp_file_path
            else:
                source_path = str(pdf_source)

            try:
                # Convert using MarkItDown
                result = self.markitdown.convert(source_path)
                content = result.text_content

                # Apply output format preference
                if output_format == "text":
                    # Remove markdown formatting for plain text
                    content = self._markdown_to_text(content)

                return {
                    "success": True,
                    "content": content,
                    "source": str(pdf_source),
                    "method": "markitdown",
                    "output_format": output_format,
                    "metadata": {
                        "word_count": len(content.split()),
                        "character_count": len(content),
                    }
                    if include_metadata
                    else None,
                }

            finally:
                # Clean up temporary file if created
                if temp_file_path and os.path.exists(temp_file_path):
                    try:
                        os.unlink(temp_file_path)
                    except OSError:
                        pass

        except Exception as e:
            logger.error(f"Error converting PDF to Markdown: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "source": str(pdf_source),
            }

    def _markdown_to_text(self, markdown_content: str) -> str:
        """Convert markdown to plain text by removing formatting."""
        try:
            # Remove markdown formatting
            text = re.sub(r"!\[.*?\]\(.*?\)", "", markdown_content)  # Images
            text = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", text)  # Links
            text = re.sub(r"[*_]{1,2}([^*_]+)[*_]{1,2}", r"\1", text)  # Bold/italic
            text = re.sub(r"`([^`]+)`", r"\1", text)  # Inline code
            text = re.sub(r"^#{1,6}\s+", "", text, flags=re.MULTILINE)  # Headers
            text = re.sub(r"^>\s+", "", text, flags=re.MULTILINE)  # Blockquotes
            text = re.sub(r"^\s*[-*+]\s+", "", text, flags=re.MULTILINE)  # Lists
            text = re.sub(
                r"^\s*\d+\.\s+", "", text, flags=re.MULTILINE
            )  # Numbered lists

            return text.strip()
        except Exception as e:
            logger.warning(f"Error converting markdown to text: {str(e)}")
            return markdown_content

    def convert_webpage_to_markdown(
        self,
        scrape_result: Dict[str, Any],
        extract_main_content: bool = True,
        include_metadata: bool = True,
        custom_options: Optional[Dict[str, Any]] = None,
        formatting_options: Optional[Dict[str, bool]] = None,
        *,
        embed_images: bool = False,
        embed_options: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Convert a scraped webpage result to Markdown format.

        Args:
            scrape_result: Result from web scraping
            extract_main_content: Whether to extract main content area
            include_metadata: Whether to include page metadata
            custom_options: Custom options (maintained for compatibility)
            formatting_options: Advanced formatting options

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

            # Get HTML content
            html_content = content_data.get("html")
            if not html_content and content_data.get("text"):
                # Build basic HTML from text content
                html_content = self._build_html_from_text(
                    content_data["text"], title, content_data
                )

            if not html_content:
                return {
                    "success": False,
                    "error": "No content found in scrape result",
                    "url": url,
                }

            # Extract main content area if requested
            if extract_main_content:
                html_content = self.extract_content_area(html_content)

            # Update formatting options temporarily if provided
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

            # Optionally embed images as data URIs
            embed_stats = None
            if embed_images:
                opts = embed_options or {}
                embed_result = self._embed_images_in_markdown(
                    markdown_content,
                    max_images=int(opts.get("max_images", 50)),
                    max_bytes_per_image=int(opts.get("max_bytes_per_image", 2_000_000)),
                    timeout_seconds=int(opts.get("timeout_seconds", 10)),
                )
                markdown_content = embed_result.get("markdown", markdown_content)
                embed_stats = embed_result.get("stats")

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
                    "embed_images": embed_images,
                    "embed_options": embed_options or {},
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

                if "links" in content_data:
                    metadata["links_count"] = len(content_data["links"])
                if "images" in content_data:
                    metadata["images_count"] = len(content_data["images"])

                if embed_stats is not None:
                    metadata["image_embedding"] = embed_stats

                result["metadata"] = metadata

            return result

        except Exception as e:
            logger.error(f"Error converting webpage to Markdown: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "url": scrape_result.get("url", ""),
            }

    def _build_html_from_text(
        self, text_content: str, title: str, content_data: Dict
    ) -> str:
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

    def batch_convert_to_markdown(
        self,
        scrape_results: List[Dict[str, Any]],
        extract_main_content: bool = True,
        include_metadata: bool = True,
        custom_options: Optional[Dict[str, Any]] = None,
        formatting_options: Optional[Dict[str, bool]] = None,
        *,
        embed_images: bool = False,
        embed_options: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Convert multiple scraped webpage results to Markdown format.

        Args:
            scrape_results: List of scraping results
            extract_main_content: Whether to extract main content area
            include_metadata: Whether to include page metadata
            custom_options: Custom options (maintained for compatibility)
            formatting_options: Advanced formatting options

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
                    embed_images=embed_images,
                    embed_options=embed_options,
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
