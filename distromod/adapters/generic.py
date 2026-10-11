"""Generic fallback adapter for plain X11 / Wayland sessions.

Used when no desktop-specific adapter matches.  GTK application appearance is
managed through ``settings.ini`` and wallpapers through whichever common
wallpaper tool is installed.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import List

from distromod.adapters.base import (
    DesktopAdapter,
    FEATURE_CURSOR_THEME,
    FEATURE_FONT,
    FEATURE_GTK_THEME,
    FEATURE_ICON_THEME,
    FEATURE_WALLPAPER,
)
from distromod.adapters.gtk_common import GtkSettingsMixin
from distromod.utils.exec import ok, run, spawn
from distromod.utils.logging import logger
from distromod.utils.paths import which, xdg_state_home

_WALLPAPER_STATE = xdg_state_home() / "distromod" / "wallpaper"


class GenericX11Adapter(GtkSettingsMixin, DesktopAdapter):
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
        ]

    # -- wallpaper ------------------------------------------------------------

    def get_wallpaper(self) -> str:
        try:
            return _WALLPAPER_STATE.read_text(encoding="utf-8").strip() or "Unknown"
        except (OSError, UnicodeError):
            return "Unknown"

    def set_wallpaper(self, path: str) -> None:
        expanded = str(Path(path).expanduser())

        # Resident Wayland compositor backgrounds first.
        if which("swaybg") and spawn(["swaybg", "-i", expanded, "-m", "fill"]):
            return self._succeed(expanded)
        if which("swww") and ok(["swww", "img", expanded]):
            return self._succeed(expanded)

        candidates = [
            ["feh", "--bg-fill", expanded],
            ["xwallpaper", "--zoom", expanded],
            ["nitrogen", "--set-zoom-fill", "--save", expanded],
            ["hsetroot", "-fill", expanded],
        ]
        for argv in candidates:
            if which(argv[0]) and run(argv).returncode == 0:
                return self._succeed(expanded)

        raise RuntimeError(
            "No supported wallpaper tool found (tried swaybg, swww, feh, "
            "xwallpaper, nitrogen, hsetroot)"
        )

    @staticmethod
    def _succeed(path: str) -> None:
        try:
            _WALLPAPER_STATE.parent.mkdir(parents=True, exist_ok=True)
            _WALLPAPER_STATE.write_text(path + "\n", encoding="utf-8")
        except OSError as exc:  # pragma: no cover
            logger.debug("Could not record wallpaper state: %s", exc)

    def get_wallpaper_config_file(self) -> str:
        return str(_WALLPAPER_STATE)
