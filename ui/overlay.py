"""Главное окно оверлея — неоновый персонаж Always On Top на tkinter.

Рисует неонового человечка (NeonCharacter) на Canvas.
Без PNG-зависимостей, вся анимация процедурная.
"""

from __future__ import annotations

import asyncio
import platform
from pathlib import Path
from typing import Any, Callable

from loguru import logger

from core.config import settings
from core.event_bus import event_bus

from .neon_character import NeonCharacter
from .hotkey import GlobalHotkey
from .drag_drop import DragDropHandler
from .chat_dialog import ChatDialog


class RuslanOverlay:
    """Прозрачное окно с неоновым персонажем поверх всех окон.

    Размер: 128×128 (по умолчанию)
    Позиция: правый нижний угол экрана
    Персонаж: NeonCharacter — процедурная анимация
    """

    def __init__(self, brain=None, voice_manager=None) -> None:
        self.brain = brain
        self.voice_manager = voice_manager
        self._visible = True

        import tkinter as tk

        self.root = tk.Tk()
        self.root.title("Ruslan")
        self._size = settings.ui_sprite_size

        # Настройки окна — без рамки, поверх всех, полупрозрачное
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.attributes("-alpha", 0.92)

        # Чёрный фон (под неон)
        self.root.configure(bg="#0a0a0a")

        self.root.geometry(f"{self._size}x{self._size}+100+100")
        self.root.resizable(False, False)

        # Холст для персонажа
        self.canvas = tk.Canvas(
            self.root,
            width=self._size,
            height=self._size,
            highlightthickness=0,
            bg="#0a0a0a",
            bd=0,
            cursor="hand2",
        )
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # Индикатор статуса (🌐 Hermes / 🏠 ollama / 🎤 слушаю)
        self.status_id = self.canvas.create_text(
            self._size - 12,
            12,
            text="🌐",
            font=("Helvetica", 11),
            fill="#00ff88",
            anchor="ne",
            tags="status",
        )

        # Подпись «спросить»
        self.hint_id = self.canvas.create_text(
            self._size // 2,
            self._size - 10,
            text="спросить",
            font=("Helvetica", 8),
            fill="#555555",
            tags="hint",
        )

        # Неоновый персонаж — рисуется в центре Canvas
        scale = self._size / 80.0  # базовый размер 80px персонажа
        self.neon = NeonCharacter(
            canvas=self.canvas,
            cx=self._size // 2,
            cy=self._size // 2 + 5,  # чуть ниже центра
            scale=scale,
        )

        # Запуск анимации (каждые 200 мс для плавности)
        self._tick_animation()

        # Подписка на статусы VoiceManager
        if self.voice_manager is not None:
            self.voice_manager._on_status_change = self._on_voice_status

        # Drag-and-drop
        self.drag_drop = DragDropHandler(on_file_dropped=self._on_files_dropped)

        # Горячая клавиша
        hotkey = settings.ui_hotkey
        if hotkey and hotkey.strip():
            self.hotkey = GlobalHotkey(
                on_activate=self._toggle_visibility,
                hotkey=hotkey,
            )
        else:
            self.hotkey = GlobalHotkey(on_activate=self._toggle_visibility, hotkey="")
        self.hotkey.start()

        # Позиция: правый нижний угол
        self.root.after(100, self._place_in_corner)

        # Клик по канвасу → диалог ввода
        self.canvas.tag_bind("hint", "<Button-1>", self._on_click_sprite)
        self.root.bind("<Button-1>", self._on_click_sprite)

        # Диалог чата
        self._chat_dialog: ChatDialog | None = None

        logger.info("🟢 Неоновый Руслан запущен (tkinter)")
        try:
            asyncio.get_event_loop().create_task(event_bus.emit("ui:ready"))
        except RuntimeError:
            pass

    def _on_click_sprite(self, event=None) -> None:
        """Клик по персонажу — открыть диалог ввода."""
        self._open_chat()

    def _open_chat(self) -> None:
        """Открыть окно чата."""
        if self._chat_dialog and self._chat_dialog.is_open:
            self._chat_dialog.focus()
            return

        self._chat_dialog = ChatDialog(
            brain=self.brain,
            on_response=self._on_chat_response,
            on_close=self._on_chat_close,
        )
        self._chat_dialog.open()

    def _on_chat_response(self, text: str) -> None:
        """Ответ получен — показать happy."""
        self.set_animation("happy")
        self.root.after(3000, lambda: self.set_animation("idle"))

    def _on_chat_close(self) -> None:
        """Диалог закрыт."""
        self._chat_dialog = None

    def _tick_animation(self) -> None:
        """Тик анимации — следующий кадр неонового персонажа."""
        self.neon.next_frame()
        self.root.after(200, self._tick_animation)

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
        self.neon.set_state(state)

    def set_status(self, status: str) -> None:
        """Обновить индикатор статуса."""
        self.canvas.itemconfig(self.status_id, text=status)

    # ------------------------------------------------------------------
    # VoiceManager integration
    # ------------------------------------------------------------------

    def _on_voice_status(self, status: str) -> None:
        """Обработать смену статуса голосового менеджера (фоновый поток)."""
        self.root.after(0, self._apply_voice_status, status)

    def _apply_voice_status(self, status: str) -> None:
        """Применить статус голоса к UI (главный поток)."""
        mapping = {
            "listening": ("thinking", "🎤"),
            "thinking": ("thinking", "💭"),
            "speaking": ("speaking", "💬"),
            "idle": ("idle", "🌐"),
        }
        anim, indicator = mapping.get(status, ("idle", "🌐"))
        self.set_animation(anim)
        self.set_status(indicator)

    def _on_files_dropped(self, paths: list[Path]) -> None:
        """Файл сброшен на персонажа — отправить в Brain."""
        logger.info(f"Файлы сброшены: {[p.name for p in paths]}")
        if self.brain and paths:
            for path in paths[:3]:
                try:
                    asyncio.get_event_loop().create_task(
                        self.brain.process_request(
                            f"прочитай файл {path} и сделай краткое содержание",
                        )
                    )
                except Exception as e:
                    logger.warning(f"Ошибка отправки файла: {e}")
        self.set_animation("happy")
        self.root.after(2000, lambda: self.set_animation("idle"))

    def close(self) -> None:
        """Остановить всё при закрытии."""
        self.hotkey.stop()
        if self.voice_manager is not None:
            self.voice_manager.stop()
        self.neon.cleanup()
        if self._chat_dialog:
            self._chat_dialog.close()
        self.root.destroy()
        logger.info("Оверлей завершён")

    @classmethod
    def launch(cls, brain=None, voice_manager=None) -> "RuslanOverlay":
        """Запустить оверлей (блокирующий вызов mainloop)."""
        import tkinter as tk

        overlay = cls(brain=brain, voice_manager=voice_manager)
        overlay.root.protocol("WM_DELETE_WINDOW", overlay.close)
        overlay.root.bind_all("<Command-q>", lambda e: overlay.close())
        overlay.root.mainloop()
        return overlay
