"""XDG base-directory and command-line helpers."""

from __future__ import annotations

import os
from pathlib import Path
from typing import List, Optional


def home() -> Path:
    """Return the current user's home directory."""
    return Path(os.environ.get("HOME") or Path.home()).expanduser()


def xdg_config_home() -> Path:
    """Return ``$XDG_CONFIG_HOME`` (defaults to ``~/.config``)."""
    return Path(os.environ.get("XDG_CONFIG_HOME") or home() / ".config")


def xdg_data_home() -> Path:
    """Return ``$XDG_DATA_HOME`` (defaults to ``~/.local/share``)."""
    return Path(os.environ.get("XDG_DATA_HOME") or home() / ".local" / "share")


def xdg_state_home() -> Path:
    """Return ``$XDG_STATE_HOME`` (defaults to ``~/.local/state``)."""
    return Path(os.environ.get("XDG_STATE_HOME") or home() / ".local" / "state")


def xdg_cache_home() -> Path:
    """Return ``$XDG_CACHE_HOME`` (defaults to ``~/.cache``)."""
    return Path(os.environ.get("XDG_CACHE_HOME") or home() / ".cache")


def xdg_data_dirs() -> List[Path]:
    """Return the system data directories, most specific first."""
    raw = os.environ.get("XDG_DATA_DIRS") or "/usr/local/share:/usr/share"
    return [Path(p) for p in raw.split(":") if p]


def which(program: str) -> Optional[str]:
    """Return the absolute path to ``program`` if it exists, else ``None``."""
    import shutil

    return shutil.which(program)


def data_dirs_with_user() -> List[Path]:
    """Return data dirs including the user data home first."""
    return [xdg_data_home(), *xdg_data_dirs()]
