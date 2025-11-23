---
id: configuration
sidebar_position: 3
title: Configuration
description: Configuration System Design and Reference
last_update:
  author: Aurelius
  date: 2025-11-23
tags:
  - Configuration
  - Settings
  - Environment
  - Deployment
---

## 概述

Data Extractor 采用基于 Pydantic Settings 的现代化配置系统，通过分层配置架构实现灵活的环境管理和参数配置。系统支持环境变量自动映射、配置验证、动态版本管理等多种高级功能，确保在不同部署环境下的稳定性和可维护性。

## 配置架构设计

### 分层配置模型

```
┌─────────────────────────────────────────────────────────────┐
│                    运行时参数 (Runtime Parameters)          │
│                   函数调用时传递的动态参数                   │
├─────────────────────────────────────────────────────────────┤
│                  环境变量 (Environment Variables)           │
│              DATA_EXTRACTOR_ 前缀的环境变量配置              │
├─────────────────────────────────────────────────────────────┤
│                  环境文件 (.env)                           │
│                   项目根目录的环境配置文件                   │
├─────────────────────────────────────────────────────────────┤
│                  默认配置 (Default Values)                 │
│                   代码中定义的默认配置值                     │
└─────────────────────────────────────────────────────────────┘
```

### 配置优先级

配置加载遵循以下优先级顺序（从高到低）：

1. **运行时参数** - 函数调用时直接传递的参数
2. **环境变量** - `DATA_EXTRACTOR_` 前缀的环境变量
3. **环境文件** - `.env` 文件中定义的配置
4. **默认配置** - `DataExtractorSettings` 类中的默认值

## 核心配置模块

### 1. 配置系统架构 (`extractor/config.py`)

**设计模式**：Settings Pattern + Environment Variable Mapping

**核心特性**：

```python
class DataExtractorSettings(BaseSettings):
    """Settings for the Data Extractor MCP Server."""

    # 配置映射规则
    model_config = {
        "env_file": ".env",                          # 环境文件路径
        "env_file_encoding": "utf-8",                # 文件编码
        "extra": "ignore",                           # 忽略额外环境变量
        "env_prefix": "DATA_EXTRACTOR_",             # 环境变量前缀
        "env_ignore_empty": True,                    # 忽略空值环境变量
        "frozen": True,                              # 实例不可变性
    }
```

**动态版本管理**：

```python
def _get_dynamic_version():
    """从 pyproject.toml 动态读取版本号"""
    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent
    pyproject_path = project_root / "pyproject.toml"

    # 动态解析版本号，确保版本一致性
    if pyproject_path.exists():
        with open(pyproject_path, "r", encoding="utf-8") as f:
            content = f.read()
            for line in content.splitlines():
                if line.startswith('version = "') and line.endswith('"'):
                    return line.split('"')[1]
    return "0.0.0"
```

### 2. 配置分类体系

#### 服务器配置 (Server Settings)

| 配置项           | 类型 | 默认值             | 环境变量                        | 描述           |
| ---------------- | ---- | ------------------ | ------------------------------- | -------------- |
| `server_name`    | str  | `"data-extractor"` | `DATA_EXTRACTOR_SERVER_NAME`    | 服务器名称标识 |
| `server_version` | str  | 动态读取           | `DATA_EXTRACTOR_SERVER_VERSION` | 服务器版本号   |

#### 框架配置 (Framework Settings)

