"""Actions package init — register all built-in actions once."""

from .engine import action_engine

# Only register if registry is empty (avoids double-registration on re-import)
if not action_engine._registry:
    action_engine.register_all()
