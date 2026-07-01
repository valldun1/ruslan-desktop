"""Pydantic schemas for all Hermes ↔ Ruslan communication.

Every command from Hermes is validated against these models.
Add new actions by extending ActionType and creating a command model.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field


# ── Action Types ─────────────────────────────────────


class ActionType(str, Enum):
    OPEN_APP = "open_app"
    CLOSE_APP = "close_app"
    MOVE_FILE = "move_file"
    COPY_FILE = "copy_file"
    DELETE_FILE = "delete_file"
    SEARCH_FILE = "search_file"
    CREATE_FOLDER = "create_folder"
    OPEN_FOLDER = "open_folder"
    CLICK = "click"
    DOUBLE_CLICK = "double_click"
    RIGHT_CLICK = "right_click"
    TYPE_TEXT = "type_text"
    PRESS_KEY = "press_key"
    HOTKEY = "hotkey"
    SCROLL = "scroll"
    OPEN_URL = "open_url"
    SEARCH_WEB = "search_web"
    SCREENSHOT = "screenshot"
    WAIT = "wait"
    MESSAGE = "message"  # show text bubble


# ── Base Command ─────────────────────────────────────


class BaseCommand(BaseModel):
    """Every command inherits from this."""

    action: ActionType
    description: str = Field(default="", description="Human-readable description for logs")
    requires_confirmation: bool = False
    dry_run: bool = False


# ── App Commands ─────────────────────────────────────


class OpenAppCommand(BaseCommand):
    action: Literal[ActionType.OPEN_APP] = ActionType.OPEN_APP
    app_name: str = Field(..., description="App name or path")
    arguments: list[str] | None = None


class CloseAppCommand(BaseCommand):
    action: Literal[ActionType.CLOSE_APP] = ActionType.CLOSE_APP
    app_name: str = Field(..., description="App name or window title")


# ── File Commands ─────────────────────────────────────


class MoveFileCommand(BaseCommand):
    action: Literal[ActionType.MOVE_FILE] = ActionType.MOVE_FILE
    source: str = Field(..., description="Full source path")
    destination: str = Field(..., description="Full destination path")


class CopyFileCommand(BaseCommand):
    action: Literal[ActionType.COPY_FILE] = ActionType.COPY_FILE
    source: str
    destination: str


class DeleteFileCommand(BaseCommand):
    action: Literal[ActionType.DELETE_FILE] = ActionType.DELETE_FILE
    path: str
    permanent: bool = False  # False = recycle bin


class SearchFileCommand(BaseCommand):
    action: Literal[ActionType.SEARCH_FILE] = ActionType.SEARCH_FILE
    query: str
    directory: str | None = None


class CreateFolderCommand(BaseCommand):
    action: Literal[ActionType.CREATE_FOLDER] = ActionType.CREATE_FOLDER
    path: str


class OpenFolderCommand(BaseCommand):
    action: Literal[ActionType.OPEN_FOLDER] = ActionType.OPEN_FOLDER
    path: str


# ── Mouse / Keyboard ──────────────────────────────────


class ClickCommand(BaseCommand):
    action: Literal[ActionType.CLICK] = ActionType.CLICK
    x: int | None = None
    y: int | None = None
    target: str | None = Field(default=None, description="UI element text to find")


class TypeTextCommand(BaseCommand):
    action: Literal[ActionType.TYPE_TEXT] = ActionType.TYPE_TEXT
    text: str
    enter: bool = False


class HotkeyCommand(BaseCommand):
    action: Literal[ActionType.HOTKEY] = ActionType.HOTKEY
    keys: list[str]


# ── Web ────────────────────────────────────────────────


class OpenUrlCommand(BaseCommand):
    action: Literal[ActionType.OPEN_URL] = ActionType.OPEN_URL
    url: str


class SearchWebCommand(BaseCommand):
    action: Literal[ActionType.SEARCH_WEB] = ActionType.SEARCH_WEB
    query: str


# ── Utility ────────────────────────────────────────────


class ScreenshotCommand(BaseCommand):
    action: Literal[ActionType.SCREENSHOT] = ActionType.SCREENSHOT
    region: list[int] | None = None  # [x, y, w, h]


class MessageCommand(BaseCommand):
    action: Literal[ActionType.MESSAGE] = ActionType.MESSAGE
    text: str
    emotion: str | None = "neutral"


class WaitCommand(BaseCommand):
    """Used in sequences — pause execution."""
    action: Literal[ActionType.WAIT] = ActionType.WAIT
    seconds: float = 1.0


# ── Union (discriminated by action field) ─────────────

AnyCommand = (
    OpenAppCommand
    | CloseAppCommand
    | MoveFileCommand
    | CopyFileCommand
    | DeleteFileCommand
    | SearchFileCommand
    | CreateFolderCommand
    | OpenFolderCommand
    | ClickCommand
    | TypeTextCommand
    | HotkeyCommand
    | OpenUrlCommand
    | SearchWebCommand
    | ScreenshotCommand
    | MessageCommand
    | WaitCommand
)


# ── Hermes LLM Response ───────────────────────────────


class LLMResponse(BaseModel):
    """Structured response from Hermes LLM.

    Hermes generates this via system prompt + structured output.
    """

    plan: list[str] = Field(default_factory=list, description="Step-by-step plan")
    commands: list[AnyCommand] = Field(
        min_length=1,
        description="One or more commands to execute sequentially",
    )
    visual_script: list[dict] | None = Field(
        default=None,
        description="Optional animation hints: [{'animation': 'walk', 'x': 100, 'y': 200}, ...]",
    )
    response_text: str | None = Field(
        default=None,
        description="Text for Ruslan to speak after execution",
    )
