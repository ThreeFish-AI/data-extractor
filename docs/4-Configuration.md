---
id: configuration
sidebar_position: 4
title: Configuration
description: Configuration System Guide
last_update:
  author: Aurelius
  date: 2026-03-22
tags:
  - Configuration
  - Settings
  - Environment
---

## 配置系统架构

Negentropy Perceives 采用基于 [pydantic-settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/) 的分层配置系统，按优先级从高到低：

1. **运行时参数** - 函数调用时直接传递（详见[用户指南 - 数据提取配置](./6-User-Guide.md)）
2. **环境变量** - `NEGENTROPY_PERCEIVES_` 前缀的环境变量
3. **环境文件** - `.env` 系列文件
4. **默认配置** - [`NegentropyPerceivesSettings`](../negentropy/perceives/config.py) 中定义的默认值

## 环境变量配置

所有环境变量统一使用 `NEGENTROPY_PERCEIVES_` 前缀，由 Pydantic 自动完成类型转换与校验。

### 服务标识

| 环境变量 | 类型 | 默认值 | 约束 | 说明 |
| --- | --- | --- | --- | --- |
| `NEGENTROPY_PERCEIVES_SERVER_NAME` | `str` | `negentropy-perceives` | - | 服务器标识名称 |
| `NEGENTROPY_PERCEIVES_SERVER_VERSION` | `str` | 自动读取 | - | 版本号（从 `pyproject.toml` 自动获取） |

### 传输层

| 环境变量 | 类型 | 默认值 | 约束 | 说明 |
| --- | --- | --- | --- | --- |
| `NEGENTROPY_PERCEIVES_TRANSPORT_MODE` | `str` | `http` | `stdio` / `http` / `sse` | MCP 传输协议模式 |
| `NEGENTROPY_PERCEIVES_HTTP_HOST` | `str` | `localhost` | - | HTTP 服务器绑定主机 |
| `NEGENTROPY_PERCEIVES_HTTP_PORT` | `int` | `8081` | - | HTTP 服务器端口 |
| `NEGENTROPY_PERCEIVES_HTTP_PATH` | `str` | `/mcp` | - | HTTP 端点路径 |
| `NEGENTROPY_PERCEIVES_HTTP_CORS_ORIGINS` | `str?` | `*` | - | CORS 来源白名单（`null` 禁用） |

### 抓取引擎

| 环境变量 | 类型 | 默认值 | 约束 | 说明 |
| --- | --- | --- | --- | --- |
| `NEGENTROPY_PERCEIVES_CONCURRENT_REQUESTS` | `int` | `16` | `> 0` | 并发请求数 |
| `NEGENTROPY_PERCEIVES_DOWNLOAD_DELAY` | `float` | `1.0` | `>= 0` | 下载间隔（秒） |
| `NEGENTROPY_PERCEIVES_RANDOMIZE_DOWNLOAD_DELAY` | `bool` | `true` | - | 随机化下载间隔 |
| `NEGENTROPY_PERCEIVES_AUTOTHROTTLE_ENABLED` | `bool` | `true` | - | 启用自动节流 |
| `NEGENTROPY_PERCEIVES_AUTOTHROTTLE_START_DELAY` | `float` | `1.0` | `>= 0` | 自动节流初始延迟（秒） |
| `NEGENTROPY_PERCEIVES_AUTOTHROTTLE_MAX_DELAY` | `float` | `60.0` | `>= 0` | 自动节流最大延迟（秒） |
| `NEGENTROPY_PERCEIVES_AUTOTHROTTLE_TARGET_CONCURRENCY` | `float` | `1.0` | `>= 0` | 自动节流目标并发度 |

### 速率限制

| 环境变量 | 类型 | 默认值 | 约束 | 说明 |
| --- | --- | --- | --- | --- |
| `NEGENTROPY_PERCEIVES_RATE_LIMIT_REQUESTS_PER_MINUTE` | `int` | `60` | `>= 1` | 每分钟请求频率上限 |

### 重试策略

| 环境变量 | 类型 | 默认值 | 约束 | 说明 |
| --- | --- | --- | --- | --- |
| `NEGENTROPY_PERCEIVES_MAX_RETRIES` | `int` | `3` | `>= 0` | 失败重试最大次数 |
| `NEGENTROPY_PERCEIVES_RETRY_DELAY` | `float` | `1.0` | `>= 0` | 重试间隔（秒） |

### 缓存系统

