"""MATE adapter."""

from __future__ import annotations

import os
from typing import List

from distromod.adapters.base import DesktopAdapter
from distromod.adapters.gsettings_common import GSettingsMixin


class MateAdapter(GSettingsMixin, DesktopAdapter):
    """Adapter for the MATE desktop."""

    name = "mate"
    display_name = "MATE"

    interface_schema = "org.mate.interface"
    background_schema = "org.mate.background"
    background_key = "picture-filename"
    background_is_uri = False
    cursor_schema = "org.mate.peripherals-mouse"
    cursor_key = "cursor-theme"
    supports_color_scheme = False

    def is_available(self) -> bool:
        if not self.gsettings_available():
            return False
        desktop = os.environ.get("XDG_CURRENT_DESKTOP", "").lower()
        session = os.environ.get("DESKTOP_SESSION", "").lower()
        return "mate" in desktop or "mate" in session

    def get_supported_features(self) -> List[str]:
        return self._gsettings_features()
