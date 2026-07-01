"""Keyboard actions — type_text, press_key, hotkey."""

from __future__ import annotations

from core.platform import platform
from .base import BaseAction, ActionResult


class TypeTextAction(BaseAction):
    action_name = "type_text"

    async def execute(self, command: dict, dry_run: bool = False) -> ActionResult:
        ctrl = platform.get_controller()
        if not ctrl:
            return ActionResult(success=False, message="Нет контроллера")
        ctrl.init()
        text = command["text"]
        enter = command.get("enter", False)
        if dry_run:
            return ActionResult(success=True, message=f"Напечатать: {text[:50]}...")
        ctrl.type_text(text)
        if enter:
            ctrl.press_key("enter")
        return ActionResult(success=True, message="Текст введён")

    def get_capability(self) -> dict:
        return {"action": "type_text", "description": "Напечатать текст", "params": {"text": "string", "enter": "boolean (нажать Enter после текста)"}}


class PressKeyAction(BaseAction):
    action_name = "press_key"

    async def execute(self, command: dict, dry_run: bool = False) -> ActionResult:
        ctrl = platform.get_controller()
        if not ctrl:
            return ActionResult(success=False, message="Нет контроллера")
        ctrl.init()
        key = command["key"]
        if dry_run:
            return ActionResult(success=True, message=f"Нажать клавишу: {key}")
        ctrl.press_key(key)
        return ActionResult(success=True, message=f"Клавиша {key} нажата")

    def get_capability(self) -> dict:
        return {"action": "press_key", "description": "Нажать клавишу", "params": {"key": "string (например, enter, ctrl, esc, tab)"}}


class HotkeyAction(BaseAction):
    action_name = "hotkey"

    async def execute(self, command: dict, dry_run: bool = False) -> ActionResult:
        ctrl = platform.get_controller()
        if not ctrl:
            return ActionResult(success=False, message="Нет контроллера")
        ctrl.init()
        keys = command["keys"]
        if dry_run:
            return ActionResult(success=True, message=f"Горячие клавиши: {'+'.join(keys)}")
        ctrl.hotkey(*keys)
        return ActionResult(success=True, message=f"{'+'.join(keys)} нажато")

    def get_capability(self) -> dict:
        return {"action": "hotkey", "description": "Нажать комбинацию клавиш", "params": {"keys": "list[string]"}}
