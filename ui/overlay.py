"""Главное окно оверлея — прозрачный спрайт Always On Top.

Замена Godot 4. PyQt5 QMainWindow:
- Qt::WindowStaysOnTopHint — поверх всех окон
- Qt::FramelessWindowHint — без рамки
- Qt::WA_TranslucentBackground — прозрачный фон
- Qt::Tool — не показывается в панели задач
"""

from __future__ import annotations

import platform
from pathlib import Path

from loguru import logger

from core.config import settings
from core.event_bus import event_bus

from .sprite_widget import SpriteAnimator
from .hotkey import GlobalHotkey
from .drag_drop import DragDropHandler

# PyQt5 — импорт с try, чтобы проект грузился без PyQt5
try:
    from PyQt5.QtCore import Qt, QTimer, QRect
    from PyQt5.QtGui import QPixmap, QPainter, QColor, QFont, QPalette
    from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QWidget, QVBoxLayout
    PYQT_AVAILABLE = True
except ImportError:
    PYQT_AVAILABLE = False
    QMainWindow = object  # type: ignore


class RuslanOverlay(QMainWindow if PYQT_AVAILABLE else object):  # type: ignore
    """Прозрачное окно со спрайтом Руслана поверх всех окон.

    Размер: 128×128 (по умолчанию)
    Позиция: правый нижний угол экрана
    """

    def __init__(self, brain=None) -> None:
        if not PYQT_AVAILABLE:
            raise RuntimeError("PyQt5 не установлен. Установи: pip install ruslan[ui]")

        super().__init__()

        self.brain = brain
        self._visible = True

        # Настройки окна
        self.setWindowFlags(
            Qt.WindowStaysOnTopHint |
            Qt.FramelessWindowHint |
            Qt.Tool |
            Qt.WindowTransparentForInput  # не перехватывает клики (кроме спрайта)
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_NoSystemBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)

        # Спрайт
        self.sprite_label = QLabel(self)
        self._size = settings.ui_sprite_size
        self.setFixedSize(self._size, self._size)
        self.sprite_label.setFixedSize(self._size, self._size)

        # Загрузка спрайта
        self._load_idle_sprite()

        # Аниматор
        self.animator = SpriteAnimator(
            assets_dir=settings.assets_dir,
            on_frame=self._on_animation_frame,
        )

        # Таймер анимации (~5 FPS для idle)
        self._anim_timer = QTimer(self)
        self._anim_timer.timeout.connect(self._tick_animation)
        self._anim_timer.start(200)  # 200 ms

        # Drag-and-drop
        self.drag_drop = DragDropHandler(on_file_dropped=self._on_files_dropped)
        self.setAcceptDrops(True)

        # Горячая клавиша
        self.hotkey = GlobalHotkey(on_activate=self._toggle_visibility)
        self.hotkey.start()

        # Позиция: правый нижний угол
        self._place_in_corner()

        # Индикатор статуса (🌐 / 🏠)
        self.status_label = QLabel("🌐", self)
        self.status_label.setStyleSheet("color: white; font-size: 14px; background: transparent;")
        self.status_label.move(self._size - 24, 0)
        self.status_label.adjustSize()

        logger.info("Оверлей Руслана запущен")
        event_bus.emit("ui:ready")

    def _load_idle_sprite(self) -> None:
        """Загрузить статичный спрайт для idle."""
        sprite_path = settings.assets_dir / "ruslan_idle.png"
        if sprite_path.exists():
            pixmap = QPixmap(str(sprite_path))
            if not pixmap.isNull():
                scaled = pixmap.scaled(
                    self._size, self._size,
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation,
                )
                self.sprite_label.setPixmap(scaled)
                return
        # Плейсхолдер если спрайта нет
        self.sprite_label.setText("🛡")
        self.sprite_label.setStyleSheet(
            "font-size: 64px; background: transparent; color: #00ff88;"
        )
        self.sprite_label.setAlignment(Qt.AlignCenter)

    def _on_animation_frame(self, path: str) -> None:
        """Смена кадра анимации."""
        pixmap = QPixmap(path)
        if not pixmap.isNull():
            scaled = pixmap.scaled(
                self._size, self._size,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation,
            )
            self.sprite_label.setPixmap(scaled)

    def _tick_animation(self) -> None:
        """Тик анимации — следующий кадр."""
        frame = self.animator.next_frame()
        if frame:
            self._on_animation_frame(frame)

    def _place_in_corner(self) -> None:
        """Поместить окно в правый нижний угол экрана."""
        screen = QApplication.primaryScreen()
        if screen:
            geometry = screen.availableGeometry()
            x = geometry.right() - self._size - 20
            y = geometry.bottom() - self._size - 20
            self.move(x, y)
            logger.debug(f"Окно размещено: ({x}, {y})")

    def _toggle_visibility(self) -> None:
        """Переключить видимость оверлея (Cmd+Shift+R)."""
        self._visible = not self._visible
        self.setVisible(self._visible)
        logger.info(f"Оверлей {'показан' if self._visible else 'скрыт'}")

    def set_animation(self, state: str) -> None:
        """Переключить анимацию персонажа."""
        self.animator.set_state(state)

    def set_status(self, status: str) -> None:
        """Обновить индикатор статуса (🌐 Hermes / 🏠 ollama)."""
        self.status_label.setText(status)

    def _on_files_dropped(self, paths: list[Path]) -> None:
        """Файл сброшен на персонажа — отправить в Brain."""
        logger.info(f"Файлы сброшены: {[p.name for p in paths]}")
        if self.brain:
            import anyio
            for path in paths:
                anyio.from_thread.run(
                    self.brain.process_request,
                    f"прочитай файл {path} и сделай краткое содержание",
                )
        self.set_animation("happy")
        QTimer.singleShot(2000, lambda: self.set_animation("idle"))

    def closeEvent(self, event) -> None:
        """Остановить всё при закрытии."""
        self.hotkey.stop()
        self._anim_timer.stop()
        event.accept()

    @classmethod
    def launch(cls, brain=None) -> "RuslanOverlay":
        """Запустить оверлей в отдельном EventLoop.

        Вызывается из core.main.main().
        """
        app = QApplication.instance() or QApplication([])
        overlay = cls(brain=brain)
        overlay.show()
        app.exec_()
        return overlay
