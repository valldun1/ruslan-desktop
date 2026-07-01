"""Logger setup — structured logging with loguru."""

from __future__ import annotations

import sys
from pathlib import Path

from loguru import logger

from .config import settings


def setup_logging() -> None:
    """Configure loguru: console + file, optional JSON."""
    # Remove default handler
    logger.remove()

    # Console handler
    fmt_console = (
        "<green>{time:HH:mm:ss}</green> | <level>{level:<8}</level> | <cyan>{name}</cyan> | {message}"
    )
    logger.add(
        sys.stderr,
        format=fmt_console,
        level=settings.log_level,
        colorize=True,
    )

    # File handler
    log_path = Path(settings.log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    fmt_file = "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level:<8} | {name}:{function}:{line} | {message}"
    logger.add(
        str(log_path),
        format=fmt_file,
        level=settings.log_level,
        rotation="10 MB",
        retention="30 days",
        compression="gz",
    )

    logger.info(f"Logging initialized: level={settings.log_level}, file={log_path}")
