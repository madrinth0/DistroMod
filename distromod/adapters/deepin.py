"""Deepin (DDE) adapter.

Deepin stores appearance settings in its own dconf schema
(``com.deepin.dde.appearance``).  Unlike GNOME, the wallpaper is an array with
one URI per monitor (``background-uris``).
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import List, Optional

from distromod.adapters.base import (
    DesktopAdapter,
    FEATURE_CURSOR_THEME,
    FEATURE_FONT,
    FEATURE_GTK_THEME,
    FEATURE_ICON_THEME,
    FEATURE_WALLPAPER,
)
from distromod.adapters.gsettings_common import (
    GSettingsMixin,
    _encode_gvariant_string,
    _uri_to_path,
)

_URI_RE = re.compile(r"'(?P<quoted>(?:[^'\\]|\\.)*)'|(?P<plain>file:[^\s'\]]+)")


class DeepinAdapter(GSettingsMixin, DesktopAdapter):
    """Adapter for the Deepin Desktop Environment (DDE)."""

    name = "deepin"
    display_name = "Deepin (DDE)"

    interface_schema = "com.deepin.dde.appearance"
    background_schema = "com.deepin.dde.appearance"
    background_key = "background-uris"
    background_is_uri = True
    cursor_schema = "com.deepin.dde.appearance"
    cursor_key = "cursor-theme"
    supports_color_scheme = False

    def is_available(self) -> bool:
        if not self.gsettings_available():
            return False
        haystack = " ".join(
            os.environ.get(var, "").lower()
            for var in ("XDG_CURRENT_DESKTOP", "XDG_SESSION_DESKTOP", "DESKTOP_SESSION")
        )
        return "deepin" in haystack or "dde" in haystack

    def get_supported_features(self) -> List[str]:
        return [
            FEATURE_GTK_THEME,
            FEATURE_ICON_THEME,
            FEATURE_CURSOR_THEME,
            FEATURE_WALLPAPER,
            FEATURE_FONT,
        ]

    # -- wallpaper (array of per-monitor URIs) --------------------------------

    @staticmethod
    def _first_uri(raw: str) -> Optional[str]:
        match = _URI_RE.search(raw)
        if not match:
            return None
        value = match.group("quoted") or match.group("plain")
        return value.replace("\\'", "'").replace("\\\\", "\\") if value else None

    def get_wallpaper(self) -> str:
        raw = self._gs_get(self.background_schema, self.background_key)
        if not raw:
            return "Unknown"
        uri = self._first_uri(raw)
        if not uri:
            return "Unknown"
        return _uri_to_path(uri) or uri

    def set_wallpaper(self, path: str) -> None:
        uri = Path(path).expanduser().as_uri()
        literal = f"[{_encode_gvariant_string(uri)}]"
        self._gs_set_raw(self.background_schema, self.background_key, literal)
