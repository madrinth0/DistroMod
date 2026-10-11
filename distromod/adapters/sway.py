"""Sway (and sway-compatible wlroots compositors) adapter.

Sway has no wallpaper API of its own; ``swaybg`` (or ``awww``) is used.  GTK
application appearance comes from the GTK ``settings.ini`` files.
"""

from __future__ import annotations

from distromod.adapters.wm_base import LightweightWMAdapter


class SwayAdapter(LightweightWMAdapter):
    """Adapter for the Sway tiling compositor."""

    name = "sway"
    display_name = "Sway"

    desktop_tokens = ("sway",)
    env_signatures = ("SWAYSOCK",)
