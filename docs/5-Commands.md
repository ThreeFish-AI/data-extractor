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

## 环境设置与安装

### 快速环境初始化

```bash
# 使用提供的脚本快速设置（推荐方式）
./scripts/setup.sh

# 检查 Python 版本要求（需要 3.12+）
python --version

# 验证 uv 包管理器安装状态
uv --version
```

### 手动环境配置

```bash
# 同步项目依赖到虚拟环境
uv sync

# 安装包含开发依赖的完整环境
uv sync --extra dev

# 创建环境配置文件
cp .env.example .env

# 安装 Playwright 浏览器依赖
uv run playwright install chromium
```

## 服务器启动与管理

### 基本服务器启动

```bash
# 启动 MCP 服务器（主要启动命令）
uv run data-extractor

# 以 Python 模块方式运行服务器
uv run python -m extractor.server

# 带环境变量配置启动服务器
uv run --env DATA_EXTRACTOR_ENABLE_JAVASCRIPT=true data-extractor
```

### 开发环境启动配置

```bash
# 启用调试模式的详细日志输出
uv run --env DATA_EXTRACTOR_DEBUG=true data-extractor

# 启用完整功能特性的开发配置
uv run --env DATA_EXTRACTOR_ENABLE_JAVASCRIPT=true \
          --env DATA_EXTRACTOR_USE_RANDOM_USER_AGENT=true \
          data-extractor
```

## 代码质量检查

### Ruff 代码格式化与检查

```bash
# 格式化项目代码
uv run ruff format extractor/ examples/ tests/

# 执行代码静态检查
uv run ruff check extractor/ examples/ tests/

# 检查并自动修复可修复的问题
uv run ruff check --fix extractor/ examples/ tests/

# 查看所有可用的检查规则
uv run ruff rule --all
```

### MyPy 类型检查工具

```bash
# 执行类型检查
uv run mypy extractor/

# 显示详细的错误代码信息
uv run mypy extractor/ --show-error-codes

# 生成 HTML 格式的类型检查报告
uv run mypy extractor/ --html-report mypy-report
```

## 测试执行与管理

### 使用测试脚本执行（推荐）

```bash
# 运行完整的项目测试套件
./scripts/run-tests.sh

# 运行单元测试集合
./scripts/run-tests.sh unit

# 运行集成测试集合
./scripts/run-tests.sh integration

# 运行快速测试（排除慢速测试用例）
./scripts/run-tests.sh quick

# 运行性能基准测试
./scripts/run-tests.sh performance

# 清理测试结果和临时文件
./scripts/run-tests.sh clean

# 生成代码覆盖率报告
./scripts/run-tests.sh coverage
```

### 手动测试命令执行

```bash
# 运行所有测试用例
uv run pytest

# 运行测试并生成 HTML 覆盖率报告
uv run pytest --cov=extractor --cov-report=html

# 运行指定的测试文件
uv run pytest tests/unit/test_config.py

# 基于标记运行特定类型的测试
uv run pytest -m "unit"           # 单元测试标记
uv run pytest -m "integration"    # 集成测试标记
uv run pytest -m "not slow"       # 排除慢速测试标记

# 并行执行测试以提升速度
uv run pytest -n auto

# 生成 JSON 格式的测试结果报告
uv run pytest --json-report --json-report-file=test-results.json
```

## 项目依赖管理

### 依赖包操作管理

```bash
# 添加生产环境依赖包
uv add <package-name>

# 添加开发环境依赖包
uv add --dev <package-name>

# 移除不需要的依赖包
uv remove <package-name>

# 更新所有依赖到最新版本
uv lock --upgrade

# 检查项目中过时的依赖
uv tree --outdated
```

### 依赖信息查询

```bash
# 显示完整的依赖关系树
uv tree

# 列出当前虚拟环境中安装的所有包
uv list

# 显示特定包的详细信息
uv pip show <package-name>
```

## 项目维护与管理

### 版本控制管理

```bash
# 更新项目版本号到所有相关文件
./scripts/update_version.py

# 查看当前项目版本号
uv run python -c "from extractor import __version__; print(__version__)"
```

### 缓存清理管理

```bash
# 清理 uv 包管理器的缓存
uv cache clean

# 清理 pip 包管理器的缓存
uv pip cache purge

# 清理 Python 编译产生的字节码文件
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete
```

## 构建与发布流程

### 项目构建准备

```bash
# 构建项目分发包
uv build

# 检查分发包的完整性
twine check dist/*

# 本地安装测试构建的包
uv pip install -e .
```

### 发布准备工作

```bash
# 更新项目变更日志
# 手动编辑 CHANGELOG.md 文件

# 创建版本标签
git tag v<version-number>

# 推送标签到远程仓库
git push origin v<version-number>
```

## 系统调试与诊断

### 环境状态检查

```bash
# 检查 Data Extractor 相关的环境变量
printenv | grep DATA_EXTRACTOR

# 验证配置文件的正确性
uv run python -c "from extractor.config import settings; print(settings.model_dump())"

# 测试项目模块导入是否正常
uv run python -c "import extractor; print('Import successful')"

# 检查 MCP 服务器可用的工具列表
uv run python -c "from extractor.server import app; print([tool.name for tool in app.tools])"
```
