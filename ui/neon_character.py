"""Неоновый персонаж Руслан — рисуется на tkinter Canvas.

Вместо PNG-спрайтов — процедурная анимация:
- Неоновый человечек (зелёное свечение #00ff88)
- 6 состояний с разными позами
- Плавное покачивание/дыхание в idle
"""

from __future__ import annotations

import math
import random
from typing import Any

from loguru import logger

# Параметры неона
NEON_GREEN = "#00ff88"
NEON_DIM = "#006644"
NEON_GLOW = "#003322"
BG_DARK = "#0a0a0a"


class NeonCharacter:
    """Неоновый человечек на Canvas.

    Позы по состояниям: idle, thinking, speaking, happy, sad, working.
    Добавляет анимацию дыхания/покачивания.
    """

    def __init__(self, canvas: Any, cx: float, cy: float, scale: float = 1.0) -> None:
        """
        Args:
            canvas: tkinter.Canvas
            cx: центр X
            cy: центр Y (точка пояса персонажа)
            scale: масштаб (1.0 = ~64px высота торса)
        """
        self.canvas = canvas
        self.cx = cx
        self.cy = cy
        self.scale = scale
        self.state = "idle"
        self.frame = 0
        self._items: list[int] = []
        self._breath_offset = 0.0

    def set_state(self, state: str) -> None:
        """Переключить состояние персонажа."""
        if state != self.state:
            self.state = state
            self.frame = 0
            logger.debug(f"Неоновый персонаж: {state}")

    def next_frame(self) -> bool:
        """Следующий кадр анимации. Возвращает True если перерисовано."""
        self.frame += 1

        # Плавное дыхание (синусоида)
        self._breath_offset = math.sin(self.frame * 0.08) * 2.0 * self.scale

        self._redraw()
        return True

    def _redraw(self) -> None:
        """Стереть старые линии и нарисовать новые."""
        for item_id in self._items:
            self.canvas.delete(item_id)
        self._items = []

        # Выбрать позу по состоянию
        draw_fn = getattr(self, f"_draw_{self.state}", self._draw_idle)
        draw_fn()

    # ---- Примитивы рисования ----

    def _neon_line(
        self,
        x1: float, y1: float,
        x2: float, y2: float,
        width: float = 2.0,
        color: str = NEON_GREEN,
    ) -> None:
        """Нарисовать неоновую линию с эффектом свечения."""
        s = self.scale
        # Внешнее свечение (толстая линия, размытая stipple)
        glow_width = width * s * 3.5
        self._items.append(
            self.canvas.create_line(
                x1, y1, x2, y2,
                fill=NEON_GLOW,
                width=glow_width,
                capstyle="round",
                stipple="gray25" if glow_width > 4 else "",
            )
        )
        # Среднее свечение
        mid_width = width * s * 2.0
        if mid_width > 2:
            self._items.append(
                self.canvas.create_line(
                    x1, y1, x2, y2,
                    fill=NEON_DIM,
                    width=mid_width,
                    capstyle="round",
                    stipple="gray50" if mid_width > 3 else "",
                )
            )
        # Основная яркая линия
        self._items.append(
            self.canvas.create_line(
                x1, y1, x2, y2,
                fill=color,
                width=max(1.0, width * s),
                capstyle="round",
            )
        )

    def _neon_circle(
        self,
        cx: float, cy: float,
        r: float,
        width: float = 2.0,
        color: str = NEON_GREEN,
    ) -> None:
        """Нарисовать неоновую окружность."""
        s = self.scale
        r_scaled = r * s
        x1, y1 = cx - r_scaled, cy - r_scaled
        x2, y2 = cx + r_scaled, cy + r_scaled

        # Свечение
        glow_w = width * s * 3.0
        if glow_w > 2:
            self._items.append(
                self.canvas.create_oval(
                    x1 - glow_w, y1 - glow_w,
                    x2 + glow_w, y2 + glow_w,
                    outline=NEON_GLOW,
                    width=glow_w,
                    stipple="gray25",
                )
            )
        # Основная линия
        self._items.append(
            self.canvas.create_oval(
                x1, y1, x2, y2,
                outline=color,
                width=max(1.0, width * s),
            )
        )

    def _neon_arc(
        self,
        cx: float, cy: float,
        r: float,
        start: float, extent: float,
        width: float = 2.0,
        color: str = NEON_GREEN,
    ) -> None:
        """Нарисовать неоновую дугу."""
        s = self.scale
        r_scaled = r * s
        x1, y1 = cx - r_scaled, cy - r_scaled
        x2, y2 = cx + r_scaled, cy + r_scaled

        self._items.append(
            self.canvas.create_arc(
                x1, y1, x2, y2,
                start=start, extent=extent,
                outline=color,
                width=max(1.0, width * s),
                style="arc",
            )
        )

    # ---- Позы ----

    def _draw_idle(self) -> None:
        """Стоит прямо, руки вдоль тела, лёгкое дыхание."""
        b = self._breath_offset
        cx, cy = self.cx, self.cy + b
        s = self.scale

        # Ноги
        leg_w = 6 * s
        self._neon_line(cx, cy + 20 * s, cx - leg_w, cy + 45 * s + b, width=2)
        self._neon_line(cx, cy + 20 * s, cx + leg_w, cy + 45 * s + b, width=2)

        # Торс
        self._neon_line(cx, cy - 20 * s, cx, cy + 20 * s, width=2.5)

        # Руки (слегка отведены)
        arm_w = 10 * s
        self._neon_line(cx, cy - 10 * s, cx - arm_w, cy + 8 * s, width=1.5)
        self._neon_line(cx, cy - 10 * s, cx + arm_w, cy + 8 * s, width=1.5)

        # Голова
        head_r = 10 * s
        head_y = cy - 20 * s - head_r + b
        self._neon_circle(cx, head_y, head_r, width=2)

        # Глаза (две точки)
        eye_off = 3 * s
        eye_r = 1.5 * s
        self._items.append(
            self.canvas.create_oval(
                cx - eye_off - eye_r, head_y - 2 * s - eye_r,
                cx - eye_off + eye_r, head_y - 2 * s + eye_r,
                fill=NEON_GREEN, outline="",
            )
        )
        self._items.append(
            self.canvas.create_oval(
                cx + eye_off - eye_r, head_y - 2 * s - eye_r,
                cx + eye_off + eye_r, head_y - 2 * s + eye_r,
                fill=NEON_GREEN, outline="",
            )
        )

        # Аура (большая полупрозрачная окружность)
        aura_r = 30 * s + abs(b) * 0.5
        self._items.append(
            self.canvas.create_oval(
                cx - aura_r, cy - aura_r - 10 * s,
                cx + aura_r, cy + aura_r - 10 * s,
                outline=NEON_GLOW, width=2 * s,
                stipple="gray12",
            )
        )

    def _draw_thinking(self) -> None:
        """Рука у подбородка, задумчивая поза."""
        b = self._breath_offset * 0.5
        cx, cy = self.cx, self.cy + b
        s = self.scale

        # Ноги (чуть шире)
        leg_w = 7 * s
        self._neon_line(cx, cy + 20 * s, cx - leg_w, cy + 45 * s, width=2)
        self._neon_line(cx, cy + 20 * s, cx + leg_w, cy + 45 * s, width=2)

        # Торс (чуть наклонён)
        self._neon_line(cx - 2 * s, cy - 20 * s, cx, cy + 20 * s, width=2.5)

        # Левая рука — на поясе
        self._neon_line(cx - 2 * s, cy - 10 * s, cx - 14 * s, cy + 5 * s, width=1.5)
        self._neon_line(cx - 14 * s, cy + 5 * s, cx - 6 * s, cy + 15 * s, width=1.5)

        # Правая рука — к подбородку
        self._neon_line(cx - 2 * s, cy - 10 * s, cx + 12 * s, cy - 8 * s, width=1.5)
        self._neon_line(cx + 12 * s, cy - 8 * s, cx + 8 * s, cy - 18 * s, width=1.5)

        # Голова (чуть наклонена)
        head_r = 10 * s
        head_x = cx + 1 * s
        head_y = cy - 20 * s - head_r
        self._neon_circle(head_x, head_y, head_r, width=2)

        # Глаза (смотрят вверх)
        eye_off = 3 * s
        eye_r = 1.5 * s
        self._items.append(
            self.canvas.create_oval(
                head_x - eye_off - eye_r, head_y - 4 * s - eye_r,
                head_x - eye_off + eye_r, head_y - 4 * s + eye_r,
                fill=NEON_GREEN, outline="",
            )
        )
        self._items.append(
            self.canvas.create_oval(
                head_x + eye_off - eye_r, head_y - 4 * s - eye_r,
                head_x + eye_off + eye_r, head_y - 4 * s + eye_r,
                fill=NEON_GREEN, outline="",
            )
        )

        # "Лампочка" над головой
        bulb_y = head_y - head_r - 10 * s
        self._neon_circle(head_x, bulb_y, 3 * s, width=1.5)
        # Лучи
        for angle in [0, 45, 90, 135, 180, 225, 270, 315]:
            rad = math.radians(angle)
            lx = head_x + math.cos(rad) * 6 * s
            ly = bulb_y + math.sin(rad) * 6 * s
            self._neon_line(head_x, bulb_y, lx, ly, width=0.8)

    def _draw_speaking(self) -> None:
        """Одна рука жестикулирует, аура пульсирует."""
        b = self._breath_offset * 0.8
        cx, cy = self.cx, self.cy + b
        s = self.scale
        pulse = math.sin(self.frame * 0.15) * 0.5 + 0.5  # 0..1

        # Ноги
        leg_w = 6 * s
        self._neon_line(cx, cy + 20 * s, cx - leg_w, cy + 45 * s, width=2)
        self._neon_line(cx, cy + 20 * s, cx + leg_w, cy + 45 * s, width=2)

        # Торс
        self._neon_line(cx, cy - 20 * s, cx, cy + 20 * s, width=2.5)

        # Левая рука вниз
        self._neon_line(cx, cy - 10 * s, cx - 8 * s, cy + 10 * s, width=1.5)

        # Правая рука — жестикулирует (меняет угол)
        arm_angle = math.sin(self.frame * 0.1) * 30
        arm_rad = math.radians(arm_angle)
        ax = cx + math.cos(arm_rad) * 16 * s
        ay = cy - 10 * s - math.sin(arm_rad) * 10 * s
        self._neon_line(cx, cy - 10 * s, ax, ay, width=1.5)

        # Голова
        head_r = 10 * s
        head_y = cy - 20 * s - head_r
        self._neon_circle(cx, head_y, head_r, width=2)

        # Глаза
        eye_off = 3 * s
        eye_r = 1.5 * s
        self._items.append(
            self.canvas.create_oval(
                cx - eye_off - eye_r, head_y - 2 * s - eye_r,
                cx - eye_off + eye_r, head_y - 2 * s + eye_r,
                fill=NEON_GREEN, outline="",
            )
        )
        self._items.append(
            self.canvas.create_oval(
                cx + eye_off - eye_r, head_y - 2 * s - eye_r,
                cx + eye_off + eye_r, head_y - 2 * s + eye_r,
                fill=NEON_GREEN, outline="",
            )
        )

        # Рот (дуга, пульсирует)
        mouth_r = 4 * s
        mouth_w = 1.5 * s + pulse * s
        self._neon_arc(
            cx, head_y + 2 * s,
            mouth_r, 190, 160,
            width=mouth_w,
        )

        # Аура пульсирует
        aura_r = 28 * s + pulse * 8 * s
        self._items.append(
            self.canvas.create_oval(
                cx - aura_r, cy - aura_r - 10 * s,
                cx + aura_r, cy + aura_r - 10 * s,
                outline=NEON_GREEN if pulse > 0.7 else NEON_GLOW,
                width=1.5 * s,
                stipple="gray12",
            )
        )

    def _draw_happy(self) -> None:
        """Руки вверх, прыжок/приподнят."""
        b = abs(self._breath_offset) * 0.5
        jump = abs(math.sin(self.frame * 0.12)) * 5 * self.scale
        cx, cy = self.cx, self.cy - jump + b
        s = self.scale

        # Ноги (широко, как прыжок)
        leg_w = 10 * s
        self._neon_line(cx, cy + 20 * s, cx - leg_w, cy + 40 * s, width=2)
        self._neon_line(cx, cy + 20 * s, cx + leg_w, cy + 40 * s, width=2)

        # Торс
        self._neon_line(cx, cy - 20 * s, cx, cy + 20 * s, width=2.5)

        # Руки вверх
        self._neon_line(cx, cy - 10 * s, cx - 14 * s, cy - 30 * s, width=1.5)
        self._neon_line(cx, cy - 10 * s, cx + 14 * s, cy - 30 * s, width=1.5)

        # Голова
        head_r = 10 * s
        head_y = cy - 20 * s - head_r
        self._neon_circle(cx, head_y, head_r, width=2)

        # Глаза (радостные — дуги)
        eye_off = 3 * s
        self._neon_arc(cx - eye_off, head_y - 2 * s, 3 * s, 190, 160, width=1.2)
        self._neon_arc(cx + eye_off, head_y - 2 * s, 3 * s, 190, 160, width=1.2)

        # Рот (улыбка)
        self._neon_arc(cx, head_y + 2 * s, 4 * s, 350, 160, width=1.5)

        # Звёздочки
        for i in range(5):
            angle = self.frame * 0.05 + i * 1.26
            star_r = 20 * s + 10 * s * math.sin(self.frame * 0.03 + i)
            sx = cx + math.cos(angle) * star_r
            sy = head_y - head_r - 5 * s + math.sin(angle) * star_r * 0.5
            sz = 2 * s + s * math.sin(self.frame * 0.1 + i * 2)
            # Маленькая звезда как 4 точки
            for j in range(4):
                ja = angle + j * 1.57
                jx = sx + math.cos(ja) * sz
                jy = sy + math.sin(ja) * sz
                self._neon_line(sx, sy, jx, jy, width=0.8)

    def _draw_sad(self) -> None:
        """Поникшая поза, голова вниз, плечи опущены."""
        b = self._breath_offset * 0.3
        cx, cy = self.cx, self.cy + abs(b) + 3 * self.scale
        s = self.scale

        # Ноги (сведены)
        leg_w = 4 * s
        self._neon_line(cx, cy + 18 * s, cx - leg_w, cy + 40 * s, width=2, color=NEON_DIM)
        self._neon_line(cx, cy + 18 * s, cx + leg_w, cy + 40 * s, width=2, color=NEON_DIM)

        # Торс (сжатый)
        self._neon_line(cx, cy - 18 * s, cx, cy + 18 * s, width=2, color=NEON_DIM)

        # Руки (висят)
        self._neon_line(cx, cy - 8 * s, cx - 10 * s, cy + 15 * s, width=1.5, color=NEON_DIM)
        self._neon_line(cx, cy - 8 * s, cx + 10 * s, cy + 15 * s, width=1.5, color=NEON_DIM)

        # Голова (опущена вниз)
        head_r = 9 * s
        head_y = cy - 16 * s - head_r * 0.5  # ниже обычного
        head_x = cx + 1 * s  # чуть вбок
        self._neon_circle(head_x, head_y, head_r, width=2, color=NEON_DIM)

        # Глаза (грустные — дуги вниз)
        eye_off = 3 * s
        self._neon_arc(head_x - eye_off, head_y + 1 * s, 2.5 * s, 10, 160, width=1.2, color=NEON_DIM)
        self._neon_arc(head_x + eye_off, head_y + 1 * s, 2.5 * s, 10, 160, width=1.2, color=NEON_DIM)

        # Капелька
        drop_x = head_x - 6 * s
        drop_y = head_y + head_r + 2 * s + math.sin(self.frame * 0.1) * 3 * s
        self._neon_circle(drop_x, drop_y, 1.5 * s, width=1, color="#4488ff")

    def _draw_working(self) -> None:
        """Деловая поза — руки заняты, чуть наклонён."""
        b = self._breath_offset * 0.6
        cx, cy = self.cx, self.cy + b
        s = self.scale

        # Ноги (уверенно)
        leg_w = 7 * s
        self._neon_line(cx, cy + 20 * s, cx - leg_w, cy + 45 * s, width=2.5)
        self._neon_line(cx, cy + 20 * s, cx + leg_w, cy + 45 * s, width=2.5)

        # Торс (чуть наклонён вперёд)
        self._neon_line(cx - 2 * s, cy - 20 * s, cx, cy + 20 * s, width=3)

        # Руки (вперёд, «печатает»)
        self._neon_line(cx - 2 * s, cy - 8 * s, cx - 14 * s, cy + 2 * s, width=1.5)
        self._neon_line(cx - 14 * s, cy + 2 * s, cx - 10 * s, cy + 12 * s, width=1.5)

        self._neon_line(cx - 2 * s, cy - 8 * s, cx + 16 * s, cy - 2 * s, width=1.5)
        self._neon_line(cx + 16 * s, cy - 2 * s, cx + 12 * s, cy + 10 * s, width=1.5)

        # Голова
        head_r = 10 * s
        head_y = cy - 20 * s - head_r
        self._neon_circle(cx - 1 * s, head_y, head_r, width=2)

        # Глаза (сосредоточены)
        eye_off = 3 * s
        eye_r = 1.5 * s
        self._items.append(
            self.canvas.create_oval(
                cx - 1 * s - eye_off - eye_r, head_y - 2 * s - eye_r,
                cx - 1 * s - eye_off + eye_r, head_y - 2 * s + eye_r,
                fill=NEON_DIM, outline="",
            )
        )
        self._items.append(
            self.canvas.create_oval(
                cx - 1 * s + eye_off - eye_r, head_y - 2 * s - eye_r,
                cx - 1 * s + eye_off + eye_r, head_y - 2 * s + eye_r,
                fill=NEON_DIM, outline="",
            )
        )

        # Искры вокруг
        for i in range(3):
            angle = self.frame * 0.15 + i * 2.1
            spark_r = 18 * s + 5 * s * math.sin(self.frame * 0.05 + i)
            sx = cx + math.cos(angle) * spark_r
            sy = cy - 10 * s + math.sin(angle) * spark_r * 0.7
            spark_s = 1.5 * s + s * math.sin(self.frame * 0.2 + i * 3)
            self._items.append(
                self.canvas.create_oval(
                    sx - spark_s, sy - spark_s,
                    sx + spark_s, sy + spark_s,
                    fill=NEON_GREEN, outline="",
                    stipple="gray50",
                )
            )

    def cleanup(self) -> None:
        """Удалить все элементы с Canvas."""
        for item_id in self._items:
            try:
                self.canvas.delete(item_id)
            except Exception:
                pass
        self._items = []
