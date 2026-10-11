"""Tests for the desktop adapters (file-backed behaviour)."""

from __future__ import annotations

import distromod.adapters.kde as kde_module
from distromod.adapters.generic import GenericX11Adapter
from distromod.adapters.kde import KdeAdapter


def test_gtk_settings_mixin_writes_settings_ini(tmp_home):
    adapter = GenericX11Adapter()
    adapter.set_gtk_theme("Adwaita-dark")
    adapter.set_icon_theme("Papirus")
    adapter.set_cursor_theme("Bibata")
    adapter.set_font("Inter", 10)

    assert adapter.get_gtk_theme() == "Adwaita-dark"
    assert adapter.get_icon_theme() == "Papirus"
    assert adapter.get_cursor_theme() == "Bibata"
    assert adapter.get_font() == "Inter 10"

    for version in (3, 4):
        settings = tmp_home / ".config" / f"gtk-{version}.0" / "settings.ini"
        assert settings.is_file()
        assert "gtk-theme-name=Adwaita-dark" in settings.read_text()


def test_kde_themes_and_fonts(tmp_path, monkeypatch):
    kdeglobals = tmp_path / "kdeglobals"
    kcminputrc = tmp_path / "kcminputrc"
    appletsrc = tmp_path / "appletsrc"
    state = tmp_path / "wallpaper"

    kdeglobals.write_text("[General]\nColorSchemeHash=abc\n\n[Icons]\nTheme=breeze\n")
    appletsrc.write_text("[Containments][1]\nImage=file:///usr/share/wallpapers/foo.png\n")

    monkeypatch.setattr(kde_module, "KDEGLOBALS", kdeglobals)
    monkeypatch.setattr(kde_module, "KCMINPUTRC", kcminputrc)
    monkeypatch.setattr(kde_module, "PLASMA_APPLETSRC", appletsrc)
    monkeypatch.setattr(kde_module, "_WALLPAPER_STATE", state)
    monkeypatch.setattr(kde_module, "which", lambda name: None)

    adapter = KdeAdapter()
    assert adapter.get_icon_theme() == "breeze"

    adapter.set_icon_theme("Papirus")
    assert adapter.get_icon_theme() == "Papirus"
    assert "[Icons]" in kdeglobals.read_text()

    adapter.set_cursor_theme("Bibata")
    assert adapter.get_cursor_theme() == "Bibata"

    adapter.set_font("Noto Sans", 12)
    assert adapter.get_font() == "Noto Sans 12"

    assert adapter.get_wallpaper() == "/usr/share/wallpapers/foo.png"
    adapter.set_wallpaper("/tmp/opencode/wall.png")
    assert adapter.get_wallpaper() == "/tmp/opencode/wall.png"


def test_kde_not_available_on_gnome(monkeypatch):
    monkeypatch.setenv("XDG_CURRENT_DESKTOP", "GNOME")
    monkeypatch.delenv("DESKTOP_SESSION", raising=False)
    monkeypatch.delenv("KDE_FULL_SESSION", raising=False)
    monkeypatch.delenv("KDE_SESSION_VERSION", raising=False)
    assert KdeAdapter().is_available() is False
