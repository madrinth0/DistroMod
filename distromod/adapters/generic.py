"""Generic fallback adapter for plain X11 / Wayland sessions.

Used when no desktop-specific adapter matches.  GTK application appearance is
managed through ``settings.ini`` and wallpapers through whichever common
wallpaper tool is installed.
"""

from __future__ import annotations

import os
from typing import List

from distromod.adapters.base import (
    DesktopAdapter,
    FEATURE_COLOR_SCHEME,
    FEATURE_CURSOR_THEME,
    FEATURE_FONT,
    FEATURE_GTK_THEME,
    FEATURE_ICON_THEME,
    FEATURE_WALLPAPER,
)
from distromod.adapters.gtk_common import GtkSettingsMixin
from distromod.adapters.wallpaper_tools import WallpaperToolsMixin


class GenericX11Adapter(WallpaperToolsMixin, GtkSettingsMixin, DesktopAdapter):
    """Fallback adapter for unsupported / minimal environments."""

    name = "generic"
    display_name = "Generic X11/Wayland"

    def is_available(self) -> bool:
        if os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"):
            return True
        return os.environ.get("XDG_SESSION_TYPE", "").lower() in ("x11", "wayland")

    def get_supported_features(self) -> List[str]:
        return [
            FEATURE_GTK_THEME,
            FEATURE_ICON_THEME,
            FEATURE_CURSOR_THEME,
            FEATURE_WALLPAPER,
            FEATURE_FONT,
            FEATURE_COLOR_SCHEME,
        ]
