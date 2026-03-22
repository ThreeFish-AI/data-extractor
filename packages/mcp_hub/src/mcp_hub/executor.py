"""Validation execution engine for mcp_hub."""

from __future__ import annotations

import inspect
import json
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Dict

from extractor.server import app as extractor_app
from extractor.validation_trace import TraceRecorder, active_trace

from .models import ValidationRun, ValidationScenario, ValidationStepResult
from .storage import RunStore


def _serialize(value: Any) -> Any:
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    if isinstance(value, dict):
        return {key: _serialize(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_serialize(item) for item in value]
    return value


def _resolve_template(value: Any, context: Dict[str, Any]) -> Any:
    if isinstance(value, str) and value.startswith("{{") and value.endswith("}}"):
        path = value[2:-2].strip().split(".")
        current: Any = context
        for segment in path:
            current = current[segment]
        return current
    if isinstance(value, dict):
        return {key: _resolve_template(item, context) for key, item in value.items()}
    if isinstance(value, list):
        return [_resolve_template(item, context) for item in value]
    return value


class LocalToolExecutor:
    """Execute tools directly against the mounted extractor app."""

    async def execute(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        tool = await extractor_app.get_tool(tool_name)
        prepared_arguments = self._prepare_arguments(tool, arguments)
        result = tool.fn(**prepared_arguments)
        if inspect.isawaitable(result):
            return await result
        return result

    def _prepare_arguments(self, tool: Any, provided: Dict[str, Any]) -> Dict[str, Any]:
        parameters = getattr(tool, "parameters", {}) or {}
        properties = parameters.get("properties", {})
        required = set(parameters.get("required", []))
        prepared = dict(provided)

        for name, schema in properties.items():
            if name in prepared:
                continue
            if "default" in schema:
                prepared[name] = schema["default"]
            elif name not in required:
                prepared[name] = None

        return prepared


class ValidationExecutor:
    """Run single-tool validations and reusable scenarios."""

    def __init__(self, store: RunStore) -> None:
        self.store = store
        self.tool_executor = LocalToolExecutor()

    async def run_tool_validation(
        self,
        *,
        tool_name: str,
        arguments: Dict[str, Any],
        label: str | None = None,
    ) -> ValidationRun:
        run = ValidationRun(
            run_id=uuid.uuid4().hex,
            kind="tool",
            label=label or f"单工具验证: {tool_name}",
            status="running",
            target_name=tool_name,
            arguments=arguments,
        )
        self.store.initialize_run(run)
        recorder = TraceRecorder()

        try:
            with active_trace(recorder), recorder.span(
                "validation_run", "run_single_tool_validation", tool_name=tool_name
            ):
                response = await self.tool_executor.execute(tool_name, arguments)
                payload = _serialize(response)
                artifacts = self._build_artifacts(run.run_id, tool_name, payload)
                step = ValidationStepResult(
                    step_id="tool_validation",
                    tool_name=tool_name,
                    success=bool(payload.get("success", True)),
                    arguments=arguments,
                    response_summary=self._summarize_payload(payload),
                    artifact_names=[artifact.name for artifact in artifacts],
                    error=payload.get("error"),
                )
                run.steps = [step]
                run.artifacts = artifacts
                run.status = "succeeded" if step.success else "failed"
        except Exception as exc:
            run.status = "failed"
            run.error = str(exc)
        finally:
            run.trace_events = [
                self._trace_event_to_model(event) for event in recorder.events
            ]
            run.completed_at = datetime.now(UTC)
            self.store.save_trace_events(run.run_id, run.trace_events)
            self.store.save_run(run)

        return run

    async def run_scenario(
        self,
        *,
        scenario: ValidationScenario,
        inputs: Dict[str, Any],
    ) -> ValidationRun:
        run = ValidationRun(
            run_id=uuid.uuid4().hex,
            kind="scenario",
            label=scenario.label,
            status="running",
            target_name=scenario.id,
            arguments=inputs,
        )
        self.store.initialize_run(run)
        recorder = TraceRecorder()
        context: Dict[str, Any] = {"input": inputs, "steps": {}}

        try:
            with active_trace(recorder), recorder.span(
                "validation_run", "run_validation_scenario", scenario_id=scenario.id
            ):
                for step_index, step in enumerate(scenario.tool_chain, start=1):
                    resolved_args = _resolve_template(step.arguments, context)
                    with recorder.span(
                        "scenario_step",
                        step.step_id,
                        tool_name=step.tool_name,
                        order=step_index,
                    ):
                        response = await self.tool_executor.execute(
                            step.tool_name, resolved_args
                        )
                        payload = _serialize(response)
                        context["steps"][step.step_id] = payload
                        artifacts = self._build_artifacts(
                            run.run_id, step.step_id, payload, prefix=f"{step_index:02d}"
                        )
                        step_result = ValidationStepResult(
                            step_id=step.step_id,
                            tool_name=step.tool_name,
                            success=bool(payload.get("success", True)),
                            arguments=resolved_args,
                            response_summary=self._summarize_payload(payload),
                            artifact_names=[artifact.name for artifact in artifacts],
                            error=payload.get("error"),
                        )
                        run.steps.append(step_result)
                        run.artifacts.extend(artifacts)
                        if not step_result.success:
                            run.status = "failed"
                            break

                if run.status != "failed":
                    run.status = "succeeded"
        except Exception as exc:
            run.status = "failed"
            run.error = str(exc)
        finally:
            run.trace_events = [
                self._trace_event_to_model(event) for event in recorder.events
            ]
            run.completed_at = datetime.now(UTC)
            self.store.save_trace_events(run.run_id, run.trace_events)
            self.store.save_run(run)

        return run

    def _build_artifacts(
        self,
        run_id: str,
        name_prefix: str,
        payload: Dict[str, Any],
        *,
        prefix: str = "",
    ):
        artifact_base = f"{prefix + '_' if prefix else ''}{name_prefix}"
        artifacts = [
            self.store.save_json_artifact(
                run_id,
                f"{artifact_base}.json",
                payload,
                description=f"{name_prefix} 原始响应",
            )
        ]
        markdown_value = payload.get("markdown_content") or payload.get("content")
        if isinstance(markdown_value, str) and markdown_value:
            media_type = "text/markdown" if "#" in markdown_value else "text/plain"
            artifacts.append(
                self.store.write_artifact(
                    run_id,
                    f"{artifact_base}.md",
                    markdown_value,
                    media_type=media_type,
                    description=f"{name_prefix} 文本产物",
                )
            )
        return artifacts

    def _summarize_payload(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        summary: Dict[str, Any] = {"success": payload.get("success", True)}
        for key in (
            "url",
            "pdf_source",
            "method",
            "word_count",
            "page_count",
            "total_links",
            "data_count",
        ):
            if key in payload:
                summary[key] = payload[key]
        if payload.get("error"):
            summary["error"] = payload["error"]
        return summary

    def _trace_event_to_model(self, event: Any):
        from .models import TraceEvent

        return TraceEvent(
            timestamp=event.timestamp,
            kind=event.kind,
            span=event.span,
            message=event.message,
            attributes=event.attributes,
        )