| 环境变量 | 类型 | 默认值 | 约束 | 说明 |
| --- | --- | --- | --- | --- |
| `NEGENTROPY_PERCEIVES_ENABLE_CACHING` | `bool` | `true` | - | 启用响应缓存 |
| `NEGENTROPY_PERCEIVES_CACHE_TTL_HOURS` | `int` | `24` | `> 0` | 缓存生存时间（小时） |
| `NEGENTROPY_PERCEIVES_CACHE_MAX_SIZE` | `int?` | `null` | - | 缓存最大条目数（`null` 不限） |

### 日志系统

| 环境变量 | 类型 | 默认值 | 约束 | 说明 |
| --- | --- | --- | --- | --- |
| `NEGENTROPY_PERCEIVES_LOG_LEVEL` | `str` | `INFO` | `DEBUG` / `INFO` / `WARNING` / `ERROR` / `CRITICAL` | 日志记录级别 |
| `NEGENTROPY_PERCEIVES_LOG_REQUESTS` | `bool?` | `null` | - | 记录请求详情 |
| `NEGENTROPY_PERCEIVES_LOG_RESPONSES` | `bool?` | `null` | - | 记录响应详情 |

### 浏览器引擎

| 环境变量 | 类型 | 默认值 | 约束 | 说明 |
| --- | --- | --- | --- | --- |
| `NEGENTROPY_PERCEIVES_ENABLE_JAVASCRIPT` | `bool` | `false` | - | 启用 JavaScript 执行 |
| `NEGENTROPY_PERCEIVES_BROWSER_HEADLESS` | `bool` | `true` | - | 无头浏览器模式 |
| `NEGENTROPY_PERCEIVES_BROWSER_TIMEOUT` | `int` | `30` | `>= 0` | 浏览器操作超时（秒） |
| `NEGENTROPY_PERCEIVES_BROWSER_WINDOW_SIZE` | `str` | `1920x1080` | - | 浏览器窗口尺寸 |

### 用户代理

| 环境变量 | 类型 | 默认值 | 约束 | 说明 |
| --- | --- | --- | --- | --- |
| `NEGENTROPY_PERCEIVES_USE_RANDOM_USER_AGENT` | `bool` | `true` | - | 启用随机 User-Agent 轮换 |
| `NEGENTROPY_PERCEIVES_DEFAULT_USER_AGENT` | `str` | Chrome 120 UA | - | 默认 User-Agent 字符串 |

### 代理服务

| 环境变量 | 类型 | 默认值 | 约束 | 说明 |
| --- | --- | --- | --- | --- |
| `NEGENTROPY_PERCEIVES_USE_PROXY` | `bool` | `false` | - | 启用代理服务器 |
| `NEGENTROPY_PERCEIVES_PROXY_URL` | `str?` | `null` | - | 代理服务器 URL（启用代理时必填） |

### 请求设置

| 环境变量 | 类型 | 默认值 | 约束 | 说明 |
| --- | --- | --- | --- | --- |
| `NEGENTROPY_PERCEIVES_REQUEST_TIMEOUT` | `float` | `30.0` | `> 0` | HTTP 请求超时（秒） |

### LLM 编排（Smart 模式）

`method="smart"` 使用 LLM 编排多引擎并行处理 PDF。需安装可选依赖 `litellm`（`uv pip install litellm`）。

| 环境变量 | 类型 | 默认值 | 约束 | 说明 |
| --- | --- | --- | --- | --- |
| `NEGENTROPY_PERCEIVES_LLM_API_KEY` | `str?` | `null` | - | LLM API Key（ZhipuAI），也可通过 `ZHIPU_API_KEY` 设置 |
| `NEGENTROPY_PERCEIVES_LLM_MODEL` | `str` | `zhipu/glm-5-plus-250414` | - | LiteLLM 模型标识 |
| `NEGENTROPY_PERCEIVES_LLM_TEMPERATURE` | `float` | `0.1` | `0.0 ~ 2.0` | LLM 温度参数 |
| `NEGENTROPY_PERCEIVES_LLM_MAX_TOKENS` | `int` | `4096` | `> 0` | LLM 最大输出 token |
| `NEGENTROPY_PERCEIVES_LLM_TIMEOUT` | `float` | `60.0` | `> 0` | LLM API 超时（秒） |
| `NEGENTROPY_PERCEIVES_LLM_MAX_RETRIES` | `int` | `2` | `>= 0` | LLM API 重试次数 |