| 配置项                            | 类型  | 默认值 | 环境变量                                         | 描述             |
| --------------------------------- | ----- | ------ | ------------------------------------------------ | ---------------- |
| `concurrent_requests`             | int   | `16`   | `DATA_EXTRACTOR_CONCURRENT_REQUESTS`             | 并发请求数量     |
| `download_delay`                  | float | `1.0`  | `DATA_EXTRACTOR_DOWNLOAD_DELAY`                  | 下载延迟时间     |
| `randomize_download_delay`        | bool  | `true` | `DATA_EXTRACTOR_RANDOMIZE_DOWNLOAD_DELAY`        | 随机化下载延迟   |
| `autothrottle_enabled`            | bool  | `true` | `DATA_EXTRACTOR_AUTOTHROTTLE_ENABLED`            | 启用自动限流     |
| `autothrottle_start_delay`        | float | `1.0`  | `DATA_EXTRACTOR_AUTOTHROTTLE_START_DELAY`        | 自动限流起始延迟 |
| `autothrottle_max_delay`          | float | `60.0` | `DATA_EXTRACTOR_AUTOTHROTTLE_MAX_DELAY`          | 自动限流最大延迟 |
| `autothrottle_target_concurrency` | float | `1.0`  | `DATA_EXTRACTOR_AUTOTHROTTLE_TARGET_CONCURRENCY` | 目标并发数       |

#### 浏览器配置 (Browser Settings)

| 配置项                | 类型      | 默认值        | 环境变量                             | 描述                 |
| --------------------- | --------- | ------------- | ------------------------------------ | -------------------- |
| `enable_javascript`   | bool      | `false`       | `DATA_EXTRACTOR_ENABLE_JAVASCRIPT`   | 启用 JavaScript 执行 |
| `browser_headless`    | bool      | `true`        | `DATA_EXTRACTOR_BROWSER_HEADLESS`    | 无头浏览器模式       |
| `browser_timeout`     | int       | `30`          | `DATA_EXTRACTOR_BROWSER_TIMEOUT`     | 浏览器操作超时时间   |
| `browser_window_size` | str/tuple | `"1920x1080"` | `DATA_EXTRACTOR_BROWSER_WINDOW_SIZE` | 浏览器窗口尺寸       |

#### 反检测配置 (Anti-Detection Settings)

| 配置项                  | 类型 | 默认值    | 环境变量                               | 描述               |
| ----------------------- | ---- | --------- | -------------------------------------- | ------------------ |
| `use_random_user_agent` | bool | `true`    | `DATA_EXTRACTOR_USE_RANDOM_USER_AGENT` | 随机用户代理       |
| `default_user_agent`    | str  | Chrome UA | `DATA_EXTRACTOR_DEFAULT_USER_AGENT`    | 默认用户代理字符串 |

#### 代理配置 (Proxy Settings)

| 配置项      | 类型 | 默认值  | 环境变量                   | 描述           |
| ----------- | ---- | ------- | -------------------------- | -------------- |
| `use_proxy` | bool | `false` | `DATA_EXTRACTOR_USE_PROXY` | 启用代理       |
| `proxy_url` | str  | `None`  | `DATA_EXTRACTOR_PROXY_URL` | 代理服务器 URL |

#### 请求配置 (Request Settings)

| 配置项                           | 类型  | 默认值 | 环境变量                                        | 描述           |
| -------------------------------- | ----- | ------ | ----------------------------------------------- | -------------- |
| `max_retries`                    | int   | `3`    | `DATA_EXTRACTOR_MAX_RETRIES`                    | 最大重试次数   |
| `retry_delay`                    | float | `1.0`  | `DATA_EXTRACTOR_RETRY_DELAY`                    | 重试延迟时间   |
| `request_timeout`                | float | `30.0` | `DATA_EXTRACTOR_REQUEST_TIMEOUT`                | 请求超时时间   |
| `rate_limit_requests_per_minute` | int   | `60`   | `DATA_EXTRACTOR_RATE_LIMIT_REQUESTS_PER_MINUTE` | 每分钟请求限制 |

#### 缓存配置 (Cache Settings)

| 配置项            | 类型 | 默认值 | 环境变量                         | 描述           |
| ----------------- | ---- | ------ | -------------------------------- | -------------- |
| `enable_caching`  | bool | `true` | `DATA_EXTRACTOR_ENABLE_CACHING`  | 启用缓存机制   |
| `cache_ttl_hours` | int  | `24`   | `DATA_EXTRACTOR_CACHE_TTL_HOURS` | 缓存生存时间   |
| `cache_max_size`  | int  | `None` | `DATA_EXTRACTOR_CACHE_MAX_SIZE`  | 缓存最大条目数 |

