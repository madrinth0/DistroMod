"""Wayfire adapter.

Wayfire's ``wf-shell`` draws the desktop background and reads it from
``~/.config/wf-shell.ini``.  The wallpaper is written there (and applied with a
helper tool when one is available so the change is visible immediately).  GTK
appearance comes from ``settings.ini``.
"""

from __future__ import annotations

from typing import Optional

from distromod.adapters.wallpaper_tools import apply_wallpaper
from distromod.adapters.wm_base import LightweightWMAdapter
from distromod.utils.exec import run
from distromod.utils.ini import read_value, set_value
from distromod.utils.logging import logger
from distromod.utils.paths import which, xdg_config_home

WFSHELL_INI = xdg_config_home() / "wf-shell.ini"


class WayfireAdapter(LightweightWMAdapter):
    """Adapter for the Wayfire compositor with wf-shell."""

    name = "wayfire"
    display_name = "Wayfire"

    desktop_tokens = ("wayfire",)

    # -- wallpaper (wf-shell.ini + helper tools) ------------------------------

    def get_wallpaper_native(self) -> Optional[str]:
        return read_value(WFSHELL_INI, "background", "wallpaper")

    def set_wallpaper_native(self, path: str) -> bool:
        try:
            set_value(WFSHELL_INI, "background", "wallpaper", path)
        except Exception as exc:  # pragma: no cover - defensive
            logger.debug("Could not write %s: %s", WFSHELL_INI, exc)
            return False

        if which("pkill"):
            # Best effort: nudge wf-shell to reload its configuration.
            run(["pkill", "-HUP", "-x", "wf-shell"], timeout=5)
        apply_wallpaper(path)
        return True

    def get_wallpaper_config_file(self) -> str:
        return str(WFSHELL_INI)
