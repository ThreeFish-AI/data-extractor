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

Data Extractor 采用基于 [pydantic-settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/) 的分层配置系统，按优先级从高到低：

1. **运行时参数** - 函数调用时直接传递（详见[用户指南 - 数据提取配置](./6-User-Guide.md)）
2. **环境变量** - `DATA_EXTRACTOR_` 前缀的环境变量
3. **环境文件** - `.env` 系列文件
4. **默认配置** - [`DataExtractorSettings`](../extractor/config.py) 中定义的默认值

## 环境变量配置

所有环境变量统一使用 `DATA_EXTRACTOR_` 前缀，由 Pydantic 自动完成类型转换与校验。

### 服务标识

| 环境变量 | 类型 | 默认值 | 约束 | 说明 |
| --- | --- | --- | --- | --- |
| `DATA_EXTRACTOR_SERVER_NAME` | `str` | `data-extractor` | - | 服务器标识名称 |
| `DATA_EXTRACTOR_SERVER_VERSION` | `str` | 自动读取 | - | 版本号（从 `pyproject.toml` 自动获取） |

### 传输层

| 环境变量 | 类型 | 默认值 | 约束 | 说明 |
| --- | --- | --- | --- | --- |
| `DATA_EXTRACTOR_TRANSPORT_MODE` | `str` | `http` | `stdio` / `http` / `sse` | MCP 传输协议模式 |
| `DATA_EXTRACTOR_HTTP_HOST` | `str` | `localhost` | - | HTTP 服务器绑定主机 |
| `DATA_EXTRACTOR_HTTP_PORT` | `int` | `8081` | - | HTTP 服务器端口 |
| `DATA_EXTRACTOR_HTTP_PATH` | `str` | `/mcp` | - | HTTP 端点路径 |
| `DATA_EXTRACTOR_HTTP_CORS_ORIGINS` | `str?` | `*` | - | CORS 来源白名单（`null` 禁用） |

### 抓取引擎

| 环境变量 | 类型 | 默认值 | 约束 | 说明 |
| --- | --- | --- | --- | --- |
| `DATA_EXTRACTOR_CONCURRENT_REQUESTS` | `int` | `16` | `> 0` | 并发请求数 |
| `DATA_EXTRACTOR_DOWNLOAD_DELAY` | `float` | `1.0` | `>= 0` | 下载间隔（秒） |
| `DATA_EXTRACTOR_RANDOMIZE_DOWNLOAD_DELAY` | `bool` | `true` | - | 随机化下载间隔 |
| `DATA_EXTRACTOR_AUTOTHROTTLE_ENABLED` | `bool` | `true` | - | 启用自动节流 |
| `DATA_EXTRACTOR_AUTOTHROTTLE_START_DELAY` | `float` | `1.0` | `>= 0` | 自动节流初始延迟（秒） |
| `DATA_EXTRACTOR_AUTOTHROTTLE_MAX_DELAY` | `float` | `60.0` | `>= 0` | 自动节流最大延迟（秒） |
| `DATA_EXTRACTOR_AUTOTHROTTLE_TARGET_CONCURRENCY` | `float` | `1.0` | `>= 0` | 自动节流目标并发度 |

### 速率限制

| 环境变量 | 类型 | 默认值 | 约束 | 说明 |
| --- | --- | --- | --- | --- |
| `DATA_EXTRACTOR_RATE_LIMIT_REQUESTS_PER_MINUTE` | `int` | `60` | `>= 1` | 每分钟请求频率上限 |

### 重试策略

| 环境变量 | 类型 | 默认值 | 约束 | 说明 |
| --- | --- | --- | --- | --- |
| `DATA_EXTRACTOR_MAX_RETRIES` | `int` | `3` | `>= 0` | 失败重试最大次数 |
| `DATA_EXTRACTOR_RETRY_DELAY` | `float` | `1.0` | `>= 0` | 重试间隔（秒） |

### 缓存系统

| 环境变量 | 类型 | 默认值 | 约束 | 说明 |
| --- | --- | --- | --- | --- |
| `DATA_EXTRACTOR_ENABLE_CACHING` | `bool` | `true` | - | 启用响应缓存 |
| `DATA_EXTRACTOR_CACHE_TTL_HOURS` | `int` | `24` | `> 0` | 缓存生存时间（小时） |
| `DATA_EXTRACTOR_CACHE_MAX_SIZE` | `int?` | `null` | - | 缓存最大条目数（`null` 不限） |

