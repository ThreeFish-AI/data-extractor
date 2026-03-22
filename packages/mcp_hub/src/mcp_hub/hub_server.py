"""FastMCP-based validation hub for the data extractor tools."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated, Any, Dict, Optional

from fastmcp import FastMCP
from pydantic import Field
from starlette.requests import Request
from starlette.responses import HTMLResponse

from extractor.server import app as extractor_app

from .executor import ValidationExecutor
from .models import (
    CompareRunsResponse,
    ManualVerdict,
    ScenarioListResponse,
    ValidationRunListResponse,
    ValidationRunResponse,
    VerdictResponse,
)
from .scenarios import SCENARIOS, SCENARIOS_BY_ID
from .storage import RunStore

STORE_ROOT = Path(".temp/mcp_hub")
store = RunStore(STORE_ROOT)
executor = ValidationExecutor(store)
app = FastMCP("mcp-hub", instructions="验证与复盘 data-extractor 的 14 个 MCP 工具。")
app.mount(extractor_app, namespace="extractor")


@app.tool()
async def list_validation_scenarios() -> ScenarioListResponse:
    """列出内置验证场景。"""
    return ScenarioListResponse(success=True, scenarios=SCENARIOS)


@app.tool()
async def run_single_tool_validation(
    tool_name: Annotated[str, Field(description="现有 data-extractor 工具名")],
    arguments: Annotated[
        Dict[str, Any], Field(description="传给目标工具的参数字典")
    ],
    label: Annotated[Optional[str], Field(default=None, description="本次验证的显示名称")] = None,
) -> ValidationRunResponse:
    """执行单工具验证并落盘产物、trace 与 run 记录。"""
    run = await executor.run_tool_validation(
        tool_name=tool_name,
        arguments=arguments,
        label=label,
    )
    return ValidationRunResponse(success=True, run=run)


@app.tool()
async def run_validation_scenario(
    scenario_id: Annotated[str, Field(description="场景 ID")],
    inputs: Annotated[
        Dict[str, Any],
        Field(description="场景输入，例如 {\"url\": \"https://...\"} 或 {\"pdf_source\": \"/tmp/a.pdf\"}"),
    ],
) -> ValidationRunResponse:
    """执行场景型验证。"""
    scenario = SCENARIOS_BY_ID.get(scenario_id)
    if scenario is None:
        raise ValueError(f"Unknown scenario_id: {scenario_id}")
    run = await executor.run_scenario(scenario=scenario, inputs=inputs)
    return ValidationRunResponse(success=True, run=run)


@app.tool()
async def list_validation_runs(
    limit: Annotated[int, Field(default=20, ge=1, le=100, description="返回最近 run 数量")] = 20,
) -> ValidationRunListResponse:
    """列出最近的验证运行记录。"""
    return ValidationRunListResponse(success=True, runs=store.list_runs(limit=limit))


@app.tool()
async def get_validation_run(
    run_id: Annotated[str, Field(description="运行 ID")]
) -> ValidationRunResponse:
    """读取单个 run 详情。"""
    return ValidationRunResponse(success=True, run=store.load_run(run_id))


@app.tool()
async def get_validation_trace(
    run_id: Annotated[str, Field(description="运行 ID")]
) -> Dict[str, Any]:
    """返回单个 run 的 trace 事件。"""
    run = store.load_run(run_id)
    return {
        "success": True,
        "run_id": run_id,
        "trace_events": [event.model_dump(mode="json") for event in run.trace_events],
    }


@app.tool()
async def get_validation_artifacts(
    run_id: Annotated[str, Field(description="运行 ID")]
) -> Dict[str, Any]:
    """返回单个 run 的 artifact 清单。"""
    run = store.load_run(run_id)
    return {
        "success": True,
        "run_id": run_id,
        "artifacts": [artifact.model_dump(mode="json") for artifact in run.artifacts],
    }


@app.tool()
async def compare_validation_runs(
    left_run_id: Annotated[str, Field(description="左侧 run ID")],
    right_run_id: Annotated[str, Field(description="右侧 run ID")],
) -> CompareRunsResponse:
    """对比两个 run 的关键摘要。"""
    left = store.load_run(left_run_id)
    right = store.load_run(right_run_id)
    differences = {
        "status": {"left": left.status, "right": right.status},
        "step_count": {"left": len(left.steps), "right": len(right.steps)},
        "artifact_count": {"left": len(left.artifacts), "right": len(right.artifacts)},
        "verdict": {
            "left": left.verdict.verdict if left.verdict else None,
            "right": right.verdict.verdict if right.verdict else None,
        },
    }
    return CompareRunsResponse(
        success=True,
        left_run_id=left_run_id,
        right_run_id=right_run_id,
        differences=differences,
    )


@app.tool()
async def record_manual_verdict(
    run_id: Annotated[str, Field(description="运行 ID")],
    verdict: Annotated[
        str,
        Field(
            description="accepted / accepted_with_notes / rejected / needs_followup"
        ),
    ],
    notes: Annotated[str, Field(default="", description="人工检查备注")] = "",
) -> VerdictResponse:
    """为 run 记录人工验收结论。"""
    run = store.load_run(run_id)
    manual_verdict = ManualVerdict(verdict=verdict, notes=notes)
    run.verdict = manual_verdict
    store.save_verdict(run_id, manual_verdict)
    store.save_run(run)
    return VerdictResponse(success=True, run_id=run_id, verdict=manual_verdict)


@app.resource("validation://scenarios")
def scenarios_resource() -> str:
    """Scenarios as JSON."""
    return json.dumps(
        [scenario.model_dump(mode="json") for scenario in SCENARIOS],
        ensure_ascii=False,
        indent=2,
    )


@app.resource("validation://runs/{run_id}")
def run_resource(run_id: str) -> str:
    """Run detail as JSON."""
    return store.load_run(run_id).model_dump_json(indent=2)


@app.resource("validation://runs/{run_id}/trace")
def trace_resource(run_id: str) -> str:
    """Run trace as JSON."""
    run = store.load_run(run_id)
    return json.dumps(
        [event.model_dump(mode="json") for event in run.trace_events],
        ensure_ascii=False,
        indent=2,
    )


@app.custom_route("/viewer", methods=["GET"])
async def viewer_index(_: Request) -> HTMLResponse:
    """Minimal HTML dashboard for manual review."""
    runs = store.list_runs(limit=30)
    scenario_items = "".join(
        f"<li><strong>{scenario.label}</strong><br>{scenario.description}</li>"
        for scenario in SCENARIOS
    )
    run_items = "".join(
        f"<li><a href='/viewer/runs/{run.run_id}'>{run.label}</a> "
        f"<code>{run.status}</code> <small>{run.created_at.isoformat()}</small></li>"
        for run in runs
    ) or "<li>暂无运行记录</li>"
    html = f"""
    <html>
      <head>
        <meta charset='utf-8'>
        <title>MCP Hub Viewer</title>
        <style>
          body {{ font-family: Georgia, serif; margin: 40px; background: #f7f3eb; color: #1f2937; }}
          .layout {{ display: grid; grid-template-columns: 1fr 1fr; gap: 24px; }}
          .card {{ background: #fffdf8; border: 1px solid #d6d3d1; border-radius: 16px; padding: 20px; }}
          h1, h2 {{ margin-top: 0; }}
          code {{ background: #e7e5e4; padding: 2px 6px; border-radius: 6px; }}
          a {{ color: #0f766e; text-decoration: none; }}
        </style>
      </head>
      <body>
        <h1>MCP Hub 验证控制面</h1>
        <p>该页面用于人工查看验证运行记录、trace 与产物。触发执行建议通过 MCP 工具调用。</p>
        <div class='layout'>
          <section class='card'>
            <h2>内置场景</h2>
            <ul>{scenario_items}</ul>
          </section>
          <section class='card'>
            <h2>最近运行</h2>
            <ul>{run_items}</ul>
          </section>
        </div>
      </body>
    </html>
    """
    return HTMLResponse(html)


@app.custom_route("/viewer/runs/{run_id}", methods=["GET"])
async def viewer_run_detail(request: Request) -> HTMLResponse:
    """Run detail page."""
    run = store.load_run(request.path_params["run_id"])
    step_html = "".join(
        f"<li><strong>{step.step_id}</strong> / <code>{step.tool_name}</code> / "
        f"<code>{'success' if step.success else 'failed'}</code><pre>{json.dumps(step.response_summary, ensure_ascii=False, indent=2)}</pre></li>"
        for step in run.steps
    ) or "<li>暂无步骤</li>"
    trace_html = "".join(
        f"<li><code>{event.kind}</code> <strong>{event.span}</strong> {event.message}<pre>{json.dumps(event.attributes, ensure_ascii=False, indent=2)}</pre></li>"
        for event in run.trace_events
    ) or "<li>暂无 trace</li>"
    artifact_html = "".join(
        f"<li><code>{artifact.media_type}</code> {artifact.name}<br><small>{artifact.path}</small></li>"
        for artifact in run.artifacts
    ) or "<li>暂无 artifact</li>"
    verdict_html = (
        f"<p><strong>{run.verdict.verdict}</strong></p><pre>{run.verdict.notes}</pre>"
        if run.verdict
        else "<p>尚未记录 verdict</p>"
    )
    html = f"""
    <html>
      <head>
        <meta charset='utf-8'>
        <title>{run.label}</title>
        <style>
          body {{ font-family: Georgia, serif; margin: 32px; background: #fcfbf7; color: #111827; }}
          .card {{ background: #ffffff; border: 1px solid #e5e7eb; border-radius: 16px; padding: 20px; margin-bottom: 20px; }}
          .meta {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; }}
          pre {{ overflow-x: auto; white-space: pre-wrap; background: #f8fafc; padding: 12px; border-radius: 10px; }}
          code {{ background: #e5e7eb; padding: 2px 6px; border-radius: 6px; }}
        </style>
      </head>
      <body>
        <p><a href='/viewer'>返回列表</a></p>
        <h1>{run.label}</h1>
        <section class='card meta'>
          <div><strong>run_id</strong><pre>{run.run_id}</pre></div>
          <div><strong>status</strong><pre>{run.status}</pre></div>
          <div><strong>kind</strong><pre>{run.kind}</pre></div>
          <div><strong>target</strong><pre>{run.target_name}</pre></div>
        </section>
        <section class='card'><h2>输入参数</h2><pre>{json.dumps(run.arguments, ensure_ascii=False, indent=2)}</pre></section>
        <section class='card'><h2>步骤结果</h2><ol>{step_html}</ol></section>
        <section class='card'><h2>Trace</h2><ol>{trace_html}</ol></section>
        <section class='card'><h2>Artifacts</h2><ul>{artifact_html}</ul></section>
        <section class='card'><h2>人工 Verdict</h2>{verdict_html}</section>
      </body>
    </html>
    """
    return HTMLResponse(html)


def main() -> None:
    """Run the hub server over HTTP for MCP + viewer access."""
    app.run(transport="http", host="localhost", port=8091, path="/mcp")


if __name__ == "__main__":
    main()
