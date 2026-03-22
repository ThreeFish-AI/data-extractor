# mcp_hub

`mcp_hub` 是面向 `data-extractor` 的验证编排与人工复盘控制面。

核心职责：

- 挂载现有 14 个 MCP 工具
- 执行单工具或场景化验证
- 保存 run / trace / artifact / verdict
- 提供最小 viewer 页面用于人工检查

启动入口：

```bash
uv run python -m mcp_hub.hub_server
```
