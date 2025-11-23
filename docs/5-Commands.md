---
id: commands
sidebar_position: 5
title: 常用 Commands
description: 常用指令
last_update:
  author: Aurelius
  date: 2025-11-22
tags:
  - Commands
---

## 🚀 环境设置和安装

### 快速初始化

```bash
# 使用提供的脚本快速设置（推荐）
./scripts/setup.sh

# 检查 Python 版本（需要 3.12+）
python --version

# 检查 uv 是否安装
uv --version
```

### 手动环境配置

```bash
# 同步项目依赖
uv sync

# 安装开发依赖
uv sync --extra dev

# 复制环境配置文件
cp .env.example .env

# 安装 Playwright 浏览器依赖
uv run playwright install chromium
```

## 🖥️ 服务器启动和管理

### 基本启动命令

```bash
# 启动 MCP 服务器（主要命令）
uv run data-extractor

# 作为 Python 模块运行
uv run python -m extractor.server

# 带环境变量启动
uv run --env DATA_EXTRACTOR_ENABLE_JAVASCRIPT=true data-extractor
```

### 开发模式启动

```bash
# 启用调试模式
uv run --env DATA_EXTRACTOR_DEBUG=true data-extractor

# 启用所有功能特性
uv run --env DATA_EXTRACTOR_ENABLE_JAVASCRIPT=true \
          --env DATA_EXTRACTOR_USE_RANDOM_USER_AGENT=true \
          data-extractor
```

## 🔍 代码质量检查

### Ruff 代码格式化和检查

```bash
# 代码格式化
uv run ruff format extractor/ examples/ tests/

# 代码检查
uv run ruff check extractor/ examples/ tests/

# 代码检查并自动修复
uv run ruff check --fix extractor/ examples/ tests/

# 查看检查规则
uv run ruff rule --all
```

### MyPy 类型检查

```bash
# 类型检查
uv run mypy extractor/

# 类型检查并显示详细错误
uv run mypy extractor/ --show-error-codes

# 生成类型检查报告
uv run mypy extractor/ --html-report mypy-report
```

## 🧪 测试执行

### 使用测试脚本（推荐）

```bash
# 运行完整测试套件
./scripts/run-tests.sh

# 运行单元测试
./scripts/run-tests.sh unit

# 运行集成测试
./scripts/run-tests.sh integration

# 运行快速测试（排除慢速测试）
./scripts/run-tests.sh quick

# 运行性能测试
./scripts/run-tests.sh performance

# 清理测试结果
./scripts/run-tests.sh clean

# 生成覆盖率报告
./scripts/run-tests.sh coverage
```

### 手动测试命令

```bash
# 运行所有测试
uv run pytest

# 运行测试并生成覆盖率报告
uv run pytest --cov=extractor --cov-report=html

# 运行特定测试文件
uv run pytest tests/unit/test_config.py

# 运行带标记的测试
uv run pytest -m "unit"           # 单元测试
uv run pytest -m "integration"    # 集成测试
uv run pytest -m "not slow"       # 排除慢速测试

# 并行运行测试
uv run pytest -n auto

# 运行测试并生成 JSON 报告
uv run pytest --json-report --json-report-file=test-results.json
```

## 📦 依赖管理

### 依赖操作

```bash
# 添加生产依赖
uv add <package-name>

# 添加开发依赖
uv add --dev <package-name>

# 移除依赖
uv remove <package-name>

# 更新依赖
uv lock --upgrade

# 检查过时的依赖
uv tree --outdated
```

### 依赖信息查看

```bash
# 查看依赖树
uv tree

# 查看已安装的包
uv list

# 查看包信息
uv pip show <package-name>
```

## 🔧 项目管理和维护

### 版本管理

```bash
# 更新版本号到所有相关文件
./scripts/update_version.py

# 查看当前版本
uv run python -c "from extractor import __version__; print(__version__)"
```

### 缓存管理

```bash
# 清理 uv 缓存
uv cache clean

# 清理 pip 缓存
uv pip cache purge

# 清理 Python 字节码
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete
```

## 📊 构建和发布

### 项目构建

```bash
# 构建分发包
uv build

# 检查包的完整性
twine check dist/*

# 本地安装测试
uv pip install -e .
```

### 发布准备

```bash
# 更新 CHANGELOG
# 手动编辑 CHANGELOG.md

# 创建 git 标签
git tag v<version-number>

# 推送标签到远程
git push origin v<version-number>
```

## 🔍 调试和诊断

```bash
# 检查环境变量
printenv | grep DATA_EXTRACTOR

# 验证配置文件
uv run python -c "from extractor.config import settings; print(settings.model_dump())"

# 测试导入
uv run python -c "import extractor; print('Import successful')"

# 检查 MCP 工具列表
uv run python -c "from extractor.server import app; print([tool.name for tool in app.tools])"
```
