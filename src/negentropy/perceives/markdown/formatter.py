"""Markdown 格式化管线：将原始 Markdown 内容增强为高质量输出。"""

import logging
import os
import re
import uuid
from typing import Dict, Optional, Tuple

logger = logging.getLogger(__name__)

# Default formatting options
DEFAULT_FORMATTING_OPTIONS: Dict[str, bool] = {
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


class MarkdownFormatter:
    """Markdown formatting pipeline for enhancing raw Markdown output."""

    def __init__(self, options: Optional[Dict[str, bool]] = None) -> None:
        self.options = dict(DEFAULT_FORMATTING_OPTIONS)
        if options:
            self.options.update(options)

    def format(self, markdown_content: str) -> str:
        """
        Apply the full formatting pipeline to Markdown content.

        Args:
            markdown_content: Raw Markdown content

        Returns:
            Enhanced and cleaned up Markdown content
        """
        try:
            # 保护代码块内容不被格式化 pass 修改
            markdown_content, protected = self._protect_code_blocks(markdown_content)

            if self.options.get("format_tables", True):
                markdown_content = self._format_tables(markdown_content)

            if self.options.get("enhance_images", True):
                markdown_content = self._format_images(markdown_content)

            if self.options.get("optimize_links", True):
                markdown_content = self._format_links(markdown_content)

            if self.options.get("format_lists", True):
                markdown_content = self._format_lists(markdown_content)

            if self.options.get("format_headings", True):
                markdown_content = self._format_headings(markdown_content)

            # Code block and quote formatting always applied
            markdown_content = self._format_code_blocks(markdown_content)
            markdown_content = self._format_quotes(markdown_content)

            if self.options.get("apply_typography", True):
                markdown_content = self._apply_typography_fixes(markdown_content)

            markdown_content = self._basic_cleanup(markdown_content)

            # 还原被保护的代码块
            markdown_content = self._restore_code_blocks(markdown_content, protected)

            return markdown_content

        except Exception as e:
            logger.warning(f"Error post-processing Markdown: {str(e)}")
            return markdown_content

    def _protect_code_blocks(
        self, markdown_content: str
    ) -> Tuple[str, Dict[str, str]]:
        """提取已标注语言的代码块并替换为占位符，防止格式化管线修改其内容。

        仅保护已有语言标签的代码块（如 ```python, ```algorithm），
        未标注语言的代码块留给 _format_code_blocks 进行语言检测。
        """
        protected: Dict[str, str] = {}

        def _replacer(match: re.Match) -> str:
            placeholder = f"%%CODEBLOCK_{uuid.uuid4().hex[:12]}%%"
            protected[placeholder] = match.group(0)
            return placeholder

        # 仅匹配带语言标签的代码块（```后紧跟字母）
        result = re.sub(
            r"^```[a-zA-Z][^\n]*\n.*?^```\s*$",
            _replacer,
            markdown_content,
            flags=re.MULTILINE | re.DOTALL,
        )
        return result, protected

    def _restore_code_blocks(
        self, markdown_content: str, protected: Dict[str, str]
    ) -> str:
        """将占位符还原为原始代码块内容。"""
        for placeholder, original in protected.items():
            markdown_content = markdown_content.replace(placeholder, original)
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
                    cells = [cell.strip() for cell in line.split("|")[1:-1]]

                    if i + 1 < len(lines) and re.match(
                        r"^\s*\|[\s\-:]+\|\s*$", lines[i + 1]
                    ):
                        formatted_line = "| " + " | ".join(cells) + " |"
                        formatted_lines.append(formatted_line)
                    elif re.match(r"^\s*\|[\s\-:]+\|\s*$", line):
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
            markdown_content = re.sub(
                r"\[([^\]]+)\]\s*\(\s*([^\s\)]+)\s*\)", r"[\1](\2)", markdown_content
            )

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
            markdown_content = re.sub(
                r"^(\s*)>\s*(.+)$", r"\1> \2", markdown_content, flags=re.MULTILINE
            )

            markdown_content = re.sub(
                r"(^>.+$)", r"\n\1\n", markdown_content, flags=re.MULTILINE
            )

            return markdown_content
        except Exception as e:
            logger.warning(f"Error formatting quotes: {str(e)}")
            return markdown_content

    def _format_lists(self, markdown_content: str) -> str:
        """Improve list formatting and nesting."""
        try:
            lines = markdown_content.split("\n")
            formatted_lines = []

            for line in lines:
                line = re.sub(r"^(\s*)([-\*\+])\s*(.+)$", r"\1- \3", line)
                line = re.sub(r"^(\s*)(\d+)[\.\)]\s*(.+)$", r"\1\2. \3", line)
                formatted_lines.append(line)

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
                    heading = line.strip()

                    if (
                        i > 0
                        and lines[i - 1].strip() != ""
                        and not re.match(r"^#{1,6}\s", lines[i - 1])
                    ):
                        formatted_lines.append("")

                    formatted_lines.append(heading)

                    if i < len(lines) - 1 and lines[i + 1].strip() != "":
                        formatted_lines.append("")
                else:
                    formatted_lines.append(line)

            return "\n".join(formatted_lines)
        except Exception as e:
            logger.warning(f"Error formatting headings: {str(e)}")
            return markdown_content

    def _apply_typography_fixes(self, markdown_content: str) -> str:
        """Apply typography improvements.

        使用 extract-process-restore 模式保护 LaTeX 数学内容，
        防止排版修正破坏公式中的空格和标点。
        """
        try:
            from ..pdf.math_formula import protect_math_content

            def _typography_inner(text: str) -> str:
                text = re.sub(r"(?<!\-)\-\-(?!\-)", "\u2014", text)

                lines = text.split("\n")
                fixed_lines = []
                for line in lines:
                    line = re.sub(r" {2,}", " ", line)
                    fixed_lines.append(line)
                text = "\n".join(fixed_lines)

                text = re.sub(r"\s+([.!?:;,])", r"\1", text)
                text = re.sub(r"([.!?])\s*([A-Z])", r"\1 \2", text)

                return text

            return protect_math_content(markdown_content, _typography_inner)
        except Exception as e:
            logger.warning(f"Error applying typography fixes: {str(e)}")
            return markdown_content

    def _basic_cleanup(self, markdown_content: str) -> str:
        """Apply basic cleanup operations."""
        try:
            lines = []
            for line in markdown_content.split("\n"):
                cleaned_line = line.rstrip()
                lines.append(cleaned_line)

            markdown_content = "\n".join(lines)
            markdown_content = re.sub(r"\n{3,}", "\n\n", markdown_content)
            markdown_content = markdown_content.strip()

            return markdown_content

        except Exception as e:
            logger.warning(f"Error in basic cleanup: {str(e)}")
            return markdown_content


def markdown_to_text(markdown_content: str) -> str:
    """Convert markdown to plain text by removing formatting."""
    try:
        text = re.sub(r"!\[.*?\]\(.*?\)", "", markdown_content)  # Images
        text = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", text)  # Links
        text = re.sub(r"[*_]{1,2}([^*_]+)[*_]{1,2}", r"\1", text)  # Bold/italic
        text = re.sub(r"`([^`]+)`", r"\1", text)  # Inline code
        text = re.sub(r"^#{1,6}\s+", "", text, flags=re.MULTILINE)  # Headers
        text = re.sub(r"^>\s+", "", text, flags=re.MULTILINE)  # Blockquotes
        text = re.sub(r"^\s*[-*+]\s+", "", text, flags=re.MULTILINE)  # Lists
        text = re.sub(r"^\s*\d+\.\s+", "", text, flags=re.MULTILINE)  # Numbered lists

        return text.strip()
    except Exception as e:
        logger.warning(f"Error converting markdown to text: {str(e)}")
        return markdown_content
