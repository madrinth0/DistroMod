"""Reusable GTK-settings behaviour for non-GNOME desktops.

GNOME (and Cinnamon/MATE) expose GTK settings through GSettings.  KDE, Hyprland
and plain X11/Wayland sessions instead rely on the ``settings.ini`` files read
by ``gtk3`` / ``gtk4``.  This mixin implements that file-backed behaviour and is
shared by those adapters.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from distromod.utils.ini import read_value, set_value
from distromod.utils.validation import validate_font_size, validate_theme_name

_GTK_GROUP = "Settings"
_DEFAULT_FONT_SIZE = 11


class GtkSettingsMixin:
    """GTK theme/icon/cursor/font support backed by ``settings.ini``."""

    def gtk_settings_path(self, version: int = 3) -> Path:
        """Return the ``settings.ini`` path for a GTK major version."""
        from distromod.utils.paths import xdg_config_home

        return xdg_config_home() / f"gtk-{version}.0" / "settings.ini"

    def _gtk_read(self, key: str) -> Optional[str]:
        for version in (4, 3):
            value = read_value(self.gtk_settings_path(version), _GTK_GROUP, key)
            if value is not None:
                return value
        return None

    def _gtk_write(self, key: str, value: str) -> None:
        for version in (3, 4):
            set_value(self.gtk_settings_path(version), _GTK_GROUP, key, value)

    # -- GTK theme ------------------------------------------------------------

    def get_gtk_theme(self) -> str:
        return self._gtk_read("gtk-theme-name") or "Unknown"

    def set_gtk_theme(self, theme_name: str) -> None:
        theme_name = validate_theme_name(theme_name, "GTK theme")
        self._gtk_write("gtk-theme-name", theme_name)

    def get_gtk_config_file(self) -> str:
        return str(self.gtk_settings_path(3))

    # -- icon theme -----------------------------------------------------------

    def get_icon_theme(self) -> str:
        return self._gtk_read("gtk-icon-theme-name") or "Unknown"

    def set_icon_theme(self, theme_name: str) -> None:
        theme_name = validate_theme_name(theme_name, "icon theme")
        self._gtk_write("gtk-icon-theme-name", theme_name)

    def get_icon_config_file(self) -> str:
        return str(self.gtk_settings_path(3))

    # -- cursor theme ---------------------------------------------------------

    def get_cursor_theme(self) -> str:
        return self._gtk_read("gtk-cursor-theme-name") or "Unknown"

    def set_cursor_theme(self, theme_name: str) -> None:
        theme_name = validate_theme_name(theme_name, "cursor theme")
        self._gtk_write("gtk-cursor-theme-name", theme_name)

    def get_cursor_config_file(self) -> str:
        return str(self.gtk_settings_path(3))

    # -- font -----------------------------------------------------------------

    @staticmethod
    def _split_font(value: str) -> tuple[str, Optional[int]]:
        """Split ``"Family 11"`` into ``("Family", 11)``."""
        value = (value or "").strip()
        if not value:
            return "", None
        parts = value.rsplit(" ", 1)
        if len(parts) == 2 and parts[1].isdigit():
            return parts[0], int(parts[1])
        return value, None

    def get_font(self) -> str:
        return self._gtk_read("gtk-font-name") or "Unknown"

    def set_font(self, font_name: str, size: Optional[int] = None) -> None:
        font_name = validate_theme_name(font_name, "font")
        size = validate_font_size(size)
        if size is None:
            _, existing = self._split_font(self._gtk_read("gtk-font-name") or "")
            size = existing or _DEFAULT_FONT_SIZE
        self._gtk_write("gtk-font-name", f"{font_name} {size}")

    def get_font_config_file(self) -> str:
        return str(self.gtk_settings_path(3))
