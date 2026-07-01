"""Windows Controller — sole module with access to Windows API.

All mouse/keyboard/window operations go through this module.
Other modules NEVER call Win32 directly.
"""

from __future__ import annotations

import sys
from typing import Any

from loguru import logger

from core.config import settings


class WindowsController:
    """Safe wrapper around Windows UI automation."""

    def __init__(self) -> None:
        self._pyautogui = None
        self._pywin32 = None
        self._initialized = False

    @property
    def is_windows(self) -> bool:
        return sys.platform == "win32"

    def init(self) -> None:
        """Lazy-import Windows-specific modules."""
        if self._initialized:
            return
        if not self.is_windows:
            logger.warning("Not on Windows — Windows Controller is a stub")
            self._initialized = True
            return
        try:
            import pyautogui as pg
            self._pyautogui = pg
            self._pyautogui.FAILSAFE = True
            self._pyautogui.PAUSE = 0.1
            logger.info("pyautogui initialized")
            self._initialized = True
        except ImportError:
            logger.warning("pyautogui not installed — Windows Controller is a stub")

    # ── Mouse ──

    def move_to(self, x: int, y: int, duration: float = 0.3) -> None:
        if not self._pyautogui:
            return
        self._pyautogui.moveTo(x, y, duration=duration)
        logger.debug(f"Mouse moved to ({x}, {y})")

    def click(self, x: int | None = None, y: int | None = None, button: str = "left") -> None:
        if not self._pyautogui:
            return
        self._pyautogui.click(x=x, y=y, button=button)
        logger.debug(f"Clicked {button} at ({x}, {y})")

    def double_click(self, x: int | None = None, y: int | None = None) -> None:
        if not self._pyautogui:
            return
        self._pyautogui.doubleClick(x=x, y=y)

    def scroll(self, clicks: int) -> None:
        if not self._pyautogui:
            return
        self._pyautogui.scroll(clicks)

    # ── Keyboard ──

    def type_text(self, text: str, interval: float = 0.05) -> None:
        if not self._pyautogui:
            return
        self._pyautogui.write(text, interval=interval)

    def press_key(self, key: str) -> None:
        if not self._pyautogui:
            return
        self._pyautogui.press(key)

    def hotkey(self, *keys: str) -> None:
        if not self._pyautogui:
            return
        self._pyautogui.hotkey(*keys)

    # ── Screen ──

    def screenshot(self, region: tuple[int, int, int, int] | None = None) -> Any | None:
        if not self._pyautogui:
            return None
        return self._pyautogui.screenshot(region=region)

    # ── Windows ──

    def get_window(self, title: str) -> Any | None:
        """Find window by title substring. Returns handle or None."""
        if not self.is_windows:
            return None
        try:
            import pygetwindow as gw
            windows = gw.getWindowsWithTitle(title)
            return windows[0] if windows else None
        except Exception:
            return None

    def activate_window(self, title: str) -> bool:
        win = self.get_window(title)
        if win:
            try:
                win.activate()
                return True
            except Exception:
                return False
        return False


# Global singleton
windows_controller = WindowsController()
