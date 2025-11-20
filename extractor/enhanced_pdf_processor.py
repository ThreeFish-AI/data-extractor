"""Enhanced PDF processing module for extracting images, tables, and mathematical formulas."""

import logging
import tempfile
import os
import re
import base64
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime



@dataclass
class ExtractedImage:
    """Data class for extracted image information."""

    id: str
    filename: str
    local_path: str
    base64_data: Optional[str] = None
    mime_type: str = "image/png"
    width: Optional[int] = None
    height: Optional[int] = None
    page_number: Optional[int] = None
    position: Optional[Dict[str, float]] = None
    caption: Optional[str] = None


@dataclass
class ExtractedTable:
    """Data class for extracted table information."""

    id: str
    markdown: str
    rows: int
    columns: int
    page_number: Optional[int] = None
    position: Optional[Dict[str, float]] = None
    caption: Optional[str] = None
    headers: Optional[List[str]] = None


@dataclass
class ExtractedFormula:
    """Data class for extracted mathematical formula."""

    id: str
    latex: str
    formula_type: str  # "inline" or "block"
    page_number: Optional[int] = None
    position: Optional[Dict[str, float]] = None
    description: Optional[str] = None


class EnhancedPDFProcessor:
    """Enhanced PDF processor with support for images, tables, and mathematical formulas."""

    def __init__(self, output_dir: Optional[str] = None):
        """
        Initialize the enhanced PDF processor.

        Args:
            output_dir: Directory to save extracted images and assets
        """
        self.logger = logging.getLogger(__name__)

        # Create output directory for extracted assets
        if output_dir:
            self.output_dir = Path(output_dir)
            self.output_dir.mkdir(parents=True, exist_ok=True)
        else:
            self.output_dir = Path(tempfile.mkdtemp(prefix="enhanced_pdf_"))

        # Extracted content storage
        self.images: List[ExtractedImage] = []
        self.tables: List[ExtractedTable] = []
        self.formulas: List[ExtractedFormula] = []

        # Processing options
        self.extract_images = True
        self.extract_tables = True
        self.extract_formulas = True

    def _generate_asset_id(self, asset_type: str, page_num: int, index: int) -> str:
        """Generate unique ID for extracted assets."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{asset_type}_{page_num}_{index}_{timestamp}"

    async def extract_images_from_pdf_page(
        self, pdf_document, page_num: int, image_format: str = "png"
    ) -> List[ExtractedImage]:
        """
        Extract images from a PDF page.

        Args:
            pdf_document: PyMuPDF document object
            page_num: Page number (0-indexed)
            image_format: Output image format (png, jpg, etc.)

        Returns:
            List of ExtractedImage objects
        """
        images = []

        try:
            # Import PyMuPDF here to avoid import issues
            import fitz

            page = pdf_document[page_num]
            image_list = page.get_images(full=True)

            for img_index, img_info in enumerate(image_list):
                try:
                    xref = img_info[0]
                    pix = fitz.Pixmap(pdf_document, xref)

                    # Skip CMYK images (not supported by some formats)
                    if pix.n - pix.alpha < 4:
                        # Generate image ID and filename
                        img_id = self._generate_asset_id("img", page_num, img_index)
                        filename = f"{img_id}.{image_format}"
                        local_path = self.output_dir / filename

                        # Save image to local file
                        if image_format.lower() == "png":
                            pix.save(str(local_path))
                        else:
                            # Convert to other formats if needed
                            pix.tobytes(image_format.upper())
                            with open(local_path, "wb") as f:
                                f.write(pix.tobytes(image_format.upper()))

                        # Get image dimensions
                        width, height = pix.width, pix.height

                        # Get base64 data for embedding
                        b64_data = base64.b64encode(
                            pix.tobytes(image_format.upper())
                        ).decode("ascii")

                        # Create ExtractedImage object
                        extracted_image = ExtractedImage(
                            id=img_id,
                            filename=filename,
                            local_path=str(local_path),
                            base64_data=b64_data,
                            mime_type=f"image/{image_format}",
                            width=width,
                            height=height,
                            page_number=page_num,
                            position={
                                "x0": img_info[1] if len(img_info) > 1 else 0,
                                "y0": img_info[2] if len(img_info) > 2 else 0,
                                "x1": img_info[3] if len(img_info) > 3 else width,
                                "y1": img_info[4] if len(img_info) > 4 else height,
                            },
                        )

                        images.append(extracted_image)
                        self.logger.info(
                            f"Extracted image {img_id} from page {page_num}"
                        )

                    pix = None  # Free memory

                except Exception as e:
                    self.logger.warning(
                        f"Failed to extract image {img_index} from page {page_num}: {str(e)}"
                    )
                    continue

        except ImportError:
            self.logger.error("PyMuPDF (fitz) is required for image extraction")
        except Exception as e:
            self.logger.error(f"Error extracting images from page {page_num}: {str(e)}")

        return images

    def extract_tables_from_text(
        self, text: str, page_num: int
    ) -> List[ExtractedTable]:
        """
        Extract tables from plain text using pattern recognition.

        Args:
            text: Text content from PDF page
            page_num: Page number

        Returns:
            List of ExtractedTable objects
        """
        tables = []

        try:
            # Split text into lines
            lines = text.split("\n")

            # Look for table patterns
            i = 0
            while i < len(lines):
                line = lines[i].strip()

                # Check if this looks like a table row (contains multiple separators)
                if self._is_table_row(line):
                    table_start = i
                    table_lines = []

                    # Collect consecutive table rows
                    while i < len(lines) and self._is_table_row(lines[i].strip()):
                        table_lines.append(lines[i].strip())
                        i += 1

                    # Convert to Markdown table
                    if len(table_lines) >= 2:  # At least header and one data row
                        table_id = self._generate_asset_id(
                            "table", page_num, len(tables)
                        )
                        markdown_table = self._convert_to_markdown_table(table_lines)

                        if markdown_table:
                            extracted_table = ExtractedTable(
                                id=table_id,
                                markdown=markdown_table,
                                rows=len(table_lines),
                                columns=len(table_lines[0].split("|")) - 2
                                if "|" in table_lines[0]
                                else len(table_lines[0].split("\t")),
                                page_number=page_num,
                                headers=self._extract_table_headers(table_lines[0])
                                if table_lines
                                else None,
                            )

                            tables.append(extracted_table)
                            self.logger.info(
                                f"Extracted table {table_id} from page {page_num}"
                            )

                i += 1

        except Exception as e:
            self.logger.error(f"Error extracting tables from page {page_num}: {str(e)}")

        return tables

    def extract_formulas_from_text(
        self, text: str, page_num: int
    ) -> List[ExtractedFormula]:
        """
        Extract mathematical formulas from text.

        Args:
            text: Text content from PDF page
            page_num: Page number

        Returns:
            List of ExtractedFormula objects
        """
        formulas = []

        try:
            # Pattern for LaTeX formulas (both inline and block)
            patterns = [
                # Block formulas: \[ ... \] or $$ ... $$
                (r"\\\[\s*([^]]+?)\s*\\\]", "block"),
                (r"\$\$\s*([^$]+?)\s*\$\$", "block"),
                # Inline formulas: \( ... \) or $ ... $
                (r"\\\(\s*([^)]+?)\s*\\\)", "inline"),
                (r"(?<!\$)\$([^$]+?)\$(?!\$)", "inline"),
            ]

            formula_index = 0
            for pattern, formula_type in patterns:
                matches = re.finditer(pattern, text, re.MULTILINE | re.DOTALL)

                for match in matches:
                    formula_content = match.group(1).strip()

                    if (
                        formula_content and len(formula_content) > 1
                    ):  # Filter out empty matches
                        formula_id = self._generate_asset_id(
                            "formula", page_num, formula_index
                        )

                        extracted_formula = ExtractedFormula(
                            id=formula_id,
                            latex=formula_content,
                            formula_type=formula_type,
                            page_number=page_num,
                            position={
                                "start": match.start(),
                                "end": match.end(),
                            },
                        )

                        formulas.append(extracted_formula)
                        formula_index += 1

                        self.logger.info(
                            f"Extracted {formula_type} formula {formula_id} from page {page_num}"
                        )

        except Exception as e:
            self.logger.error(
                f"Error extracting formulas from page {page_num}: {str(e)}"
            )

        return formulas

    def _is_table_row(self, line: str) -> bool:
        """Check if a line looks like a table row."""
        # Remove extra spaces and check for patterns
        cleaned = re.sub(r"\s+", " ", line.strip())

        # Check for tab-separated or pipe-separated values
        tab_count = cleaned.count("\t")
        pipe_count = cleaned.count("|")

        # Multiple separators suggest a table row
        return tab_count >= 2 or (
            pipe_count >= 2 and cleaned.startswith("|") and cleaned.endswith("|")
        )

    def _convert_to_markdown_table(self, table_lines: List[str]) -> str:
        """Convert table lines to Markdown format."""
        if not table_lines:
            return ""

        try:
            # Determine separator type
            first_line = table_lines[0]

            if "|" in first_line:
                # Pipe-separated table
                rows = []
                for line in table_lines:
                    # Clean up pipe separators
                    cleaned = (
                        "| "
                        + " | ".join(
                            [cell.strip() for cell in line.split("|") if cell.strip()]
                        )
                        + " |"
                    )
                    rows.append(cleaned)

                # Add header separator after first row
                if len(rows) >= 2:
                    header_cols = len(rows[0].split("|")) - 2
                    separator = "| " + " | ".join(["---"] * header_cols) + " |"
                    rows.insert(1, separator)

                return "\n".join(rows)

            elif "\t" in first_line:
                # Tab-separated table - convert to pipe
                rows = []
                for line in table_lines:
                    cells = [cell.strip() for cell in line.split("\t")]
                    markdown_row = "| " + " | ".join(cells) + " |"
                    rows.append(markdown_row)

                # Add header separator
                if len(rows) >= 2:
                    header_cols = len(rows[0].split("|")) - 2
                    separator = "| " + " | ".join(["---"] * header_cols) + " |"
                    rows.insert(1, separator)

                return "\n".join(rows)
            else:
                # Space-separated table
                rows = []
                for line in table_lines:
                    # Split by multiple spaces
                    cells = re.split(r"\s{2,}", line.strip())
                    if len(cells) > 1:
                        markdown_row = "| " + " | ".join(cells) + " |"
                        rows.append(markdown_row)

                # Add header separator
                if len(rows) >= 2:
                    header_cols = len(rows[0].split("|")) - 2
                    separator = "| " + " | ".join(["---"] * header_cols) + " |"
                    rows.insert(1, separator)

                return "\n".join(rows)

        except Exception as e:
            self.logger.error(f"Error converting table to Markdown: {str(e)}")
            return ""

    def _extract_table_headers(self, header_line: str) -> List[str]:
        """Extract headers from table header line."""
        try:
            if "|" in header_line:
                return [cell.strip() for cell in header_line.split("|") if cell.strip()]
            elif "\t" in header_line:
                return [cell.strip() for cell in header_line.split("\t")]
            else:
                return re.split(r"\s{2,}", header_line.strip())
        except:
            return []

    def enhance_markdown_with_assets(
        self,
        original_markdown: str,
        embed_images: bool = False,
        image_size: Optional[Tuple[int, int]] = None,
    ) -> str:
        """
        Enhance Markdown content with extracted images, tables, and formulas.

        Args:
            original_markdown: Original Markdown content
            embed_images: Whether to embed images as base64
            image_size: Optional resize dimensions (width, height)

        Returns:
            Enhanced Markdown content
        """
        enhanced_content = original_markdown

        try:
            # Add images section if any images were extracted
            if self.images:
                enhanced_content += "\n\n## Extracted Images\n\n"

                for img in self.images:
                    if embed_images and img.base64_data:
                        # Embed as base64 data URI
                        enhanced_content += f"![{img.caption or img.filename}](data:{img.mime_type};base64,{img.base64_data})\n\n"
                    else:
                        # Reference local file
                        enhanced_content += (
                            f"![{img.caption or img.filename}]({img.filename})\n\n"
                        )

                    # Add image metadata
                    if img.width and img.height:
                        enhanced_content += (
                            f"*Dimensions: {img.width}×{img.height}px*\n"
                        )
                    if img.page_number is not None:
                        enhanced_content += f"*Source: Page {img.page_number + 1}*\n"
                    enhanced_content += "\n"

            # Add tables section if any tables were extracted
            if self.tables:
                enhanced_content += "\n## Extracted Tables\n\n"

                for table in self.tables:
                    if table.caption:
                        enhanced_content += f"**{table.caption}**\n\n"

                    enhanced_content += table.markdown + "\n\n"

                    # Add table metadata
                    enhanced_content += (
                        f"*Table: {table.rows} rows × {table.columns} columns*\n"
                    )
                    if table.page_number is not None:
                        enhanced_content += f"*Source: Page {table.page_number + 1}*\n"
                    enhanced_content += "\n"

            # Add formulas section if any formulas were extracted
            if self.formulas:
                enhanced_content += "\n## Mathematical Formulas\n\n"

                for formula in self.formulas:
                    if formula.formula_type == "block":
                        enhanced_content += f"\n$$\n{formula.latex}\n$$\n\n"
                    else:
                        enhanced_content += f"${formula.latex}$\n\n"

                    # Add formula metadata
                    if formula.description:
                        enhanced_content += f"*{formula.description}*\n"
                    if formula.page_number is not None:
                        enhanced_content += (
                            f"*Source: Page {formula.page_number + 1}*\n"
                        )
                    enhanced_content += "\n"

        except Exception as e:
            self.logger.error(f"Error enhancing Markdown with assets: {str(e)}")

        return enhanced_content

    def get_extraction_summary(self) -> Dict[str, Any]:
        """Get a summary of all extracted content."""
        return {
            "images": {
                "count": len(self.images),
                "files": [img.filename for img in self.images],
                "total_size_mb": sum(
                    os.path.getsize(img.local_path)
                    for img in self.images
                    if os.path.exists(img.local_path)
                )
                / (1024 * 1024),
            },
            "tables": {
                "count": len(self.tables),
                "total_rows": sum(table.rows for table in self.tables),
                "total_columns": sum(table.columns for table in self.tables),
            },
            "formulas": {
                "count": len(self.formulas),
                "inline_count": len(
                    [f for f in self.formulas if f.formula_type == "inline"]
                ),
                "block_count": len(
                    [f for f in self.formulas if f.formula_type == "block"]
                ),
            },
            "output_directory": str(self.output_dir),
        }

    def cleanup(self):
        """Clean up temporary files and reset processor state."""
        try:
            # Clear extracted content
            self.images.clear()
            self.tables.clear()
            self.formulas.clear()

            # Note: Don't delete output directory here as it might contain
            # files that the user wants to keep

        except Exception as e:
            self.logger.error(f"Error during cleanup: {str(e)}")
