"""Task Queue — ordered execution of actions with progress tracking.

Each task is a structured dict from Hermes. Queue allows:
- sequential execution
- cancellation
- progress reporting
- visual feedback (Godot animations)
"""

from __future__ import annotations

import asyncio
import uuid
from enum import Enum
from typing import Any

from loguru import logger

from .event_bus import event_bus


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Task:
    """A single executable unit."""

    def __init__(self, command: dict) -> None:
        self.id: str = uuid.uuid4().hex[:12]
        self.command = command
        self.status = TaskStatus.PENDING
        self.result: dict | None = None
        self.error: str | None = None

    def __repr__(self) -> str:
        return f"<Task {self.id}: {self.command.get('action','?')} [{self.status.value}]>"


class TaskQueue:
    """Async queue that processes tasks one by one."""

    def __init__(self) -> None:
        self._queue: asyncio.Queue[Task] = asyncio.Queue()
        self._current: Task | None = None
        self._cancelled: set[str] = set()

    async def enqueue(self, command: dict) -> Task:
        task = Task(command)
        await self._queue.put(task)
        logger.info(f"Enqueued task {task.id}: {command.get('action', '?')}")
        await event_bus.emit("task:enqueued", task=task)
        return task

    async def process_loop(self) -> None:
        """Run forever: pull tasks, execute, report."""
        while True:
            task = await self._queue.get()
            if task.id in self._cancelled:
                task.status = TaskStatus.CANCELLED
                self._cancelled.discard(task.id)
                await event_bus.emit("task:cancelled", task=task)
                continue

            self._current = task
            task.status = TaskStatus.RUNNING
            await event_bus.emit("task:started", task=task)
            # Actual execution is done by ActionEngine — this just manages lifecycle
            # ActionEngine should call task_complete() when done
            self._current = None

    def cancel(self, task_id: str) -> None:
        self._cancelled.add(task_id)
        logger.info(f"Task {task_id} marked for cancellation")

    async def task_complete(self, task: Task, result: dict, error: str | None = None) -> None:
        if error:
            task.status = TaskStatus.FAILED
            task.error = error
        else:
            task.status = TaskStatus.COMPLETED
            task.result = result
        await event_bus.emit("task:completed", task=task, result=result, error=error)

    @property
    def current(self) -> Task | None:
        return self._current


# Global singleton
task_queue = TaskQueue()