### 日志系统

| 环境变量 | 类型 | 默认值 | 约束 | 说明 |
| --- | --- | --- | --- | --- |
| `DATA_EXTRACTOR_LOG_LEVEL` | `str` | `INFO` | `DEBUG` / `INFO` / `WARNING` / `ERROR` / `CRITICAL` | 日志记录级别 |
| `DATA_EXTRACTOR_LOG_REQUESTS` | `bool?` | `null` | - | 记录请求详情 |
| `DATA_EXTRACTOR_LOG_RESPONSES` | `bool?` | `null` | - | 记录响应详情 |

### 浏览器引擎

| 环境变量 | 类型 | 默认值 | 约束 | 说明 |
| --- | --- | --- | --- | --- |
| `DATA_EXTRACTOR_ENABLE_JAVASCRIPT` | `bool` | `false` | - | 启用 JavaScript 执行 |
| `DATA_EXTRACTOR_BROWSER_HEADLESS` | `bool` | `true` | - | 无头浏览器模式 |
| `DATA_EXTRACTOR_BROWSER_TIMEOUT` | `int` | `30` | `>= 0` | 浏览器操作超时（秒） |
| `DATA_EXTRACTOR_BROWSER_WINDOW_SIZE` | `str` | `1920x1080` | - | 浏览器窗口尺寸 |

### 用户代理

| 环境变量 | 类型 | 默认值 | 约束 | 说明 |
| --- | --- | --- | --- | --- |
| `DATA_EXTRACTOR_USE_RANDOM_USER_AGENT` | `bool` | `true` | - | 启用随机 User-Agent 轮换 |
| `DATA_EXTRACTOR_DEFAULT_USER_AGENT` | `str` | Chrome 120 UA | - | 默认 User-Agent 字符串 |

### 代理服务

| 环境变量 | 类型 | 默认值 | 约束 | 说明 |
| --- | --- | --- | --- | --- |
| `DATA_EXTRACTOR_USE_PROXY` | `bool` | `false` | - | 启用代理服务器 |
| `DATA_EXTRACTOR_PROXY_URL` | `str?` | `null` | - | 代理服务器 URL（启用代理时必填） |

### 请求设置

| 环境变量 | 类型 | 默认值 | 约束 | 说明 |
| --- | --- | --- | --- | --- |
| `DATA_EXTRACTOR_REQUEST_TIMEOUT` | `float` | `30.0` | `> 0` | HTTP 请求超时（秒） |

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
DATA_EXTRACTOR_TRANSPORT_MODE=stdio
DATA_EXTRACTOR_LOG_LEVEL=DEBUG
DATA_EXTRACTOR_ENABLE_JAVASCRIPT=true
DATA_EXTRACTOR_BROWSER_HEADLESS=false
DATA_EXTRACTOR_CONCURRENT_REQUESTS=4
DATA_EXTRACTOR_CACHE_TTL_HOURS=1
```

### 生产环境

```bash
# .env.production
DATA_EXTRACTOR_TRANSPORT_MODE=http
DATA_EXTRACTOR_HTTP_HOST=0.0.0.0
DATA_EXTRACTOR_HTTP_PORT=8081
DATA_EXTRACTOR_LOG_LEVEL=INFO
DATA_EXTRACTOR_ENABLE_JAVASCRIPT=true
DATA_EXTRACTOR_BROWSER_HEADLESS=true
DATA_EXTRACTOR_CONCURRENT_REQUESTS=32
DATA_EXTRACTOR_CACHE_TTL_HOURS=72
DATA_EXTRACTOR_USE_RANDOM_USER_AGENT=true
```

## 配置管理最佳实践

- `.env` — 本地开发配置（不纳入版本控制，权限 `600`）
- `.env.example` — 配置模板（纳入版本控制）
- `.env.development` / `.env.production` — 环境专用配置
- 启用代理时务必同时配置 `PROXY_URL`，否则启动验证将报错

## 故障诊断

```bash
# 查看所有 Data Extractor 环境变量
env | grep DATA_EXTRACTOR_

# 检查配置文件
cat .env
```

**常见问题**：环境变量未生效（检查 `DATA_EXTRACTOR_` 前缀）、类型转换错误（确认数值/布尔值格式）、配置验证失败（查看错误信息中的约束提示）。

---

更多配置详情请参考 [`.env.example`](../.env.example) 和 [`extractor/config.py`](../extractor/config.py)。
