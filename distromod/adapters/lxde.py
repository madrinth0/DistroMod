"""LXDE adapter.

LXDE combines the Openbox window manager with the PCManFM desktop, which is
responsible for the wallpaper.  GTK appearance is read from ``settings.ini``.
"""

from __future__ import annotations

from distromod.adapters.wm_base import LightweightWMAdapter


class LxdeAdapter(LightweightWMAdapter):
    """Adapter for the LXDE desktop."""

    name = "lxde"
    display_name = "LXDE"

    desktop_tokens = ("lxde",)
