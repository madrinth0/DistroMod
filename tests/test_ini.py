"""Tests for the INI keyfile helpers."""

from __future__ import annotations

from distromod.utils.ini import delete_value, read_value, set_value


def test_set_and_read_existing_group(tmp_path):
    path = tmp_path / "kdeglobals"
    path.write_text("[General]\nColorSchemeHash=abc\n\n[Icons]\nTheme=breeze\n")

    set_value(path, "Icons", "Theme", "Papirus")
    assert read_value(path, "Icons", "Theme") == "Papirus"
    # Unrelated content is preserved.
    assert read_value(path, "General", "ColorSchemeHash") == "abc"


def test_add_new_key_to_existing_group(tmp_path):
    path = tmp_path / "kcminputrc"
    path.write_text("[Mouse]\ncursorSize=24\n")
    set_value(path, "Mouse", "cursorTheme", "Bibata")
    assert read_value(path, "Mouse", "cursorTheme") == "Bibata"
    assert read_value(path, "Mouse", "cursorSize") == "24"


def test_create_new_group_and_file(tmp_path):
    path = tmp_path / "nested" / "settings.ini"
    set_value(path, "Settings", "gtk-theme-name", "Adwaita")
    assert path.is_file()
    assert read_value(path, "Settings", "gtk-theme-name") == "Adwaita"


def test_read_missing_returns_default(tmp_path):
    assert read_value(tmp_path / "nope.ini", "A", "B", default="x") == "x"


def test_delete_value(tmp_path):
    path = tmp_path / "f.ini"
    path.write_text("[G]\na=1\nb=2\n")
    delete_value(path, "G", "a")
    assert read_value(path, "G", "a") is None
    assert read_value(path, "G", "b") == "2"
