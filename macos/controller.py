"""macOS Controller — AppleScript + pyautogui for macOS UI automation.

This is the sole module with macOS-specific code.
Other modules must NOT call AppleScript or pyautogui directly.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Any

from loguru import logger

from core.config import settings


class MacOSController:
    """Controls macOS: apps, windows, mouse, keyboard, files."""

    def __init__(self) -> None:
        self._pyautogui = None
        self._initialized = False

    @property
    def is_macos(self) -> bool:
        return sys.platform == "darwin"

    def init(self) -> None:
        if self._initialized:
            return
        if not self.is_macos:
            logger.warning("Not on macOS — MacOSController is a stub")
            self._initialized = True
            return
        try:
            import pyautogui as pg
            self._pyautogui = pg
            self._pyautogui.FAILSAFE = True
            self._pyautogui.PAUSE = 0.1
            logger.info("pyautogui initialized (macOS)")
            self._initialized = True
        except ImportError:
            logger.warning("pyautogui not installed — MacOSController is a stub")

    # ── AppleScript helpers ──

    def _osascript(self, script: str) -> str:
        """Run AppleScript and return stdout."""
        try:
            result = subprocess.run(
                ["osascript", "-e", script],
                capture_output=True, text=True, timeout=10,
            )
            return result.stdout.strip()
        except Exception as e:
            logger.error(f"osascript failed: {e}")
            return ""

    # ── App control ──

    def open_app(self, app_name: str) -> bool:
        """Open application by name (e.g. 'Telegram', 'Safari')."""
        try:
            subprocess.Popen(["open", "-a", app_name])
            logger.info(f"Opened app: {app_name}")
            return True
        except Exception as e:
            logger.error(f"open_app failed: {e}")
            return False

    def close_app(self, app_name: str) -> bool:
        """Quit application gracefully."""
        self._osascript(f'tell application "{app_name}" to quit')
        logger.info(f"Closed app: {app_name}")
        return True

    def activate_app(self, app_name: str) -> bool:
        """Bring app to front."""
        self._osascript(f'tell application "{app_name}" to activate')
        return True

    def get_open_apps(self) -> list[str]:
        """Return list of foreground app names."""
        raw = self._osascript(
            'tell application "System Events" to get name of every process whose background only is false'  # noqa: E501
        )
        if not raw:
            return []
        return [a.strip() for a in raw.split(",")]

    # ── Finder / Files ──

    def open_folder(self, path: str) -> bool:
        """Open folder in Finder."""
        try:
            subprocess.Popen(["open", path])
            return True
        except Exception as e:
            logger.error(f"open_folder failed: {e}")
            return False

    def open_url(self, url: str) -> bool:
        """Open URL in default browser."""
        try:
            subprocess.Popen(["open", url])
            return True
        except Exception as e:
            logger.error(f"open_url failed: {e}")
            return False

    # ── Mouse (pyautogui) ──

    def move_to(self, x: int, y: int, duration: float = 0.3) -> None:
        if not self._pyautogui:
            return
        self._pyautogui.moveTo(x, y, duration=duration)
        logger.debug(f"Mouse moved to ({x}, {y})")

    def click(self, x: int | None = None, y: int | None = None, button: str = "left") -> None:
        if not self._pyautogui:
            return
        self._pyautogui.click(x=x, y=y, button=button)

    def double_click(self, x: int | None = None, y: int | None = None) -> None:
        if not self._pyautogui:
            return
        self._pyautogui.doubleClick(x=x, y=y)

    def right_click(self, x: int | None = None, y: int | None = None) -> None:
        self.click(x=x, y=y, button="right")

    def scroll(self, clicks: int) -> None:
        if not self._pyautogui:
            return
        self._pyautogui.scroll(clicks)

    # ── Keyboard (pyautogui) ──

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

    # ── Notifications ──

    def show_notification(self, title: str, text: str) -> None:
        """Show macOS notification banner."""
        self._osascript(f'display notification "{text}" with title "{title}"')


macos_controller = MacOSController()