#### 日志配置 (Logging Settings)

| 配置项          | 类型 | 默认值   | 环境变量                       | 描述         |
| --------------- | ---- | -------- | ------------------------------ | ------------ |
| `log_level`     | str  | `"INFO"` | `DATA_EXTRACTOR_LOG_LEVEL`     | 日志级别     |
| `log_requests`  | bool | `None`   | `DATA_EXTRACTOR_LOG_REQUESTS`  | 记录请求日志 |
| `log_responses` | bool | `None`   | `DATA_EXTRACTOR_LOG_RESPONSES` | 记录响应日志 |

### 3. 配置验证机制

**字段验证器**：

```python
@field_validator("log_level")
@classmethod
def validate_log_level(cls, v):
    """验证日志级别是否为标准值"""
    valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    if v.upper() not in valid_levels:
        raise ValueError(f"log_level must be one of: {valid_levels}")
    return v.upper()
```

**类型验证**：

- 使用 Pydantic Field 进行类型约束
- 支持 `gt`、`ge`、`lt`、`le` 等数值约束
- 自动类型转换和验证

### 4. Scrapy 集成配置

**配置适配器**：

```python
def get_scrapy_settings(self) -> Dict[str, Any]:
    """获取 Scrapy 特定的配置字典"""
    return {
        "CONCURRENT_REQUESTS": self.concurrent_requests,
        "DOWNLOAD_DELAY": self.download_delay,
        "RANDOMIZE_DOWNLOAD_DELAY": self.randomize_download_delay,
        "AUTOTHROTTLE_ENABLED": self.autothrottle_enabled,
        "AUTOTHROTTLE_START_DELAY": self.autothrottle_start_delay,
        "AUTOTHROTTLE_MAX_DELAY": self.autothrottle_max_delay,
        "AUTOTHROTTLE_TARGET_CONCURRENCY": self.autothrottle_target_concurrency,
        "RETRY_TIMES": self.max_retries,
        "DOWNLOAD_TIMEOUT": self.request_timeout,
        "USER_AGENT": self.default_user_agent,
    }
```

## 环境配置参考

### 开发环境配置 (.env.development)

```bash
# Data Extractor Development Configuration
DATA_EXTRACTOR_SERVER_NAME=data-extractor-dev
DATA_EXTRACTOR_LOG_LEVEL=DEBUG
DATA_EXTRACTOR_LOG_REQUESTS=true
DATA_EXTRACTOR_LOG_RESPONSES=true

# 开发环境浏览器设置
DATA_EXTRACTOR_ENABLE_JAVASCRIPT=true
DATA_EXTRACTOR_BROWSER_HEADLESS=false
DATA_EXTRACTOR_BROWSER_TIMEOUT=60

# 开发环境并发限制
DATA_EXTRACTOR_CONCURRENT_REQUESTS=4
DATA_EXTRACTOR_RATE_LIMIT_REQUESTS_PER_MINUTE=30

# 开发环境缓存设置
DATA_EXTRACTOR_ENABLE_CACHING=true
DATA_EXTRACTOR_CACHE_TTL_HOURS=1
```

### 测试环境配置 (.env.test)

```bash
# Data Extractor Test Configuration
DATA_EXTRACTOR_SERVER_NAME=data-extractor-test
DATA_EXTRACTOR_LOG_LEVEL=WARNING
DATA_EXTRACTOR_LOG_REQUESTS=false
DATA_EXTRACTOR_LOG_RESPONSES=false

# 测试环境浏览器设置
DATA_EXTRACTOR_ENABLE_JAVASCRIPT=false
DATA_EXTRACTOR_BROWSER_HEADLESS=true
DATA_EXTRACTOR_BROWSER_TIMEOUT=10

# 测试环境并发限制
DATA_EXTRACTOR_CONCURRENT_REQUESTS=1
DATA_EXTRACTOR_RATE_LIMIT_REQUESTS_PER_MINUTE=10

# 测试环境缓存设置
DATA_EXTRACTOR_ENABLE_CACHING=false
```

