"""Shared validation trace hooks for extractor."""

from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar, Token
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Dict, Iterator, List, Optional


@dataclass
class TraceEventRecord:
    """Single trace event record."""

    kind: str
    span: str
    message: str
    attributes: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))


class TraceRecorder:
    """Collect trace events for one validation run."""

    def __init__(self) -> None:
        self.events: List[TraceEventRecord] = []

    def emit(self, kind: str, span: str, message: str, **attributes: Any) -> None:
        self.events.append(
            TraceEventRecord(
                kind=kind,
                span=span,
                message=message,
                attributes=dict(attributes),
            )
        )

    @contextmanager
    def span(self, span: str, message: str, **attributes: Any) -> Iterator[None]:
        self.emit("span_start", span, message, **attributes)
        try:
            yield
        finally:
            self.emit("span_end", span, f"{message}:done")


_active_recorder: ContextVar[Optional[TraceRecorder]] = ContextVar(
    "extractor_validation_trace_recorder", default=None
)


def get_recorder() -> Optional[TraceRecorder]:
    """Return current active recorder."""
    return _active_recorder.get()


def trace_event(span: str, message: str, **attributes: Any) -> None:
    """Emit a trace event if a recorder is active."""
    recorder = get_recorder()
    if recorder is not None:
        recorder.emit("event", span, message, **attributes)


@contextmanager
def active_trace(recorder: TraceRecorder) -> Iterator[TraceRecorder]:
    """Bind a recorder to current context."""
    token: Token[Optional[TraceRecorder]] = _active_recorder.set(recorder)
    try:
        yield recorder
    finally:
        _active_recorder.reset(token)
