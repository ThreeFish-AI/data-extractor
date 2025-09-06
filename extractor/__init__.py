"""Data Extractor MCP Server - A robust web scraping MCP server."""

from pathlib import Path


def _get_version_from_pyproject():
    """从 pyproject.toml 中动态读取版本号"""
    try:
        # 找到项目根目录下的 pyproject.toml
        current_file = Path(__file__).resolve()
        project_root = (
            current_file.parent.parent
        )  # extractor/__init__.py -> project_root
        pyproject_path = project_root / "pyproject.toml"

        if pyproject_path.exists():
            with open(pyproject_path, "r", encoding="utf-8") as f:
                content = f.read()
                # 简单解析 version = "x.y.z" 行
                for line in content.splitlines():
                    line = line.strip()
                    if line.startswith('version = "') and line.endswith('"'):
                        return line.split('"')[1]
    except Exception:
        pass

    # 如果读取失败，使用备用版本号
    return "0.0.0"


__version__ = _get_version_from_pyproject()
__author__ = "Aurelius"
__email__ = "aureliusshu@gmail.com"