### 生产环境配置 (.env.production)

```bash
# Data Extractor Production Configuration
DATA_EXTRACTOR_SERVER_NAME=data-extractor-prod
DATA_EXTRACTOR_LOG_LEVEL=INFO
DATA_EXTRACTOR_LOG_REQUESTS=false
DATA_EXTRACTOR_LOG_RESPONSES=false

# 生产环境浏览器设置
DATA_EXTRACTOR_ENABLE_JAVASCRIPT=true
DATA_EXTRACTOR_BROWSER_HEADLESS=true
DATA_EXTRACTOR_BROWSER_TIMEOUT=30

# 生产环境高并发设置
DATA_EXTRACTOR_CONCURRENT_REQUESTS=32
DATA_EXTRACTOR_RATE_LIMIT_REQUESTS_PER_MINUTE=120

# 生产环境缓存优化
DATA_EXTRACTOR_ENABLE_CACHING=true
DATA_EXTRACTOR_CACHE_TTL_HOURS=72
DATA_EXTRACTOR_CACHE_MAX_SIZE=10000

# 生产环境反检测设置
DATA_EXTRACTOR_USE_RANDOM_USER_AGENT=true
DATA_EXTRACTOR_USE_PROXY=true
DATA_EXTRACTOR_PROXY_URL=http://proxy-server:8080
```

## 配置最佳实践

### 1. 安全配置管理

**敏感信息处理**：

```bash
# ❌ 错误：硬编码敏感信息
DATA_EXTRACTOR_API_KEY=sk-1234567890abcdef

# ✅ 正确：使用环境变量
export DATA_EXTRACTOR_API_KEY=$(cat /path/to/secure/api_key)
```

**配置文件权限**：

```bash
# 设置 .env 文件权限仅限当前用户读写
chmod 600 .env
chmod 644 .env.example
```

### 2. 环境分离策略

**配置文件命名规范**：

- `.env` - 本地开发配置（不提交到版本控制）
- `.env.example` - 配置模板（提交到版本控制）
- `.env.development` - 开发环境配置
- `.env.staging` - 预发布环境配置
- `.env.production` - 生产环境配置

**Git 排除配置**：

```gitignore
# .gitignore
.env
.env.local
.env.*.local
```

### 3. 配置验证

**启动时验证**：

```python
# 在应用启动时验证关键配置
def validate_configuration():
    """验证配置的完整性和合理性"""
    if settings.enable_javascript and not settings.browser_timeout:
        raise ValueError("JavaScript enabled requires browser timeout")

    if settings.use_proxy and not settings.proxy_url:
        raise ValueError("Proxy enabled requires proxy URL")

    if settings.concurrent_requests > 100:
        logger.warning("High concurrent requests may cause rate limiting")
```

### 4. 配置监控

**配置变更追踪**：

```python
import logging

class ConfigMonitor:
    """配置变更监控器"""

    def __init__(self):
        self.original_config = settings.model_dump()

    def detect_changes(self):
        """检测配置变更"""
        current_config = settings.model_dump()
        changes = {}

        for key, original_value in self.original_config.items():
            current_value = current_config.get(key)
            if original_value != current_value:
                changes[key] = {
                    'from': original_value,
                    'to': current_value
                }

        if changes:
            logger.info(f"Configuration changes detected: {changes}")
```

## 工具配置文件

### 1. 测试配置 (pyproject.toml)

```toml
[tool.pytest.ini_options]
minversion = "8.0"
python_files = ["test_*.py", "*_test.py"]
testpaths = ["tests"]
addopts = [
    "-ra",
    "--strict-config",
    "--cov=extractor",
    "--cov-report=html:htmlcov",
    "--cov-report=term-missing",
]

markers = [
    "slow: marks tests as slow",
    "integration: marks tests as integration tests",
    "unit: marks tests as unit tests",
    "requires_network: marks tests that require network access",
    "requires_browser: marks tests that require browser setup"
]
```

