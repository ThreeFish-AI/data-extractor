"""
单元测试：PDF处理模块
测试 extractor.pdf_processor 模块的PDF文档处理和转换功能
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from pathlib import Path
import tempfile
import os

from extractor.pdf_processor import PDFProcessor


class TestPDFProcessor:
    """测试PDF处理器主要功能"""

    def setup_method(self):
        """测试前准备"""
        self.processor = PDFProcessor()

    def teardown_method(self):
        """测试后清理"""
        self.processor.cleanup()

    def test_processor_initialization(self):
        """测试处理器初始化"""
        assert self.processor is not None
        assert hasattr(self.processor, "process_pdf")
        assert hasattr(self.processor, "batch_process_pdfs")
        assert self.processor.supported_methods == ["pymupdf", "pypdf", "auto"]
        assert os.path.exists(self.processor.temp_dir)

    def test_supported_methods(self):
        """测试支持的方法列表"""
        expected_methods = ["pymupdf", "pypdf", "auto"]
        assert self.processor.supported_methods == expected_methods

    def test_url_detection(self):
        """测试URL检测功能"""
        # 有效的URL
        assert self.processor._is_url("https://example.com/document.pdf") is True
        assert self.processor._is_url("http://example.com/document.pdf") is True

        # 无效的URL
        assert self.processor._is_url("/local/path/document.pdf") is False
        assert self.processor._is_url("document.pdf") is False
        assert self.processor._is_url("ftp://example.com/document.pdf") is False
        assert self.processor._is_url("") is False

    @pytest.mark.asyncio
    async def test_invalid_method_validation(self):
        """测试无效方法验证"""
        result = await self.processor.process_pdf("test.pdf", method="invalid_method")

        assert result["success"] is False
        assert "Method must be one of" in result["error"]
        assert result["source"] == "test.pdf"

    @pytest.mark.asyncio
    async def test_nonexistent_file_handling(self):
        """测试不存在文件的处理"""
        result = await self.processor.process_pdf("nonexistent.pdf")

        assert result["success"] is False
        assert result["error"] == "PDF file does not exist"
        assert result["source"] == "nonexistent.pdf"

    @pytest.mark.asyncio
    @patch("aiohttp.ClientSession.get")
    async def test_pdf_download_success(self, mock_get):
        """测试PDF下载成功"""
        # 模拟成功的HTTP响应
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.read = AsyncMock(return_value=b"fake PDF content")
        mock_get.return_value.__aenter__.return_value = mock_response

        result_path = await self.processor._download_pdf("https://example.com/test.pdf")

        assert result_path is not None
        assert isinstance(result_path, Path)
        assert result_path.suffix == ".pdf"
        assert str(result_path).startswith(self.processor.temp_dir)

    @pytest.mark.asyncio
    @patch("aiohttp.ClientSession.get")
    async def test_pdf_download_failure(self, mock_get):
        """测试PDF下载失败"""
        # 模拟HTTP错误响应
        mock_response = AsyncMock()
        mock_response.status = 404
        mock_get.return_value.__aenter__.return_value = mock_response

        result_path = await self.processor._download_pdf(
            "https://example.com/nonexistent.pdf"
        )

        assert result_path is None

    @pytest.mark.asyncio
    @patch("aiohttp.ClientSession.get")
    async def test_pdf_download_network_error(self, mock_get):
        """测试PDF下载网络错误"""
        # 模拟网络异常
        mock_get.side_effect = Exception("Network error")

        result_path = await self.processor._download_pdf("https://example.com/test.pdf")

        assert result_path is None


class TestPyMuPDFExtraction:
    """测试PyMuPDF提取功能"""

    def setup_method(self):
        """测试前准备"""
        self.processor = PDFProcessor()

    def teardown_method(self):
        """测试后清理"""
        self.processor.cleanup()

    @pytest.mark.asyncio
    @patch("extractor.pdf_processor._import_fitz")
    async def test_pymupdf_extraction_success(self, mock_import_fitz):
        """测试PyMuPDF提取成功"""
        # 模拟fitz模块
        mock_fitz = Mock()
        mock_import_fitz.return_value = mock_fitz

        # 模拟PDF文档
        mock_doc = Mock()
        mock_doc.page_count = 2
        mock_doc.metadata = {
            "title": "Test Document",
            "author": "Test Author",
            "creationDate": "2023-01-01",
        }
        mock_fitz.open.return_value = mock_doc

        # 模拟页面
        mock_page1 = Mock()
        mock_page1.get_text.return_value = "Page 1 content"
        mock_page2 = Mock()
        mock_page2.get_text.return_value = "Page 2 content"
        mock_doc.load_page.side_effect = [mock_page1, mock_page2]

        # 创建临时PDF文件
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_file:
            tmp_path = Path(tmp_file.name)

        try:
            result = await self.processor._extract_with_pymupdf(
                tmp_path, include_metadata=True
            )

            assert result["success"] is True
            assert "Page 1 content" in result["text"]
            assert "Page 2 content" in result["text"]
            assert result["pages_processed"] == 2
            assert result["total_pages"] == 2
            assert result["metadata"]["title"] == "Test Document"
            assert result["metadata"]["author"] == "Test Author"

            mock_doc.close.assert_called_once()

        finally:
            # 清理临时文件
            if tmp_path.exists():
                tmp_path.unlink()

    @pytest.mark.asyncio
    @patch("extractor.pdf_processor._import_fitz")
    async def test_pymupdf_with_page_range(self, mock_import_fitz):
        """测试PyMuPDF页面范围提取"""
        # 模拟fitz模块
        mock_fitz = Mock()
        mock_import_fitz.return_value = mock_fitz

        # 模拟PDF文档
        mock_doc = Mock()
        mock_doc.page_count = 5
        mock_doc.metadata = {}
        mock_fitz.open.return_value = mock_doc

        # 模拟页面
        mock_pages = []
        for i in range(5):
            mock_page = Mock()
            mock_page.get_text.return_value = f"Page {i + 1} content"
            mock_pages.append(mock_page)
        mock_doc.load_page.side_effect = mock_pages

        # 创建临时PDF文件
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_file:
            tmp_path = Path(tmp_file.name)

        try:
            result = await self.processor._extract_with_pymupdf(
                tmp_path, page_range=(1, 3), include_metadata=False
            )

            assert result["success"] is True
            assert "Page 2 content" in result["text"]
            assert "Page 3 content" in result["text"]
            assert "Page 1 content" not in result["text"]
            assert "Page 4 content" not in result["text"]
            assert result["pages_processed"] == 2  # pages 1-2 (0-indexed)
            assert "metadata" not in result

        finally:
            if tmp_path.exists():
                tmp_path.unlink()

    @pytest.mark.asyncio
    @patch("extractor.pdf_processor._import_fitz")
    async def test_pymupdf_extraction_error(self, mock_import_fitz):
        """测试PyMuPDF提取错误"""
        # 模拟导入错误
        mock_import_fitz.side_effect = ImportError("PyMuPDF not available")

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_file:
            tmp_path = Path(tmp_file.name)

        try:
            result = await self.processor._extract_with_pymupdf(tmp_path)

            assert result["success"] is False
            assert "PyMuPDF extraction failed" in result["error"]

        finally:
            if tmp_path.exists():
                tmp_path.unlink()


class TestPyPDFExtraction:
    """测试pypdf提取功能"""

    def setup_method(self):
        """测试前准备"""
        self.processor = PDFProcessor()

    def teardown_method(self):
        """测试后清理"""
        self.processor.cleanup()

    @pytest.mark.asyncio
    @patch("extractor.pdf_processor._import_pypdf")
    @patch("builtins.open", create=True)
    async def test_pypdf_extraction_success(self, mock_open, mock_import_pypdf):
        """测试pypdf提取成功"""
        # 模拟pypdf模块
        mock_pypdf = Mock()
        mock_import_pypdf.return_value = mock_pypdf

        # 模拟PDF阅读器
        mock_reader = Mock()
        mock_reader.pages = [Mock(), Mock()]  # 2页
        mock_reader.metadata = {
            "/Title": "Test Document",
            "/Author": "Test Author",
            "/CreationDate": "D:20230101000000Z",
        }
        mock_pypdf.PdfReader.return_value = mock_reader

        # 模拟页面
        mock_reader.pages[0].extract_text.return_value = "Page 1 content"
        mock_reader.pages[1].extract_text.return_value = "Page 2 content"

        # 模拟文件操作
        mock_file = Mock()
        mock_open.return_value.__enter__.return_value = mock_file

        # 创建临时PDF文件
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_file:
            tmp_path = Path(tmp_file.name)

        try:
            result = await self.processor._extract_with_pypdf(
                tmp_path, include_metadata=True
            )

            assert result["success"] is True
            assert "Page 1 content" in result["text"]
            assert "Page 2 content" in result["text"]
            assert result["pages_processed"] == 2
            assert result["total_pages"] == 2
            assert result["metadata"]["title"] == "Test Document"
            assert result["metadata"]["author"] == "Test Author"

        finally:
            if tmp_path.exists():
                tmp_path.unlink()

    @pytest.mark.asyncio
    @patch("extractor.pdf_processor._import_pypdf")
    @patch("builtins.open", create=True)
    async def test_pypdf_with_page_range(self, mock_open, mock_import_pypdf):
        """测试pypdf页面范围提取"""
        # 模拟pypdf模块
        mock_pypdf = Mock()
        mock_import_pypdf.return_value = mock_pypdf

        # 模拟PDF阅读器（5页）
        mock_reader = Mock()
        mock_reader.pages = [Mock() for _ in range(5)]
        mock_reader.metadata = None
        mock_pypdf.PdfReader.return_value = mock_reader

        # 模拟页面内容
        for i, page in enumerate(mock_reader.pages):
            page.extract_text.return_value = f"Page {i + 1} content"

        # 模拟文件操作
        mock_file = Mock()
        mock_open.return_value.__enter__.return_value = mock_file

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_file:
            tmp_path = Path(tmp_file.name)

        try:
            result = await self.processor._extract_with_pypdf(
                tmp_path, page_range=(2, 4), include_metadata=False
            )

            assert result["success"] is True
            assert "Page 3 content" in result["text"]
            assert "Page 4 content" in result["text"]
            assert "Page 1 content" not in result["text"]
            assert "Page 5 content" not in result["text"]
            assert result["pages_processed"] == 2
            assert "metadata" not in result

        finally:
            if tmp_path.exists():
                tmp_path.unlink()

    @pytest.mark.asyncio
    @patch("extractor.pdf_processor._import_pypdf")
    async def test_pypdf_extraction_error(self, mock_import_pypdf):
        """测试pypdf提取错误"""
        mock_import_pypdf.side_effect = ImportError("pypdf not available")

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_file:
            tmp_path = Path(tmp_file.name)

        try:
            result = await self.processor._extract_with_pypdf(tmp_path)

            assert result["success"] is False
            assert "pypdf extraction failed" in result["error"]

        finally:
            if tmp_path.exists():
                tmp_path.unlink()


class TestAutoExtraction:
    """测试自动提取功能"""

    def setup_method(self):
        """测试前准备"""
        self.processor = PDFProcessor()

    def teardown_method(self):
        """测试后清理"""
        self.processor.cleanup()

    @pytest.mark.asyncio
    async def test_auto_extraction_pymupdf_success(self):
        """测试自动提取PyMuPDF成功"""
        with patch.object(self.processor, "_extract_with_pymupdf") as mock_pymupdf:
            mock_pymupdf.return_value = {
                "success": True,
                "text": "Extracted text",
                "pages_processed": 1,
            }

            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_file:
                tmp_path = Path(tmp_file.name)

            try:
                result = await self.processor._auto_extract(tmp_path)

                assert result["success"] is True
                assert result["method_used"] == "pymupdf"
                assert result["text"] == "Extracted text"
                mock_pymupdf.assert_called_once()

            finally:
                if tmp_path.exists():
                    tmp_path.unlink()

    @pytest.mark.asyncio
    async def test_auto_extraction_fallback_to_pypdf(self):
        """测试自动提取回退到pypdf"""
        with (
            patch.object(self.processor, "_extract_with_pymupdf") as mock_pymupdf,
            patch.object(self.processor, "_extract_with_pypdf") as mock_pypdf,
        ):
            # PyMuPDF失败
            mock_pymupdf.side_effect = Exception("PyMuPDF failed")

            # pypdf成功
            mock_pypdf.return_value = {
                "success": True,
                "text": "Extracted with pypdf",
                "pages_processed": 1,
            }

            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_file:
                tmp_path = Path(tmp_file.name)

            try:
                result = await self.processor._auto_extract(tmp_path)

                assert result["success"] is True
                assert result["method_used"] == "pypdf"
                assert result["text"] == "Extracted with pypdf"
                mock_pymupdf.assert_called_once()
                mock_pypdf.assert_called_once()

            finally:
                if tmp_path.exists():
                    tmp_path.unlink()

    @pytest.mark.asyncio
    async def test_auto_extraction_both_methods_fail(self):
        """测试自动提取两种方法都失败"""
        with (
            patch.object(self.processor, "_extract_with_pymupdf") as mock_pymupdf,
            patch.object(self.processor, "_extract_with_pypdf") as mock_pypdf,
        ):
            # 两种方法都失败
            mock_pymupdf.side_effect = Exception("PyMuPDF failed")
            mock_pypdf.side_effect = Exception("pypdf failed")

            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_file:
                tmp_path = Path(tmp_file.name)

            try:
                result = await self.processor._auto_extract(tmp_path)

                assert result["success"] is False
                assert (
                    "Both PyMuPDF and pypdf extraction methods failed"
                    in result["error"]
                )

            finally:
                if tmp_path.exists():
                    tmp_path.unlink()


class TestMarkdownConversion:
    """测试Markdown转换功能"""

    def setup_method(self):
        """测试前准备"""
        self.processor = PDFProcessor()

    def teardown_method(self):
        """测试后清理"""
        self.processor.cleanup()

    def test_basic_markdown_conversion(self):
        """测试基本Markdown转换"""
        text = "INTRODUCTION\n\nThis is a paragraph.\n\nSection Title:\n\nAnother paragraph."

        result = self.processor._convert_to_markdown(text)

        assert "# INTRODUCTION" in result
        assert "## Section Title:" in result
        assert "This is a paragraph." in result
        assert "Another paragraph." in result

    def test_heading_detection(self):
        """测试标题检测"""
        text = "MAIN TITLE\n\nSubsection Header:\n\nNormal text here."

        result = self.processor._convert_to_markdown(text)

        assert "# MAIN TITLE" in result
        assert "## Subsection Header:" in result
        assert "Normal text here." in result

    def test_empty_lines_handling(self):
        """测试空行处理"""
        text = "Line 1\n\n\nLine 2\n\n\n\nLine 3"

        result = self.processor._convert_to_markdown(text)
        lines = result.split("\n")

        assert "Line 1" in result
        assert "Line 2" in result
        assert "Line 3" in result

    def test_long_heading_not_converted(self):
        """测试长标题不被转换"""
        text = "THIS IS A VERY LONG TITLE THAT SHOULD NOT BE CONVERTED TO HEADING"

        result = self.processor._convert_to_markdown(text)

        # 由于标题太长（超过5个词），不应该转换为Markdown标题
        assert result.strip() == text


class TestPDFProcessing:
    """测试PDF完整处理流程"""

    def setup_method(self):
        """测试前准备"""
        self.processor = PDFProcessor()

    def teardown_method(self):
        """测试后清理"""
        self.processor.cleanup()

    @pytest.mark.asyncio
    async def test_process_pdf_with_text_output(self):
        """测试PDF处理文本输出"""
        with patch.object(self.processor, "_extract_with_pymupdf") as mock_extract:
            mock_extract.return_value = {
                "success": True,
                "text": "Extracted PDF text",
                "pages_processed": 1,
                "total_pages": 1,
                "metadata": {"title": "Test PDF"},
            }

            # 创建临时PDF文件
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_file:
                tmp_file.write(b"fake PDF content")
                tmp_path = tmp_file.name

            try:
                result = await self.processor.process_pdf(
                    tmp_path, method="pymupdf", output_format="text"
                )

                assert result["success"] is True
                assert result["text"] == "Extracted PDF text"
                assert result["output_format"] == "text"
                assert result["method_used"] == "pymupdf"
                assert result["pages_processed"] == 1
                assert result["word_count"] == 3  # "Extracted PDF text"
                assert "markdown" not in result

            finally:
                os.unlink(tmp_path)

    @pytest.mark.asyncio
    async def test_process_pdf_with_markdown_output(self):
        """测试PDF处理Markdown输出"""
        with patch.object(self.processor, "_extract_with_pymupdf") as mock_extract:
            mock_extract.return_value = {
                "success": True,
                "text": "TITLE\n\nContent paragraph.",
                "pages_processed": 1,
                "total_pages": 1,
            }

            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_file:
                tmp_file.write(b"fake PDF content")
                tmp_path = tmp_file.name

            try:
                result = await self.processor.process_pdf(
                    tmp_path, method="pymupdf", output_format="markdown"
                )

                assert result["success"] is True
                assert "markdown" in result
                assert "# TITLE" in result["markdown"]
                assert "Content paragraph." in result["markdown"]
                assert result["output_format"] == "markdown"

            finally:
                os.unlink(tmp_path)

    @pytest.mark.asyncio
    @patch("aiohttp.ClientSession.get")
    async def test_process_pdf_from_url(self, mock_get):
        """测试从URL处理PDF"""
        # 模拟HTTP下载
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.read = AsyncMock(return_value=b"fake PDF content")
        mock_get.return_value.__aenter__.return_value = mock_response

        with patch.object(self.processor, "_extract_with_pymupdf") as mock_extract:
            mock_extract.return_value = {
                "success": True,
                "text": "URL PDF content",
                "pages_processed": 1,
                "total_pages": 1,
            }

            result = await self.processor.process_pdf(
                "https://example.com/test.pdf", method="pymupdf"
            )

            assert result["success"] is True
            assert result["source"] == "https://example.com/test.pdf"
            assert "URL PDF content" in result["text"]


class TestBatchProcessing:
    """测试批量处理功能"""

    def setup_method(self):
        """测试前准备"""
        self.processor = PDFProcessor()

    def teardown_method(self):
        """测试后清理"""
        self.processor.cleanup()

    @pytest.mark.asyncio
    async def test_empty_batch_processing(self):
        """测试空批量处理"""
        result = await self.processor.batch_process_pdfs([])

        assert result["success"] is False
        assert result["error"] == "PDF sources list cannot be empty"

    @pytest.mark.asyncio
    async def test_successful_batch_processing(self):
        """测试成功的批量处理"""
        with patch.object(self.processor, "process_pdf") as mock_process:
            # 模拟成功的处理结果
            mock_process.side_effect = [
                {
                    "success": True,
                    "text": "PDF 1 content",
                    "pages_processed": 2,
                    "word_count": 10,
                    "source": "pdf1.pdf",
                },
                {
                    "success": True,
                    "text": "PDF 2 content",
                    "pages_processed": 3,
                    "word_count": 15,
                    "source": "pdf2.pdf",
                },
                {"success": False, "error": "Processing failed", "source": "pdf3.pdf"},
            ]

            pdf_sources = ["pdf1.pdf", "pdf2.pdf", "pdf3.pdf"]
            result = await self.processor.batch_process_pdfs(
                pdf_sources, method="auto", output_format="markdown"
            )

            assert result["success"] is True
            assert len(result["results"]) == 3
            assert result["summary"]["total_pdfs"] == 3
            assert result["summary"]["successful"] == 2
            assert result["summary"]["failed"] == 1
            assert result["summary"]["total_pages_processed"] == 5  # 2 + 3
            assert result["summary"]["total_words_extracted"] == 25  # 10 + 15
            assert result["summary"]["method_used"] == "auto"
            assert result["summary"]["output_format"] == "markdown"

    @pytest.mark.asyncio
    async def test_batch_processing_with_exceptions(self):
        """测试批量处理异常情况"""
        with patch.object(self.processor, "process_pdf") as mock_process:
            # 模拟处理异常
            mock_process.side_effect = [
                {
                    "success": True,
                    "text": "Success",
                    "pages_processed": 1,
                    "word_count": 5,
                },
                Exception("Processing error"),
                {"success": False, "error": "Failed", "source": "pdf3.pdf"},
            ]

            pdf_sources = ["pdf1.pdf", "pdf2.pdf", "pdf3.pdf"]
            result = await self.processor.batch_process_pdfs(pdf_sources)

            assert result["success"] is True
            assert len(result["results"]) == 3
            assert result["results"][0]["success"] is True
            assert result["results"][1]["success"] is False
            assert "Processing error" in result["results"][1]["error"]
            assert result["results"][2]["success"] is False
            assert result["summary"]["successful"] == 1
            assert result["summary"]["failed"] == 2


class TestCleanup:
    """测试清理功能"""

    def test_cleanup_temp_directory(self):
        """测试清理临时目录"""
        processor = PDFProcessor()
        temp_dir = processor.temp_dir

        # 验证临时目录存在
        assert os.path.exists(temp_dir)

        # 执行清理
        processor.cleanup()

        # 验证临时目录被删除
        assert not os.path.exists(temp_dir)

    def test_cleanup_with_missing_directory(self):
        """测试清理不存在的目录"""
        processor = PDFProcessor()

        # 手动删除目录
        import shutil

        shutil.rmtree(processor.temp_dir)

        # 清理应该不会抛出异常
        processor.cleanup()  # 应该正常执行


class TestErrorHandling:
    """测试错误处理"""

    def setup_method(self):
        """测试前准备"""
        self.processor = PDFProcessor()

    def teardown_method(self):
        """测试后清理"""
        self.processor.cleanup()

    @pytest.mark.asyncio
    async def test_extraction_method_failure(self):
        """测试提取方法失败"""
        with patch.object(self.processor, "_extract_with_pymupdf") as mock_extract:
            mock_extract.return_value = {"success": False, "error": "Extraction failed"}

            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_file:
                tmp_path = tmp_file.name

            try:
                result = await self.processor.process_pdf(tmp_path, method="pymupdf")

                assert result["success"] is False
                assert result["error"] == "Extraction failed"

            finally:
                os.unlink(tmp_path)

    @pytest.mark.asyncio
    async def test_general_processing_exception(self):
        """测试处理过程中的一般异常"""
        with patch.object(self.processor, "_extract_with_pymupdf") as mock_extract:
            mock_extract.side_effect = Exception("Unexpected error")

            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_file:
                tmp_path = tmp_file.name

            try:
                result = await self.processor.process_pdf(tmp_path, method="pymupdf")

                assert result["success"] is False
                assert "Unexpected error" in result["error"]

            finally:
                os.unlink(tmp_path)

    @pytest.mark.asyncio
    async def test_file_cleanup_after_error(self):
        """测试错误后的文件清理"""
        with (
            patch.object(self.processor, "_download_pdf") as mock_download,
            patch.object(self.processor, "_extract_with_pymupdf") as mock_extract,
        ):
            # 模拟下载成功
            temp_file = tempfile.NamedTemporaryFile(
                suffix=".pdf", dir=self.processor.temp_dir, delete=False
            )
            temp_path = Path(temp_file.name)
            temp_file.close()
            mock_download.return_value = temp_path

            # 模拟提取失败
            mock_extract.side_effect = Exception("Extraction error")

            # 文件应该存在
            assert temp_path.exists()

            result = await self.processor.process_pdf("https://example.com/test.pdf")

            # 处理应该失败
            assert result["success"] is False

            # 临时文件应该被清理
            assert not temp_path.exists()
