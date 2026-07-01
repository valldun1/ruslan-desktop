"""Utility actions — screenshot, wait, message."""

from __future__ import annotations

import asyncio
import time

from loguru import logger

from core.platform import platform
from .base import BaseAction, ActionResult


class ScreenshotAction(BaseAction):
    action_name = "screenshot"

    async def execute(self, command: dict, dry_run: bool = False) -> ActionResult:
        ctrl = platform.get_controller()
        if not ctrl:
            return ActionResult(success=False, message="Нет контроллера")
        ctrl.init()

        if dry_run:
            return ActionResult(success=True, message="Снимок экрана")

        region = command.get("region")
        img = ctrl.screenshot(tuple(region) if region else None)
        if img is None:
            return ActionResult(success=False, message="Не удалось сделать скриншот")

        path = f"logs/screenshot_{int(time.time())}.png"
        img.save(path)
        logger.info(f"Screenshot saved: {path}")
        return ActionResult(success=True, message="Скриншот сохранён", data={"path": path})

    def get_capability(self) -> dict:
        return {"action": "screenshot", "description": "Сделать снимок экрана", "params": {"region": "list[int] (optional): x,y,w,h"}}


class WaitAction(BaseAction):
    action_name = "wait"

    async def execute(self, command: dict, dry_run: bool = False) -> ActionResult:
        seconds = command.get("seconds", 1.0)
        logger.info(f"Waiting {seconds}s...")
        await asyncio.sleep(seconds)
        return ActionResult(success=True, message=f"Ожидание {seconds}с")

    def get_capability(self) -> dict:
        return {"action": "wait", "description": "Пауза между действиями", "params": {"seconds": "float"}}


class MessageAction(BaseAction):
    action_name = "message"

    async def execute(self, command: dict, dry_run: bool = False) -> ActionResult:
        text = command.get("text", "")
        emotion = command.get("emotion", "neutral")
        logger.info(f"Ruslan [emotion={emotion}]: {text}")

        if not dry_run:
            ctrl = platform.get_controller()
            if ctrl:
                ctrl.init()
                try:
                    ctrl.show_notification("Руслан", text)
                except Exception:
                    pass

        return ActionResult(success=True, message=text, data={"emotion": emotion})

    def get_capability(self) -> dict:
        return {"action": "message", "description": "Показать сообщение или эмоцию", "params": {"text": "string", "emotion": "string (neutral/happy/sad/thinking)"}}