### 2. 代码质量配置 (mypy.ini)

```ini
[mypy]
python_version = 3.12
warn_return_any = True
warn_unused_configs = True
disallow_untyped_defs = True

# 第三方库配置
[mypy-scrapy.*]
ignore_missing_imports = True

[mypy-selenium.*]
ignore_missing_imports = True

[mypy-fastmcp.*]
ignore_missing_imports = True
```

### 3. 依赖管理配置 (pyproject.toml)

```toml
[project]
dependencies = [
    "fastmcp>=2.11.0",
    "scrapy>=2.11.0",
    "pydantic>=2.8.0",
    "pydantic-settings>=2.0.0",
    "python-dotenv>=1.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.0",
    "mypy>=1.10.0",
    "pre-commit>=3.8.0",
]
```

## 配置系统扩展

### 1. 动态配置加载

```python
class DynamicConfigLoader:
    """动态配置加载器"""

    @staticmethod
    def load_from_database(config_table: str) -> Dict[str, Any]:
        """从数据库加载配置"""
        # 实现数据库配置加载逻辑
        pass

    @staticmethod
    def load_from_remote_config_service(url: str) -> Dict[str, Any]:
        """从远程配置服务加载"""
        # 实现远程配置加载逻辑
        pass

    @staticmethod
    def load_from_vault(secret_path: str) -> Dict[str, Any]:
        """从 Vault 加载敏感配置"""
        # 实现 Vault 配置加载逻辑
        pass
```

### 2. 配置热重载

```python
import asyncio
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class ConfigWatcher(FileSystemEventHandler):
    """配置文件监控器"""

    def on_modified(self, event):
        if event.src_path.endswith('.env'):
            logger.info("Configuration file changed, reloading...")
            # 重新加载配置
            asyncio.create_task(reload_configuration())
```

### 3. 配置模板系统

```python
from jinja2 import Template

class ConfigTemplate:
    """配置模板管理器"""

    @staticmethod
    def generate_config(template_name: str, context: Dict[str, Any]) -> str:
        """生成配置文件"""
        template_path = f"config/templates/{template_name}.j2"

        with open(template_path, 'r') as f:
            template = Template(f.read())

        return template.render(**context)
```

## 故障排除

### 常见配置问题

**问题 1：环境变量未生效**

```bash
# 检查环境变量是否正确设置
env | grep DATA_EXTRACTOR_

# 确认 .env 文件格式正确
cat .env
```

**问题 2：配置验证失败**

```python
# 查看详细的验证错误
try:
    config = DataExtractorSettings()
except ValidationError as e:
    print(f"Configuration validation failed: {e}")
```

**问题 3：类型转换错误**

```bash
# 确保环境变量类型正确
export DATA_EXTRACTOR_CONCURRENT_REQUESTS=16    # 数字，不是字符串 "16"
export DATA_EXTRACTOR_ENABLE_JAVASCRIPT=true    # 布尔值，小写
```

### 调试配置

**配置调试工具**：

```python
def debug_configuration():
    """调试配置信息"""
    print("=== Configuration Debug ===")
    print(f"Server Name: {settings.server_name}")
    print(f"Server Version: {settings.server_version}")
    print(f"Log Level: {settings.log_level}")
    print(f"JavaScript Enabled: {settings.enable_javascript}")
    print(f"Concurrent Requests: {settings.concurrent_requests}")
    print(f"Request Timeout: {settings.request_timeout}")

    # 显示所有配置项
    for field_name, field_value in settings.model_dump().items():
        print(f"{field_name}: {field_value}")
```

---

本配置系统文档涵盖了 Data Extractor 项目的完整配置设计方案，包括架构设计、配置分类、环境管理、最佳实践和故障排除指南，为项目的配置管理和部署提供详细的技术参考。
