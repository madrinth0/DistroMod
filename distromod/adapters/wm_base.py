"""Base class for minimal sessions and tiling window managers.

Desktops such as Sway, i3, Openbox, niri and Wayfire do not expose a wallpaper
or appearance API.  Their GTK applications read ``settings.ini`` and wallpapers
are applied with a helper tool.  This base class combines those two mixins and
provides detection based on a list of desktop tokens.
"""

from __future__ import annotations

import os
from typing import List, Sequence

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


class LightweightWMAdapter(WallpaperToolsMixin, GtkSettingsMixin, DesktopAdapter):
    """Shared behaviour for non-DE, ``settings.ini``-based sessions."""

    #: Lower-case tokens matched against the various session env variables.
    desktop_tokens: Sequence[str] = ()
    #: Extra environment variables whose presence indicates this session.
    env_signatures: Sequence[str] = ()

    def _session_haystack(self) -> str:
        return " ".join(
            os.environ.get(var, "").lower()
            for var in ("XDG_CURRENT_DESKTOP", "XDG_SESSION_DESKTOP", "DESKTOP_SESSION")
        )

    def is_available(self) -> bool:
        haystack = self._session_haystack()
        if any(token.lower() in haystack for token in self.desktop_tokens):
            return True
        return any(os.environ.get(var) for var in self.env_signatures)

    def get_supported_features(self) -> List[str]:
        return [
            FEATURE_GTK_THEME,
            FEATURE_ICON_THEME,
            FEATURE_CURSOR_THEME,
            FEATURE_WALLPAPER,
            FEATURE_FONT,
            FEATURE_COLOR_SCHEME,
        ]
