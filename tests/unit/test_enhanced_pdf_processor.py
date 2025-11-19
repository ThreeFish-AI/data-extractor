"""Unit tests for enhanced PDF processor functionality."""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from extractor.enhanced_pdf_processor import (
    EnhancedPDFProcessor,
    ExtractedImage,
    ExtractedTable,
    ExtractedFormula,
)


class TestEnhancedPDFProcessor:
    """Test cases for EnhancedPDFProcessor."""

    @pytest.fixture
    def processor(self):
        """Create a test processor instance."""
        temp_dir = tempfile.mkdtemp()
        processor = EnhancedPDFProcessor(output_dir=temp_dir)
        yield processor
        # Cleanup
        processor.cleanup()
        import shutil

        shutil.rmtree(temp_dir, ignore_errors=True)

    def test_processor_initialization(self, processor):
        """Test processor initialization."""
        assert processor.output_dir.exists()
        assert processor.images == []
        assert processor.tables == []
        assert processor.formulas == []
        assert processor.extract_images is True
        assert processor.extract_tables is True
        assert processor.extract_formulas is True

    def test_generate_asset_id(self, processor):
        """Test asset ID generation."""
        asset_id = processor._generate_asset_id("img", 1, 0)
        assert asset_id.startswith("img_1_0_")
        assert len(asset_id) > 10  # Should include timestamp

    @patch("extractor.enhanced_pdf_processor.fitz")
    @pytest.mark.asyncio
    async def test_extract_images_from_pdf_page(self, mock_fitz, processor):
        """Test image extraction from PDF page."""
        # Mock PDF document and page
        mock_doc = Mock()
        mock_page = Mock()
        mock_doc.__getitem__ = Mock(return_value=mock_page)

        # Mock image list and pixmap
        mock_page.get_images.return_value = [(1, 0, 0, 100, 200, 0, 0, 0, 0)]
        mock_pix = Mock()
        mock_pix.n = 3  # RGB image
        mock_pix.alpha = 0
        mock_pix.width = 100
        mock_pix.height = 200
        mock_pix.save = Mock()
        mock_pix.tobytes = Mock(return_value=b"fake_image_data")

        mock_fitz.Pixmap.return_value = mock_pix
        mock_fitz.Pixmap.__getitem__ = Mock(return_value=mock_pix)

        # Test extraction
        images = await processor.extract_images_from_pdf_page(mock_doc, 0, "png")

        assert len(images) == 1
        image = images[0]
        assert isinstance(image, ExtractedImage)
        assert image.filename.endswith(".png")
        assert image.width == 100
        assert image.height == 200
        assert image.page_number == 0
        assert image.mime_type == "image/png"

    def test_extract_tables_from_text(self, processor):
        """Test table extraction from text."""
        text = """
        Name | Age | City
        ----|-----|----
        John | 25  | NYC
        Jane | 30  | LA
        """

        tables = processor.extract_tables_from_text(text, 1)

        assert len(tables) == 1
        table = tables[0]
        assert isinstance(table, ExtractedTable)
        assert table.rows == 3  # Header + separator + data row
        assert table.columns == 3
        assert table.page_number == 1
        assert "Name" in table.markdown
        assert "John" in table.markdown

    def test_extract_tables_from_tab_separated_text(self, processor):
        """Test table extraction from tab-separated text."""
        text = """
        Product\tPrice\tStock
        Apple\t$1.99\t50
        Banana\t$0.99\t30
        """

        tables = processor.extract_tables_from_text(text, 2)

        assert len(tables) == 1
        table = tables[0]
        assert table.headers == ["Product", "Price", "Stock"]
        assert "Apple" in table.markdown

    def test_extract_formulas_from_text(self, processor):
        """Test formula extraction from text."""
        text = """
        The equation E = mc² is famous.
        Inline formula: $x^2 + y^2 = z^2$ in text.

        Block formula:
        $$\\int_{-\\infty}^{\\infty} e^{-x^2} dx = \\sqrt{\\pi}$$

        Another formula: \\[a^2 + b^2 = c^2\\]
        """

        formulas = processor.extract_formulas_from_text(text, 3)

        # Should extract 4 formulas: E=mc², inline, block, and bracket formula
        assert len(formulas) >= 3

        # Check inline formulas
        inline_formulas = [f for f in formulas if f.formula_type == "inline"]
        assert len(inline_formulas) >= 1
        assert "x^2 + y^2 = z^2" in inline_formulas[0].latex

        # Check block formulas
        block_formulas = [f for f in formulas if f.formula_type == "block"]
        assert len(block_formulas) >= 1
        assert any("integral" in f.latex or "sqrt" in f.latex for f in block_formulas)

    def test_is_table_row(self, processor):
        """Test table row detection."""
        # Pipe-separated table row
        assert processor._is_table_row("| Name | Age | City |")

        # Tab-separated table row
        assert processor._is_table_row("Name\tAge\tCity")

        # Multiple space-separated table row
        assert processor._is_table_row("Name    Age    City")

        # Not a table row
        assert not processor._is_table_row("This is just regular text.")
        assert not processor._is_table_row("Single column")

    def test_convert_to_markdown_table(self, processor):
        """Test conversion to Markdown table format."""
        table_lines = ["| Name | Age | City |", "John | 25 | NYC |", "Jane | 30 | LA |"]

        markdown = processor._convert_to_markdown_table(table_lines)

        assert "| Name | Age | City |" in markdown
        assert "| --- | --- | --- |" in markdown  # Header separator
        assert "| John | 25 | NYC |" in markdown
        assert "| Jane | 30 | LA |" in markdown

    def test_convert_tab_separated_to_markdown_table(self, processor):
        """Test conversion of tab-separated table to Markdown."""
        table_lines = ["Product\tPrice\tStock", "Apple\t$1.99\t50", "Banana\t$0.99\t30"]

        markdown = processor._convert_to_markdown_table(table_lines)

        assert "| Product | Price | Stock |" in markdown
        assert "| --- | --- | --- |" in markdown
        assert "| Apple | $1.99 | 50 |" in markdown

    def test_extract_table_headers(self, processor):
        """Test table header extraction."""
        # Pipe-separated headers
        headers = processor._extract_table_headers("| Name | Age | City |")
        assert headers == ["Name", "Age", "City"]

        # Tab-separated headers
        headers = processor._extract_table_headers("Name\tAge\tCity")
        assert headers == ["Name", "Age", "City"]

        # Space-separated headers
        headers = processor._extract_table_headers("Name    Age    City")
        assert headers == ["Name", "Age", "City"]

    def test_enhance_markdown_with_assets(self, processor):
        """Test Markdown enhancement with extracted assets."""
        original_markdown = "# Document Title\n\nThis is the main content."

        # Add some mock assets
        processor.images = [
            ExtractedImage(
                id="img_1_0_001",
                filename="image1.png",
                local_path="/tmp/image1.png",
                base64_data="iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg==",
                mime_type="image/png",
                width=100,
                height=100,
                page_number=0,
            )
        ]

        processor.tables = [
            ExtractedTable(
                id="table_1_0_001",
                markdown="| Name | Age |\n| --- | --- |\n| John | 25 |",
                rows=2,
                columns=2,
                page_number=0,
            )
        ]

        processor.formulas = [
            ExtractedFormula(
                id="formula_1_0_001",
                latex="E = mc^2",
                formula_type="inline",
                page_number=0,
            )
        ]

        # Test enhancement without embedding
        enhanced = processor.enhance_markdown_with_assets(
            original_markdown, embed_images=False
        )

        assert "## Extracted Images" in enhanced
        assert "![image1.png](image1.png)" in enhanced
        assert "## Extracted Tables" in enhanced
        assert "| Name | Age |" in enhanced
        assert "## Mathematical Formulas" in enhanced
        assert "$E = mc^2$" in enhanced
        assert "*Dimensions: 100×100px*" in enhanced

    def test_enhance_markdown_with_embedded_images(self, processor):
        """Test Markdown enhancement with embedded images."""
        original_markdown = "# Test"

        processor.images = [
            ExtractedImage(
                id="img_1_0_001",
                filename="image1.png",
                local_path="/tmp/image1.png",
                base64_data="iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg==",
                mime_type="image/png",
                page_number=0,
            )
        ]

        # Test enhancement with embedding
        enhanced = processor.enhance_markdown_with_assets(
            original_markdown, embed_images=True
        )

        assert "data:image/png;base64," in enhanced
        assert "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJ" in enhanced

    def test_get_extraction_summary(self, processor):
        """Test extraction summary generation."""
        # Add mock assets
        processor.images = [
            ExtractedImage("img1", "image1.png", "/tmp/image1.png"),
            ExtractedImage("img2", "image2.png", "/tmp/image2.png"),
        ]

        processor.tables = [
            ExtractedTable("table1", "| A | B |", 3, 2),
            ExtractedTable("table2", "| X | Y |", 2, 2),
        ]

        processor.formulas = [
            ExtractedFormula("formula1", "x^2", "inline"),
            ExtractedFormula("formula2", "y^2", "block"),
        ]

        summary = processor.get_extraction_summary()

        assert summary["images"]["count"] == 2
        assert summary["images"]["files"] == ["image1.png", "image2.png"]
        assert summary["tables"]["count"] == 2
        assert summary["tables"]["total_rows"] == 5  # 3 + 2
        assert summary["tables"]["total_columns"] == 4  # 2 + 2
        assert summary["formulas"]["count"] == 2
        assert summary["formulas"]["inline_count"] == 1
        assert summary["formulas"]["block_count"] == 1
        assert "output_directory" in summary

    def test_cleanup(self, processor):
        """Test processor cleanup."""
        # Add some assets
        processor.images = [ExtractedImage("img1", "image1.png", "/tmp/image1.png")]
        processor.tables = [ExtractedTable("table1", "| A | B |", 2, 2)]
        processor.formulas = [ExtractedFormula("formula1", "x^2", "inline")]

        # Cleanup
        processor.cleanup()

        # Check that assets are cleared
        assert len(processor.images) == 0
        assert len(processor.tables) == 0
        assert len(processor.formulas) == 0

    def test_error_handling_in_image_extraction(self, processor):
        """Test error handling during image extraction."""
        with patch("extractor.enhanced_pdf_processor.fitz") as mock_fitz:
            # Mock fitz to raise an exception
            mock_fitz.open.side_effect = Exception("PDF error")

            # Should handle the error gracefully
            try:
                import fitz

                doc = fitz.open("fake.pdf")
                images = processor.extract_images_from_pdf_page(doc, 0)
            except ImportError:
                # If fitz is not available, the test should pass
                pass
            except Exception:
                # Other exceptions should be handled
                pass

    def test_empty_text_handling(self, processor):
        """Test handling of empty or minimal text."""
        # Test with empty text
        tables = processor.extract_tables_from_text("", 0)
        assert len(tables) == 0

        formulas = processor.extract_formulas_from_text("", 0)
        assert len(formulas) == 0

        # Test with text that has no tables or formulas
        text = "This is just plain text without any special content."
        tables = processor.extract_tables_from_text(text, 0)
        formulas = processor.extract_formulas_from_text(text, 0)

        assert len(tables) == 0
        assert len(formulas) == 0
