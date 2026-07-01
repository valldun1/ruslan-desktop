"""Главное окно оверлея — спрайт Always On Top на tkinter.

Замена PyQt5 (не собирается на macOS 10.13).
tkinter — встроен в Python, 0 зависимостей.
"""

from __future__ import annotations

import asyncio
import platform
from pathlib import Path
from typing import Any, Callable

from loguru import logger

from core.config import settings
from core.event_bus import event_bus

from .sprite_widget import SpriteAnimator
from .hotkey import GlobalHotkey
from .drag_drop import DragDropHandler
from .chat_dialog import ChatDialog

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

        # Тёмный фон
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
            cursor="hand2",
        )
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # Плейсхолдер спрайта — эмодзи (fallback, если нет PNG)
        self.sprite_text_id = self.canvas.create_text(
            self._size // 2,
            self._size // 2,
            text="🛡",
            font=("Helvetica", 48),
            fill="#00ff88",
            tags="sprite",
        )

        # Изображение спрайта (PNG через Pillow) — скрыто, пока нет PhotoImage
        self.sprite_img_id = self.canvas.create_image(
            self._size // 2,
            self._size // 2,
            image=None,
            tags="sprite",
            state="hidden",
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

        # Подпись «Нажми, чтобы спросить»
        self.hint_id = self.canvas.create_text(
            self._size // 2,
            self._size - 12,
            text="спросить",
            font=("Helvetica", 8),
            fill="#555555",
            tags="hint",
        )

        # Аниматор
        self.animator = SpriteAnimator(
            assets_dir=settings.assets_dir,
            on_frame=self._on_animation_frame,
        )

        # Запуск анимации
        self._tick_animation()

        # Подписка на статусы VoiceManager (если передан)
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

        # Клик по спрайту → диалог ввода
        self.canvas.tag_bind("sprite", "<Button-1>", self._on_click_sprite)
        self.canvas.tag_bind("hint", "<Button-1>", self._on_click_sprite)
        self.root.bind("<Button-1>", self._on_click_sprite)

        # Диалог чата (создаётся по клику)
        self._chat_dialog: ChatDialog | None = None

        logger.info("🛡 Оверлей Руслана запущен (tkinter)")
        try:
            asyncio.get_event_loop().create_task(event_bus.emit("ui:ready"))
        except RuntimeError:
            pass

    def _on_click_sprite(self, event=None) -> None:
        """Клик по спрайту — открыть диалог ввода."""
        self._open_chat()

    def _open_chat(self) -> None:
        """Открыть окно чата для ввода запроса."""
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
        """Ответ получен — показать реакцию."""
        self.set_animation("happy")
        self.root.after(3000, lambda: self.set_animation("idle"))

    def _on_chat_close(self) -> None:
        """Диалог закрыт."""
        self._chat_dialog = None

    def _on_animation_frame(self, state: str) -> None:
        """Смена состояния анимации."""
        logger.debug(f"Смена анимации: {state}")

    def _tick_animation(self) -> None:
        """Тик анимации — обновить спрайт каждые 500 мс."""
        photo = self.animator.next_frame()
        if photo is not None:
            # Есть PNG — показываем изображение, прячем эмодзи
            self.canvas.itemconfig(self.sprite_img_id, image=photo, state="normal")
            self.canvas.itemconfig(self.sprite_text_id, state="hidden")
        else:
            # Нет PNG — fallback на эмодзи
            state = self.animator.current_state
            emoji = STATE_EMOJI.get(state, "🛡")
            self.canvas.itemconfig(self.sprite_text_id, text=emoji, state="normal")
            self.canvas.itemconfig(self.sprite_img_id, state="hidden")
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

    # ------------------------------------------------------------------
    # VoiceManager integration
    # ------------------------------------------------------------------

    def _on_voice_status(self, status: str) -> None:
        """Обработать смену статуса голосового менеджера.

        Вызывается из фонового потока — используем root.after() для
        безопасного обновления UI в главном потоке tkinter.
        """
        self.root.after(0, self._apply_voice_status, status)

    def _apply_voice_status(self, status: str) -> None:
        """Применить статус голоса к UI (главный поток tkinter).

        Маппинг:
            'listening' → анимация thinking + индикатор 🎤
            'thinking'  → анимация thinking + индикатор 💭
            'speaking'  → анимация speaking + индикатор 💬
            'idle'      → анимация idle   + индикатор 🌐
        """
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
