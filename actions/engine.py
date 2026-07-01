"""Action Engine — registry and execution dispatcher.

Central module that:
- registers all available actions
- dispatches commands to the right handler
- reports results via EventBus
"""

from __future__ import annotations

from typing import Type

from loguru import logger

from core.event_bus import event_bus
from core.task_queue import task_queue, TaskStatus

from .base import BaseAction, ActionResult
from .file_ops import (
    MoveFileAction,
    CopyFileAction,
    DeleteFileAction,
    SearchFileAction,
    CreateFolderAction,
)
from .window_ops import (
    OpenAppAction,
    CloseAppAction,
    OpenFolderAction,
    OpenUrlAction,
)
from .mouse_ops import (
    ClickAction,
    DoubleClickAction,
    RightClickAction,
    ScrollAction,
)
from .keyboard_ops import (
    TypeTextAction,
    PressKeyAction,
    HotkeyAction,
)
from .web_ops import (
    SearchWebAction,
)
from .utility_ops import (
    ScreenshotAction,
    WaitAction,
    MessageAction,
)
from .system_ops import (
    SystemInfoAction,
    ClipboardGetAction,
    ClipboardSetAction,
    VolumeSetAction,
    SpeakTextAction,
    DiskUsageAction,
    BatteryAction,
    WindowMinimizeAction,
    LockScreenAction,
    EmptyTrashAction,
    RunCommandAction,
    OpenTrashAction,
)


class ActionEngine:
    """Registry + dispatcher for all actions."""

    def __init__(self) -> None:
        self._registry: dict[str, Type[BaseAction]] = {}

    def register(self, action_cls: Type[BaseAction]) -> None:
        """Register an action class by its action_name."""
        instance = action_cls()
        name = instance.action_name
        self._registry[name] = action_cls
        logger.info(f"Registered action: {name}")

    def register_all(self) -> None:
        """Зарегистрировать все встроенные действия (однократно)."""
        if self._registry:
            return  # уже зарегистрированы
        action_classes = [
            MoveFileAction,
            CopyFileAction,
            DeleteFileAction,
            SearchFileAction,
            CreateFolderAction,
            OpenAppAction,
            CloseAppAction,
            OpenFolderAction,
            OpenUrlAction,
            ClickAction,
            DoubleClickAction,
            RightClickAction,
            ScrollAction,
            TypeTextAction,
            PressKeyAction,
            HotkeyAction,
            SearchWebAction,
            ScreenshotAction,
            WaitAction,
            MessageAction,
            SystemInfoAction,
            ClipboardGetAction,
            ClipboardSetAction,
            VolumeSetAction,
            SpeakTextAction,
            DiskUsageAction,
            BatteryAction,
            WindowMinimizeAction,
            LockScreenAction,
            EmptyTrashAction,
            RunCommandAction,
            OpenTrashAction,
        ]
        for cls in action_classes:
            self.register(cls)

    def get_capabilities(self) -> list[dict]:
        """Return all registered capabilities for Hermes."""
        capabilities = []
        for name, cls in self._registry.items():
            instance = cls()
            capabilities.append(instance.get_capability())
        return capabilities

    async def execute(self, command: dict, task_id: str | None = None) -> ActionResult:
        """Execute a single command. Task ID optional (for queue integration)."""
        action_name = command.get("action")
        dry_run = command.get("dry_run", False)

        if action_name not in self._registry:
            return ActionResult(success=False, error=f"Unknown action: {action_name}", message="Неизвестная команда")

        action_cls = self._registry[action_name]
        instance = action_cls()

        logger.info(f"Executing: {action_name} (dry_run={dry_run})")
        await event_bus.emit("action:before", action=action_name, command=command)

        try:
            result = await instance.execute(command, dry_run=dry_run)
        except Exception as e:
            logger.error(f"Action '{action_name}' crashed: {e}")
            result = ActionResult(success=False, error=str(e), message="Ошибка выполнения")

        await event_bus.emit("action:after", action=action_name, result=result.model_dump())
        return result

    async def execute_sequence(self, commands: list[dict]) -> list[ActionResult]:
        """Execute multiple commands in sequence. Each goes through task queue."""
        results = []
        for cmd in commands:
            task = await task_queue.enqueue(cmd)
            result = await self.execute(cmd, task.id)
            await task_queue.task_complete(task, result.model_dump() if result.success else None, result.error)
            results.append(result)
        return results


# Global singleton
action_engine = ActionEngine()
