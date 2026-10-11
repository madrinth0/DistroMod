"""COSMIC desktop adapter.

System76's COSMIC stores its configuration as RON files under
``~/.config/cosmic/``.  The desktop background lives in
``com.system76.CosmicBackground/v1/all`` and the light/dark preference in
``com.system76.CosmicTheme.Mode/v1/is_dark``.  GTK application appearance is
still read from the GTK ``settings.ini`` files.
"""

from __future__ import annotations

import os
import re
from pathlib import Path
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
from distromod.adapters.gtk_common import GtkSettingsMixin
from distromod.utils.exec import run
from distromod.utils.logging import logger
from distromod.utils.paths import which, xdg_config_home

_SOURCE_RE = re.compile(r'source\s*:\s*Path\(\s*"(?P<path>(?:[^"\\]|\\.)*)"\s*\)')


def _mode_file() -> Path:
    return xdg_config_home() / "cosmic" / "com.system76.CosmicTheme.Mode" / "v1" / "is_dark"


def _background_file() -> Path:
    return xdg_config_home() / "cosmic" / "com.system76.CosmicBackground" / "v1" / "all"


def _escape_ron(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


class CosmicAdapter(GtkSettingsMixin, DesktopAdapter):
    """Adapter for the COSMIC desktop."""

    name = "cosmic"
    display_name = "COSMIC"

    def is_available(self) -> bool:
        haystack = " ".join(
            os.environ.get(var, "").lower()
            for var in ("XDG_CURRENT_DESKTOP", "XDG_SESSION_DESKTOP", "DESKTOP_SESSION")
        )
        return "cosmic" in haystack

    def get_supported_features(self) -> List[str]:
        return [
            FEATURE_GTK_THEME,
            FEATURE_ICON_THEME,
            FEATURE_CURSOR_THEME,
            FEATURE_WALLPAPER,
            FEATURE_FONT,
            FEATURE_COLOR_SCHEME,
        ]

    # -- wallpaper ------------------------------------------------------------

    def get_wallpaper(self) -> str:
        try:
            content = _background_file().read_text(encoding="utf-8", errors="replace")
        except OSError:
            return "Unknown"
        match = _SOURCE_RE.search(content)
        if not match:
            return "Unknown"
        return match.group("path").replace('\\"', '"').replace("\\\\", "\\")

    def set_wallpaper(self, path: str) -> None:
        expanded = str(Path(path).expanduser())
        target = _background_file()
        content = (
            "(\n"
            "    all: [\n"
            "        (\n"
            '            output: "all",\n'
            f'            source: Path("{_escape_ron(expanded)}"),\n'
            "            filter_by_theme: false,\n"
            "            rotation_frequency: 3600,\n"
            "            filter_method: Lanczos,\n"
            "            scaling_mode: Zoom,\n"
            "        ),\n"
            "    ],\n"
            ")\n"
        )
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        # cosmic-config watches the directory and reloads automatically; nudge
        # the background daemon as a best effort so the change appears at once.
        if which("pkill"):
            run(["pkill", "-USR1", "-x", "cosmic-bg"], timeout=5)
        logger.debug("Wrote COSMIC background config to %s", target)

    def get_wallpaper_config_file(self) -> str:
        return str(_background_file())

    # -- colour scheme (light/dark) -------------------------------------------

    def get_color_scheme(self) -> str:
        try:
            value = _mode_file().read_text(encoding="utf-8", errors="replace").strip().lower()
        except OSError:
            return "Unknown"
        if value in ("true", "1", "yes"):
            return "prefer-dark"
        if value in ("false", "0", "no"):
            return "default"
        return "Unknown"

    def set_color_scheme(self, scheme: str) -> None:
        dark = str(scheme).strip().lower() in ("dark", "prefer-dark", "prefer_dark", "true", "1")
        target = _mode_file()
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("true\n" if dark else "false\n", encoding="utf-8")

    def list_color_schemes(self) -> List[str]:
        return ["default", "prefer-dark"]
