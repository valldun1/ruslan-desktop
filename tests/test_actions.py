"""Tests for Action Engine — file ops, window ops, web ops."""

from __future__ import annotations

from pathlib import Path

import pytest

from actions.base import ActionResult
from actions.engine import action_engine
from actions.file_ops import MoveFileAction, CopyFileAction, DeleteFileAction, SearchFileAction
from actions.window_ops import OpenAppAction, CloseAppAction
from actions.mouse_ops import ClickAction
from actions.keyboard_ops import TypeTextAction
from actions.web_ops import SearchWebAction
from actions.utility_ops import MessageAction, WaitAction


class TestActionEngine:
    def test_register_all(self):
        action_engine.register_all()
        assert "open_app" in action_engine._registry
        assert "move_file" in action_engine._registry
        assert len(action_engine._registry) >= 15

    def test_get_capabilities(self):
        caps = action_engine.get_capabilities()
        assert isinstance(caps, list)
        names = {c["action"] for c in caps}
        assert "open_app" in names
        assert "message" in names

    @pytest.mark.asyncio
    async def test_execute_unknown_action(self):
        result = await action_engine.execute({"action": "nonexistent"})
        assert result.success is False
        assert "Unknown" in result.error

    @pytest.mark.asyncio
    async def test_execute_message_action(self):
        result = await action_engine.execute({
            "action": "message",
            "text": "test",
        })
        assert result.success is True


class TestFileOps:
    def test_action_names(self):
        assert MoveFileAction().action_name == "move_file"
        assert CopyFileAction().action_name == "copy_file"
        assert DeleteFileAction().action_name == "delete_file"
        assert SearchFileAction().action_name == "search_file"

    @pytest.mark.asyncio
    async def test_move_file_dry_run(self, tmp_path):
        src = tmp_path / "a.txt"
        src.write_text("hello")
        dst = tmp_path / "b.txt"
        result = await MoveFileAction().execute(
            {"action": "move_file", "source": str(src), "destination": str(dst)},
            dry_run=True,
        )
        assert result.success is True
        assert src.exists()  # dry run — файл не тронут

    @pytest.mark.asyncio
    async def test_copy_file_dry_run(self, tmp_path):
        src = tmp_path / "a.txt"
        src.write_text("hello")
        dst = tmp_path / "b.txt"
        result = await CopyFileAction().execute(
            {"action": "copy_file", "source": str(src), "destination": str(dst)},
            dry_run=True,
        )
        assert result.success is True
        assert not dst.exists()  # dry run

    @pytest.mark.asyncio
    async def test_delete_file_dry_run(self, tmp_path):
        f = tmp_path / "del.txt"
        f.write_text("delete me")
        result = await DeleteFileAction().execute(
            {"action": "delete_file", "path": str(f)},
            dry_run=True,
        )
        assert result.success is True
        assert f.exists()  # dry run

    @pytest.mark.asyncio
    async def test_search_file_dry_run(self, tmp_path):
        (tmp_path / "found.txt").write_text("data")
        result = await SearchFileAction().execute(
            {"action": "search_file", "query": "found", "directory": str(tmp_path)},
            dry_run=True,
        )
        assert result.success is True

    @pytest.mark.asyncio
    async def test_move_file_real(self, tmp_path):
        src = tmp_path / "real.txt"
        src.write_text("data")
        dst = tmp_path / "moved.txt"
        result = await MoveFileAction().execute(
            {"action": "move_file", "source": str(src), "destination": str(dst)},
            dry_run=False,
        )
        assert result.success is True
        assert not src.exists()
        assert dst.read_text() == "data"

    @pytest.mark.asyncio
    async def test_copy_file_real(self, tmp_path):
        src = tmp_path / "src.txt"
        src.write_text("data")
        dst = tmp_path / "copy.txt"
        result = await CopyFileAction().execute(
            {"action": "copy_file", "source": str(src), "destination": str(dst)},
            dry_run=False,
        )
        assert result.success is True
        assert src.exists()
        assert dst.read_text() == "data"

    @pytest.mark.asyncio
    async def test_delete_file_real(self, tmp_path):
        f = tmp_path / "rm.txt"
        f.write_text("bye")
        result = await DeleteFileAction().execute(
            {"action": "delete_file", "path": str(f)},
            dry_run=False,
        )
        assert result.success is True
        assert not f.exists()

    @pytest.mark.asyncio
    async def test_search_file_real(self, tmp_path):
        (tmp_path / "report_2025.pdf").write_text("pdf")
        (tmp_path / "notes.txt").write_text("text")
        result = await SearchFileAction().execute(
            {"action": "search_file", "query": "report", "directory": str(tmp_path)},
            dry_run=False,
        )
        assert result.success is True
        assert any("report_2025" in f for f in result.data.get("files", []))


class TestWindowOps:
    def test_action_names(self):
        assert OpenAppAction().action_name == "open_app"
        assert CloseAppAction().action_name == "close_app"


class TestMouseOps:
    def test_action_name(self):
        assert ClickAction().action_name == "click"


class TestKeyboardOps:
    def test_action_name(self):
        assert TypeTextAction().action_name == "type_text"


class TestWebOps:
    def test_action_name(self):
        assert SearchWebAction().action_name == "search_web"


class TestUtilityOps:
    def test_action_names(self):
        assert MessageAction().action_name == "message"
        assert WaitAction().action_name == "wait"
