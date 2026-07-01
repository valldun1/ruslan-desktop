"""Tests for plugin system."""

from __future__ import annotations

from pathlib import Path

from plugins.manager import plugin_manager


def test_discover():
    manifests = plugin_manager.discover()
    names = [m["name"] for m in manifests]
    assert len(names) >= 1
    assert "example-plugin" in names


def test_load_example():
    example_path = Path("plugins/__example__")
    actions = plugin_manager.load_plugin(example_path)
    assert actions is not None
    assert len(actions) >= 1
    assert actions[0].__name__ == "HelloWorldAction"


def test_discover_telegram():
    manifests = plugin_manager.discover()
    names = [m["name"] for m in manifests]
    # telegram plugin should be discovered
    assert "telegram" in names


def test_manifest_valid():
    """All manifests must have name, version, capabilities."""
    manifests = plugin_manager.discover()
    for m in manifests:
        assert "name" in m
        assert "version" in m
        assert "capabilities" in m
        assert len(m["capabilities"]) >= 1
