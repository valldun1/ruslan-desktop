"""Анимации спрайта Руслана — проигрывание кадров по таймеру.

Состояния персонажа: idle, thinking, speaking, happy, sad, working.
Каждое состояние — это PNG-файл в assets/sprites/{state}.png, загружаемый через Pillow.
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable

from loguru import logger
from PIL import Image, ImageTk

# Состояния персонажа
ANIM_STATES = frozenset({"idle", "thinking", "speaking", "happy", "sad", "working"})


class SpriteAnimator:
    """Проигрывает кадры анимации по таймеру.

    Загружает PNG-спрайты из assets/sprites/{state}.png через Pillow (ImageTk.PhotoImage).
    Если PNG нет для состояния — возвращает None (оверлей использует эмодзи-заглушку).
    """

    def __init__(self, assets_dir: str | Path, on_frame: Callable[[str], None]) -> None:
        """
        Args:
            assets_dir: Путь к корневой папке assets/.
            on_frame: Функция, вызываемая при смене кадра (принимает имя состояния).
        """
        self.assets_dir = Path(assets_dir)
        self.on_frame = on_frame
        self._sprites_dir = self.assets_dir / "sprites"
        self._images: dict[str, ImageTk.PhotoImage] = {}
        self._current_state: str = "idle"
        self._current_frame: int = 0
        self._load_sprites()

    def _load_sprites(self) -> None:
        """Загрузить PNG-спрайты из assets/sprites/*.png через Pillow."""
        if not self._sprites_dir.is_dir():
            logger.warning(f"Папка спрайтов не найдена: {self._sprites_dir}")
            return

        for state in sorted(ANIM_STATES):
            png_path = self._sprites_dir / f"{state}.png"
            if png_path.is_file():
                try:
                    img = Image.open(png_path)
                    photo = ImageTk.PhotoImage(img)
                    self._images[state] = photo
                    logger.info(f"Спрайт '{state}' загружен: {png_path.name} ({img.size})")
                except Exception as e:
                    logger.warning(f"Не удалось загрузить {png_path.name}: {e}")

        if not self._images:
            logger.warning("Спрайты не найдены — будет использован fallback на эмодзи")

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
        self.on_frame(state)

    def next_frame(self) -> ImageTk.PhotoImage | None:
        """Вернуть PhotoImage для текущего состояния или None (fallback на эмодзи)."""
        photo = self._images.get(self._current_state)
        if photo is None:
            return None
        return photo
