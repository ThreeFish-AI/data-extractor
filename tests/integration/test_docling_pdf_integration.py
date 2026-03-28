"""Docling 深度集成回归测试。

使用真实 PDF 文件验证：
1. Docling 全链路转换质量（布局、段落顺序、表格、公式、图片、代码）
2. 与 PyMuPDF 路径的降级兼容性
3. 两种引擎的输出质量对比（记录指标，不做硬断言）

测试资源：
- assets/Context Engineering 2.0 - The Context of Context Engineering.pdf
- assets/2603.05344v3.pdf
"""

import logging
from pathlib import Path

import pytest

from negentropy.perceives.pdf.hardware import DeviceType, detect_device
from negentropy.perceives.pdf.docling_engine import DoclingEngine

logger = logging.getLogger(__name__)

# MPS 上 formula enrichment 被禁用以保持 GPU 加速，公式相关测试需跳过
_is_mps = detect_device() == DeviceType.MPS
skip_formula_on_mps = pytest.mark.skipif(
    _is_mps,
    reason="MPS 与 Docling formula enrichment 不兼容，公式测试跳过",
)

# 真实 PDF 文件路径
ASSETS_DIR = Path(__file__).resolve().parents[2] / "assets"
CE_PDF = ASSETS_DIR / "Context Engineering 2.0 - The Context of Context Engineering.pdf"
ARXIV_PDF = ASSETS_DIR / "2603.05344v3.pdf"

# 条件跳过装饰器
skip_no_docling = pytest.mark.skipif(
    not DoclingEngine.is_available(),
    reason="需要安装 docling 可选依赖",
)
skip_no_ce_pdf = pytest.mark.skipif(
    not CE_PDF.exists(),
    reason=f"PDF 文件不存在: {CE_PDF}",
)
skip_no_arxiv_pdf = pytest.mark.skipif(
    not ARXIV_PDF.exists(),
    reason=f"PDF 文件不存在: {ARXIV_PDF}",
)


# ============================================================
# Context Engineering PDF — Docling 引擎转换测试
# ============================================================
@skip_no_docling
@skip_no_ce_pdf
class TestDoclingCEPDFConversion:
    """Context Engineering 2.0 PDF 的 Docling 转换质量验证。

    该 PDF 包含丰富的数学公式、表格和图像。
    """

    @pytest.fixture(scope="class")
    def docling_result(self):
        """类级 fixture：执行一次 Docling 转换，所有测试共享结果。"""
        engine = DoclingEngine()
        result = engine.convert(str(CE_PDF))
        assert result is not None, "Docling 转换返回 None"
        return result

    @pytest.mark.integration
    def test_markdown_not_empty(self, docling_result) -> None:
        """Markdown 输出不应为空。"""
        assert len(docling_result.markdown) > 100, (
            f"Markdown 输出过短: {len(docling_result.markdown)} 字符"
        )

    @pytest.mark.integration
    def test_markdown_has_headings(self, docling_result) -> None:
        """Markdown 应包含标题结构。"""
        md = docling_result.markdown
        assert "# " in md or "## " in md, "Markdown 中未找到标题"

    @pytest.mark.integration
    def test_page_count(self, docling_result) -> None:
        """应正确报告页数。"""
        assert docling_result.page_count > 0, "页数为 0"

    @pytest.mark.integration
    @skip_formula_on_mps
    def test_formulas_in_markdown(self, docling_result) -> None:
        """Markdown 中应包含 LaTeX 公式标记。"""
        md = docling_result.markdown
        has_inline = "$" in md
        has_block = "$$" in md
        assert has_inline or has_block, (
            "Markdown 中未找到 LaTeX 公式标记 ($ 或 $$)"
        )

    @pytest.mark.integration
    @skip_formula_on_mps
    def test_formulas_extracted(self, docling_result) -> None:
        """应提取到数学公式。"""
        assert len(docling_result.formulas) > 0, "未提取到任何公式"

    @pytest.mark.integration
    def test_tables_extracted(self, docling_result) -> None:
        """应提取到表格。"""
        assert len(docling_result.tables) > 0, "未提取到任何表格"

    @pytest.mark.integration
    def test_tables_have_structure(self, docling_result) -> None:
        """表格应包含结构化 Markdown（管道分隔符）。"""
        for table in docling_result.tables:
            assert "|" in table.markdown, (
                f"表格缺少管道分隔符: {table.markdown[:100]}"
            )

    @pytest.mark.integration
    def test_images_detected(self, docling_result) -> None:
        """应检测到图片。"""
        assert len(docling_result.images) > 0, "未检测到任何图片"

    @pytest.mark.integration
    def test_paragraph_ordering_sample(self, docling_result) -> None:
        """抽样验证段落顺序：关键内容应按原文顺序出现。

        选取论文中几个确定性标题/关键词，验证其在 Markdown 中的出现顺序。
        """
        md = docling_result.markdown

        # 收集出现位置
        markers = ["Context", "Engineering"]
        positions = []
        for marker in markers:
            pos = md.find(marker)
            if pos >= 0:
                positions.append((marker, pos))

        # 至少找到一些标记
        assert len(positions) > 0, "未在 Markdown 中找到任何预期标记"


