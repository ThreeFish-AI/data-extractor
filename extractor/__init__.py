"""Data Extractor MCP Server - A robust web scraping MCP server."""

import re
from pathlib import Path


def _get_version_from_pyproject():
    """从 pyproject.toml 动态读取版本号，支持多种部署场景"""
    try:
        # 方法1: 从当前文件位置向上查找
        current_file = Path(__file__).resolve()
        project_root = current_file.parent.parent
        pyproject_path = project_root / "pyproject.toml"

        # 方法2: 从当前工作目录查找
        if not pyproject_path.exists():
            pyproject_path = Path.cwd() / "pyproject.toml"

        # 方法3: 从模块根目录查找
        if not pyproject_path.exists():
            import extractor

            module_path = Path(extractor.__file__).parent
            pyproject_path = module_path.parent / "pyproject.toml"

        if pyproject_path.exists():
            with open(pyproject_path, "r", encoding="utf-8") as f:
                content = f.read()

                # 正则匹配 version 行
                version_pattern = r'^version\s*=\s*["\']([^"\']+)["\']'
                for line in content.splitlines():
                    match = re.match(version_pattern, line.strip())
                    if match:
                        return match.group(1)

                # 备用：查找 [project] 段下的 version
                project_section = False
                for line in content.splitlines():
                    stripped = line.strip()
                    if stripped == "[project]":
                        project_section = True
                    elif stripped.startswith("[") and stripped != "[project]":
                        project_section = False
                    elif project_section and stripped.startswith("version ="):
                        version_match = re.search(r'["\']([^"\']+)["\']', stripped)
                        if version_match:
                            return version_match.group(1)

    except (
        FileNotFoundError,
        PermissionError,
        OSError,
        UnicodeDecodeError,
        ImportError,
    ):
        pass

    # 最后的备用方案：从已安装的包中获取版本
    try:
        import importlib.metadata

        return importlib.metadata.version("mcp-data-extractor")
    except (importlib.metadata.PackageNotFoundError, ImportError):
        pass

    return "0.0.0"


__version__ = _get_version_from_pyproject()
__author__ = "Aurelius"
__email__ = "aureliusshu@gmail.com"
