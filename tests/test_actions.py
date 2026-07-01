"""Tests for Action Engine."""

from __future__ import annotations

import pytest

from actions.file_ops import MoveFileAction, SearchFileAction
from actions.window_ops import OpenAppAction


@pytest.mark.asyncio
async def test_move_file_dry_run():
    action = MoveFileAction()
    result = await action.execute(
        {"source": "/tmp/test.txt", "destination": "/tmp/dest/"},
        dry_run=True,
    )
    assert result.success is True
    assert "Планируется" in result.message


@pytest.mark.asyncio
async def test_search_file_no_results():
    action = SearchFileAction()
    result = await action.execute(
        {"query": "___nonexistent_file_xyz___"},
        dry_run=False,
    )
    assert result.success is False
    assert "Ничего" in result.message


@pytest.mark.asyncio
async def test_open_app_dry_run():
    action = OpenAppAction()
    result = await action.execute({"app_name": "calc"}, dry_run=True)
    assert result.success is True
    assert "calc" in result.message.lower()


def test_capability_format():
    action = MoveFileAction()
    cap = action.get_capability()
    assert "action" in cap
    assert "description" in cap
    assert "params" in cap
    assert cap["action"] == "move_file"
