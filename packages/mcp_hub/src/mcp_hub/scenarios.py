"""Built-in validation scenarios for the MCP hub."""

from __future__ import annotations

from .models import ValidationScenario, ValidationScenarioStep


SCENARIOS = [
    ValidationScenario(
        id="complex_webpage_markdown",
        label="复杂网页转 Markdown",
        description="抓取复杂 URL 并生成 Markdown，适合检查正文提取与排版质量。",
        input_kind="url",
        tool_chain=[
            ValidationScenarioStep(
                step_id="page_info",
                tool_name="get_page_info",
                arguments={"url": "{{input.url}}"},
            ),
            ValidationScenarioStep(
                step_id="markdown",
                tool_name="convert_webpage_to_markdown",
                arguments={
                    "url": "{{input.url}}",
                    "method": "auto",
                    "extract_main_content": True,
                    "include_metadata": True,
                    "embed_images": False,
                },
            ),
        ],
        expected_artifact_types=["application/json", "text/markdown"],
        manual_checklist=[
            "检查页面标题与元数据是否合理",
            "检查 Markdown 是否保留主要结构与内容顺序",
            "检查广告/导航等噪音是否被有效过滤",
        ],
        risk_level="medium",
    ),
    ValidationScenario(
        id="complex_pdf_conversion",
        label="复杂 PDF 转换",
        description="转换复杂 PDF，检查图片、表格、公式等增强提取结果。",
        input_kind="pdf",
        tool_chain=[
            ValidationScenarioStep(
                step_id="pdf_markdown",
                tool_name="convert_pdf_to_markdown",
                arguments={
                    "pdf_source": "{{input.pdf_source}}",
                    "method": "auto",
                    "include_metadata": True,
                    "output_format": "markdown",
                    "extract_images": True,
                    "extract_tables": True,
                    "extract_formulas": True,
                    "embed_images": False,
                },
            ),
        ],
        expected_artifact_types=["application/json", "text/markdown"],
        manual_checklist=[
            "检查页数、元数据与字数统计是否合理",
            "检查 Markdown 中标题层级与正文是否完整",
            "检查 enhanced_assets 的图片/表格/公式统计是否符合预期",
        ],
        risk_level="medium",
    ),
    ValidationScenario(
        id="link_discovery_pipeline",
        label="链接发现链路",
        description="先抽取链接，再检查结构化链接结果，适合验证发现链路。",
        input_kind="url",
        tool_chain=[
            ValidationScenarioStep(
                step_id="links",
                tool_name="extract_links",
                arguments={"url": "{{input.url}}", "internal_only": False},
            ),
            ValidationScenarioStep(
                step_id="structured",
                tool_name="extract_structured_data",
                arguments={"url": "{{input.url}}", "data_type": "all"},
            ),
        ],
        expected_artifact_types=["application/json"],
        manual_checklist=[
            "检查内部/外部链接分类是否正确",
            "检查联系方式、地址、社交链接等结构化内容是否覆盖预期字段",
        ],
        risk_level="low",
    ),
]

SCENARIOS_BY_ID = {scenario.id: scenario for scenario in SCENARIOS}
