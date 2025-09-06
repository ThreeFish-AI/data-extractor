#!/usr/bin/env python3
"""
版本号统一更新脚本
从 pyproject.toml 读取版本号，更新所有相关文件
"""

import sys
from pathlib import Path


def get_version_from_pyproject(project_root: Path) -> str:
    """从 pyproject.toml 读取版本号"""
    pyproject_path = project_root / "pyproject.toml"
    if not pyproject_path.exists():
        raise FileNotFoundError(f"pyproject.toml not found at {pyproject_path}")

    content = pyproject_path.read_text(encoding="utf-8")
    for line in content.splitlines():
        line = line.strip()
        if line.startswith('version = "') and line.endswith('"'):
            return line.split('"')[1]

    raise ValueError("Version not found in pyproject.toml")


def update_file_version(file_path: Path, old_version: str, new_version: str) -> bool:
    """更新文件中的版本号"""
    if not file_path.exists():
        print(f"警告: {file_path} 不存在，跳过")
        return False

    content = file_path.read_text(encoding="utf-8")
    updated_content = content.replace(old_version, new_version)

    if content != updated_content:
        file_path.write_text(updated_content, encoding="utf-8")
        print(f"已更新: {file_path}")
        return True
    else:
        print(f"无需更新: {file_path}")
        return False


def main():
    """主函数"""
    project_root = Path(__file__).parent.parent

    try:
        # 读取当前版本
        current_version = get_version_from_pyproject(project_root)
        print(f"从 pyproject.toml 读取到版本号: {current_version}")

        # 定义需要更新的文件和旧版本模式
        files_to_update = [
            # 文档文件
            (project_root / "README.md", ["0.0.0", "v0.0.0"]),
            (project_root / "TEST_RESULTS.md", ["0.0.0", "v0.0.0"]),
            (project_root / ".env.example", ["0.0.0"]),
            # 代码文件 - 但这些现在应该动态读取，所以可能不需要更新
        ]

        updated_count = 0

        for file_path, old_versions in files_to_update:
            for old_version in old_versions:
                if update_file_version(file_path, old_version, current_version):
                    updated_count += 1

        print(f"\n总计更新了 {updated_count} 个文件")

        # 特殊处理：更新 __init__.py 中的版本号（如果需要手动更新）
        init_file = project_root / "extractor" / "__init__.py"
        if init_file.exists():
            content = init_file.read_text(encoding="utf-8")
            # 检查是否使用动态版本读取
            if "_get_version_from_pyproject" in content:
                print(f"✅ {init_file} 已使用动态版本读取")
            else:
                print(f"⚠️ {init_file} 未使用动态版本读取，建议检查")

    except Exception as e:
        print(f"错误: {e}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
