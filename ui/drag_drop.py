"""Drag-and-drop файлов на спрайт Руслана.

На macOS 10.13 tkinter не поддерживает нативный DnD из Finder.
Используется эмуляция: кнопка «Загрузить файл» как fallback.
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable

from loguru import logger


class DragDropHandler:
    """Обработчик drag-and-drop файлов.

    На macOS с tkinter — ограничен. Для полноценного DnD
    требуется pyobjc (Apple Events) или внешняя библиотека.
    """

    def __init__(self, on_file_dropped: Callable[[list[Path]], None]) -> None:
        """
        Args:
            on_file_dropped: Функция при сбросе файлов.
        """
        self.on_file_dropped = on_file_dropped

    def bind_to_tk(self, widget) -> None:
        """Привязать DnD к tkinter-виджету (macOS — не работает)."""
        logger.info(
            "Drag-and-drop из Finder не поддерживается на macOS 10.13 "
            "(tkinter limitation). Используйте команду 'прочитай файл' в чате."
        )
