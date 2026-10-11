"""XFCE adapter (uses ``xfconf-query``)."""

from __future__ import annotations

import os
from typing import List, Optional

from distromod.adapters.base import (
    DesktopAdapter,
    FEATURE_CURSOR_SIZE,
    FEATURE_CURSOR_THEME,
    FEATURE_FONT,
    FEATURE_GTK_THEME,
    FEATURE_ICON_THEME,
    FEATURE_WALLPAPER,
)
from distromod.utils.exec import run
from distromod.utils.logging import logger
from distromod.utils.paths import which, xdg_config_home
from distromod.utils.validation import validate_font_size, validate_theme_name

XSETTINGS = "xsettings"
DESKTOP_CHANNEL = "xfce4-desktop"
_DEFAULT_WALLPAPER_PROP = "/backdrop/screen0/monitor0/workspace0/last-image"


class XfceAdapter(DesktopAdapter):
    """Adapter for the XFCE desktop."""

    name = "xfce"
    display_name = "XFCE"

    def is_available(self) -> bool:
        if which("xfconf-query") is None:
            return False
        desktop = os.environ.get("XDG_CURRENT_DESKTOP", "").lower()
        session = os.environ.get("DESKTOP_SESSION", "").lower()
        return "xfce" in desktop or "xfce" in session

    def get_supported_features(self) -> List[str]:
        return [
            FEATURE_GTK_THEME,
            FEATURE_ICON_THEME,
            FEATURE_CURSOR_THEME,
            FEATURE_CURSOR_SIZE,
            FEATURE_WALLPAPER,
            FEATURE_FONT,
        ]

    # -- xfconf helpers -------------------------------------------------------

    @staticmethod
    def _get(channel: str, prop: str) -> Optional[str]:
        result = run(["xfconf-query", "-c", channel, "-p", prop])
        if result.returncode != 0:
            return None
        return result.stdout.strip()

    @staticmethod
    def _set(channel: str, prop: str, value: str) -> None:
        result = run(["xfconf-query", "-c", channel, "-p", prop, "-s", value])
        if result.returncode != 0:
            result = run(
                ["xfconf-query", "-c", channel, "-p", prop, "-n", "-t", "string", "-s", value]
            )
        if result.returncode != 0:
            raise RuntimeError(f"xfconf-query failed for {prop}: {result.stderr.strip()}")

    # -- themes ---------------------------------------------------------------

    def get_gtk_theme(self) -> str:
        return self._get(XSETTINGS, "/Net/ThemeName") or "Unknown"

    def set_gtk_theme(self, theme_name: str) -> None:
        self._set(XSETTINGS, "/Net/ThemeName", validate_theme_name(theme_name, "GTK theme"))

    def get_icon_theme(self) -> str:
        return self._get(XSETTINGS, "/Net/IconThemeName") or "Unknown"

    def set_icon_theme(self, theme_name: str) -> None:
        self._set(XSETTINGS, "/Net/IconThemeName", validate_theme_name(theme_name, "icon theme"))

    def get_cursor_theme(self) -> str:
        return self._get(XSETTINGS, "/Gtk/CursorThemeName") or "Unknown"

    def set_cursor_theme(self, theme_name: str) -> None:
        self._set(XSETTINGS, "/Gtk/CursorThemeName", validate_theme_name(theme_name, "cursor theme"))

    def get_cursor_size(self) -> int:
        raw = self._get(XSETTINGS, "/Gtk/CursorThemeSize")
        try:
            return int(raw) if raw else 24
        except ValueError:
            return 24

    def set_cursor_size(self, size: int) -> None:
        size = validate_font_size(size, 16, 128)
        self._set(XSETTINGS, "/Gtk/CursorThemeSize", str(size))

    def get_font(self) -> str:
        return self._get(XSETTINGS, "/Gtk/FontName") or "Unknown"

    def set_font(self, font_name: str, size: Optional[int] = None) -> None:
        size = validate_font_size(size)
        family, embedded = _split_family_size(font_name)
        if size is None and embedded is not None:
            font_name, size = family, embedded
        font_name = validate_theme_name(font_name, "font")
        if size is None:
            _, size = _split_family_size(self.get_font())
            size = size or 11
        self._set(XSETTINGS, "/Gtk/FontName", f"{font_name} {size}")

    # -- wallpaper ------------------------------------------------------------

    @staticmethod
    def _wallpaper_props() -> List[str]:
        result = run(["xfconf-query", "-c", DESKTOP_CHANNEL, "-l"])
        if result.returncode != 0:
            return []
        return [line.strip() for line in result.stdout.splitlines() if line.strip().endswith("last-image")]

    def get_wallpaper(self) -> str:
        for prop in self._wallpaper_props():
            value = self._get(DESKTOP_CHANNEL, prop)
            if value:
                return value
        return "Unknown"

    def set_wallpaper(self, path: str) -> None:
        props = self._wallpaper_props()
        if not props:
            props = [_DEFAULT_WALLPAPER_PROP]
        for prop in props:
            try:
                self._set(DESKTOP_CHANNEL, prop, path)
            except RuntimeError as exc:
                logger.debug("Could not set %s: %s", prop, exc)

    # -- config files ---------------------------------------------------------

    def _xml_path(self, channel: str) -> str:
        return str(
            xdg_config_home() / "xfce4" / "xfconf" / "xfce-perchannel-xml" / f"{channel}.xml"
        )

    def get_gtk_config_file(self) -> str:
        return self._xml_path(XSETTINGS)

    def get_icon_config_file(self) -> str:
        return self._xml_path(XSETTINGS)

    def get_cursor_config_file(self) -> str:
        return self._xml_path(XSETTINGS)

    def get_font_config_file(self) -> str:
        return self._xml_path(XSETTINGS)

    def get_wallpaper_config_file(self) -> str:
        return self._xml_path(DESKTOP_CHANNEL)


def _split_family_size(value: str) -> tuple[str, Optional[int]]:
    value = (value or "").strip()
    if not value:
        return "", None
    parts = value.rsplit(" ", 1)
    if len(parts) == 2 and parts[1].isdigit():
        return parts[0], int(parts[1])
    return value, None
