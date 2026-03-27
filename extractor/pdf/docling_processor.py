"""Docling-based PDF processor with GPU acceleration support.

This module provides a PDF processor that uses Docling for enhanced PDF extraction
with GPU acceleration support for Apple Silicon (MPS), NVIDIA (CUDA), and CPU.

Hardware Acceleration:
    - MPS: Apple Silicon M-series chips (M1/M2/M3/M4)
    - CUDA: NVIDIA GPUs
    - XPU: Intel GPUs
    - CPU: Universal fallback

References:
    - Docling Documentation: https://docling-project.github.io/docling/
    - Docling GitHub: https://github.com/docling-project/docling
    - GPU Support: https://docling-project.github.io/docling/usage/gpu/
"""

import logging
import tempfile
import os
import re
from typing import Dict, List, Any, Optional
from pathlib import Path
from urllib.parse import urlparse
import asyncio
import aiohttp

from ..hardware import (
    DeviceType,
    detect_device,
    get_device_for_docling,
    get_hardware_info,
    is_gpu_acceleration_available,
)

logger = logging.getLogger(__name__)


def _import_docling():
    """Lazy import Docling to avoid startup overhead.

    Returns:
        module: The docling module

    Raises:
        ImportError: If docling is not installed
    """
    try:
        import docling

        return docling
    except ImportError as e:
        raise ImportError(
            f"Docling is required for GPU-accelerated PDF processing. "
            f"Install with: pip install docling. Error: {e}"
        )


def _import_docling_types():
    """Lazy import Docling types.

    Returns:
        tuple: (DocumentConverter, AcceleratorDevice, AcceleratorOptions, PdfFormatOption)
    """
    docling = _import_docling()
    from docling.document_converter import DocumentConverter, PdfFormatOption
    from docling.datamodel.accelerator_options import (
        AcceleratorDevice,
        AcceleratorOptions,
    )
    from docling.datamodel.pipeline_options import PdfPipelineOptions

    return DocumentConverter, AcceleratorDevice, AcceleratorOptions, PdfPipelineOptions, PdfFormatOption


