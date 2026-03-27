"""Docling 文档转换引擎封装。

当 ``docling`` 可选依赖已安装时，提供基于 Docling DocumentConverter 的
全功能 PDF→Markdown 转换路径，包括布局分析、表格结构识别（TableFormer）、
代码检测、公式提取与图片处理。

降级策略：当 ``docling`` 未安装时，``is_available()`` 返回 ``False``，
``convert()`` 安全返回 ``None``，由上层 ``PDFProcessor`` 自动切换至
PyMuPDF 路径。
"""

import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# 数据类：标准化 Docling 输出
# ---------------------------------------------------------------------------


@dataclass
class DoclingTable:
    """Docling 提取的表格。"""

    markdown: str
    rows: int = 0
    columns: int = 0
    page_number: Optional[int] = None
    caption: Optional[str] = None
    bbox: Optional[Tuple[float, float, float, float]] = None


@dataclass
class DoclingImage:
    """Docling 提取的图片。"""

    page_number: Optional[int] = None
    caption: Optional[str] = None
    classification: Optional[str] = None
    bbox: Optional[Tuple[float, float, float, float]] = None
    image_ref: Any = None  # Docling ImageRef 对象


@dataclass
class DoclingFormula:
    """Docling 提取的数学公式。"""

    latex: str
    formula_type: str = "block"  # "inline" or "block"
    page_number: Optional[int] = None
    original_text: str = ""


@dataclass
class DoclingCodeBlock:
    """Docling 提取的代码块。"""

    code: str
    language: Optional[str] = None
    page_number: Optional[int] = None


@dataclass
class DoclingConversionResult:
    """Docling 转换结果的标准化数据结构。"""

    markdown: str
    tables: List[DoclingTable] = field(default_factory=list)
    images: List[DoclingImage] = field(default_factory=list)
    formulas: List[DoclingFormula] = field(default_factory=list)
    code_blocks: List[DoclingCodeBlock] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    page_count: int = 0


# ---------------------------------------------------------------------------
# Docling 引擎
# ---------------------------------------------------------------------------


