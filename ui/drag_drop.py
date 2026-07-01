"""Drag-and-drop файлов на спрайт Руслана.

Пользователь бросает файл (PDF, .md, .txt и т.д.) на персонажа —
Руслан читает и обрабатывает его.
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable


class DragDropHandler:
    """Обработчик drag-and-drop файлов.

    Подключается к QMainWindow через dragEnterEvent/dropEvent.
    """

    def __init__(self, on_file_dropped: Callable[[list[Path]], None]) -> None:
        """
        Args:
            on_file_dropped: Функция, вызываемая при сбросе файлов.
                             Принимает список путей.
        """
        self.on_file_dropped = on_file_dropped

    def handle_drag_enter(self, event) -> bool:
        """Проверить, можно ли принять сброс.

        Возвращает True, если событие принято.
        """
        from PyQt5.QtCore import QUrl
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            return True
        return False

    def handle_drop(self, event) -> None:
        """Обработать сброшенные файлы."""
        from PyQt5.QtCore import QUrl

        urls: list[QUrl] = event.mimeData().urls()
        paths: list[Path] = []
        for url in urls:
            if url.isLocalFile():
                path = Path(url.toLocalFile())
                if path.is_file():
                    paths.append(path)

        if paths:
            self.on_file_dropped(paths)
