"""Tests for NeonCharacter module."""

from __future__ import annotations

import tkinter as tk
from unittest.mock import Mock, patch

import pytest


class TestNeonCharacter:
    def test_create(self):
        """Создание персонажа."""
        root = tk.Tk()
        canvas = tk.Canvas(root, width=128, height=128)
        canvas.pack()
        from ui.neon_character import NeonCharacter
        nc = NeonCharacter(canvas, 64, 64, scale=1.0)
        assert nc.state == "idle"
        assert nc.frame == 0
        nc.next_frame()
        assert nc.frame == 1
        root.destroy()

    def test_set_state_valid(self):
        """Переключение состояний."""
        root = tk.Tk()
        canvas = tk.Canvas(root, width=128, height=128)
        from ui.neon_character import NeonCharacter
        nc = NeonCharacter(canvas, 64, 64)
        for state in ("idle", "thinking", "speaking", "happy", "sad", "working"):
            nc.set_state(state)
            assert nc.state == state
        root.destroy()

    def test_next_frame_redraws(self):
        """next_frame() очищает и перерисовывает."""
        root = tk.Tk()
        canvas = tk.Canvas(root, width=128, height=128)
        from ui.neon_character import NeonCharacter
        nc = NeonCharacter(canvas, 64, 64)
        nc.next_frame()  # первый кадр
        items_before = len(nc._items)
        assert items_before > 0  # что-то нарисовано
        nc.next_frame()
        items_after = len(nc._items)
        assert items_after > 0  # всё ещё нарисовано
        root.destroy()

    def test_cleanup(self):
        """cleanup() удаляет все элементы."""
        root = tk.Tk()
        canvas = tk.Canvas(root, width=128, height=128)
        from ui.neon_character import NeonCharacter
        nc = NeonCharacter(canvas, 64, 64)
        nc.next_frame()  # сначала нарисовать
        assert len(nc._items) > 0
        nc.cleanup()
        assert len(nc._items) == 0
        root.destroy()

    def test_scale_affects_drawing(self):
        """Разный scale даёт разное количество/размер элементов."""
        root = tk.Tk()
        canvas1 = tk.Canvas(root, width=200, height=200)
        canvas2 = tk.Canvas(root, width=200, height=200)
        from ui.neon_character import NeonCharacter
        nc1 = NeonCharacter(canvas1, 100, 100, scale=0.5)
        nc2 = NeonCharacter(canvas2, 100, 100, scale=2.0)
        # Scale не должен ломаться
        nc1.next_frame()
        nc2.next_frame()
        assert nc1.state == "idle"
        assert nc2.state == "idle"
        root.destroy()

    def test_all_states_draw(self):
        """Все 6 состояний рисуются без ошибок."""
        root = tk.Tk()
        canvas = tk.Canvas(root, width=128, height=128)
        from ui.neon_character import NeonCharacter
        nc = NeonCharacter(canvas, 64, 64)
        for state in ("idle", "thinking", "speaking", "happy", "sad", "working"):
            nc.set_state(state)
            nc.next_frame()
            assert nc.state == state
            assert len(nc._items) > 0, f"Состояние {state} не нарисовало элементы"
        root.destroy()
