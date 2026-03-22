"""docs/4-Configuration.md 文档完整性测试。

验证配置文档的结构完整性、链接有效性和与代码实现的一致性。
"""

import re
from pathlib import Path

import pytest

from extractor.config import DataExtractorSettings

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DOCS_DIR = PROJECT_ROOT / "docs"
CONFIG_DOC = DOCS_DIR / "4-Configuration.md"

# DataExtractorSettings 中非配置元字段（model_config 等不映射为环境变量）
_EXCLUDED_FIELDS = {"model_config"}

# 从 DataExtractorSettings 的 model_fields 中推导 DATA_EXTRACTOR_* 环境变量名
_SETTINGS_ENV_VARS: set[str] = {
    f"DATA_EXTRACTOR_{name.upper()}"
    for name in DataExtractorSettings.model_fields
    if name not in _EXCLUDED_FIELDS
}


@pytest.fixture(scope="module")
def doc_content() -> str:
    """读取配置文档内容。"""
    return CONFIG_DOC.read_text(encoding="utf-8")


class TestDocExists:
    """文档文件存在性验证。"""

    def test_configuration_doc_exists(self):
        """4-Configuration.md 文件存在。"""
        assert CONFIG_DOC.exists(), f"{CONFIG_DOC} 不存在"


class TestFrontmatter:
    """Frontmatter 完整性验证。"""

    REQUIRED_FIELDS = ["id", "title", "description", "last_update"]

    def test_has_frontmatter(self, doc_content: str):
        """文档包含 YAML frontmatter。"""
        assert doc_content.startswith("---"), "文档缺少 frontmatter 起始标记"
        second_marker = doc_content.index("---", 3)
        assert second_marker > 3, "文档缺少 frontmatter 结束标记"

    @pytest.mark.parametrize("field", REQUIRED_FIELDS)
    def test_frontmatter_has_field(self, doc_content: str, field: str):
        """Frontmatter 包含必需字段: {field}。"""
        end = doc_content.index("---", 3)
        frontmatter = doc_content[3:end]
        assert f"{field}:" in frontmatter, f"frontmatter 缺少必需字段 '{field}'"


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


class TestEnvVarConsistency:
    """文档中环境变量与代码实现的一致性验证。"""

    ENV_VAR_PATTERN = re.compile(r"`(DATA_EXTRACTOR_\w+)`")

    def test_doc_covers_all_code_env_vars(self, doc_content: str):
        """文档覆盖 config.py 中所有配置字段对应的环境变量。"""
        doc_vars = set(self.ENV_VAR_PATTERN.findall(doc_content))
        missing = _SETTINGS_ENV_VARS - doc_vars
        assert missing == set(), (
            f"以下环境变量在 config.py 中定义但文档未记录: {sorted(missing)}"
        )

    def test_doc_env_vars_exist_in_code(self, doc_content: str):
        """文档中引用的环境变量在 config.py 中有对应字段。"""
        doc_vars = set(self.ENV_VAR_PATTERN.findall(doc_content))
        extra = doc_vars - _SETTINGS_ENV_VARS
        assert extra == set(), (
            f"以下环境变量在文档中出现但 config.py 中无对应字段: {sorted(extra)}"
        )


class TestConfigGroupCompleteness:
    """文档表格对 config.py 字段的覆盖完整性验证。"""

    TABLE_ROW_PATTERN = re.compile(
        r"^\| `DATA_EXTRACTOR_(\w+)` \|", re.MULTILINE
    )

    def test_all_fields_in_tables(self, doc_content: str):
        """文档表格行覆盖 config.py 中所有配置字段。"""
        table_fields = {
            match.lower() for match in self.TABLE_ROW_PATTERN.findall(doc_content)
        }
        code_fields = {
            name for name in DataExtractorSettings.model_fields
            if name not in _EXCLUDED_FIELDS
        }
        missing = code_fields - table_fields
        assert missing == set(), (
            f"以下字段在 config.py 中定义但未出现在文档表格中: {sorted(missing)}"
        )
