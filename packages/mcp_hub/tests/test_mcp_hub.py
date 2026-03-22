"""Tests for the MCP validation hub."""

from pathlib import Path
from unittest.mock import patch

import pytest

from mcp_hub.executor import ValidationExecutor
from mcp_hub.hub_server import (
    get_validation_run,
    get_validation_trace,
    list_validation_scenarios,
    record_manual_verdict,
    run_single_tool_validation,
)
from mcp_hub.storage import RunStore


@pytest.fixture
def hub_store(tmp_path, monkeypatch):
    store = RunStore(Path(tmp_path) / "mcp_hub")
    monkeypatch.setattr("mcp_hub.hub_server.store", store)
    monkeypatch.setattr("mcp_hub.hub_server.executor", ValidationExecutor(store))
    return store


@pytest.mark.asyncio
async def test_list_validation_scenarios():
    response = await list_validation_scenarios()

    assert response.success is True
    assert len(response.scenarios) >= 3


@pytest.mark.asyncio
async def test_run_single_tool_validation_persists_run_and_trace(hub_store):
    mock_result = {
        "url": "https://example.com",
        "title": "Example",
        "content": {"html": "<html><body><h1>Example</h1></body></html>"},
    }

    with patch("extractor.tools.scraping.web_scraper.scrape_url") as mock_scrape:
        mock_scrape.return_value = mock_result
        response = await run_single_tool_validation(
            tool_name="scrape_webpage",
            arguments={"url": "https://example.com", "method": "simple"},
            label="测试抓取",
        )

    assert response.success is True
    assert response.run.status == "succeeded"
    assert response.run.steps[0].tool_name == "scrape_webpage"
    assert response.run.trace_events
    persisted = hub_store.load_run(response.run.run_id)
    assert persisted.label == "测试抓取"
    assert persisted.artifacts[0].name.endswith(".json")


@pytest.mark.asyncio
async def test_record_manual_verdict_updates_run(hub_store):
    response = await run_single_tool_validation(
        tool_name="get_server_metrics",
        arguments={},
        label="metrics run",
    )
    verdict_response = await record_manual_verdict(
        run_id=response.run.run_id,
        verdict="accepted_with_notes",
        notes="结果符合预期",
    )

    assert verdict_response.success is True
    stored = await get_validation_run(response.run.run_id)
    assert stored.run.verdict is not None
    assert stored.run.verdict.verdict == "accepted_with_notes"


@pytest.mark.asyncio
async def test_get_validation_trace_returns_trace_events(hub_store):
    response = await run_single_tool_validation(
        tool_name="get_server_metrics",
        arguments={},
    )

    trace_response = await get_validation_trace(response.run.run_id)

    assert trace_response["success"] is True
    assert trace_response["trace_events"]
