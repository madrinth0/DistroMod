"""Shared pytest fixtures for the DistroMod test-suite."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


@pytest.fixture
def tmp_home(tmp_path, monkeypatch):
    """Point the XDG directories at a temporary home directory."""
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(home / ".config"))
    monkeypatch.setenv("XDG_DATA_HOME", str(home / ".local" / "share"))
    monkeypatch.setenv("XDG_STATE_HOME", str(home / ".local" / "state"))
    monkeypatch.setenv("XDG_CACHE_HOME", str(home / ".cache"))
    return home


@pytest.fixture
def clean_desktop_env(monkeypatch):
    """Remove desktop/session related environment variables."""
    for var in (
        "XDG_CURRENT_DESKTOP",
        "DESKTOP_SESSION",
        "GNOME_SHELL_SESSION_MODE",
        "KDE_FULL_SESSION",
        "KDE_SESSION_VERSION",
        "HYPRLAND_INSTANCE_SIGNATURE",
        "XDG_SESSION_TYPE",
        "WAYLAND_DISPLAY",
        "DISPLAY",
    ):
        monkeypatch.delenv(var, raising=False)
    return monkeypatch
