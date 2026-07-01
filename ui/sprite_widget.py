"""Анимации спрайта Руслана — проигрывание кадров по таймеру.

Состояния персонажа: idle, thinking, speaking, happy, sad, working.
Каждое состояние — это набор PNG-кадров в assets/ruslan_{state}_*.png
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Callable

from loguru import logger

# Состояния персонажа
ANIM_STATES = frozenset({"idle", "thinking", "speaking", "happy", "sad", "working"})


class SpriteAnimator:
    """Проигрывает кадры анимации по таймеру.

    Ищет файлы assets/ruslan_{state}_1.png, _2.png, и т.д.
    Если кадров нет — использует один статичный спрайт.
    """

    def __init__(self, assets_dir: str | Path, on_frame: Callable[[str], None]) -> None:
        """
        Args:
            assets_dir: Путь к папке со спрайтами.
            on_frame: Функция, вызываемая при смене кадра (принимает путь к PNG).
        """
        self.assets_dir = Path(assets_dir)
        self.on_frame = on_frame
        self._frames: dict[str, list[str]] = {}
        self._current_state: str = "idle"
        self._current_frame: int = 0
        self._scan_frames()

    def _scan_frames(self) -> None:
        """Сканировать assets/ на предмет кадров анимации."""
        for state in ANIM_STATES:
            pattern = f"ruslan_{state}_"
            frames: list[str] = []
            for f in sorted(os.listdir(self.assets_dir)):
                if pattern in f and f.endswith((".png", ".gif")):
                    frames.append(str(self.assets_dir / f))
            if frames:
                self._frames[state] = frames
                logger.info(f"Анимация '{state}': {len(frames)} кадров")

        # Если кадров нет — статичный спрайт
        for state in ANIM_STATES:
            if state not in self._frames:
                static = self.assets_dir / f"ruslan_{state}.png"
                if static.exists():
                    self._frames[state] = [str(static)]
                else:
                    # fallback на idle
                    idle = self.assets_dir / "ruslan_idle.png"
                    if idle.exists():
                        self._frames[state] = [str(idle)]
                    else:
                        self._frames[state] = []

    @property
    def current_state(self) -> str:
        return self._current_state

    def set_state(self, state: str) -> None:
        """Переключить анимацию."""
        if state not in ANIM_STATES:
            logger.warning(f"Неизвестное состояние анимации: {state}")
            return
        if state == self._current_state:
            return
        self._current_state = state
        self._current_frame = 0
        logger.debug(f"Анимация: {state}")

    def next_frame(self) -> str | None:
        """Вернуть следующий кадр для текущего состояния."""
        frames = self._frames.get(self._current_state, [])
        if not frames:
            return None
        frame = frames[self._current_frame % len(frames)]
        self._current_frame = (self._current_frame + 1) % len(frames)
        return frame
