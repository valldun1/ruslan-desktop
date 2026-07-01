"""Example plugin — demonstrates how to add custom actions."""

from __future__ import annotations

from actions.base import BaseAction, ActionResult


class HelloWorldAction(BaseAction):
    action_name = "hello_world"

    async def execute(self, command: dict, dry_run: bool = False) -> ActionResult:
        return ActionResult(success=True, message="Привет, мир! Я — плагин.")

    def get_capability(self) -> dict:
        return {"action": "hello_world", "description": "Тестовое действие плагина", "params": {}}
