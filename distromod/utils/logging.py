"""Logging configuration for DistroMod.

Logging is intentionally non-intrusive: human-readable messages go to stderr at
WARNING level by default (so normal command output stays clean), while a full
DEBUG log is written to ``$XDG_STATE_HOME/distromod/distromod.log``.

Behaviour can be tuned with environment variables:

``DISTROMOD_LOG_LEVEL``
    Console log level (``DEBUG``, ``INFO``, ``WARNING`` ...).
``DISTROMOD_LOG_FILE``
    Override the log file location. Set to ``-`` to disable file logging.
"""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path
from typing import Optional, Union

logger = logging.getLogger("distromod")

_CONFIGURED = False
_FILE_FORMAT = "%(asctime)s %(levelname)-7s %(name)s:%(lineno)d: %(message)s"


def default_log_file() -> Path:
    """Return the default log file path following the XDG base directory spec."""
    state_home = os.environ.get("XDG_STATE_HOME") or str(Path.home() / ".local" / "state")
    return Path(state_home) / "distromod" / "distromod.log"


def setup_logging(
    level: Optional[Union[str, int]] = None,
    log_file: Optional[Union[str, Path]] = None,
    force: bool = False,
) -> logging.Logger:
    """Configure the ``distromod`` logger.

    Idempotent unless ``force`` is set, so it is safe to call from both the CLI
    and the test-suite.

    Args:
        level: Console log level. Defaults to ``DISTROMOD_LOG_LEVEL`` or WARNING.
        log_file: Log file path. ``"-"`` disables file logging.
        force: Reconfigure even if logging was already set up.

    Returns:
        The configured logger instance.
    """
    global _CONFIGURED
    if _CONFIGURED and not force:
        return logger

    resolved_level = level or os.environ.get("DISTROMOD_LOG_LEVEL", "WARNING")
    if isinstance(resolved_level, str):
        resolved_level = getattr(logging, resolved_level.upper(), logging.WARNING)

    logger.setLevel(logging.DEBUG)
    logger.propagate = False
    for handler in list(logger.handlers):
        logger.removeHandler(handler)
        handler.close()

    console = logging.StreamHandler(sys.stderr)
    console.setLevel(resolved_level)
    console.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
    logger.addHandler(console)

    target = log_file if log_file is not None else os.environ.get("DISTROMOD_LOG_FILE")
    if target is None:
        target = default_log_file()
    if str(target) != "-":
        try:
            path = Path(target).expanduser()
            path.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(path, encoding="utf-8")
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(logging.Formatter(_FILE_FORMAT))
            logger.addHandler(file_handler)
        except OSError as exc:  # pragma: no cover - depends on filesystem
            logger.debug("Could not open log file %s: %s", target, exc)

    _CONFIGURED = True
    return logger
