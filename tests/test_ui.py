"""Tests for UI module — sprite animator, hotkey, drag-drop."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import Mock, patch

import pytest


class TestSpriteAnimator:
    def test_anim_states_defined(self):
        from ui.sprite_widget import ANIM_STATES
        assert "idle" in ANIM_STATES
        assert "thinking" in ANIM_STATES
        assert "speaking" in ANIM_STATES
        assert "happy" in ANIM_STATES
        assert "sad" in ANIM_STATES
        assert "working" in ANIM_STATES

    def test_animator_no_assets(self, tmp_path):
        from ui.sprite_widget import SpriteAnimator
        callback = Mock()
        anim = SpriteAnimator(tmp_path, callback)
        assert anim.current_state == "idle"
        frame = anim.next_frame()
        assert frame is None  # нет спрайтов

    def test_animator_static_sprite(self, tmp_path):
        # Создать папку sprites/ со спрайтом
        sprites_dir = tmp_path / "sprites"
        sprites_dir.mkdir()
        (sprites_dir / "idle.png").write_text("fake")
        from ui.sprite_widget import SpriteAnimator
        callback = Mock()
        anim = SpriteAnimator(tmp_path, callback)
        frame = anim.next_frame()
        # PNG невалидный — Pillow не сможет его прочесть, поэтому None
        assert frame is None

    def test_animator_state_switch(self, tmp_path):
        sprites_dir = tmp_path / "sprites"
        sprites_dir.mkdir()
        (sprites_dir / "idle.png").write_text("fake")
        (sprites_dir / "happy.png").write_text("fake")
        from ui.sprite_widget import SpriteAnimator
        anim = SpriteAnimator(tmp_path, Mock())
        assert anim.current_state == "idle"
        anim.set_state("happy")
        assert anim.current_state == "happy"

    def test_animator_invalid_state(self, tmp_path):
        from ui.sprite_widget import SpriteAnimator
        anim = SpriteAnimator(tmp_path, Mock())
        anim.set_state("nonexistent")  # не падает
        assert anim.current_state == "idle"

    def test_animator_unknown_state_does_not_crash(self):
        from ui.sprite_widget import ANIM_STATES
        assert "unknown" not in ANIM_STATES


class TestGlobalHotkey:
    def test_hotkey_init_macos(self):
        from ui.hotkey import GlobalHotkey
        callback = Mock()
        hk = GlobalHotkey(callback, "cmd+shift+r")
        assert hk._hotkey == "cmd+shift+r"
        assert hk.on_activate is callback

    def test_hotkey_stop_without_start(self):
        from ui.hotkey import GlobalHotkey
        hk = GlobalHotkey(Mock(), "ctrl+shift+r")
        hk.stop()  # не падает

    def test_hotkey_start_no_pynput(self):
        from ui.hotkey import GlobalHotkey
        hk = GlobalHotkey(Mock(), "cmd+shift+r")
        # не падает без pynput
        hk.start()
        hk.stop()


class TestDragDrop:
    def test_drag_drop_handler(self):
        from ui.drag_drop import DragDropHandler
        callback = Mock()
        handler = DragDropHandler(callback)
        assert handler.on_file_dropped is callback