class DoclingEngine:
    """Docling 文档转换引擎。

    封装 Docling ``DocumentConverter`` 的完整能力：

    * 全文档 Markdown 转换（含布局分析与阅读顺序保持）
    * 结构化表格提取（TableFormer ACCURATE 模式）
    * 代码块检测与语言识别
    * 数学公式 LaTeX 提取（CodeFormula 模型）
    * 图片提取与分类

    Converter 实例在首次调用时延迟初始化并**类级缓存**，
    避免重复加载 AI 模型（首次约 10-30 秒）。
    """

    # 类级缓存：不同配置签名 → converter 实例
    _converters: Dict[str, Any] = {}

    def __init__(
        self,
        enable_table_structure: bool = True,
        table_mode: str = "accurate",
        enable_code_enrichment: bool = True,
        enable_formula_enrichment: bool = True,
        enable_picture_images: bool = True,
        enable_ocr: bool = False,
        images_scale: float = 2.0,
        output_dir: Optional[str] = None,
    ) -> None:
        self._enable_table_structure = enable_table_structure
        self._table_mode = table_mode
        self._enable_code_enrichment = enable_code_enrichment
        self._enable_formula_enrichment = enable_formula_enrichment
        self._enable_picture_images = enable_picture_images
        self._enable_ocr = enable_ocr
        self._images_scale = images_scale
        self._output_dir = Path(output_dir) if output_dir else None

    # ------------------------------------------------------------------
    # 可用性检测
    # ------------------------------------------------------------------

    @staticmethod
    def is_available() -> bool:
        """检测 ``docling`` 是否已安装且可用。"""
        try:
            import docling  # noqa: F401

            return True
        except ImportError:
            return False

    # ------------------------------------------------------------------
    # 配置签名（用于 converter 缓存键）
    # ------------------------------------------------------------------

    def _config_key(self) -> str:
        return (
            f"tbl={self._enable_table_structure}:{self._table_mode}"
            f"|code={self._enable_code_enrichment}"
            f"|formula={self._enable_formula_enrichment}"
            f"|pic={self._enable_picture_images}"
            f"|ocr={self._enable_ocr}"
            f"|scale={self._images_scale}"
        )

    # ------------------------------------------------------------------
    # Converter 延迟初始化
    # ------------------------------------------------------------------

    def _get_converter(self) -> Any:
        """延迟初始化并返回 DocumentConverter 实例。"""
        key = self._config_key()
        if key in DoclingEngine._converters:
            return DoclingEngine._converters[key]

        from docling.datamodel.base_models import InputFormat  # type: ignore[import-untyped]
        from docling.datamodel.pipeline_options import (  # type: ignore[import-untyped]
            PdfPipelineOptions,
        )
        from docling.document_converter import (  # type: ignore[import-untyped]
            DocumentConverter,
            PdfFormatOption,
        )

        pipeline_options = PdfPipelineOptions()
        pipeline_options.do_table_structure = self._enable_table_structure
        pipeline_options.do_code_enrichment = self._enable_code_enrichment
        pipeline_options.do_formula_enrichment = self._enable_formula_enrichment
        pipeline_options.generate_picture_images = self._enable_picture_images
        pipeline_options.images_scale = self._images_scale
        pipeline_options.do_ocr = self._enable_ocr

        # 禁用非必要的页面图像生成以节省内存
        pipeline_options.generate_page_images = False

        if self._enable_table_structure:
            from docling.datamodel.pipeline_options import (  # type: ignore[import-untyped]
                TableFormerMode,
                TableStructureOptions,
            )

            mode = (
                TableFormerMode.ACCURATE
                if self._table_mode == "accurate"
                else TableFormerMode.FAST
            )
            pipeline_options.table_structure_options = TableStructureOptions(
                mode=mode,
                do_cell_matching=True,
            )

        converter = DocumentConverter(
            format_options={
                InputFormat.PDF: PdfFormatOption(
                    pipeline_options=pipeline_options,
                )
            }
        )
        DoclingEngine._converters[key] = converter
        logger.info("Docling DocumentConverter 初始化完成 (config=%s)", key)
        return converter

    # ------------------------------------------------------------------
    # 核心转换
    # ------------------------------------------------------------------

    def convert(
        self,
        pdf_path: str,
        page_range: Optional[Tuple[int, int]] = None,
    ) -> Optional[DoclingConversionResult]:
        """执行完整文档转换。

        Args:
            pdf_path: PDF 文件本地路径。
            page_range: 可选的页码范围 ``(start, end)``。

        Returns:
            ``DoclingConversionResult`` 或 ``None``（当 Docling 不可用或转换失败时）。
        """
        if not self.is_available():
            return None

        try:
            converter = self._get_converter()

            # Docling convert() 接受 str 路径
            result = converter.convert(pdf_path)
            doc = result.document

            # 1. 导出完整 Markdown
            markdown = doc.export_to_markdown()

            # 2. LaTeX 后处理（复用现有清洗逻辑）
            from .math_formula import DoclingFormulaEnricher

            markdown = DoclingFormulaEnricher.postprocess_latex(markdown)

            # 3. 提取结构化元素
            tables = self._extract_tables(doc)
            images = self._extract_images(doc)
            formulas = self._extract_formulas(doc, markdown)
            code_blocks = self._extract_code_blocks(doc)

            # 4. 元数据
            metadata = self._extract_metadata(doc)

            # 5. 页数
            page_count = len(doc.pages) if hasattr(doc, "pages") and doc.pages else 0

            return DoclingConversionResult(
                markdown=markdown,
                tables=tables,
                images=images,
                formulas=formulas,
                code_blocks=code_blocks,
                metadata=metadata,
                page_count=page_count,
            )
        except Exception as e:
            logger.warning("Docling 转换失败: %s", e)
            return None

    # ------------------------------------------------------------------
    # 结构化元素提取
    # ------------------------------------------------------------------

    def _extract_tables(self, doc: Any) -> List[DoclingTable]:
        """从 DoclingDocument 提取结构化表格。"""
        tables: List[DoclingTable] = []
        if not hasattr(doc, "tables"):
            return tables

        for table_item in doc.tables:
            try:
                md = table_item.export_to_markdown(doc=doc)

                # 表格维度
                rows = 0
                cols = 0
                data = getattr(table_item, "data", None)
                if data is not None:
                    rows = getattr(data, "num_rows", 0)
                    cols = getattr(data, "num_cols", 0)

                # 标题（captions 可能是 RefItem 列表，需安全提取 text）
                caption = self._safe_caption(table_item)

                # 页码
                page_no = self._get_page_number(table_item)

                tables.append(
                    DoclingTable(
                        markdown=md,
                        rows=rows,
                        columns=cols,
                        page_number=page_no,
                        caption=caption,
                    )
                )
            except Exception as e:
                logger.warning("提取 Docling 表格失败: %s", e)

        return tables

    def _extract_images(self, doc: Any) -> List[DoclingImage]:
        """从 DoclingDocument 提取图片信息。"""
        images: List[DoclingImage] = []
        if not hasattr(doc, "pictures"):
            return images

        for pic in doc.pictures:
            try:
                caption = self._safe_caption(pic)

                classification = getattr(pic, "classification", None)
                page_no = self._get_page_number(pic)
                image_ref = getattr(pic, "image", None)

                images.append(
                    DoclingImage(
                        page_number=page_no,
                        caption=caption,
                        classification=str(classification) if classification else None,
                        image_ref=image_ref,
                    )
                )
            except Exception as e:
                logger.warning("提取 Docling 图片失败: %s", e)

        return images

    def _extract_formulas(
        self, doc: Any, markdown: str
    ) -> List[DoclingFormula]:
        """从 Markdown 文本中提取公式。

        Docling 将公式内嵌在 Markdown 输出中，通过正则匹配提取。
        """
        formulas: List[DoclingFormula] = []

        # 块级公式: $$ ... $$
        for match in re.finditer(r"\$\$([\s\S]+?)\$\$", markdown):
            latex = match.group(1).strip()
            if latex:
                formulas.append(
                    DoclingFormula(latex=latex, formula_type="block")
                )

        # 行内公式: $ ... $ (排除 $$)
        for match in re.finditer(r"(?<!\$)\$(?!\$)([^$]+?)\$(?!\$)", markdown):
            latex = match.group(1).strip()
            if latex and len(latex) > 1:
                formulas.append(
                    DoclingFormula(latex=latex, formula_type="inline")
                )

        return formulas

    def _extract_code_blocks(self, doc: Any) -> List[DoclingCodeBlock]:
        """从 DoclingDocument 提取代码块。"""
        code_blocks: List[DoclingCodeBlock] = []

        try:
            if not hasattr(doc, "iterate_items"):
                return code_blocks

            for item, _level in doc.iterate_items():
                label = str(getattr(item, "label", "")).lower()
                if "code" in label:
                    code = getattr(item, "text", "")
                    lang = getattr(item, "code_language", None)
                    if code:
                        page_no = self._get_page_number(item)
                        code_blocks.append(
                            DoclingCodeBlock(
                                code=code,
                                language=str(lang) if lang else None,
                                page_number=page_no,
                            )
                        )
        except Exception as e:
            logger.warning("提取 Docling 代码块失败: %s", e)

        return code_blocks

    def _extract_metadata(self, doc: Any) -> Dict[str, Any]:
        """提取文档元数据。"""
        meta: Dict[str, Any] = {}
        if hasattr(doc, "name"):
            meta["title"] = doc.name

        origin = getattr(doc, "origin", None)
        if origin:
            if hasattr(origin, "filename"):
                meta["filename"] = origin.filename
            if hasattr(origin, "mimetype"):
                meta["mimetype"] = origin.mimetype

        return meta

    @staticmethod
    def _safe_caption(item: Any) -> str:
        """安全提取 Docling 元素的 caption 文本。

        captions 列表中的元素可能是 ``TextItem``（有 ``.text``）
        或 ``RefItem``（无 ``.text``），需防御性处理。
        """
        captions = getattr(item, "captions", None)
        if not captions:
            return ""
        first = captions[0]
        text = getattr(first, "text", None)
        if text is not None:
            return str(text)
        # RefItem: 尝试 cref / $ref 等其他属性
        return ""

    @staticmethod
    def _get_page_number(item: Any) -> Optional[int]:
        """从 Docling 元素的 prov 属性中获取页码。"""
        prov = getattr(item, "prov", None)
        if prov and len(prov) > 0:
            return getattr(prov[0], "page_no", None)
        return None

    # ------------------------------------------------------------------
    # 缓存管理
    # ------------------------------------------------------------------

    @classmethod
    def reset_cache(cls) -> None:
        """清除 converter 缓存（主要用于测试）。"""
        cls._converters.clear()
