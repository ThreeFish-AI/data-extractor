"""Markdown conversion utilities for HTML content."""

import logging
import re
from typing import Dict, Any, List, Optional
from urllib.parse import urljoin, urlparse

from markdownify import markdownify as md
from bs4 import BeautifulSoup, Comment
import base64
import mimetypes
import requests

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
            "strip": ["script", "style"],  # Strip unwanted tags
            "default_title": False,  # Don't include title in links
            "escape_asterisks": False,  # Don't escape asterisks in text
            "escape_underscores": False,  # Don't escape underscores in text
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

            # Mark paragraph boundaries for later processing
            for i, tag in enumerate(soup.find_all("p")):
                text_content = tag.get_text(strip=True)
                if text_content:  # Only if paragraph has content
                    # Check if paragraph contains only images or other media without text
                    media_tags = tag.find_all(["img", "video", "audio"])
                    if media_tags and not text_content:
                        # Skip paragraphs that only contain media elements
                        continue

                    # Simple and safe approach: add markers around the entire paragraph
                    from bs4 import NavigableString

                    tag.insert(0, NavigableString(f"PARAGRAPH_START_{i} "))
                    tag.append(NavigableString(f" PARAGRAPH_END_{i}"))

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

    def _embed_images_in_markdown(
        self,
        markdown_content: str,
        *,
        max_images: int = 50,
        max_bytes_per_image: int = 2_000_000,
        timeout_seconds: int = 10,
    ) -> Dict[str, Any]:
        """Embed remote images referenced in Markdown as data URIs.

        Best-effort: on failure or limits exceeded, preserves original links.
        Returns new markdown and embedding stats for diagnostics.
        """
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
            # Detect common code patterns and add language hints (handle indented code blocks)
            # Use more specific patterns to avoid overlapping matches
            code_patterns = {
                r"(?m)^(\s*)```\s*\n((?:(?!```).)*?function\s+\w+(?:(?!```).)*?)^\1```": r"\1```javascript\n\2\1```",
                r"(?m)^(\s*)```\s*\n((?:(?!```).)*?def\s+\w+(?:(?!```).)*?)^\1```": r"\1```python\n\2\1```",
                r"(?m)^(\s*)```\s*\n((?:(?!```).)*?class\s+\w+(?:(?!```).)*?)^\1```": r"\1```python\n\2\1```",
                r"(?m)^(\s*)```\s*\n((?:(?!```).)*?import\s+(?:(?!```).)*?)^\1```": r"\1```python\n\2\1```",
                r"(?m)^(\s*)```\s*\n((?:(?!```).)*?<\?php(?:(?!```).)*?)^\1```": r"\1```php\n\2\1```",
                r"(?m)^(\s*)```\s*\n((?:(?!```).)*?<html(?:(?!```).)*?)^\1```": r"\1```html\n\2\1```",
                r"(?m)^(\s*)```\s*\n((?:(?!```).)*?<!DOCTYPE(?:(?!```).)*?)^\1```": r"\1```html\n\2\1```",
                r"(?m)^(\s*)```\s*\n((?:(?!```).)*?SELECT\s+(?:(?!```).)*?)^\1```": r"\1```sql\n\2\1```",
                r'(?m)^(\s*)```\s*\n((?:(?!```).)*?\{.*?".*?".*?\}(?:(?!```).)*?)^\1```': r"\1```json\n\2\1```",
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
            # Ensure blockquotes are properly formatted (handle indented quotes)
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
        """Improve list formatting and nesting while preserving paragraph structure."""
        try:
            lines = markdown_content.split("\n")
            formatted_lines = []

            for line in lines:
                # Ensure consistent list marker spacing (normalize to -)
                line = re.sub(r"^(\s*)([-\*\+])\s*(.+)$", r"\1- \3", line)

                # Ensure consistent numbered list formatting
                line = re.sub(r"^(\s*)(\d+)[\.\)]\s*(.+)$", r"\1\2. \3", line)

                formatted_lines.append(line)

            # Clean up empty list items only if they're truly empty
            markdown_content = "\n".join(formatted_lines)
            markdown_content = re.sub(r"\n[-*+]\s*\n(?=\n)", "\n", markdown_content)

            return markdown_content
        except Exception as e:
            logger.warning(f"Error formatting lists: {str(e)}")
            return markdown_content

    def _format_headings(self, markdown_content: str) -> str:
        """Improve heading formatting and hierarchy while preserving paragraph structure."""
        try:
            lines = markdown_content.split("\n")
            formatted_lines = []

            for i, line in enumerate(lines):
                if re.match(r"^#{1,6}\s", line):
                    # Ensure proper heading spacing
                    heading = line.strip()

                    # Add spacing before headings (except if first line or after blank line)
                    if (
                        i > 0
                        and lines[i - 1].strip() != ""
                        and not re.match(r"^#{1,6}\s", lines[i - 1])
                    ):
                        formatted_lines.append("")  # Add blank line before heading

                    formatted_lines.append(heading)

                    # Add spacing after headings (except if next line is blank)
                    if i < len(lines) - 1 and lines[i + 1].strip() != "":
                        formatted_lines.append("")  # Add blank line after heading
                else:
                    # Always append non-heading lines preserving original structure
                    formatted_lines.append(line)

            return "\n".join(formatted_lines)
        except Exception as e:
            logger.warning(f"Error formatting headings: {str(e)}")
            return markdown_content

    def _apply_typography_fixes(self, markdown_content: str) -> str:
        """Apply typography improvements while preserving paragraph structure."""
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

            # Fix multiple spaces within lines (but not between lines)
            lines = markdown_content.split("\n")
            fixed_lines = []
            for line in lines:
                # Fix multiple spaces in all lines, including those with only whitespace
                line = re.sub(r" {2,}", " ", line)
                fixed_lines.append(line)
            markdown_content = "\n".join(fixed_lines)

            # Fix spacing around punctuation within lines
            markdown_content = re.sub(r"\s+([.!?:;,])", r"\1", markdown_content)
            markdown_content = re.sub(r"([.!?])\s*([A-Z])", r"\1 \2", markdown_content)

            return markdown_content
        except Exception as e:
            logger.warning(f"Error applying typography fixes: {str(e)}")
            return markdown_content

    def _basic_cleanup(self, markdown_content: str) -> str:
        """Apply basic cleanup operations while preserving paragraph structure."""
        try:
            # Restore paragraph boundaries from markers
            # Handle both complete and partial markers
            markdown_content = re.sub(
                r"PARAGRAPH_START_\d+ (.*?) PARAGRAPH_END_\d+",
                r"\1\n\n",
                markdown_content,
                flags=re.DOTALL,
            )

            # Clean up any remaining markers that weren't matched
            markdown_content = re.sub(
                r"PARAGRAPH_START_\d+[.?]?\s*", "", markdown_content
            )
            markdown_content = re.sub(r"\s*PARAGRAPH_END_\d+", "\n\n", markdown_content)

            # Clean up excessive spaces but preserve line structure
            lines = []
            for line in markdown_content.split("\n"):
                # Remove trailing spaces but preserve intentional line breaks
                cleaned_line = line.rstrip()
                lines.append(cleaned_line)

            markdown_content = "\n".join(lines)

            # Remove excessive blank lines (more than 2 consecutive) while preserving paragraph breaks
            # This removes multiple consecutive empty lines but keeps essential paragraph separators
            markdown_content = re.sub(r"\n{3,}", "\n\n", markdown_content)

            # Remove leading/trailing whitespace
            markdown_content = markdown_content.strip()

            return markdown_content

        except Exception as e:
            logger.warning(f"Error in basic cleanup: {str(e)}")
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
            import re

            # Pre-processing: clean up text
            text = text_content.strip()

            # Step 1: Split by double newlines (most reliable)
            parts = text.split("\n\n")
            if len(parts) > 1:
                paragraphs = []
                for part in parts:
                    part = part.replace("\n", " ").strip()
                    if part:
                        # Further split long parts
                        paragraphs.extend(self._split_long_text(part))
                return paragraphs

            # Step 2: Split by newline + capital letter patterns
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

            # Step 3: Split by semantic patterns (topic transitions)
            paragraphs = self._split_by_semantic_patterns(text)
            if len(paragraphs) > 1:
                return paragraphs

            # Step 4: Split by sentence boundaries with smart grouping
            return self._split_by_sentences(text)

        except Exception as e:
            logger.warning(f"Error splitting text into paragraphs: {str(e)}")
            return [text_content]

    def _split_long_text(self, text: str, max_length: int = 150) -> list:
        """Split text that's too long into smaller chunks."""
        import re

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

    def _split_by_semantic_patterns(self, text: str) -> list:
        """Split text by semantic patterns like topic changes."""
        import re

        # Patterns that indicate new topics/sections
        topic_patterns = [
            r"([.!?])\s+(However|Therefore|Furthermore|Moreover|Additionally|Meanwhile|In contrast|For example|Similarly|On the other hand|In fact|Indeed|Specifically|Generally|Overall|Finally)",
            r"([.!?])\s+(The\s+[A-Z][a-z]+)",
            r"([.!?])\s+([A-Z][a-z]+\s+(agents?|tools?|methods?|approaches?|strategies?|techniques?|systems?|models?|applications?))",
        ]

        for pattern in topic_patterns:
            if re.search(pattern, text):
                parts = re.split(pattern, text)
                if len(parts) > 3:  # We have actual splits
                    paragraphs = []
                    current = ""

                    for i in range(
                        0, len(parts), 4
                    ):  # Groups of 4 due to capturing groups
                        if i + 3 < len(parts):
                            segment = (
                                parts[i] + parts[i + 1] + parts[i + 2] + parts[i + 3]
                            )
                        else:
                            segment = "".join(parts[i:])

                        if current and len(current + segment) > 200:
                            paragraphs.extend(self._split_long_text(current.strip()))
                            current = segment
                        else:
                            current += segment

                    if current:
                        paragraphs.extend(self._split_long_text(current.strip()))

                    if len(paragraphs) > 1:
                        return paragraphs

        return [text]

    def _split_by_sentences(self, text: str) -> list:
        """Split text by sentences with intelligent grouping."""
        import re

        # Split by sentence boundaries
        sentences = re.split(r"([.!?])\s+", text)

        paragraphs = []
        current_paragraph = ""

        i = 0
        while i < len(sentences):
            sentence = sentences[i]
            ending = sentences[i + 1] if i + 1 < len(sentences) else ""
            full_sentence = sentence + ending

            # Rules for paragraph boundaries:
            should_break = False

            if current_paragraph:
                # Check length (ultra aggressive threshold)
                if len(current_paragraph) > 90:
                    should_break = True

                # Force break after any sentence if the paragraph already has content
                # This handles the worst cases with many sentences crammed together
                if current_paragraph.strip() and "." in current_paragraph:
                    sentence_count = (
                        current_paragraph.count(".")
                        + current_paragraph.count("!")
                        + current_paragraph.count("?")
                    )
                    if sentence_count >= 1 and len(current_paragraph) > 80:
                        should_break = True

                # Check for transition words (expanded list)
                transition_words = [
                    "However",
                    "Therefore",
                    "Furthermore",
                    "Moreover",
                    "Meanwhile",
                    "Additionally",
                    "In contrast",
                    "For example",
                    "Similarly",
                    "The",
                    "This",
                    "These",
                    "That",
                    "Agents",
                    "Context",
                    "Memory",
                    "Tools",
                    "When",
                    "Where",
                    "Why",
                    "How",
                    "First",
                    "Second",
                    "Third",
                    "Finally",
                    "Also",
                    "But",
                    "So",
                    "And",
                    "As",
                    "If",
                    "With",
                    "For",
                    "To",
                    "In",
                    "On",
                    "At",
                    "By",
                    "From",
                    "What",
                    "Which",
                    "Who",
                    "ChatGPT",
                    "Claude",
                    "GPT",
                    "AI",
                    "LLM",
                    "Another",
                    "One",
                    "Many",
                    "Some",
                    "All",
                    "Most",
                    "Few",
                    "Several",
                    "Each",
                    "Every",
                    "Any",
                    "Other",
                    "Both",
                    "Either",
                    "Neither",
                ]

                for word in transition_words:
                    if full_sentence.strip().startswith(word + " "):
                        should_break = True
                        break

                # Additional rules for better splitting
                # Break after questions
                if (
                    current_paragraph.strip().endswith("?")
                    and len(current_paragraph) > 60
                ):
                    should_break = True

                # Break before quotes
                if (
                    full_sentence.strip().startswith('"')
                    and len(current_paragraph) > 50
                ):
                    should_break = True

                # Break on topic shifts (detect capitalized nouns)
                import re

                if (
                    re.match(r"^[A-Z][a-z]+\s+[a-z]+", full_sentence.strip())
                    and len(current_paragraph) > 80
                ):
                    should_break = True

                # Break on specific patterns that indicate new topics
                topic_starters = [
                    "LangGraph",
                    "Claude Code",
                    "ChatGPT",
                    "Anthropic",
                    "OpenAI",
                    "Cognition",
                    "HuggingFace",
                    "Scrapy",
                    "Selenium",
                ]
                for starter in topic_starters:
                    if (
                        full_sentence.strip().startswith(starter)
                        and len(current_paragraph) > 60
                    ):
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

        # Final pass: split any remaining long paragraphs (ultra aggressive)
        final_paragraphs = []
        for para in paragraphs if len(paragraphs) > 1 else [text]:
            if len(para) > 150:  # Very low threshold for ultra aggressive splitting
                final_paragraphs.extend(self._force_split_long_paragraph(para))
            elif (
                len(para) > 120 and para.count(".") > 1
            ):  # Split multi-sentence short paras too
                final_paragraphs.extend(self._force_split_long_paragraph(para))
            else:
                final_paragraphs.append(para)

        return final_paragraphs

    def _force_split_long_paragraph(self, text: str) -> list:
        """Force split very long paragraphs that other methods missed."""
        import re

        if len(text) <= 180:
            return [text]

        # Strategy 1: Split by sentences more aggressively
        sentences = re.split(r"([.!?])\s+", text)
        if len(sentences) > 2:
            paragraphs = []
            current = ""

            i = 0
            while i < len(sentences):
                sentence = sentences[i]
                ending = sentences[i + 1] if i + 1 < len(sentences) else ""
                full_sentence = sentence + ending

                # Ultra aggressive: break after every sentence if current has any content
                # This handles cases where multiple sentences are crammed together
                if current and (
                    len(current + full_sentence) > 120 or current.count(".") >= 1
                ):
                    paragraphs.append(current.strip())
                    current = full_sentence
                else:
                    current += full_sentence

                i += 2 if ending else 1

            if current:
                paragraphs.append(current.strip())

            if len(paragraphs) > 1:
                return paragraphs

        # Strategy 2: Split at commas followed by space and capital letters
        comma_splits = re.split(r"(,\s+)(?=[A-Z])", text)
        if len(comma_splits) > 2:
            paragraphs = []
            current = ""
            for i in range(0, len(comma_splits), 2):
                chunk = comma_splits[i] + (
                    comma_splits[i + 1] if i + 1 < len(comma_splits) else ""
                )
                if len(current + chunk) > 160 and current:
                    paragraphs.append(current.strip())
                    current = chunk
                else:
                    current += chunk
            if current:
                paragraphs.append(current.strip())
            if len(paragraphs) > 1:
                return paragraphs

        # Strategy 3: Split at colons (often indicate lists or definitions)
        colon_splits = re.split(r"(:)\s+", text)
        if len(colon_splits) > 2:
            paragraphs = []
            current = ""
            for i in range(0, len(colon_splits), 2):
                chunk = colon_splits[i] + (
                    colon_splits[i + 1] if i + 1 < len(colon_splits) else ""
                )
                if len(current + chunk) > 160 and current:
                    paragraphs.append(current.strip())
                    current = chunk
                else:
                    current += chunk
            if current:
                paragraphs.append(current.strip())
            if len(paragraphs) > 1:
                return paragraphs

        # Strategy 4: Split at semicolons
        semi_splits = text.split(";")
        if len(semi_splits) > 1:
            paragraphs = []
            current = ""
            for chunk in semi_splits:
                chunk = (
                    chunk.strip() + ";" if chunk != semi_splits[-1] else chunk.strip()
                )
                if len(current + chunk) > 160 and current:
                    paragraphs.append(current.strip())
                    current = chunk
                else:
                    current += " " + chunk if current else chunk
            if current:
                paragraphs.append(current.strip())
            if len(paragraphs) > 1:
                return paragraphs

        # Strategy 5: Split at word boundaries (last resort)
        words = text.split()
        paragraphs = []
        current = ""

        for word in words:
            if len(current + " " + word) > 150 and current:  # Even more aggressive
                paragraphs.append(current.strip())
                current = word
            else:
                current += " " + word if current else word

        if current:
            paragraphs.append(current.strip())

        return paragraphs if len(paragraphs) > 1 else [text]

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
                        if (
                            text_length > 10
                        ):  # Minimum content length (very low for testing)
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

                # Add main text content with smart paragraph splitting
                html_parts.append("<div class='main-content'>")

                # Smart paragraph detection and splitting
                paragraphs = self._split_text_into_paragraphs(text_content)
                for paragraph in paragraphs:
                    if paragraph.strip():  # Skip empty paragraphs
                        html_parts.append(f"<p>{paragraph.strip()}</p>")

                html_parts.append("</div>")

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

            # Optionally embed images as data URIs for portability
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

                # Add links and images count if available
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
