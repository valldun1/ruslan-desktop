"""Plugin System — load external capabilities dynamically.

Each plugin is a folder with:
- manifest.json (metadata + capabilities)
- plugin.py (Python module with Plugin class)

Plugins are loaded at startup and registered in ActionEngine.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

from loguru import logger

from actions.base import BaseAction


class PluginManager:
    """Scans and loads plugins from plugins/ directory."""

    def __init__(self, plugins_dir: str | Path | None = None) -> None:
        self._plugins_dir = Path(plugins_dir or Path(__file__).resolve().parent.parent / "plugins")
        self._plugins_dir.mkdir(parents=True, exist_ok=True)
        self._loaded: dict[str, dict] = {}

    def discover(self) -> list[dict]:
        """Find all plugin folders with manifest.json."""
        discovered = []
        for folder in self._plugins_dir.iterdir():
            if folder.is_dir():
                manifest_path = folder / "manifest.json"
                if manifest_path.exists():
                    try:
                        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                        manifest["path"] = str(folder)
                        discovered.append(manifest)
                        logger.info(f"Discovered plugin: {manifest.get('name', folder.name)}")
                    except Exception as e:
                        logger.warning(f"Invalid manifest in {folder.name}: {e}")
        return discovered

    def load_plugin(self, folder: Path) -> list[type[BaseAction]] | None:
        """Load a single plugin, return its action classes."""
        manifest_path = folder / "manifest.json"
        plugin_path = folder / "plugin.py"

        if not plugin_path.exists():
            logger.warning(f"No plugin.py in {folder.name}")
            return None

        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        plugin_name = manifest.get("name", folder.name)

        # Import plugin module
        spec = importlib.util.spec_from_file_location(plugin_name, str(plugin_path))
        if not spec or not spec.loader:
            return None

        module = importlib.util.module_from_spec(spec)
        sys.modules[plugin_name] = module
        spec.loader.exec_module(module)

        # Find BaseAction subclasses
        actions = []
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if isinstance(attr, type) and issubclass(attr, BaseAction) and attr is not BaseAction:
                actions.append(attr)

        self._loaded[plugin_name] = {
            "manifest": manifest,
            "actions": actions,
            "module": module,
        }

        logger.info(f"Loaded plugin '{plugin_name}': {len(actions)} action(s)")
        return actions

    def load_all(self) -> list[type[BaseAction]]:
        """Discover and load all plugins. Returns all action classes."""
        all_actions = []
        for manifest in self.discover():
            folder = Path(manifest["path"])
            actions = self.load_plugin(folder)
            if actions:
                all_actions.extend(actions)
        return all_actions


plugin_manager = PluginManager()
