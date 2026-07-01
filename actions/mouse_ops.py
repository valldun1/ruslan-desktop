"""Mouse actions — click, double_click, right_click, scroll."""

from __future__ import annotations

from core.platform import platform
from .base import BaseAction, ActionResult


class ClickAction(BaseAction):
    action_name = "click"

    async def execute(self, command: dict, dry_run: bool = False) -> ActionResult:
        ctrl = platform.get_controller()
        if not ctrl:
            return ActionResult(success=False, message="Нет контроллера для этой платформы")
        ctrl.init()
        x, y = command.get("x"), command.get("y")
        if dry_run:
            return ActionResult(success=True, message=f"Клик в ({x}, {y})")
        ctrl.click(x, y)
        return ActionResult(success=True, message="Клик выполнен")

    def get_capability(self) -> dict:
        return {"action": "click", "description": "Кликнуть левой кнопкой мыши", "params": {"x": "int (optional)", "y": "int (optional)", "target": "string (optional)"}}


class DoubleClickAction(BaseAction):
    action_name = "double_click"

    async def execute(self, command: dict, dry_run: bool = False) -> ActionResult:
        ctrl = platform.get_controller()
        if not ctrl:
            return ActionResult(success=False, message="Нет контроллера")
        ctrl.init()
        x, y = command.get("x"), command.get("y")
        if dry_run:
            return ActionResult(success=True, message=f"Двойной клик в ({x}, {y})")
        ctrl.double_click(x, y)
        return ActionResult(success=True, message="Двойной клик выполнен")

    def get_capability(self) -> dict:
        return {"action": "double_click", "description": "Двойной клик", "params": {"x": "int (optional)", "y": "int (optional)"}}


class RightClickAction(BaseAction):
    action_name = "right_click"

    async def execute(self, command: dict, dry_run: bool = False) -> ActionResult:
        ctrl = platform.get_controller()
        if not ctrl:
            return ActionResult(success=False, message="Нет контроллера")
        ctrl.init()
        x, y = command.get("x"), command.get("y")
        if dry_run:
            return ActionResult(success=True, message=f"Правый клик в ({x}, {y})")
        ctrl.right_click(x, y)
        return ActionResult(success=True, message="Правый клик выполнен")

    def get_capability(self) -> dict:
        return {"action": "right_click", "description": "Правый клик мыши", "params": {"x": "int", "y": "int"}}


class ScrollAction(BaseAction):
    action_name = "scroll"

    async def execute(self, command: dict, dry_run: bool = False) -> ActionResult:
        ctrl = platform.get_controller()
        if not ctrl:
            return ActionResult(success=False, message="Нет контроллера")
        ctrl.init()
        clicks = command.get("clicks", 1)
        if dry_run:
            return ActionResult(success=True, message=f"Скролл на {clicks}")
        ctrl.scroll(clicks)
        return ActionResult(success=True, message="Скролл выполнен")

    def get_capability(self) -> dict:
        return {"action": "scroll", "description": "Прокрутить колесо мыши", "params": {"clicks": "int (positive=up, negative=down)"}}
