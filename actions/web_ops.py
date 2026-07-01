"""Web actions — search_web (opens browser with search query)."""

from __future__ import annotations

from urllib.parse import quote

from core.platform import platform
from .base import BaseAction, ActionResult


class SearchWebAction(BaseAction):
    action_name = "search_web"

    async def execute(self, command: dict, dry_run: bool = False) -> ActionResult:
        query = command["query"]
        url = f"https://google.com/search?q={quote(query)}"

        if dry_run:
            return ActionResult(success=True, message=f"Поиск в браузере: {query}")

        ctrl = platform.get_controller()
        if ctrl:
            ctrl.init()
            ctrl.open_url(url)
            return ActionResult(success=True, message=f"Ищу: {query}")
        return ActionResult(success=False, message="Нет контроллера")

    def get_capability(self) -> dict:
        return {"action": "search_web", "description": "Поискать в интернете (открывает браузер)", "params": {"query": "string"}}
