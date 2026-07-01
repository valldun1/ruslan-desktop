"""Actions package init — register all."""

from .engine import action_engine

# Register all built-in actions on import
action_engine.register_all()
