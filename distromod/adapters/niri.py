"""niri adapter.

niri is a scrollable-tiling Wayland compositor.  It has no wallpaper facility,
so ``swaybg`` / ``swww`` are used; GTK appearance is read from ``settings.ini``.
"""

from __future__ import annotations

from distromod.adapters.wm_base import LightweightWMAdapter


class NiriAdapter(LightweightWMAdapter):
    """Adapter for the niri compositor."""

    name = "niri"
    display_name = "niri"

    desktop_tokens = ("niri",)
    env_signatures = ("NIRI_SOCKET",)
