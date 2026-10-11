"""Desktop environment detection and adapter selection."""

from __future__ import annotations

import os
from typing import List, Optional

from distromod.adapters.base import DesktopAdapter
from distromod.adapters.cinnamon import CinnamonAdapter
from distromod.adapters.generic import GenericX11Adapter
from distromod.adapters.gnome import GnomeAdapter
from distromod.adapters.hyprland import HyprlandAdapter
from distromod.adapters.kde import KdeAdapter
from distromod.adapters.lxqt import LxqtAdapter
from distromod.adapters.mate import MateAdapter
from distromod.adapters.xfce import XfceAdapter
from distromod.utils.logging import logger


class DesktopDetector:
    """Detect the desktop environment and select an appropriate adapter."""

    # Order matters: more specific environments first, generic last.
    ADAPTERS = [
        GnomeAdapter,
        KdeAdapter,
        HyprlandAdapter,
        XfceAdapter,
        CinnamonAdapter,
        MateAdapter,
        LxqtAdapter,
        GenericX11Adapter,
    ]

    def detect_environment(self) -> Optional[str]:
        """Return a human-readable desktop environment name.

        Returns:
            The desktop environment name, or ``None`` if it cannot be
            determined.
        """
        xdg_desktop = os.environ.get("XDG_CURRENT_DESKTOP", "")
        if xdg_desktop:
            parts = [p for p in xdg_desktop.split(":") if p]
            if parts:
                return parts[0]

        desktop_session = os.environ.get("DESKTOP_SESSION", "")
        if desktop_session and desktop_session != "default":
            # DESKTOP_SESSION is sometimes a path (e.g. a .desktop file).
            return os.path.basename(desktop_session).removesuffix(".desktop")

        if os.environ.get("GNOME_SHELL_SESSION_MODE"):
            return "GNOME"
        if os.environ.get("KDE_FULL_SESSION") or os.environ.get("KDE_SESSION_VERSION"):
            return "KDE"
        if os.environ.get("HYPRLAND_INSTANCE_SIGNATURE"):
            return "Hyprland"

        return None

    def get_session_type(self) -> Optional[str]:
        """Return the session type: ``"wayland"``, ``"x11"`` or ``None``."""
        session_type = os.environ.get("XDG_SESSION_TYPE", "").lower()
        if session_type in ("wayland", "x11"):
            return session_type

        if os.environ.get("WAYLAND_DISPLAY"):
            return "wayland"
        if os.environ.get("DISPLAY"):
            return "x11"

        return None

    def get_adapter(self) -> Optional[DesktopAdapter]:
        """Return the most appropriate adapter for the current session.

        Adapters are tried in order of specificity; the first one that reports
        itself as available wins.
        """
        desktop = self.detect_environment()
        logger.debug("Detected desktop environment: %s", desktop)

        for adapter_class in self.ADAPTERS:
            try:
                adapter = adapter_class()
            except Exception as exc:  # pragma: no cover - defensive
                logger.debug("Could not instantiate %s: %s", adapter_class.__name__, exc)
                continue
            try:
                available = adapter.is_available()
            except Exception as exc:  # pragma: no cover - defensive
                logger.debug("%s.is_available() raised: %s", adapter_class.__name__, exc)
                continue
            if available:
                logger.info("Using adapter: %s", adapter.name)
                return adapter

        logger.warning("No suitable desktop adapter found")
        return None

    def available_adapters(self) -> List[DesktopAdapter]:
        """Return every adapter that reports itself available (debug aid)."""
        result: List[DesktopAdapter] = []
        for adapter_class in self.ADAPTERS:
            adapter = adapter_class()
            if adapter.is_available():
                result.append(adapter)
        return result
