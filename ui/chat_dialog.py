"""Диалог ввода запроса для Руслана.

Всплывающее окно, куда пользователь пишет вопрос,
а Руслан отвечает через Brain (Hermes/Ollama).
"""

from __future__ import annotations

import asyncio
import threading
import tkinter as tk
from tkinter import scrolledtext
from typing import Any, Callable

from loguru import logger


class ChatDialog:
    """Окно чата: поле ввода + вывод ответа."""

    def __init__(
        self,
        brain: Any | None = None,
        on_response: Callable[[str], None] | None = None,
        on_close: Callable[[], None] | None = None,
    ) -> None:
        self.brain = brain
        self.on_response = on_response
        self.on_close = on_close
        self.is_open = False

        self.root = tk.Toplevel()
        self.root.title("Руслан — вопрос")
        self.root.geometry("480x320+200+200")
        self.root.resizable(True, True)
        self.root.configure(bg="#1e1e1e")
        self.root.attributes("-topmost", True)

        # Поле ввода
        frame = tk.Frame(self.root, bg="#1e1e1e")
        frame.pack(fill=tk.X, padx=8, pady=(8, 4))

        self.entry = tk.Entry(
            frame,
            font=("Helvetica", 12),
            bg="#2d2d2d",
            fg="#ffffff",
            insertbackground="#00ff88",
            relief=tk.FLAT,
            bd=8,
        )
        self.entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.entry.bind("<Return>", self._on_send)

        self.send_btn = tk.Button(
            frame,
            text="→",
            font=("Helvetica", 12, "bold"),
            bg="#00ff88",
            fg="#1e1e1e",
            relief=tk.FLAT,
            cursor="hand2",
            command=self._on_send,
            bd=4,
        )
        self.send_btn.pack(side=tk.RIGHT, padx=(4, 0))

        # Область ответа
        self.output = scrolledtext.ScrolledText(
            self.root,
            font=("Helvetica", 11),
            bg="#1e1e1e",
            fg="#cccccc",
            relief=tk.FLAT,
            bd=0,
            wrap=tk.WORD,
            state=tk.DISABLED,
        )
        self.output.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0, 8))

        # Обработка закрытия
        self.root.protocol("WM_DELETE_WINDOW", self.close)

        # Статус
        self._thinking = False

    def open(self) -> None:
        """Показать диалог."""
        self.is_open = True
        self.root.deiconify()
        self.entry.focus_set()
        self._add_output("🛡 Руслан ждёт ваш вопрос...\n", "system")

    def focus(self) -> None:
        """Вернуть фокус."""
        self.root.lift()
        self.entry.focus_set()

    def close(self) -> None:
        """Закрыть диалог."""
        self.is_open = False
        if self.root:
            try:
                self.root.destroy()
            except Exception:
                pass
        if self.on_close:
            self.on_close()

    def _add_output(self, text: str, tag: str = "response") -> None:
        """Добавить текст в область вывода."""
        self.output.config(state=tk.NORMAL)
        self.output.insert(tk.END, text + "\n")
        self.output.see(tk.END)
        self.output.config(state=tk.DISABLED)

    def _on_send(self, event=None) -> None:
        """Отправить запрос в Brain."""
        if self._thinking:
            return

        text = self.entry.get().strip()
        if not text:
            return

        self.entry.delete(0, tk.END)
        self._add_output(f"👤 {text}", "user")
        self._add_output("🛡 Думаю...", "thinking")
        self._thinking = True
        self.send_btn.config(state=tk.DISABLED)

        # Запуск в фоновом потоке (Brain — асинхронный)
        thread = threading.Thread(
            target=self._process_in_thread,
            args=(text,),
            daemon=True,
        )
        thread.start()

    def _process_in_thread(self, text: str) -> None:
        """Обработать запрос в фоне."""
        try:
            if self.brain:
                # Создаём event loop для этого потока
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                result = loop.run_until_complete(self.brain.process_request(text))
                loop.close()

                if result:
                    response = result.response_text or "✅ Выполнено"
                    commands = result.commands
                    cmd_summary = ""
                    for cmd in commands:
                        if hasattr(cmd, "action"):
                            cmd_summary += f"\n  • {cmd.action}: {cmd.description or ''}"
                    full = response + cmd_summary
                else:
                    full = "❌ Не удалось обработать запрос"
            else:
                full = "⚠️ Brain не подключён. Запустите с HERMES_API_URL"
        except Exception as e:
            full = f"❌ Ошибка: {e}"

        # Обновить UI в главном потоке
        self.root.after(0, self._on_result, full)

    def _on_result(self, text: str) -> None:
        """Показать результат."""
        # Убрать "Думаю..."
        self.output.config(state=tk.NORMAL)
        # Удалить последнюю строку "Думаю..."
        lines = self.output.get("1.0", tk.END).split("\n")
        if lines and "Думаю" in lines[-2]:
            self.output.delete(f"end-2l", "end-1l")
        self.output.config(state=tk.DISABLED)

        self._add_output(f"🛡 {text}", "response")
        self._thinking = False
        self.send_btn.config(state=tk.NORMAL)
        self.entry.focus_set()

        if self.on_response:
            self.on_response(text)
