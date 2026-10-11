"""Desktop environment detection and adapter selection."""

from __future__ import annotations

import os
from typing import List, Optional

from distromod.adapters.base import DesktopAdapter
from distromod.adapters.budgie import BudgieAdapter
from distromod.adapters.cinnamon import CinnamonAdapter
from distromod.adapters.cosmic import CosmicAdapter
from distromod.adapters.deepin import DeepinAdapter
from distromod.adapters.generic import GenericX11Adapter
from distromod.adapters.gnome import GnomeAdapter
from distromod.adapters.hyprland import HyprlandAdapter
from distromod.adapters.i3 import I3Adapter
from distromod.adapters.kde import KdeAdapter
from distromod.adapters.lxde import LxdeAdapter
from distromod.adapters.lxqt import LxqtAdapter
from distromod.adapters.mate import MateAdapter
from distromod.adapters.niri import NiriAdapter
from distromod.adapters.openbox import OpenboxAdapter
from distromod.adapters.pantheon import PantheonAdapter
from distromod.adapters.sway import SwayAdapter
from distromod.adapters.wayfire import WayfireAdapter
from distromod.adapters.xfce import XfceAdapter
from distromod.utils.logging import logger


class DesktopDetector:
    """Detect the desktop environment and select an appropriate adapter."""

    # Order matters: more specific environments first, generic last.
    ADAPTERS = [
        CosmicAdapter,
        DeepinAdapter,
        BudgieAdapter,
        PantheonAdapter,
        GnomeAdapter,
        KdeAdapter,
        HyprlandAdapter,
        NiriAdapter,
        SwayAdapter,
        WayfireAdapter,
        I3Adapter,
        OpenboxAdapter,
        LxdeAdapter,
        XfceAdapter,
        CinnamonAdapter,
        MateAdapter,
        LxqtAdapter,
        GenericX11Adapter,
    ]

    #: Fallback probe: (environment variable, reported name).
    _ENV_FALLBACKS = (
        ("GNOME_SHELL_SESSION_MODE", "GNOME"),
        ("KDE_FULL_SESSION", "KDE"),
        ("KDE_SESSION_VERSION", "KDE"),
        ("HYPRLAND_INSTANCE_SIGNATURE", "Hyprland"),
        ("SWAYSOCK", "Sway"),
        ("NIRI_SOCKET", "niri"),
        ("I3SOCK", "i3"),
    )

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

        for variable, name in self._ENV_FALLBACKS:
            if os.environ.get(variable):
                return name

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
            try:
                adapter = adapter_class()
            except Exception as exc:  # pragma: no cover - defensive
                logger.debug("Could not instantiate %s: %s", adapter_class.__name__, exc)
                continue
            try:
                if adapter.is_available():
                    result.append(adapter)
            except Exception as exc:  # pragma: no cover - defensive
                logger.debug("%s.is_available() raised: %s", adapter_class.__name__, exc)
        return result

    def describe_adapters(self) -> List[dict]:
        """Return diagnostic information about every known adapter.

        Each entry contains the adapter name, display name, whether it is
        available and (when available) its supported features.
        """
        results: List[dict] = []
        for adapter_class in self.ADAPTERS:
            entry = {
                "name": getattr(adapter_class, "name", adapter_class.__name__),
                "display_name": getattr(adapter_class, "display_name", adapter_class.__name__),
                "available": False,
                "features": [],
            }
            try:
                adapter = adapter_class()
                entry["available"] = bool(adapter.is_available())
                if entry["available"]:
                    entry["features"] = list(adapter.get_supported_features())
            except Exception as exc:  # pragma: no cover - defensive
                entry["error"] = str(exc)
            results.append(entry)
        return results
