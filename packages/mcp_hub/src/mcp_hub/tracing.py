"""Compatibility re-export for the shared trace hooks."""

from extractor.validation_trace import TraceRecorder, active_trace, get_recorder, trace_event

__all__ = ["TraceRecorder", "active_trace", "get_recorder", "trace_event"]
