"""File operations actions — move, copy, delete, search, create folder."""

from __future__ import annotations

import shutil
from pathlib import Path

from loguru import logger

from .base import BaseAction, ActionResult


class MoveFileAction(BaseAction):
    action_name = "move_file"

    async def execute(self, command: dict, dry_run: bool = False) -> ActionResult:
        source = Path(command["source"])
        dest = Path(command["destination"])

        if not source.exists():
            return ActionResult(success=False, error=f"Source not found: {source}", message="Файл не найден")

        if dry_run:
            return ActionResult(success=True, message=f"Планируется переместить {source.name} → {dest}")

        try:
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(source), str(dest))
            logger.info(f"Moved: {source} → {dest}")
            return ActionResult(success=True, message=f"Файл {source.name} перемещён")
        except Exception as e:
            logger.error(f"Move failed: {e}")
            return ActionResult(success=False, error=str(e), message="Ошибка перемещения")

    def get_capability(self) -> dict:
        return {
            "action": "move_file",
            "description": "Переместить файл из source в destination",
            "params": {"source": {"type": "string", "description": "Полный путь к файлу"}, "destination": {"type": "string", "description": "Куда переместить"}},
        }


class CopyFileAction(BaseAction):
    action_name = "copy_file"

    async def execute(self, command: dict, dry_run: bool = False) -> ActionResult:
        source = Path(command["source"])
        dest = Path(command["destination"])

        if not source.exists():
            return ActionResult(success=False, error=f"Source not found: {source}", message="Файл не найден")

        if dry_run:
            return ActionResult(success=True, message=f"Планируется копировать {source.name} → {dest}")

        try:
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(str(source), str(dest))
            logger.info(f"Copied: {source} → {dest}")
            return ActionResult(success=True, message=f"Файл {source.name} скопирован")
        except Exception as e:
            logger.error(f"Copy failed: {e}")
            return ActionResult(success=False, error=str(e), message="Ошибка копирования")

    def get_capability(self) -> dict:
        return {"action": "copy_file", "description": "Скопировать файл", "params": {"source": "string", "destination": "string"}}


class DeleteFileAction(BaseAction):
    action_name = "delete_file"

    async def execute(self, command: dict, dry_run: bool = False) -> ActionResult:
        path = Path(command["path"])
        permanent = command.get("permanent", False)

        if not path.exists():
            return ActionResult(success=False, error=f"Not found: {path}", message="Файл не найден")

        if dry_run:
            return ActionResult(success=True, message=f"Будет удалён: {path}")

        try:
            if path.is_dir():
                shutil.rmtree(path)
            else:
                path.unlink()
            logger.warning(f"Deleted: {path} (permanent={permanent})")
            return ActionResult(success=True, message=f"Удалено: {path.name}")
        except Exception as e:
            logger.error(f"Delete failed: {e}")
            return ActionResult(success=False, error=str(e), message="Ошибка удаления")

    def get_capability(self) -> dict:
        return {"action": "delete_file", "description": "Удалить файл или папку", "params": {"path": "string", "permanent": "boolean"}}


class SearchFileAction(BaseAction):
    action_name = "search_file"

    async def execute(self, command: dict, dry_run: bool = False) -> ActionResult:
        query = command["query"]
        directory = command.get("directory", str(Path.home()))
        query_lower = query.lower()

        results = []
        search_path = Path(directory)

        try:
            for f in search_path.rglob("*"):
                if f.is_file() and query_lower in f.name.lower():
                    results.append(str(f))
                    if len(results) >= 20:
                        break
        except PermissionError:
            pass

        logger.info(f"Search '{query}': found {len(results)} files")
        return ActionResult(
            success=True if results else False,
            message=f"Найдено {len(results)} файлов" if results else "Ничего не найдено",
            data={"files": results},
        )

    def get_capability(self) -> dict:
        return {"action": "search_file", "description": "Искать файл по имени", "params": {"query": "string", "directory": "string (optional)"}}


class CreateFolderAction(BaseAction):
    action_name = "create_folder"

    async def execute(self, command: dict, dry_run: bool = False) -> ActionResult:
        path = Path(command["path"])

        if dry_run:
            return ActionResult(success=True, message=f"Будет создана папка: {path}")

        try:
            path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Folder created: {path}")
            return ActionResult(success=True, message=f"Папка создана: {path.name}")
        except Exception as e:
            logger.error(f"Folder creation failed: {e}")
            return ActionResult(success=False, error=str(e), message="Ошибка создания папки")

    def get_capability(self) -> dict:
        return {"action": "create_folder", "description": "Создать папку", "params": {"path": "string"}}