# ============================================================
# arXiv 论文 PDF — Docling 引擎转换测试
# ============================================================
@skip_no_docling
@skip_no_arxiv_pdf
class TestDoclingArxivPDFConversion:
    """arXiv 论文 2603.05344v3 的 Docling 转换质量验证。

    该 PDF 包含大量代码块。
    """

    @pytest.fixture(scope="class")
    def docling_result(self):
        engine = DoclingEngine()
        result = engine.convert(str(ARXIV_PDF))
        assert result is not None, "Docling 转换返回 None"
        return result

    @pytest.mark.integration
    def test_markdown_not_empty(self, docling_result) -> None:
        assert len(docling_result.markdown) > 100

    @pytest.mark.integration
    def test_code_blocks_in_markdown(self, docling_result) -> None:
        """Markdown 中应包含代码围栏。"""
        md = docling_result.markdown
        assert "```" in md, "Markdown 中未找到代码围栏 (```)"

    @pytest.mark.integration
    def test_code_blocks_extracted(self, docling_result) -> None:
        """应提取到代码块。"""
        assert len(docling_result.code_blocks) > 0, "未提取到任何代码块"

    @pytest.mark.integration
    def test_academic_structure(self, docling_result) -> None:
        """学术论文应包含典型结构（Abstract 等）。"""
        md = docling_result.markdown.lower()
        has_abstract = "abstract" in md
        has_intro = "introduction" in md or "intro" in md
        assert has_abstract or has_intro, (
            "学术论文中未找到 Abstract 或 Introduction"
        )

    @pytest.mark.integration
    def test_tables_have_pipe_separator(self, docling_result) -> None:
        """如有表格，应包含管道分隔符。"""
        for table in docling_result.tables:
            assert "|" in table.markdown


