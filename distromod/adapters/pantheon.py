"""elementary Pantheon adapter.

Pantheon (Gala) reads GTK/icon/cursor/font settings and the desktop background
from the standard GNOME ``gsettings`` schemas.
"""

from __future__ import annotations

import os
from typing import List

from distromod.adapters.base import DesktopAdapter
from distromod.adapters.gsettings_common import GSettingsMixin


class PantheonAdapter(GSettingsMixin, DesktopAdapter):
    """Adapter for the elementary Pantheon desktop."""

    name = "pantheon"
    display_name = "Pantheon"

    def is_available(self) -> bool:
        if not self.gsettings_available():
            return False
        haystack = " ".join(
            os.environ.get(var, "").lower()
            for var in ("XDG_CURRENT_DESKTOP", "XDG_SESSION_DESKTOP", "DESKTOP_SESSION")
        )
        return "pantheon" in haystack

    def get_supported_features(self) -> List[str]:
        return self._gsettings_features()
