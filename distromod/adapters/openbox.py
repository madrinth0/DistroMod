"""Openbox adapter.

Openbox is an X11 window manager without a wallpaper daemon; ``feh`` /
``nitrogen`` (and similar) are used.  GTK themes are honoured through the GTK
``settings.ini`` files.
"""

from __future__ import annotations

from distromod.adapters.wm_base import LightweightWMAdapter


class OpenboxAdapter(LightweightWMAdapter):
    """Adapter for the Openbox window manager."""

    name = "openbox"
    display_name = "Openbox"

    desktop_tokens = ("openbox",)
