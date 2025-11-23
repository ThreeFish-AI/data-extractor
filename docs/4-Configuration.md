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

## 配置优先级

Data Extractor 采用分层配置，优先级从高到低：

1. **运行时参数** - 函数调用时直接传递
2. **环境变量** - `DATA_EXTRACTOR_` 前缀
3. **环境文件** - `.env` 文件配置
4. **默认配置** - 代码中定义的默认值

## 运行时参数

运行时参数具有最高优先级，在调用 MCP 工具时直接传递，可覆盖所有其他配置。

### 数据提取配置

灵活的数据提取配置支持简单 CSS 选择器和复杂属性提取：

```python
# 简单配置
extract_config = {"title": "h1"}

# 复杂配置
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

**支持的属性提取**：

- `text` - 文本内容
- `href` - 链接地址
- `src` - 图片/资源地址
- 自定义属性 - 如 `data-id`、`class` 等

### 使用示例

```python
# 在 MCP 工具调用中使用
result = await scrape_webpage(
    url="https://example.com",
    extract_config={
        "title": "h1",
        "content": ".main-content p",
        "links": {"selector": "a", "multiple": true, "attr": "href"}
    }
)
```

## 常用配置项

### 服务器配置

| 环境变量                     | 默认值           | 说明       |
| ---------------------------- | ---------------- | ---------- |
| `DATA_EXTRACTOR_SERVER_NAME` | `data-extractor` | 服务器名称 |

### 性能配置

| 环境变量                                        | 默认值 | 说明             |
| ----------------------------------------------- | ------ | ---------------- |
| `DATA_EXTRACTOR_CONCURRENT_REQUESTS`            | `16`   | 并发请求数       |
| `DATA_EXTRACTOR_RATE_LIMIT_REQUESTS_PER_MINUTE` | `60`   | 每分钟请求限制   |
| `DATA_EXTRACTOR_REQUEST_TIMEOUT`                | `30.0` | 请求超时时间(秒) |
| `DATA_EXTRACTOR_MAX_RETRIES`                    | `3`    | 最大重试次数     |

### 浏览器配置

| 环境变量                           | 默认值  | 说明                 |
| ---------------------------------- | ------- | -------------------- |
| `DATA_EXTRACTOR_ENABLE_JAVASCRIPT` | `false` | 启用 JavaScript 执行 |
| `DATA_EXTRACTOR_BROWSER_HEADLESS`  | `true`  | 无头浏览器模式       |
| `DATA_EXTRACTOR_BROWSER_TIMEOUT`   | `30`    | 浏览器操作超时时间   |

### 反检测配置

| 环境变量                               | 默认值  | 说明           |
| -------------------------------------- | ------- | -------------- |
| `DATA_EXTRACTOR_USE_RANDOM_USER_AGENT` | `true`  | 随机用户代理   |
| `DATA_EXTRACTOR_USE_PROXY`             | `false` | 启用代理       |
| `DATA_EXTRACTOR_PROXY_URL`             | -       | 代理服务器 URL |

### 缓存配置

| 环境变量                         | 默认值 | 说明               |
| -------------------------------- | ------ | ------------------ |
| `DATA_EXTRACTOR_ENABLE_CACHING`  | `true` | 启用缓存机制       |
| `DATA_EXTRACTOR_CACHE_TTL_HOURS` | `24`   | 缓存生存时间(小时) |

### 日志配置

| 环境变量                   | 默认值 | 说明     |
| -------------------------- | ------ | -------- |
| `DATA_EXTRACTOR_LOG_LEVEL` | `INFO` | 日志级别 |

## 环境配置示例

### 开发环境

```bash
# .env.development
DATA_EXTRACTOR_LOG_LEVEL=DEBUG
DATA_EXTRACTOR_ENABLE_JAVASCRIPT=true
DATA_EXTRACTOR_BROWSER_HEADLESS=false
DATA_EXTRACTOR_CONCURRENT_REQUESTS=4
DATA_EXTRACTOR_CACHE_TTL_HOURS=1
```

### 生产环境

```bash
# .env.production
DATA_EXTRACTOR_LOG_LEVEL=INFO
DATA_EXTRACTOR_ENABLE_JAVASCRIPT=true
DATA_EXTRACTOR_BROWSER_HEADLESS=true
DATA_EXTRACTOR_CONCURRENT_REQUESTS=32
DATA_EXTRACTOR_CACHE_TTL_HOURS=72
DATA_EXTRACTOR_USE_RANDOM_USER_AGENT=true
```

## 最佳实践

### 配置文件命名

- `.env` - 本地开发（不提交版本控制）
- `.env.example` - 配置模板（提交版本控制）
- `.env.development` - 开发环境
- `.env.production` - 生产环境

### 安全管理

```bash
# 设置文件权限
chmod 600 .env

# Git 排除敏感文件
echo ".env" >> .gitignore
```

### 配置验证

```python
# 启动时验证关键配置
if settings.use_proxy and not settings.proxy_url:
    raise ValueError("Proxy enabled requires proxy URL")
```

## 故障排除

### 检查配置

```bash
# 查看环境变量
env | grep DATA_EXTRACTOR_

# 查看配置文件
cat .env
```

### 常见问题

- **环境变量未生效**：检查前缀和文件格式
- **类型转换错误**：确保数值和布尔值格式正确
- **验证失败**：查看详细错误信息

---

更多详细配置请参考 `.env.example` 文件和源码中的配置定义。
