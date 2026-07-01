"""Window and app actions — open, close, find windows."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from loguru import logger

from .base import BaseAction, ActionResult


IS_WINDOWS = sys.platform == "win32"


class OpenAppAction(BaseAction):
    action_name = "open_app"

    async def execute(self, command: dict, dry_run: bool = False) -> ActionResult:
        app_name = command["app_name"]
        args = command.get("arguments")

        if dry_run:
            return ActionResult(success=True, message=f"Открыть: {app_name}")

        try:
            if IS_WINDOWS:
                subprocess.Popen(["start", app_name], shell=True)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", "-a", app_name])
            else:
                # Linux / Termux fallback
                subprocess.Popen([app_name] + (args or []))
            logger.info(f"Opened app: {app_name}")
            return ActionResult(success=True, message=f"Открываю {app_name}")
        except Exception as e:
            logger.error(f"Failed to open {app_name}: {e}")
            return ActionResult(success=False, error=str(e), message=f"Не удалось открыть {app_name}")

    def get_capability(self) -> dict:
        return {"action": "open_app", "description": "Открыть программу", "params": {"app_name": "string", "arguments": "list (optional)"}}


class CloseAppAction(BaseAction):
    action_name = "close_app"

    async def execute(self, command: dict, dry_run: bool = False) -> ActionResult:
        app_name = command["app_name"]

        if dry_run:
            return ActionResult(success=True, message=f"Закрыть: {app_name}")

        try:
            if IS_WINDOWS:
                subprocess.run(["taskkill", "/F", "/IM", f"{app_name}.exe"], capture_output=True, text=True)
            else:
                subprocess.run(["pkill", "-f", app_name], capture_output=True)
            logger.info(f"Closed app: {app_name}")
            return ActionResult(success=True, message=f"Закрываю {app_name}")
        except Exception as e:
            logger.error(f"Failed to close {app_name}: {e}")
            return ActionResult(success=False, error=str(e), message=f"Не удалось закрыть {app_name}")

    def get_capability(self) -> dict:
        return {"action": "close_app", "description": "Закрыть программу", "params": {"app_name": "string"}}


class OpenFolderAction(BaseAction):
    action_name = "open_folder"

    async def execute(self, command: dict, dry_run: bool = False) -> ActionResult:
        folder_path = command["path"]
        path = Path(folder_path)

        if not path.exists():
            return ActionResult(success=False, error=f"Path not found: {path}", message="Папка не найдена")

        if dry_run:
            return ActionResult(success=True, message=f"Открыть папку: {path}")

        try:
            if IS_WINDOWS:
                subprocess.Popen(["explorer", str(path)])
            elif sys.platform == "darwin":
                subprocess.Popen(["open", str(path)])
            else:
                subprocess.Popen(["xdg-open", str(path)])
            logger.info(f"Opened folder: {path}")
            return ActionResult(success=True, message=f"Открываю папку: {path.name}")
        except Exception as e:
            logger.error(f"Failed to open folder: {e}")
            return ActionResult(success=False, error=str(e), message="Ошибка открытия папки")

    def get_capability(self) -> dict:
        return {"action": "open_folder", "description": "Открыть папку в проводнике", "params": {"path": "string"}}


class OpenUrlAction(BaseAction):
    action_name = "open_url"

    async def execute(self, command: dict, dry_run: bool = False) -> ActionResult:
        url = command["url"]

        if dry_run:
            return ActionResult(success=True, message=f"Открыть URL: {url}")

        try:
            if IS_WINDOWS:
                subprocess.Popen(["start", url], shell=True)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", url])
            else:
                subprocess.Popen(["xdg-open", url])
            logger.info(f"Opened URL: {url}")
            return ActionResult(success=True, message=f"Открываю сайт")
        except Exception as e:
            logger.error(f"Failed to open URL: {e}")
            return ActionResult(success=False, error=str(e), message="Не удалось открыть сайт")

    def get_capability(self) -> dict:
        return {"action": "open_url", "description": "Открыть сайт в браузере", "params": {"url": "string"}}
