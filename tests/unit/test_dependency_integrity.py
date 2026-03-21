"""依赖完整性验证测试。

验证所有运行时直接依赖可正常 import，
以及已移除或降级的包不在 extractor/ 源码中被直接引用。
"""

import ast
from pathlib import Path

import pytest

# extractor/ 源码目录
EXTRACTOR_DIR = Path(__file__).parent.parent.parent / "extractor"


def _collect_imports(source_dir: Path) -> list[tuple[str, str, str]]:
    """扫描源码目录，收集所有 import 语句。

    Returns:
        列表元素为 (文件名, import类型, 模块名)
    """
    results: list[tuple[str, str, str]] = []
    for py_file in source_dir.rglob("*.py"):
        tree = ast.parse(py_file.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    results.append((py_file.name, "import", alias.name))
            elif isinstance(node, ast.ImportFrom) and node.module:
                results.append((py_file.name, "from", node.module))
    return results


# 预先收集一次，供多个测试复用
_ALL_IMPORTS = _collect_imports(EXTRACTOR_DIR)


class TestRuntimeDependencies:
    """验证运行时依赖的可导入性。"""

    @pytest.mark.parametrize(
        "module_name",
        [
            "fastmcp",
            "scrapy",
            "aiohttp",
            "bs4",
            "requests",
            "selenium",
            "playwright",
            "fake_useragent",
            "pydantic",
            "pydantic_settings",
            "markitdown",
            "pymupdf",
            "pypdf",
        ],
    )
    def test_runtime_dependency_importable(self, module_name: str) -> None:
        """运行时依赖必须可导入。"""
        __import__(module_name)


class TestRemovedDependencies:
    """验证已从主依赖删除的包不在 extractor/ 源码中被直接 import。"""

    @pytest.mark.parametrize(
        "module_name,reason",
        [
            ("httpx", "项目使用 requests + aiohttp，httpx 未被使用"),
            ("lxml", "BeautifulSoup 全部使用 html.parser"),
            ("dotenv", "pydantic-settings 原生支持 .env 加载"),
        ],
    )
    def test_removed_package_not_imported(
        self, module_name: str, reason: str
    ) -> None:
        """已移除的包不应在 extractor/ 中被直接 import。"""
        for file_name, import_type, mod in _ALL_IMPORTS:
            top_module = mod.split(".")[0]
            assert top_module != module_name, (
                f"{file_name} 中 {import_type} {mod}，"
                f"但 {module_name} 已从主依赖移除（{reason}）"
            )


class TestDevDependencyClassification:
    """验证仅属于 dev 的工具不在运行时源码中被 import。"""

    @pytest.mark.parametrize(
        "module_name",
        [
            "ruff",
        ],
    )
    def test_dev_tool_not_in_runtime_imports(self, module_name: str) -> None:
        """dev 工具不应在 extractor/ 源码中被直接 import。"""
        for file_name, import_type, mod in _ALL_IMPORTS:
            top_module = mod.split(".")[0]
            assert top_module != module_name, (
                f"{file_name} 中 {import_type} {mod}，"
                f"但 {module_name} 已移至 dev 依赖"
            )
