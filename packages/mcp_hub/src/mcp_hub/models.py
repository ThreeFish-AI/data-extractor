"""Pydantic models for the MCP validation hub."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field

VerdictValue = Literal[
    "accepted",
    "accepted_with_notes",
    "rejected",
    "needs_followup",
]
RunStatus = Literal["pending", "running", "succeeded", "failed", "cancelled"]
RunKind = Literal["tool", "scenario"]


class ArtifactRecord(BaseModel):
    """Artifact metadata stored for a validation run."""

    name: str
    path: str
    media_type: str
    description: Optional[str] = None


class TraceEvent(BaseModel):
    """Single trace event emitted during validation."""

    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    kind: Literal["span_start", "span_end", "event"] = "event"
    span: str
    message: str
    attributes: Dict[str, Any] = Field(default_factory=dict)


class ValidationStepResult(BaseModel):
    """One step within a scenario run."""

    step_id: str
    tool_name: str
    success: bool
    arguments: Dict[str, Any]
    response_summary: Dict[str, Any] = Field(default_factory=dict)
    artifact_names: List[str] = Field(default_factory=list)
    error: Optional[str] = None


class ManualVerdict(BaseModel):
    """Human validation verdict."""

    verdict: VerdictValue
    notes: str = ""
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ValidationRun(BaseModel):
    """Persisted validation run."""

    run_id: str
    kind: RunKind
    label: str
    status: RunStatus
    target_name: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    completed_at: Optional[datetime] = None
    arguments: Dict[str, Any] = Field(default_factory=dict)
    steps: List[ValidationStepResult] = Field(default_factory=list)
    trace_events: List[TraceEvent] = Field(default_factory=list)
    artifacts: List[ArtifactRecord] = Field(default_factory=list)
    verdict: Optional[ManualVerdict] = None
    error: Optional[str] = None


class ValidationScenarioStep(BaseModel):
    """Single step in a reusable validation scenario."""

    step_id: str
    tool_name: str
    arguments: Dict[str, Any] = Field(default_factory=dict)


class ValidationScenario(BaseModel):
    """Reusable validation scenario."""

    id: str
    label: str
    description: str
    input_kind: Literal["url", "pdf", "mixed"]
    tool_chain: List[ValidationScenarioStep]
    default_arguments: Dict[str, Any] = Field(default_factory=dict)
    expected_artifact_types: List[str] = Field(default_factory=list)
    manual_checklist: List[str] = Field(default_factory=list)
    risk_level: Literal["low", "medium", "high"] = "medium"


class ScenarioListResponse(BaseModel):
    """Scenario list response."""

    success: bool
    scenarios: List[ValidationScenario]


class ValidationRunResponse(BaseModel):
    """Single validation run response."""

    success: bool
    run: ValidationRun


class ValidationRunListResponse(BaseModel):
    """Validation run list response."""

    success: bool
    runs: List[ValidationRun]


class CompareRunsResponse(BaseModel):
    """Comparison response between two runs."""

    success: bool
    left_run_id: str
    right_run_id: str
    differences: Dict[str, Any]


class VerdictResponse(BaseModel):
    """Manual verdict response."""

    success: bool
    run_id: str
    verdict: ManualVerdict
