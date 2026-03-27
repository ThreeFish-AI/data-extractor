"""Data Extractor MCP Server - A robust web scraping MCP server."""

import importlib.metadata
import re
from pathlib import Path


def _get_version_from_pyproject():
    """从 pyproject.toml 动态读取版本号"""
    try:
        # 从当前文件位置向上查找项目根目录
        pyproject_path = Path(__file__).resolve().parent.parent / "pyproject.toml"

        if pyproject_path.exists():
            content = pyproject_path.read_text(encoding="utf-8")
            version_pattern = r'^version\s*=\s*["\']([^"\']+)["\']'
            for line in content.splitlines():
                match = re.match(version_pattern, line.strip())
                if match:
                    return match.group(1)

    except (FileNotFoundError, PermissionError, OSError, UnicodeDecodeError):
        pass

    # 最后的备用方案：从已安装的包中获取版本
    for package_name in ("document-reader", "mcp-data-extractor"):
        try:
            return importlib.metadata.version(package_name)
        except importlib.metadata.PackageNotFoundError:
            continue

    return "0.0.0"


__version__ = _get_version_from_pyproject()
__app_name__ = "document-reader"
__author__ = "Aurelius"
__email__ = "aureliusshu@gmail.com"

__all__ = [
    "__version__",
    "__app_name__",
]
