"""GNOME adapter (GNOME Shell, including Ubuntu/Pop variants)."""

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
from distromod.adapters.gsettings_common import GSettingsMixin

_GNOME_DESKTOPS = ("gnome", "ubuntu", "unity", "pop", "pop:gnome", "budgie")


class GnomeAdapter(GSettingsMixin, DesktopAdapter):
    """Adapter for GNOME-based desktops."""

    name = "gnome"
    display_name = "GNOME"

    def is_available(self) -> bool:
        if not self.gsettings_available():
            return False
        desktop = os.environ.get("XDG_CURRENT_DESKTOP", "").lower()
        session = os.environ.get("DESKTOP_SESSION", "").lower()
        if any(token in desktop or token in session for token in _GNOME_DESKTOPS):
            return True
        return bool(os.environ.get("GNOME_SHELL_SESSION_MODE"))

    def get_supported_features(self) -> List[str]:
        return [
            FEATURE_GTK_THEME,
            FEATURE_ICON_THEME,
            FEATURE_CURSOR_THEME,
            FEATURE_WALLPAPER,
            FEATURE_FONT,
            FEATURE_COLOR_SCHEME,
        ]