### 硬件加速

| 环境变量 | 类型 | 默认值 | 约束 | 说明 |
| --- | --- | --- | --- | --- |
| `NEGENTROPY_PERCEIVES_ACCELERATOR_DEVICE` | `str` | `auto` | `auto` / `cpu` / `cuda` / `mps` / `xpu` | 推理设备选择，按运行环境自动或显式指定 |
| `NEGENTROPY_PERCEIVES_ACCELERATOR_NUM_THREADS` | `int` | `4` | `>= 1` | CPU 推理线程数 |

### Docling PDF 引擎

| 环境变量 | 类型 | 默认值 | 约束 | 说明 |
| --- | --- | --- | --- | --- |
| `NEGENTROPY_PERCEIVES_DOCLING_ENABLED` | `bool` | `false` | - | 启用 Docling 作为可选 PDF 提取引擎 |
| `NEGENTROPY_PERCEIVES_DOCLING_OCR_ENABLED` | `bool` | `true` | - | 为扫描版 PDF 启用 OCR |
| `NEGENTROPY_PERCEIVES_DOCLING_TABLE_EXTRACTION_ENABLED` | `bool` | `true` | - | 启用 Docling 高级表格提取 |
| `NEGENTROPY_PERCEIVES_DOCLING_FORMULA_EXTRACTION_ENABLED` | `bool` | `true` | - | 启用 Docling 数学公式提取 |

## 配置验证规则

### 字段验证器

系统内置两个 `@field_validator`，在加载时自动规范化输入：

- **`log_level`** — 自动转为大写，仅接受 `DEBUG`、`INFO`、`WARNING`、`ERROR`、`CRITICAL`
- **`transport_mode`** — 自动转为小写，仅接受 `stdio`、`http`、`sse`

### 配置不可变性

全局实例 `settings` 通过 `frozen=True` 配置为不可变对象，创建后不可修改，保障运行时配置一致性。

### Scrapy 设置映射

`get_scrapy_settings()` 方法将抓取引擎配置映射为 Scrapy 原生设置字典，供 Scrapy 框架直接消费。

## 环境配置模板

### 开发环境

```bash
# .env.development
NEGENTROPY_PERCEIVES_TRANSPORT_MODE=stdio
NEGENTROPY_PERCEIVES_LOG_LEVEL=DEBUG
NEGENTROPY_PERCEIVES_ENABLE_JAVASCRIPT=true
NEGENTROPY_PERCEIVES_BROWSER_HEADLESS=false
NEGENTROPY_PERCEIVES_CONCURRENT_REQUESTS=4
NEGENTROPY_PERCEIVES_CACHE_TTL_HOURS=1
```

### 生产环境

```bash
# .env.production
NEGENTROPY_PERCEIVES_TRANSPORT_MODE=http
NEGENTROPY_PERCEIVES_HTTP_HOST=0.0.0.0
NEGENTROPY_PERCEIVES_HTTP_PORT=8081
NEGENTROPY_PERCEIVES_LOG_LEVEL=INFO
NEGENTROPY_PERCEIVES_ENABLE_JAVASCRIPT=true
NEGENTROPY_PERCEIVES_BROWSER_HEADLESS=true
NEGENTROPY_PERCEIVES_CONCURRENT_REQUESTS=32
NEGENTROPY_PERCEIVES_CACHE_TTL_HOURS=72
NEGENTROPY_PERCEIVES_USE_RANDOM_USER_AGENT=true
```

## 配置管理最佳实践

- `.env` — 本地开发配置（不纳入版本控制，权限 `600`）
- `.env.example` — 配置模板（纳入版本控制）
- `.env.development` / `.env.production` — 环境专用配置
- 启用代理时务必同时配置 `PROXY_URL`，否则启动验证将报错

## 故障诊断

```bash
# 查看所有 Negentropy Perceives 环境变量
env | grep NEGENTROPY_PERCEIVES_

# 检查配置文件
cat .env
```

**常见问题**：环境变量未生效时，先确认执行的是 `negentropy-perceives` 而不是旧入口残留；再检查 `.env` 是否位于当前工作目录，并使用 `uv run python -c "from negentropy.perceives.config import settings; print(settings.model_dump())"` 验证最终配置。

---

更多配置详情请参考 [`.env.example`](../.env.example) 和 [`negentropy/perceives/config.py`](../negentropy/perceives/config.py)。