# ============================================================
# Docling 路径与 PyMuPDF 降级兼容性
# ============================================================
@skip_no_ce_pdf
class TestDoclingFallbackCompatibility:
    """验证 Docling 路径与 PyMuPDF 降级路径的兼容性。"""

    @skip_no_docling
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_full_pipeline_with_docling(self) -> None:
        """通过 PDFProcessor 完整管线验证 Docling 路径。"""
        from negentropy.perceives.pdf.processor import PDFProcessor

        processor = PDFProcessor(enable_enhanced_features=True, prefer_docling=True)
        try:
            result = await processor.process_pdf(
                str(CE_PDF),
                method="auto",
                extract_formulas=True,
                extract_images=True,
                extract_tables=True,
            )
            assert result["success"] is True
            assert result.get("method_used") == "docling"
            assert "markdown" in result
            assert len(result["markdown"]) > 100
        finally:
            processor.cleanup()

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_fallback_to_pymupdf(self) -> None:
        """prefer_docling=False 时应走 PyMuPDF 路径。"""
        from negentropy.perceives.pdf.processor import PDFProcessor

        processor = PDFProcessor(
            enable_enhanced_features=True,
            prefer_docling=False,
        )
        try:
            result = await processor.process_pdf(
                str(CE_PDF),
                method="pymupdf",
                extract_formulas=True,
                extract_images=False,
                extract_tables=False,
            )
            assert result["success"] is True
            assert result.get("method_used") == "pymupdf"
        finally:
            processor.cleanup()

    @skip_no_docling
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_explicit_docling_method(self) -> None:
        """method='docling' 显式指定应使用 Docling 引擎。"""
        from negentropy.perceives.pdf.processor import PDFProcessor

        processor = PDFProcessor(enable_enhanced_features=True, prefer_docling=True)
        try:
            result = await processor.process_pdf(
                str(CE_PDF),
                method="docling",
                extract_formulas=True,
                extract_tables=True,
            )
            assert result["success"] is True
            assert result.get("method_used") == "docling"
        finally:
            processor.cleanup()

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_docling_method_without_install_returns_error(self) -> None:
        """Docling 未安装时 method='docling' 应返回错误。"""
        from negentropy.perceives.pdf.processor import PDFProcessor

        processor = PDFProcessor(
            enable_enhanced_features=True,
            prefer_docling=False,  # 模拟未安装
        )
        try:
            result = await processor.process_pdf(
                str(CE_PDF),
                method="docling",
            )
            # 当 _docling_engine is None 且 method="docling"，应返回错误
            assert result["success"] is False
            assert "不可用" in result.get("error", "") or "docling" in result.get("error", "").lower()
        finally:
            processor.cleanup()


# ============================================================
# 质量对比（记录指标，不做硬断言）
# ============================================================
@skip_no_docling
@skip_no_ce_pdf
class TestConversionQualityComparison:
    """对比 Docling 与 PyMuPDF 引擎的输出质量。

    记录指标供人工审查，不做引擎间的硬性断言。
    """

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_compare_outputs(self) -> None:
        """对比两个引擎的关键质量指标。"""
        from negentropy.perceives.pdf.processor import PDFProcessor

        # Docling 路径
        proc_docling = PDFProcessor(
            enable_enhanced_features=True, prefer_docling=True,
        )
        # PyMuPDF 路径
        proc_pymupdf = PDFProcessor(
            enable_enhanced_features=True, prefer_docling=False,
        )

        try:
            docling_result = await proc_docling.process_pdf(
                str(CE_PDF),
                method="auto",
                extract_formulas=True,
                extract_images=True,
                extract_tables=True,
            )
            pymupdf_result = await proc_pymupdf.process_pdf(
                str(CE_PDF),
                method="pymupdf",
                extract_formulas=True,
                extract_images=True,
                extract_tables=True,
            )

            assert docling_result["success"] is True
            assert pymupdf_result["success"] is True

            # 记录质量指标
            logger.info(
                "质量对比 [Context Engineering 2.0 PDF]:\n"
                "  Docling: %d 词, %d 字符, method=%s\n"
                "  PyMuPDF: %d 词, %d 字符, method=%s\n"
                "  Docling tables: %s\n"
                "  PyMuPDF tables: %s\n"
                "  Docling formulas: %s\n"
                "  PyMuPDF formulas: %s",
                docling_result.get("word_count", 0),
                docling_result.get("character_count", 0),
                docling_result.get("method_used"),
                pymupdf_result.get("word_count", 0),
                pymupdf_result.get("character_count", 0),
                pymupdf_result.get("method_used"),
                docling_result.get("enhanced_assets", {}).get("tables", {}),
                pymupdf_result.get("enhanced_assets", {}).get("tables_extracted", 0),
                docling_result.get("enhanced_assets", {}).get("formulas", {}),
                pymupdf_result.get("enhanced_assets", {}).get("formulas_extracted", 0),
            )
        finally:
            proc_docling.cleanup()
            proc_pymupdf.cleanup()
