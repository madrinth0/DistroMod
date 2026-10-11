"""Budgie desktop adapter.

Budgie uses the GNOME ``gsettings`` schemas for GTK/icon/cursor/font and the
desktop background (``org.gnome.desktop.background``).
"""

from __future__ import annotations

import os
from typing import List

from distromod.adapters.base import DesktopAdapter
from distromod.adapters.gsettings_common import GSettingsMixin


class BudgieAdapter(GSettingsMixin, DesktopAdapter):
    """Adapter for the Budgie desktop."""

    name = "budgie"
    display_name = "Budgie"

    def is_available(self) -> bool:
        if not self.gsettings_available():
            return False
        haystack = " ".join(
            os.environ.get(var, "").lower()
            for var in ("XDG_CURRENT_DESKTOP", "XDG_SESSION_DESKTOP", "DESKTOP_SESSION")
        )
        return "budgie" in haystack

    def get_supported_features(self) -> List[str]:
        return self._gsettings_features()
