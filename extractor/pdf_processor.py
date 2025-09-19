"""PDF processing module for extracting text and converting to Markdown."""

import logging
import tempfile
import os
import re
from typing import Dict, List, Any, Optional
from pathlib import Path
from urllib.parse import urlparse
import asyncio

import aiohttp


# 延迟导入 PDF 处理库，避免启动时的 SWIG 警告
def _import_fitz():
    """延迟导入 PyMuPDF (fitz) 以避免启动时警告"""
    try:
        import fitz

        return fitz
    except ImportError as e:
        raise ImportError(f"PyMuPDF (fitz) is required for PDF processing: {e}")


def _import_pypdf():
    """延迟导入 pypdf"""
    try:
        import pypdf

        return pypdf
    except ImportError as e:
        raise ImportError(f"pypdf is required for PDF processing: {e}")


logger = logging.getLogger(__name__)


class PDFProcessor:
    """PDF processor for extracting text and converting to Markdown."""

    def __init__(self):
        self.supported_methods = ["pymupdf", "pypdf", "auto"]
        self.temp_dir = tempfile.mkdtemp(prefix="pdf_extractor_")

    async def process_pdf(
        self,
        pdf_source: str,
        method: str = "auto",
        include_metadata: bool = True,
        page_range: Optional[tuple] = None,
        output_format: str = "markdown",
    ) -> Dict[str, Any]:
        """
        Process a PDF file from URL or local path.

        Args:
            pdf_source: URL or local file path to PDF
            method: Extraction method: auto, pymupdf, pypdf (default: auto)
            include_metadata: Include PDF metadata in result (default: True)
            page_range: Tuple of (start_page, end_page) for partial extraction (optional)
            output_format: Output format: markdown, text (default: markdown)

        Returns:
            Dict containing extracted text/markdown and metadata
        """
        pdf_path = None
        try:
            # Validate method
            if method not in self.supported_methods:
                return {
                    "success": False,
                    "error": f"Method must be one of: {', '.join(self.supported_methods)}",
                    "source": pdf_source,
                }

            # Check if source is URL or local path
            if self._is_url(pdf_source):
                pdf_path = await self._download_pdf(pdf_source)
                if not pdf_path:
                    return {
                        "success": False,
                        "error": "Failed to download PDF from URL",
                        "source": pdf_source,
                    }
            else:
                pdf_path = Path(pdf_source)
                if not pdf_path.exists():
                    return {
                        "success": False,
                        "error": "PDF file does not exist",
                        "source": pdf_source,
                    }

            # Extract text using selected method
            extraction_result = None
            if method == "auto":
                extraction_result = await self._auto_extract(
                    pdf_path, page_range, include_metadata
                )
            elif method == "pymupdf":
                extraction_result = await self._extract_with_pymupdf(
                    pdf_path, page_range, include_metadata
                )
            elif method == "pypdf":
                extraction_result = await self._extract_with_pypdf(
                    pdf_path, page_range, include_metadata
                )

            if not extraction_result or not extraction_result.get("success"):
                return extraction_result or {
                    "success": False,
                    "error": "Unknown extraction error",
                    "source": pdf_source,
                }

            # Convert to markdown if requested
            if output_format == "markdown":
                markdown_content = self._convert_to_markdown(extraction_result["text"])
                extraction_result["markdown"] = markdown_content

            # Add processing info
            extraction_result.update(
                {
                    "source": pdf_source,
                    "method_used": extraction_result.get("method_used", method),
                    "output_format": output_format,
                    "pages_processed": extraction_result.get("pages_processed", 0),
                    "word_count": len(extraction_result["text"].split()),
                    "character_count": len(extraction_result["text"]),
                }
            )

            return extraction_result

        except Exception as e:
            logger.error(f"Error processing PDF {pdf_source}: {str(e)}")
            return {"success": False, "error": str(e), "source": pdf_source}
        finally:
            # Clean up downloaded files if they're in temp directory
            if pdf_path and str(pdf_path).startswith(self.temp_dir):
                try:
                    os.unlink(pdf_path)
                except Exception:
                    pass

    async def batch_process_pdfs(
        self,
        pdf_sources: List[str],
        method: str = "auto",
        include_metadata: bool = True,
        page_range: Optional[tuple] = None,
        output_format: str = "markdown",
    ) -> Dict[str, Any]:
        """
        Process multiple PDF files concurrently.

        Args:
            pdf_sources: List of URLs or local file paths
            method: Extraction method for all PDFs
            include_metadata: Include metadata for all PDFs
            page_range: Page range for all PDFs (if applicable)
            output_format: Output format for all PDFs

        Returns:
            Dict containing batch processing results and summary
        """
        if not pdf_sources:
            return {"success": False, "error": "PDF sources list cannot be empty"}

        logger.info(f"Batch processing {len(pdf_sources)} PDFs with method: {method}")

        # Process PDFs concurrently
        tasks = [
            self.process_pdf(
                pdf_source=source,
                method=method,
                include_metadata=include_metadata,
                page_range=page_range,
                output_format=output_format,
            )
            for source in pdf_sources
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results and handle exceptions
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append(
                    {"success": False, "error": str(result), "source": pdf_sources[i]}
                )
            else:
                processed_results.append(result)

        # Calculate summary statistics
        successful_results = [r for r in processed_results if r.get("success")]
        failed_results = [r for r in processed_results if not r.get("success")]

        total_pages = sum(r.get("pages_processed", 0) for r in successful_results)
        total_words = sum(r.get("word_count", 0) for r in successful_results)

        return {
            "success": True,
            "results": processed_results,
            "summary": {
                "total_pdfs": len(pdf_sources),
                "successful": len(successful_results),
                "failed": len(failed_results),
                "total_pages_processed": total_pages,
                "total_words_extracted": total_words,
                "method_used": method,
                "output_format": output_format,
            },
        }

    def _is_url(self, source: str) -> bool:
        """Check if source is a URL."""
        try:
            parsed = urlparse(source)
            return parsed.scheme in ["http", "https"]
        except Exception:
            return False

    async def _download_pdf(self, url: str) -> Optional[Path]:
        """Download PDF from URL to temporary file."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        # Create temporary file
                        temp_file = tempfile.NamedTemporaryFile(
                            suffix=".pdf", dir=self.temp_dir, delete=False
                        )

                        # Write PDF content
                        content = await response.read()
                        temp_file.write(content)
                        temp_file.close()

                        return Path(temp_file.name)
            return None
        except Exception as e:
            logger.error(f"Error downloading PDF from {url}: {str(e)}")
            return None

    async def _auto_extract(
        self,
        pdf_path: Path,
        page_range: Optional[tuple] = None,
        include_metadata: bool = True,
    ) -> Dict[str, Any]:
        """Auto-select best method for PDF extraction."""
        # Try PyMuPDF first (generally more reliable)
        try:
            result = await self._extract_with_pymupdf(
                pdf_path, page_range, include_metadata
            )
            if result.get("success"):
                result["method_used"] = "pymupdf"
                return result
        except Exception as e:
            logger.warning(f"PyMuPDF failed for {pdf_path}, trying pypdf: {str(e)}")

        # Fall back to pypdf
        try:
            result = await self._extract_with_pypdf(
                pdf_path, page_range, include_metadata
            )
            if result.get("success"):
                result["method_used"] = "pypdf"
                return result
        except Exception as e:
            logger.error(f"Both methods failed for {pdf_path}: {str(e)}")

        return {
            "success": False,
            "error": "Both PyMuPDF and pypdf extraction methods failed",
        }

    async def _extract_with_pymupdf(
        self,
        pdf_path: Path,
        page_range: Optional[tuple] = None,
        include_metadata: bool = True,
    ) -> Dict[str, Any]:
        """Extract text using PyMuPDF (fitz)."""
        try:
            fitz = _import_fitz()
            doc = fitz.open(str(pdf_path))

            # Determine page range
            total_pages = doc.page_count
            start_page = 0
            end_page = total_pages

            if page_range:
                start_page = max(0, page_range[0])
                end_page = min(total_pages, page_range[1])

            # Extract text from pages
            text_content = []
            for page_num in range(start_page, end_page):
                page = doc.load_page(page_num)
                text = page.get_text()
                if text.strip():  # Only add non-empty pages
                    text_content.append(f"<!-- Page {page_num + 1} -->\n{text}")

            full_text = "\n\n".join(text_content)

            result = {
                "success": True,
                "text": full_text,
                "pages_processed": end_page - start_page,
                "total_pages": total_pages,
            }

            # Add metadata if requested
            if include_metadata:
                metadata = doc.metadata
                result["metadata"] = {
                    "title": metadata.get("title", ""),
                    "author": metadata.get("author", ""),
                    "subject": metadata.get("subject", ""),
                    "creator": metadata.get("creator", ""),
                    "producer": metadata.get("producer", ""),
                    "creation_date": metadata.get("creationDate", ""),
                    "modification_date": metadata.get("modDate", ""),
                    "total_pages": total_pages,
                    "file_size_bytes": pdf_path.stat().st_size,
                }

            doc.close()
            return result

        except Exception as e:
            return {"success": False, "error": f"PyMuPDF extraction failed: {str(e)}"}

    async def _extract_with_pypdf(
        self,
        pdf_path: Path,
        page_range: Optional[tuple] = None,
        include_metadata: bool = True,
    ) -> Dict[str, Any]:
        """Extract text using pypdf library."""
        try:
            with open(pdf_path, "rb") as file:
                pypdf = _import_pypdf()
                reader = pypdf.PdfReader(file)
                total_pages = len(reader.pages)

                # Determine page range
                start_page = 0
                end_page = total_pages

                if page_range:
                    start_page = max(0, page_range[0])
                    end_page = min(total_pages, page_range[1])

                # Extract text from pages
                text_content = []
                for page_num in range(start_page, end_page):
                    page = reader.pages[page_num]
                    text = page.extract_text()
                    if text.strip():  # Only add non-empty pages
                        text_content.append(f"<!-- Page {page_num + 1} -->\n{text}")

                full_text = "\n\n".join(text_content)

                result = {
                    "success": True,
                    "text": full_text,
                    "pages_processed": end_page - start_page,
                    "total_pages": total_pages,
                }

                # Add metadata if requested
                if include_metadata:
                    metadata = reader.metadata or {}
                    result["metadata"] = {
                        "title": str(metadata.get("/Title", "")),
                        "author": str(metadata.get("/Author", "")),
                        "subject": str(metadata.get("/Subject", "")),
                        "creator": str(metadata.get("/Creator", "")),
                        "producer": str(metadata.get("/Producer", "")),
                        "creation_date": str(metadata.get("/CreationDate", "")),
                        "modification_date": str(metadata.get("/ModDate", "")),
                        "total_pages": total_pages,
                        "file_size_bytes": pdf_path.stat().st_size,
                    }

                return result

        except Exception as e:
            return {"success": False, "error": f"pypdf extraction failed: {str(e)}"}

    def _convert_to_markdown(self, text: str) -> str:
        """Convert extracted text to Markdown format using MarkItDown."""
        try:
            # Try to use the new MarkdownConverter for better formatting
            from .markdown_converter import MarkdownConverter

            converter = MarkdownConverter()

            # Create a simple HTML structure from the text for better conversion
            html_content = f"<html><body><div>{text}</div></body></html>"

            # Use MarkItDown through the converter
            result = converter.html_to_markdown(html_content)

            # Check if the result has proper markdown formatting (headers, structure)
            # If not, fall back to our simple conversion which is better for PDFs
            if not self._has_markdown_structure(result):
                logger.info(
                    "MarkdownConverter didn't add structure, using simple conversion"
                )
                return self._simple_markdown_conversion(text)

            return result

        except Exception as e:
            logger.warning(
                f"Failed to use MarkdownConverter, falling back to simple conversion: {str(e)}"
            )
            # Fallback to the simple conversion method
            return self._simple_markdown_conversion(text)

    def _simple_markdown_conversion(self, text: str) -> str:
        """Simple fallback markdown conversion."""
        # Clean up the text
        lines = text.split("\n")
        cleaned_lines = []

        for line in lines:
            line = line.strip()
            if line:
                # Convert common patterns to Markdown
                if line.isupper() and len(line.split()) <= 5:
                    # Potential heading
                    cleaned_lines.append(f"# {line}")
                elif line.endswith(":") and len(line.split()) <= 8:
                    # Potential subheading
                    cleaned_lines.append(f"## {line}")
                elif self._looks_like_title(line):
                    # Check if it looks like a title (capitalized, short)
                    cleaned_lines.append(f"# {line}")
                else:
                    cleaned_lines.append(line)
            else:
                cleaned_lines.append("")

        return "\n".join(cleaned_lines)

    def _looks_like_title(self, line: str) -> bool:
        """Check if a line looks like a title."""
        # Title heuristics
        words = line.split()
        if len(words) > 8:  # Too long to be a title
            return False

        # Check if most words are capitalized
        capitalized_count = sum(1 for word in words if word and word[0].isupper())

        # If more than half the words are capitalized, it might be a title
        return capitalized_count > len(words) * 0.6

    def _has_markdown_structure(self, text: str) -> bool:
        """Check if text has proper markdown structure (headers, formatting, etc.)."""
        # Check for common markdown structures
        has_headers = bool(re.search(r"^#{1,6}\s+", text, re.MULTILINE))
        has_lists = bool(re.search(r"^[\s]*[-*+]\s+", text, re.MULTILINE))
        has_bold = "**" in text or "__" in text
        has_italic = "*" in text or "_" in text
        has_links = "[" in text and "](" in text
        has_code = "`" in text

        # If it has any meaningful markdown structure, consider it good
        structure_count = sum(
            [has_headers, has_lists, has_bold, has_italic, has_links, has_code]
        )

        # We especially want headers for PDF content
        return has_headers or structure_count >= 2

    def cleanup(self):
        """Clean up temporary files and directories."""
        try:
            import shutil

            if os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
        except Exception as e:
            logger.warning(f"Failed to cleanup temp directory: {str(e)}")
