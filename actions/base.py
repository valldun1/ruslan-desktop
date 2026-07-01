"""Base Action — abstract class for all executable actions.

Each action is a self-contained command unit.
Add new actions by subclassing BaseAction and registering in engine.py.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel, Field


class ActionResult(BaseModel):
    """Standard result from any action execution."""

    success: bool
    message: str = Field(default="", description="Human-readable result")
    data: dict = Field(default_factory=dict)
    error: str | None = None


class BaseAction(ABC):
    """Abstract action — implement execute() and capability."""

    @abstractmethod
    async def execute(self, command: dict, dry_run: bool = False) -> ActionResult:
        """Execute the action with given parameters."""
        ...

    @abstractmethod
    def get_capability(self) -> dict:
        """Return capability descriptor for Hermes."""
        ...

    @property
    @abstractmethod
    def action_name(self) -> str:
        """Unique action name (matches action field in JSON)."""
        ...
