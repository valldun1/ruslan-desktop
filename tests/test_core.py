"""Tests for Ruslan core modules."""

from __future__ import annotations

import pytest

from core.config import settings
from core.event_bus import event_bus
from core.task_queue import task_queue, Task, TaskStatus


class TestEventBus:
    @pytest.mark.asyncio
    async def test_emit_and_receive(self):
        results = []

        async def handler(**data):
            results.append(data)

        event_bus.subscribe("test:event", handler)
        await event_bus.emit("test:event", value=42)
        assert len(results) == 1
        assert results[0]["value"] == 42

    @pytest.mark.asyncio
    async def test_multiple_handlers(self):
        results = []

        async def h1(**data): results.append("h1")
        async def h2(**data): results.append("h2")

        event_bus.subscribe("test:multi", h1)
        event_bus.subscribe("test:multi", h2)
        await event_bus.emit("test:multi")
        assert len(results) == 2


class TestTaskQueue:
    @pytest.mark.asyncio
    async def test_enqueue(self):
        task = await task_queue.enqueue({"action": "test"})
        assert isinstance(task, Task)
        assert task.status == TaskStatus.PENDING
        assert task.command["action"] == "test"

    def test_cancel(self):
        pass  # placeholder

    def test_task_id_unique(self):
        t1 = Task({"action": "a"})
        t2 = Task({"action": "b"})
        assert t1.id != t2.id


class TestConfig:
    def test_defaults(self):
        assert settings.api_port == 8000
        assert settings.log_level == "DEBUG"
        assert settings.wake_word == "руслан"