class DoclingPDFProcessor:
    """GPU-accelerated PDF processor using Docling.

    This processor provides enhanced PDF extraction capabilities with:
    - Hardware acceleration (MPS for Apple Silicon, CUDA for NVIDIA, CPU fallback)
    - OCR support for scanned documents
    - Advanced table structure recognition
    - Mathematical formula extraction
    - Image extraction

    The processor automatically detects the best available hardware device
    and configures Docling accordingly.

    Example:
        >>> processor = DoclingPDFProcessor()
        >>> result = await processor.process_pdf(
        ...     "https://example.com/document.pdf",
        ...     method="docling",
        ...     include_metadata=True
        ... )
        >>> print(result["content"])
    """

    def __init__(
        self,
        device: Optional[str] = None,
        num_threads: int = 4,
        enable_ocr: bool = True,
        enable_table_extraction: bool = True,
        enable_formula_extraction: bool = True,
        output_dir: Optional[str] = None,
    ):
        """Initialize the Docling PDF processor.

        Args:
            device: Accelerator device preference ('auto', 'cpu', 'cuda', 'mps', 'xpu')
                   If 'auto' or None, auto-detection is performed.
            num_threads: Number of CPU threads for inference (default: 4)
            enable_ocr: Enable OCR for scanned PDFs (default: True)
            enable_table_extraction: Enable advanced table extraction (default: True)
            enable_formula_extraction: Enable formula extraction (default: True)
            output_dir: Directory to save extracted images and assets
        """
        self.logger = logging.getLogger(__name__)

        # Determine the best device
        self.device = get_device_for_docling(device)
        self.num_threads = num_threads
        self.enable_ocr = enable_ocr
        self.enable_table_extraction = enable_table_extraction
        self.enable_formula_extraction = enable_formula_extraction

        # Setup output directory
        if output_dir:
            self.output_dir = Path(output_dir)
            self.output_dir.mkdir(parents=True, exist_ok=True)
        else:
            self.output_dir = Path(tempfile.mkdtemp(prefix="docling_pdf_"))

        # Log hardware info
        hardware_info = get_hardware_info()
        self.logger.info(
            f"Initialized DoclingPDFProcessor with device={self.device}, "
            f"hardware={hardware_info.device_name or 'Unknown'}"
        )
        if hardware_info.is_gpu:
            self.logger.info(
                f"GPU acceleration enabled: {hardware_info.device_type.value}"
            )

        # Converter instance (lazy initialized)
        self._converter = None
        self.temp_dir = tempfile.mkdtemp(prefix="docling_extractor_")

    @property
    def converter(self):
        """Get or create the DocumentConverter instance (lazy initialization)."""
        if self._converter is None:
            self._converter = self._create_converter()
        return self._converter

    def _create_converter(self):
        """Create and configure a DocumentConverter with hardware acceleration."""
        (
            DocumentConverter,
            AcceleratorDevice,
            AcceleratorOptions,
            PdfPipelineOptions,
            PdfFormatOption,
        ) = _import_docling_types()

        # Configure accelerator options
        accelerator_options = AcceleratorOptions(
            device=AcceleratorDevice(self.device),
            num_threads=self.num_threads,
        )

        # Configure pipeline options
        pipeline_options = PdfPipelineOptions()
        pipeline_options.accelerator_options = accelerator_options

        # Configure OCR if enabled
        if self.enable_ocr:
            try:
                from docling.datamodel.pipeline_options import OcrOptions

                pipeline_options.ocr_options = OcrOptions(force_full_page_ocr=False)
            except ImportError:
                self.logger.warning(
                    "OCR options not available, using default OCR settings"
                )

        # Create converter with options
        converter = DocumentConverter(
            format_options={
                "pdf": PdfFormatOption(pipeline_options=pipeline_options),
            }
        )

        return converter

    async def process_pdf(
        self,
        pdf_source: str,
        method: str = "docling",
        include_metadata: bool = True,
        page_range: Optional[tuple] = None,
        output_format: str = "markdown",
        *,
        extract_images: bool = True,
        extract_tables: bool = True,
        extract_formulas: bool = True,
        embed_images: bool = False,
        enhanced_options: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Process a PDF file using Docling with GPU acceleration.

        Args:
            pdf_source: URL or local file path to PDF
            method: Extraction method (for interface compatibility, always uses docling)
            include_metadata: Include PDF metadata in result (default: True)
            page_range: Tuple of (start_page, end_page) for partial extraction (optional)
            output_format: Output format: markdown, text (default: markdown)
            extract_images: Whether to extract images (default: True)
            extract_tables: Whether to extract tables (default: True)
            extract_formulas: Whether to extract mathematical formulas (default: True)
            embed_images: Whether to embed images as base64 in markdown (default: False)
            enhanced_options: Additional options for enhanced processing (optional)

        Returns:
            Dict containing extracted text/markdown and metadata
        """
        pdf_path = None
        try:
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

            # Process with Docling
            result = await self._process_with_docling(
                pdf_path,
                include_metadata=include_metadata,
                page_range=page_range,
                extract_images=extract_images,
                extract_tables=extract_tables,
                extract_formulas=extract_formulas,
            )

            if not result.get("success"):
                return result

            # Convert to requested format
            content = result.get("text", "")
            if output_format == "markdown":
                content = self._convert_to_markdown(content)

            # Add processing info
            result.update(
                {
                    "source": pdf_source,
                    "method_used": "docling",
                    "output_format": output_format,
                    "content": content,
                    "pages_processed": result.get("pages_processed", 0),
                    "word_count": len(content.split()) if content else 0,
                    "character_count": len(content) if content else 0,
                    "device_used": self.device,
                }
            )

            return result

        except Exception as e:
            self.logger.error(f"Error processing PDF {pdf_source}: {str(e)}")
            return {"success": False, "error": str(e), "source": pdf_source}
        finally:
            # Clean up downloaded files
            if pdf_path and str(pdf_path).startswith(self.temp_dir):
                try:
                    os.unlink(pdf_path)
                except (FileNotFoundError, PermissionError, OSError):
                    pass

    async def _process_with_docling(
        self,
        pdf_path: Path,
        include_metadata: bool = True,
        page_range: Optional[tuple] = None,
        extract_images: bool = True,
        extract_tables: bool = True,
        extract_formulas: bool = True,
    ) -> Dict[str, Any]:
        """Process PDF with Docling.

        Args:
            pdf_path: Path to PDF file
            include_metadata: Whether to include metadata
            page_range: Optional page range tuple
            extract_images: Whether to extract images
            extract_tables: Whether to extract tables
            extract_formulas: Whether to extract formulas

        Returns:
            Dict with extraction results
        """
        try:
            # Run Docling conversion in thread pool (it's synchronous)
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                self._convert_sync,
                pdf_path,
                page_range,
            )

            if result is None:
                return {
                    "success": False,
                    "error": "Docling conversion returned no result",
                }

            # Extract text from Docling result
            doc = result.document
            text_content = doc.export_to_markdown()

            # Get page count
            page_count = len(doc.pages) if hasattr(doc, "pages") else 1

            result_dict = {
                "success": True,
                "text": text_content,
                "pages_processed": page_count,
                "total_pages": page_count,
            }

            # Add metadata if requested
            if include_metadata:
                metadata = {}
                if hasattr(doc, "name"):
                    metadata["title"] = doc.name
                metadata["file_size_bytes"] = pdf_path.stat().st_size
                metadata["processor"] = "docling"
                metadata["device"] = self.device
                result_dict["metadata"] = metadata

            # Extract enhanced assets
            enhanced_assets = {}
            if extract_tables and self.enable_table_extraction:
                tables = self._extract_tables_from_doc(doc)
                if tables:
                    enhanced_assets["tables"] = tables

            if extract_formulas and self.enable_formula_extraction:
                formulas = self._extract_formulas_from_doc(doc)
                if formulas:
                    enhanced_assets["formulas"] = formulas

            if enhanced_assets:
                result_dict["enhanced_assets"] = enhanced_assets

            return result_dict

        except Exception as e:
            self.logger.error(f"Docling processing error: {str(e)}")
            return {"success": False, "error": f"Docling processing failed: {str(e)}"}

    def _convert_sync(self, pdf_path: Path, page_range: Optional[tuple] = None):
        """Synchronous Docling conversion (run in thread pool)."""
        try:
            # For page range, we may need to preprocess the PDF
            # Docling doesn't natively support page ranges in the same way
            # For now, we process the entire document
            # Future: implement page extraction using PyMuPDF before Docling

            convert_result = self.converter.convert(str(pdf_path))
            return convert_result
        except Exception as e:
            self.logger.error(f"Docling convert error: {str(e)}")
            return None

    def _extract_tables_from_doc(self, doc) -> List[Dict[str, Any]]:
        """Extract tables from Docling document.

        Args:
            doc: Docling document object

        Returns:
            List of extracted tables
        """
        tables = []
        try:
            # Docling provides table data in the document structure
            if hasattr(doc, "tables"):
                for i, table in enumerate(doc.tables):
                    table_data = {
                        "id": f"table_{i}",
                        "markdown": getattr(table, "export_to_markdown", lambda: "")(),
                        "page_number": getattr(table, "page", None),
                    }
                    tables.append(table_data)
        except Exception as e:
            self.logger.warning(f"Table extraction error: {str(e)}")

        return tables

    def _extract_formulas_from_doc(self, doc) -> List[Dict[str, Any]]:
        """Extract mathematical formulas from Docling document.

        Args:
            doc: Docling document object

        Returns:
            List of extracted formulas
        """
        formulas = []
        try:
            # Extract formulas from document text using regex patterns
            text = doc.export_to_markdown() if hasattr(doc, "export_to_markdown") else ""

            # Pattern for LaTeX formulas
            patterns = [
                (r"\$\$\s*([^$]+?)\s*\$\$", "block"),
                (r"(?<!\$)\$([^$]+?)\$(?!\$)", "inline"),
            ]

            for pattern, formula_type in patterns:
                matches = re.finditer(pattern, text, re.MULTILINE | re.DOTALL)
                for i, match in enumerate(matches):
                    formula_content = match.group(1).strip()
                    if formula_content and len(formula_content) > 1:
                        formulas.append({
                            "id": f"formula_{len(formulas)}",
                            "latex": formula_content,
                            "formula_type": formula_type,
                        })

        except Exception as e:
            self.logger.warning(f"Formula extraction error: {str(e)}")

        return formulas

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
                        temp_file = tempfile.NamedTemporaryFile(
                            suffix=".pdf", dir=self.temp_dir, delete=False
                        )
                        content = await response.read()
                        temp_file.write(content)
                        temp_file.close()
                        return Path(temp_file.name)
            return None
        except Exception as e:
            self.logger.error(f"Error downloading PDF from {url}: {str(e)}")
            return None

    def _convert_to_markdown(self, text: str) -> str:
        """Convert extracted text to Markdown format.

        Docling's export_to_markdown already provides markdown,
        so this mainly handles any additional formatting.
        """
        # Docling already exports to markdown, so minimal processing needed
        # Just ensure proper paragraph separation
        paragraphs = text.split("\n\n")
        result = []
        for p in paragraphs:
            p = p.strip()
            if p:
                result.append(p)
        return "\n\n".join(result)

    async def batch_process_pdfs(
        self,
        pdf_sources: List[str],
        method: str = "docling",
        include_metadata: bool = True,
        page_range: Optional[tuple] = None,
        output_format: str = "markdown",
        extract_images: bool = True,
        extract_tables: bool = True,
        extract_formulas: bool = True,
        embed_images: bool = False,
        enhanced_options: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Process multiple PDF files concurrently.

        Args:
            pdf_sources: List of URLs or local file paths
            method: Extraction method for all PDFs
            include_metadata: Include metadata for all PDFs
            page_range: Page range for all PDFs (if applicable)
            output_format: Output format for all PDFs
            extract_images: Extract images from all PDFs
            extract_tables: Extract tables from all PDFs
            extract_formulas: Extract formulas from all PDFs
            embed_images: Embed images as base64 instead of saving as files
            enhanced_options: Enhanced processing options for all PDFs

        Returns:
            Dict containing batch processing results and summary
        """
        if not pdf_sources:
            return {"success": False, "error": "PDF sources list cannot be empty"}

        self.logger.info(
            f"Batch processing {len(pdf_sources)} PDFs with Docling on {self.device}"
        )

        # Process PDFs concurrently
        tasks = [
            self.process_pdf(
                pdf_source=source,
                method=method,
                include_metadata=include_metadata,
                page_range=page_range,
                output_format=output_format,
                extract_images=extract_images,
                extract_tables=extract_tables,
                extract_formulas=extract_formulas,
                embed_images=embed_images,
                enhanced_options=enhanced_options,
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
                "method_used": "docling",
                "device_used": self.device,
                "output_format": output_format,
            },
        }

    def cleanup(self):
        """Clean up temporary files and directories."""
        try:
            import shutil

            if os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
        except Exception as e:
            self.logger.warning(f"Failed to cleanup temp directory: {str(e)}")

    def get_hardware_info(self) -> Dict[str, Any]:
        """Get information about the current hardware configuration.

        Returns:
            Dict containing hardware information
        """
        info = get_hardware_info()
        return {
            **info.to_dict(),
            "configured_device": self.device,
            "num_threads": self.num_threads,
        }
