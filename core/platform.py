"""Platform abstraction — unified access to OS-specific features.

Usage:
    from core.platform import platform
    ctrl = platform.get_controller()
    ctrl.init()
    ctrl.click(100, 200)
"""

from __future__ import annotations

import sys
import platform as _platform
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from windows.controller import WindowsController
    from macos.controller import MacOSController

ControllerType = "WindowsController | MacOSController"


class OSType(str, Enum):
    WINDOWS = "windows"
    MACOS = "macos"
    LINUX = "linux"
    ANDROID = "android"
    UNKNOWN = "unknown"


class Platform:
    """Detects OS and provides appropriate controller."""

    @property
    def os_name(self) -> OSType:
        if sys.platform == "win32":
            return OSType.WINDOWS
        if sys.platform == "darwin":
            return OSType.MACOS
        if "android" in _platform.platform().lower() or "termux" in _platform.platform().lower():
            return OSType.ANDROID
        if sys.platform.startswith("linux"):
            return OSType.LINUX
        return OSType.UNKNOWN

    @property
    def is_windows(self) -> bool:
        return self.os_name == OSType.WINDOWS

    @property
    def is_macos(self) -> bool:
        return self.os_name == OSType.MACOS

    @property
    def is_linux(self) -> bool:
        return self.os_name in (OSType.LINUX, OSType.ANDROID)

    def get_controller(self) -> ControllerType | None:
        """Return the appropriate OS controller singleton."""
        if self.is_windows:
            from windows.controller import windows_controller
            return windows_controller
        if self.is_macos:
            from macos.controller import macos_controller
            return macos_controller
        if self.is_linux:
            from windows.controller import windows_controller  # stub-compatible
            return windows_controller
        return None


platform = Platform()
