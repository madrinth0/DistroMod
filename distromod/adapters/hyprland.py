"""Hyprland adapter.

Hyprland itself manages window rules and layout, while GTK app appearance (and
cursors) is controlled through the GTK ``settings.ini`` files.  Wallpapers are
handled by ``hyprpaper`` (preferred) or ``swww``.
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
from distromod.utils.exec import run
from distromod.utils.logging import logger
from distromod.utils.paths import which, xdg_config_home, xdg_state_home

HYPRPAPER_CONF = xdg_config_home() / "hypr" / "hyprpaper.conf"
_WALLPAPER_STATE = xdg_state_home() / "distromod" / "wallpaper"


class HyprlandAdapter(GtkSettingsMixin, DesktopAdapter):
    """Adapter for the Hyprland compositor."""

    name = "hyprland"
    display_name = "Hyprland"

    def is_available(self) -> bool:
        if os.environ.get("HYPRLAND_INSTANCE_SIGNATURE"):
            return True
        desktop = os.environ.get("XDG_CURRENT_DESKTOP", "").lower()
        return "hyprland" in desktop

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
            for line in HYPRPAPER_CONF.read_text(encoding="utf-8", errors="replace").splitlines():
                stripped = line.strip()
                if stripped.startswith("wallpaper"):
                    _, _, value = stripped.partition("=")
                    _, _, path = value.partition(",")
                    if path.strip():
                        return path.strip()
        except OSError:
            pass
        try:
            return _WALLPAPER_STATE.read_text(encoding="utf-8").strip() or "Unknown"
        except (OSError, UnicodeError):
            return "Unknown"

    def set_wallpaper(self, path: str) -> None:
        expanded = str(Path(path).expanduser())

        if which("swww") and run(["swww", "img", expanded]).returncode == 0:
            _remember(expanded)
            return

        self._write_hyprpaper_conf(expanded)
        hyprctl = which("hyprctl")
        if hyprctl:
            for args in (
                [hyprctl, "hyprpaper", "wallpaper", f",{expanded}"],
                [hyprctl, "hyprpaper", "reload", f",{expanded}"],
            ):
                if run(args).returncode == 0:
                    _remember(expanded)
                    return
            logger.debug("hyprctl could not update hyprpaper; config written instead")
        _remember(expanded)

    @staticmethod
    def _write_hyprpaper_conf(path: str) -> None:
        HYPRPAPER_CONF.parent.mkdir(parents=True, exist_ok=True)
        content = (
            "# Managed by DistroMod\n"
            f"preload = {path}\n"
            f"wallpaper = ,{path}\n"
            "splash = false\n"
        )
        HYPRPAPER_CONF.write_text(content, encoding="utf-8")

    # -- config files ---------------------------------------------------------

    def get_wallpaper_config_file(self) -> str:
        return str(HYPRPAPER_CONF)


def _remember(path: str) -> None:
    try:
        _WALLPAPER_STATE.parent.mkdir(parents=True, exist_ok=True)
        _WALLPAPER_STATE.write_text(path + "\n", encoding="utf-8")
    except OSError as exc:  # pragma: no cover
        logger.debug("Could not record wallpaper state: %s", exc)
