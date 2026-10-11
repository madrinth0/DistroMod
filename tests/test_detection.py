"""Tests for desktop detection and adapter selection."""

from __future__ import annotations

from distromod.detection import DesktopDetector


def test_detect_environment(monkeypatch):
    monkeypatch.setenv("XDG_CURRENT_DESKTOP", "KDE")
    monkeypatch.delenv("DESKTOP_SESSION", raising=False)
    assert DesktopDetector().detect_environment() == "KDE"


def test_detect_environment_from_desktop_session_path(monkeypatch):
    monkeypatch.delenv("XDG_CURRENT_DESKTOP", raising=False)
    monkeypatch.setenv("DESKTOP_SESSION", "/usr/share/wayland-sessions/plasma.desktop")
    assert DesktopDetector().detect_environment() == "plasma"


def test_session_type(monkeypatch):
    monkeypatch.setenv("XDG_SESSION_TYPE", "wayland")
    assert DesktopDetector().get_session_type() == "wayland"
    monkeypatch.setenv("XDG_SESSION_TYPE", "x11")
    assert DesktopDetector().get_session_type() == "x11"


def test_adapter_prefers_kde(monkeypatch):
    monkeypatch.setenv("XDG_CURRENT_DESKTOP", "KDE")
    adapter = DesktopDetector().get_adapter()
    assert adapter is not None
    assert adapter.name == "kde"


def test_generic_fallback(clean_desktop_env):
    clean_desktop_env.setenv("DISPLAY", ":0")
    adapter = DesktopDetector().get_adapter()
    assert adapter is not None
    assert adapter.name == "generic"


def test_no_adapter_without_display(clean_desktop_env):
    assert DesktopDetector().get_adapter() is None


def test_gnome_selected_when_available(clean_desktop_env, monkeypatch):
    from distromod.adapters import gnome

    monkeypatch.setattr(gnome.GnomeAdapter, "gsettings_available", staticmethod(lambda: True))
    monkeypatch.setenv("XDG_CURRENT_DESKTOP", "GNOME")
    adapter = DesktopDetector().get_adapter()
    assert adapter is not None
    assert adapter.name == "gnome"
