"""docs/2.1-Workflows.md 文档完整性测试。

验证工作流文档的结构完整性、链接有效性和事实源一致性。
"""

import re
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DOCS_DIR = PROJECT_ROOT / "docs"
WORKFLOWS_DIR = PROJECT_ROOT / ".github" / "workflows"
WORKFLOWS_DOC = DOCS_DIR / "2.1-Workflows.md"


@pytest.fixture(scope="module")
def doc_content() -> str:
    """读取工作流文档内容。"""
    return WORKFLOWS_DOC.read_text(encoding="utf-8")


class TestDocExists:
    """文档文件存在性验证。"""

    def test_workflows_doc_exists(self):
        """2.1-Workflows.md 文件存在。"""
        assert WORKFLOWS_DOC.exists(), f"{WORKFLOWS_DOC} 不存在"

    def test_workflows_dir_exists(self):
        """.github/workflows/ 目录存在。"""
        assert WORKFLOWS_DIR.exists(), f"{WORKFLOWS_DIR} 不存在"


class TestFrontmatter:
    """Frontmatter 完整性验证。"""

    REQUIRED_FIELDS = ["id", "title", "description", "last_update"]

    def test_has_frontmatter(self, doc_content: str):
        """文档包含 YAML frontmatter。"""
        assert doc_content.startswith("---"), "文档缺少 frontmatter 起始标记"
        # 查找第二个 --- 标记
        second_marker = doc_content.index("---", 3)
        assert second_marker > 3, "文档缺少 frontmatter 结束标记"

    @pytest.mark.parametrize("field", REQUIRED_FIELDS)
    def test_frontmatter_has_field(self, doc_content: str, field: str):
        """Frontmatter 包含必需字段: {field}。"""
        # 提取 frontmatter 区域
        end = doc_content.index("---", 3)
        frontmatter = doc_content[3:end]
        assert (
            f"{field}:" in frontmatter
        ), f"frontmatter 缺少必需字段 '{field}'"


class TestRelativeLinks:
    """文档内相对路径链接有效性验证。"""

    LINK_PATTERN = re.compile(r"\[.*?\]\((\.\.?/[^)#]+?)(?:#[^)]*)?\)")

    def test_all_relative_links_resolve(self, doc_content: str):
        """所有相对路径链接指向的文件存在。"""
        links = self.LINK_PATTERN.findall(doc_content)
        assert len(links) > 0, "未找到任何相对路径链接"

        broken = []
        for link in links:
            target = (DOCS_DIR / link).resolve()
            if not target.exists():
                broken.append(link)

        assert broken == [], f"以下链接目标不存在: {broken}"


class TestWorkflowFileReferences:
    """文档中引用的工作流文件一致性验证。"""

    YML_REF_PATTERN = re.compile(r"`(\w[\w-]*\.yml)`")

    def test_all_referenced_yml_files_exist(self, doc_content: str):
        """文档中引用的每个 .yml 文件在 .github/workflows/ 下存在。"""
        refs = set(self.YML_REF_PATTERN.findall(doc_content))
        assert len(refs) > 0, "未找到任何 .yml 文件引用"

        missing = []
        for yml in refs:
            if not (WORKFLOWS_DIR / yml).exists():
                missing.append(yml)

        assert missing == [], f"以下工作流文件不存在: {missing}"


class TestMermaidIntegrity:
    """Mermaid 代码块结构完整性验证。"""

    MERMAID_PATTERN = re.compile(
        r"```mermaid\s*\n(.*?)\n```", re.DOTALL
    )

    def test_has_mermaid_block(self, doc_content: str):
        """文档包含至少一个 Mermaid 代码块。"""
        matches = self.MERMAID_PATTERN.findall(doc_content)
        assert len(matches) >= 1, "文档中未找到 Mermaid 代码块"

    def test_mermaid_brackets_balanced(self, doc_content: str):
        """Mermaid 代码块中括号配对平衡。"""
        matches = self.MERMAID_PATTERN.findall(doc_content)
        for i, block in enumerate(matches):
            for open_ch, close_ch, name in [
                ("[", "]", "方括号"),
                ("(", ")", "圆括号"),
                ("{", "}", "花括号"),
            ]:
                opens = block.count(open_ch)
                closes = block.count(close_ch)
                assert opens == closes, (
                    f"Mermaid 块 {i}: {name}不平衡 "
                    f"('{open_ch}': {opens}, '{close_ch}': {closes})"
                )

    def test_mermaid_has_subgraph(self, doc_content: str):
        """Mermaid 代码块使用 subgraph 进行逻辑分组。"""
        matches = self.MERMAID_PATTERN.findall(doc_content)
        assert any(
            "subgraph" in block for block in matches
        ), "Mermaid 代码块缺少 subgraph 分组"
