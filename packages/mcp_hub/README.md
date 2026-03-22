# mcp_hub

`mcp_hub` 是面向 `data-extractor` 的验证编排与人工复盘控制面。

目录采用标准 `src` 布局：

- `src/mcp_hub/`：可导入源码包
- `tests/`：Hub 自身测试
- `pyproject.toml`：独立 package 元数据与依赖

核心职责：

- 挂载现有 14 个 MCP 工具
- 执行单工具或场景化验证
- 保存 run / trace / artifact / verdict
- 提供最小 viewer 页面用于人工检查

启动入口：

```bash
uv run --project packages/mcp_hub python -m mcp_hub
```
