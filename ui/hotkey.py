"""Глобальная горячая клавиша для вызова Руслана.

macOS: pynput + CGEventTap
Windows: pynput (RegisterHotKey)
"""

from __future__ import annotations

import platform
from typing import Callable

from loguru import logger


class GlobalHotkey:
    """Регистрирует глобальную горячую клавишу.

    По умолчанию Cmd+Shift+R (macOS) или Ctrl+Shift+R (Windows).
    """

    def __init__(self, on_activate: Callable[[], None], hotkey: str | None = None) -> None:
        """
        Args:
            on_activate: Функция, вызываемая при нажатии хоткея.
            hotkey: Строка вида 'cmd+shift+r' или 'ctrl+shift+r'.
                    Если None — автоопределение по платформе.
        """
        self.on_activate = on_activate
        self._listener = None

        if hotkey is None:
            system = platform.system()
            if system == "Darwin":
                hotkey = "<cmd>+<shift>+r"
            else:
                hotkey = "<ctrl>+<shift>+r"
        self._hotkey = hotkey

    def start(self) -> None:
        """Запустить прослушивание хоткея в фоновом потоке."""
        if not self._hotkey:
            logger.info("Горячая клавиша отключена (пустая строка)")
            return
        try:
            from pynput import keyboard
            # Комбинация из строки
            combo = {}
            for part in self._hotkey.replace("<", "").replace(">", "").split("+"):
                part = part.strip()
                if part in ("cmd", "ctrl", "alt", "shift"):
                    combo[part] = True
                else:
                    combo[part] = part

            self._listener = keyboard.GlobalHotKeys({
                self._hotkey: self.on_activate,
            })
            self._listener.start()
            logger.info(f"Горячая клавиша запущена: {self._hotkey}")
        except ImportError:
            logger.warning("pynput не установлен — горячая клавиша недоступна")
        except Exception as e:
            logger.error(f"Ошибка запуска хоткея: {e}")

    def stop(self) -> None:
        """Остановить прослушивание."""
        if self._listener:
            self._listener.stop()
            self._listener = None
            logger.info("Горячая клавиша остановлена")
