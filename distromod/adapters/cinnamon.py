"""Cinnamon adapter."""

from __future__ import annotations

import os
from typing import List

from distromod.adapters.base import DesktopAdapter
from distromod.adapters.gsettings_common import GSettingsMixin


class CinnamonAdapter(GSettingsMixin, DesktopAdapter):
    """Adapter for the Cinnamon desktop."""

    name = "cinnamon"
    display_name = "Cinnamon"

    interface_schema = "org.cinnamon.desktop.interface"
    background_schema = "org.cinnamon.desktop.background"
    background_key = "picture-uri"
    background_is_uri = True
    cursor_schema = "org.cinnamon.desktop.interface"
    cursor_key = "cursor-theme"
    supports_color_scheme = False

    def is_available(self) -> bool:
        if not self.gsettings_available():
            return False
        desktop = os.environ.get("XDG_CURRENT_DESKTOP", "").lower()
        session = os.environ.get("DESKTOP_SESSION", "").lower()
        return "cinnamon" in desktop or "cinnamon" in session

    def get_supported_features(self) -> List[str]:
        return self._gsettings_features()
