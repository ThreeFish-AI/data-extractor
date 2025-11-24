---
id: configuration
sidebar_position: 4
title: Configuration
description: Configuration System Guide
last_update:
  author: Aurelius
  date: 2025-11-23
tags:
  - Configuration
  - Settings
  - Environment
---

## 配置系统架构

Data Extractor 采用分层配置系统，按优先级从高到低依次为：

1. **运行时参数** - 函数调用时直接传递的参数
2. **环境变量** - `DATA_EXTRACTOR_` 前缀的环境变量
3. **环境文件** - `.env` 系列文件配置
4. **默认配置** - 代码中定义的默认值

## 运行时配置

### 数据提取配置

运行时参数具有最高优先级，支持灵活的 CSS 选择器和属性提取配置：

```python
# 简单选择器配置
extract_config = {"title": "h1"}

# 复杂选择器配置
extract_config = {
    "products": {
        "selector": ".product",
        "multiple": true,
        "attr": "text"
    },
    "images": {
        "selector": ".product-image img",
        "multiple": true,
        "attr": "src"
    }
}
```

**支持的属性类型**：

- `text` - 元素文本内容
- `href` - 链接地址
- `src` - 图片或资源地址
- 自定义属性 - 如 `data-id`、`class` 等

### 实际应用示例

```python
# MCP 工具调用中的配置使用
result = await scrape_webpage(
    url="https://example.com",
    extract_config={
        "title": "h1",
        "content": ".main-content p",
        "links": {"selector": "a", "multiple": true, "attr": "href"}
    }
)
```

## 环境变量配置

### 核心服务配置

| 环境变量                     | 默认值           | 说明           |
| ---------------------------- | ---------------- | -------------- |
| `DATA_EXTRACTOR_SERVER_NAME` | `data-extractor` | 服务器标识名称 |

### 性能优化配置

| 环境变量                                        | 默认值 | 说明               |
| ----------------------------------------------- | ------ | ------------------ |
| `DATA_EXTRACTOR_CONCURRENT_REQUESTS`            | `16`   | 并发请求处理数量   |
| `DATA_EXTRACTOR_RATE_LIMIT_REQUESTS_PER_MINUTE` | `60`   | 每分钟请求频率限制 |
| `DATA_EXTRACTOR_REQUEST_TIMEOUT`                | `30.0` | 请求超时时间（秒） |
| `DATA_EXTRACTOR_MAX_RETRIES`                    | `3`    | 失败重试最大次数   |

### 浏览器引擎配置

| 环境变量                           | 默认值  | 说明                     |
| ---------------------------------- | ------- | ------------------------ |
| `DATA_EXTRACTOR_ENABLE_JAVASCRIPT` | `false` | 是否启用 JavaScript 执行 |
| `DATA_EXTRACTOR_BROWSER_HEADLESS`  | `true`  | 是否使用无头浏览器模式   |
| `DATA_EXTRACTOR_BROWSER_TIMEOUT`   | `30`    | 浏览器操作超时时间       |

### 反检测机制配置

| 环境变量                               | 默认值  | 说明                 |
| -------------------------------------- | ------- | -------------------- |
| `DATA_EXTRACTOR_USE_RANDOM_USER_AGENT` | `true`  | 是否启用随机用户代理 |
| `DATA_EXTRACTOR_USE_PROXY`             | `false` | 是否启用代理服务器   |
| `DATA_EXTRACTOR_PROXY_URL`             | -       | 代理服务器地址 URL   |

### 缓存系统配置

| 环境变量                         | 默认值 | 说明                     |
| -------------------------------- | ------ | ------------------------ |
| `DATA_EXTRACTOR_ENABLE_CACHING`  | `true` | 是否启用缓存机制         |
| `DATA_EXTRACTOR_CACHE_TTL_HOURS` | `24`   | 缓存数据生存时间（小时） |

### 日志系统配置

| 环境变量                   | 默认值 | 说明         |
| -------------------------- | ------ | ------------ |
| `DATA_EXTRACTOR_LOG_LEVEL` | `INFO` | 日志记录级别 |

## 环境配置模板

### 开发环境配置

```bash
# .env.development
DATA_EXTRACTOR_LOG_LEVEL=DEBUG
DATA_EXTRACTOR_ENABLE_JAVASCRIPT=true
DATA_EXTRACTOR_BROWSER_HEADLESS=false
DATA_EXTRACTOR_CONCURRENT_REQUESTS=4
DATA_EXTRACTOR_CACHE_TTL_HOURS=1
```

### 生产环境配置

```bash
# .env.production
DATA_EXTRACTOR_LOG_LEVEL=INFO
DATA_EXTRACTOR_ENABLE_JAVASCRIPT=true
DATA_EXTRACTOR_BROWSER_HEADLESS=true
DATA_EXTRACTOR_CONCURRENT_REQUESTS=32
DATA_EXTRACTOR_CACHE_TTL_HOURS=72
DATA_EXTRACTOR_USE_RANDOM_USER_AGENT=true
```

## 配置管理最佳实践

### 文件命名规范

- `.env` - 本地开发配置（不纳入版本控制）
- `.env.example` - 配置模板文件（纳入版本控制）
- `.env.development` - 开发环境专用配置
- `.env.production` - 生产环境专用配置

### 安全防护措施

```bash
# 设置配置文件访问权限
chmod 600 .env

# 将敏感文件排除出版本控制
echo ".env" >> .gitignore
```

### 配置验证机制

```python
# 系统启动时的关键配置验证
if settings.use_proxy and not settings.proxy_url:
    raise ValueError("代理启用状态下必须提供代理服务器地址")
```

## 故障诊断与排除

### 配置检查命令

```bash
# 查看所有 Data Extractor 相关环境变量
env | grep DATA_EXTRACTOR_

# 显示当前配置文件内容
cat .env
```

### 常见问题处理

- **环境变量未生效**：检查变量前缀格式和文件编码
- **数据类型转换错误**：确认数值和布尔值使用正确的格式
- **配置验证失败**：查看系统输出的详细错误信息

---

更多配置详情请参考项目根目录的 `.env.example` 文件和源码中的配置模块定义。
