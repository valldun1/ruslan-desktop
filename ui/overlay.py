"""Главное окно оверлея — спрайт Always On Top на tkinter.

Замена PyQt5 (не собирается на macOS 10.13).
tkinter — встроен в Python, 0 зависимостей.
"""

from __future__ import annotations

import platform
from pathlib import Path
from typing import Any, Callable

from loguru import logger

from core.config import settings
from core.event_bus import event_bus

from .sprite_widget import SpriteAnimator
from .hotkey import GlobalHotkey
from .drag_drop import DragDropHandler

# Эмодзи для состояний (пока нет PNG-спрайтов)
STATE_EMOJI = {
    "idle": "🛡",
    "thinking": "💭",
    "speaking": "💬",
    "happy": "✨",
    "sad": "😢",
    "working": "⚙️",
}


class RuslanOverlay:
    """Прозрачное окно со спрайтом Руслана поверх всех окон.

    Размер: 128×128 (по умолчанию)
    Позиция: правый нижний угол экрана
    """

    def __init__(self, brain=None) -> None:
        self.brain = brain
        self._visible = True

        import tkinter as tk

        self.root = tk.Tk()
        self.root.title("Ruslan")
        self._size = settings.ui_sprite_size

        # Настройки окна — без рамки, поверх всех, полупрозрачное
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.attributes("-alpha", 0.92)

        # Тёмный фон для «прозрачности» на тёмном рабочем столе
        self.root.configure(bg="#1e1e1e")

        self.root.geometry(f"{self._size}x{self._size}+100+100")
        self.root.resizable(False, False)

        # Холст для спрайта
        self.canvas = tk.Canvas(
            self.root,
            width=self._size,
            height=self._size,
            highlightthickness=0,
            bg="#1e1e1e",
            bd=0,
        )
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # Плейсхолдер спрайта (🛡)
        self.sprite_id = self.canvas.create_text(
            self._size // 2,
            self._size // 2,
            text="🛡",
            font=("Helvetica", 48),
            fill="#00ff88",
            tags="sprite",
        )

        # Индикатор статуса (🌐 Hermes / 🏠 ollama)
        self.status_id = self.canvas.create_text(
            self._size - 12,
            12,
            text="🌐",
            font=("Helvetica", 11),
            fill="#00ff88",
            anchor="ne",
            tags="status",
        )

        # Аниматор
        self.animator = SpriteAnimator(
            assets_dir=settings.assets_dir,
            on_frame=self._on_animation_frame,
        )

        # Запуск анимации
        self._tick_animation()

        # Drag-and-drop (tkinter — ограниченная поддержка на macOS)
        self.drag_drop = DragDropHandler(on_file_dropped=self._on_files_dropped)

        # Горячая клавиша Cmd+Shift+R
        self.hotkey = GlobalHotkey(on_activate=self._toggle_visibility)
        self.hotkey.start()

        # Позиция: правый нижний угол
        self.root.after(100, self._place_in_corner)

        logger.info("🛡 Оверлей Руслана запущен (tkinter)")
        import asyncio
        try:
            asyncio.get_event_loop().create_task(event_bus.emit("ui:ready"))
        except RuntimeError:
            pass  # нет event loop

    def _on_animation_frame(self, path: str) -> None:
        """Смена кадра анимации — пока заглушка (нет PNG)."""
        pass

    def _tick_animation(self) -> None:
        """Тик анимации — обновить эмодзи каждые 500 мс."""
        state = self.animator.current_state
        emoji = STATE_EMOJI.get(state, "🛡")
        self.canvas.itemconfig(self.sprite_id, text=emoji)
        self.root.after(500, self._tick_animation)

    def _place_in_corner(self) -> None:
        """Поместить окно в правый нижний угол экрана."""
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        x = screen_w - self._size - 20
        y = screen_h - self._size - 40  # отступ от Dock
        self.root.geometry(f"+{x}+{y}")
        logger.debug(f"Окно размещено: ({x}, {y})")

    def _toggle_visibility(self) -> None:
        """Переключить видимость оверлея (Cmd+Shift+R)."""
        self._visible = not self._visible
        if self._visible:
            self.root.deiconify()
        else:
            self.root.withdraw()
        logger.info(f"Оверлей {'показан' if self._visible else 'скрыт'}")

    def set_animation(self, state: str) -> None:
        """Переключить анимацию персонажа."""
        self.animator.set_state(state)

    def set_status(self, status: str) -> None:
        """Обновить индикатор статуса (🌐 Hermes / 🏠 ollama)."""
        self.canvas.itemconfig(self.status_id, text=status)

    def _on_files_dropped(self, paths: list[Path]) -> None:
        """Файл сброшен на персонажа — отправить в Brain."""
        logger.info(f"Файлы сброшены: {[p.name for p in paths]}")
        if self.brain and paths:
            import anyio

            for path in paths[:3]:  # макс 3 за раз
                anyio.from_thread.run(
                    self.brain.process_request,
                    f"прочитай файл {path} и сделай краткое содержание",
                )
        self.set_animation("happy")
        self.root.after(2000, lambda: self.set_animation("idle"))

    def close(self) -> None:
        """Остановить всё при закрытии."""
        self.hotkey.stop()
        self.root.destroy()
        logger.info("Оверлей завершён")

    @classmethod
    def launch(cls, brain=None) -> "RuslanOverlay":
        """Запустить оверлей (блокирующий вызов mainloop)."""
        import tkinter as tk

        overlay = cls(brain=brain)
        overlay.root.protocol("WM_DELETE_WINDOW", overlay.close)

        # Обработка Cmd+Q
        overlay.root.bind_all("<Command-q>", lambda e: overlay.close())

        overlay.root.mainloop()
        return overlay
