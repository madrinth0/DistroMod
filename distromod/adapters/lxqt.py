"""LXQt adapter.

LXQt is GTK-adjacent: Qt widget themes live in ``lxqt.conf`` while GTK app
appearance is taken from ``settings.ini``.  Icon themes are configured in
``lxqt.conf`` and mirrored to GTK.
"""

from __future__ import annotations

import os
from typing import List

from distromod.adapters.base import (
    DesktopAdapter,
    FEATURE_CURSOR_THEME,
    FEATURE_FONT,
    FEATURE_GTK_THEME,
    FEATURE_ICON_THEME,
)
from distromod.adapters.gtk_common import GtkSettingsMixin
from distromod.utils.ini import read_value, set_value
from distromod.utils.paths import xdg_config_home
from distromod.utils.validation import validate_theme_name

LXQT_CONF = xdg_config_home() / "lxqt" / "lxqt.conf"


class LxqtAdapter(GtkSettingsMixin, DesktopAdapter):
    """Adapter for the LXQt desktop."""

    name = "lxqt"
    display_name = "LXQt"

    def is_available(self) -> bool:
        desktop = os.environ.get("XDG_CURRENT_DESKTOP", "").lower()
        session = os.environ.get("DESKTOP_SESSION", "").lower()
        return "lxqt" in desktop or "lxqt" in session

    def get_supported_features(self) -> List[str]:
        return [
            FEATURE_GTK_THEME,
            FEATURE_ICON_THEME,
            FEATURE_CURSOR_THEME,
            FEATURE_FONT,
        ]

    # -- icon theme (prefers lxqt.conf, mirror to GTK) ------------------------

    def get_icon_theme(self) -> str:
        value = read_value(LXQT_CONF, "General", "icon_theme")
        if value:
            return value
        return super().get_icon_theme()

    def set_icon_theme(self, theme_name: str) -> None:
        theme_name = validate_theme_name(theme_name, "icon theme")
        set_value(LXQT_CONF, "General", "icon_theme", theme_name)
        super().set_icon_theme(theme_name)

    def get_icon_config_file(self) -> str:
        return str(LXQT_CONF)
