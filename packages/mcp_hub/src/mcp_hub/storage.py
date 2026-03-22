"""Filesystem-backed storage for validation hub runs."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, List, Optional

from .models import ArtifactRecord, ManualVerdict, TraceEvent, ValidationRun


class RunStore:
    """Persist validation runs in a local directory tree."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self.runs_dir = self.root / "runs"
        self.runs_dir.mkdir(parents=True, exist_ok=True)

    def _run_dir(self, run_id: str) -> Path:
        return self.runs_dir / run_id

    def initialize_run(self, run: ValidationRun) -> ValidationRun:
        run_dir = self._run_dir(run.run_id)
        (run_dir / "artifacts").mkdir(parents=True, exist_ok=True)
        self.save_run(run)
        return run

    def save_run(self, run: ValidationRun) -> ValidationRun:
        run_dir = self._run_dir(run.run_id)
        run_dir.mkdir(parents=True, exist_ok=True)
        (run_dir / "run.json").write_text(
            run.model_dump_json(indent=2), encoding="utf-8"
        )
        return run

    def load_run(self, run_id: str) -> ValidationRun:
        run_path = self._run_dir(run_id) / "run.json"
        return ValidationRun.model_validate_json(run_path.read_text(encoding="utf-8"))

    def list_runs(self, limit: int = 20) -> List[ValidationRun]:
        runs: List[ValidationRun] = []
        for run_path in sorted(
            self.runs_dir.glob("*/run.json"),
            key=lambda path: path.stat().st_mtime,
            reverse=True,
        )[:limit]:
            runs.append(
                ValidationRun.model_validate_json(run_path.read_text(encoding="utf-8"))
            )
        return runs

    def save_trace_events(self, run_id: str, trace_events: List[TraceEvent]) -> None:
        run_dir = self._run_dir(run_id)
        payload = [event.model_dump(mode="json") for event in trace_events]
        (run_dir / "trace.json").write_text(
            json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8"
        )

    def write_artifact(
        self,
        run_id: str,
        name: str,
        content: str,
        *,
        media_type: str,
        description: Optional[str] = None,
    ) -> ArtifactRecord:
        artifact_path = self._run_dir(run_id) / "artifacts" / name
        artifact_path.write_text(content, encoding="utf-8")
        return ArtifactRecord(
            name=name,
            path=str(artifact_path),
            media_type=media_type,
            description=description,
        )

    def save_json_artifact(
        self,
        run_id: str,
        name: str,
        payload: Any,
        *,
        description: Optional[str] = None,
    ) -> ArtifactRecord:
        artifact_path = self._run_dir(run_id) / "artifacts" / name
        artifact_path.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        return ArtifactRecord(
            name=name,
            path=str(artifact_path),
            media_type="application/json",
            description=description,
        )

    def save_verdict(self, run_id: str, verdict: ManualVerdict) -> None:
        run_dir = self._run_dir(run_id)
        (run_dir / "verdict.json").write_text(
            verdict.model_dump_json(indent=2), encoding="utf-8"
        )
