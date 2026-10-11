"""i3 (and i3-gaps) adapter.

i3 is an X11 window manager: GTK appearance is read from ``settings.ini`` and
wallpapers are set with a helper such as ``feh`` or ``nitrogen``.
"""

from __future__ import annotations

from distromod.adapters.wm_base import LightweightWMAdapter


class I3Adapter(LightweightWMAdapter):
    """Adapter for the i3 window manager."""

    name = "i3"
    display_name = "i3"

    desktop_tokens = ("i3", "i3-gaps")
    env_signatures = ("I3SOCK",)
