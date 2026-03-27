"""docs/2.1-Workflows.md 文档完整性测试。"""

import re

import pytest
from tests.unit.doc_contracts import (
    PROJECT_ROOT,
    assert_doc_exists,
    assert_relative_links_resolve,
    assert_required_frontmatter,
    read_doc,
)

WORKFLOWS_DIR = PROJECT_ROOT / ".github" / "workflows"
WORKFLOWS_DOC = "2.1-Workflows.md"


@pytest.fixture(scope="module")
def doc_content() -> str:
    """读取工作流文档内容。"""
    return read_doc(WORKFLOWS_DOC)


class TestDocExists:
    """文档文件存在性验证。"""

    def test_workflows_doc_exists(self):
        """2.1-Workflows.md 文件存在。"""
        assert_doc_exists(WORKFLOWS_DOC)

    def test_workflows_dir_exists(self):
        """.github/workflows/ 目录存在。"""
        assert WORKFLOWS_DIR.exists(), f"{WORKFLOWS_DIR} 不存在"


class TestFrontmatter:
    """Frontmatter 完整性验证。"""

    def test_has_frontmatter(self, doc_content: str):
        """文档包含 YAML frontmatter。"""
        assert_required_frontmatter(doc_content)


class TestRelativeLinks:
    """文档内相对路径链接有效性验证。"""

    LINK_PATTERN = re.compile(r"\[.*?\]\((\.\.?/[^)#]+?)(?:#[^)]*)?\)")

    def test_all_relative_links_resolve(self, doc_content: str):
        """所有相对路径链接指向的文件存在。"""
        assert_relative_links_resolve(doc_content)


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
