"""Desktop environment detection."""

import os
from typing import Optional

from distromod.adapters.base import DesktopAdapter
from distromod.adapters.gnome import GnomeAdapter
from distromod.adapters.kde import KdeAdapter
from distromod.adapters.hyprland import HyprlandAdapter
from distromod.adapters.xfce import XfceAdapter
from distromod.adapters.generic import GenericX11Adapter
from distromod.utils.logging import logger


class DesktopDetector:
    """Detect desktop environment and select appropriate adapter."""

    # Order matters: more specific environments first
    ADAPTERS = [
        GnomeAdapter,
        KdeAdapter,
        HyprlandAdapter,
        XfceAdapter,
        GenericX11Adapter,
    ]

    def detect_environment(self) -> Optional[str]:
        """Detect desktop environment name.

        Returns:
            Desktop environment name or None if not detected
        """
        # Check XDG_CURRENT_DESKTOP
        xdg_desktop = os.environ.get("XDG_CURRENT_DESKTOP", "")
        if xdg_desktop:
            return xdg_desktop.split(":")[0]

        # Check DESKTOP_SESSION
        desktop_session = os.environ.get("DESKTOP_SESSION", "")
        if desktop_session and desktop_session != "default":
            return desktop_session

        # Check common variables
        if os.environ.get("GNOME_SHELL_SESSION_MODE"):
            return "GNOME"
        if os.environ.get("KDE_SESSION_VERSION"):
            return "KDE"
        if os.environ.get("HYPRLAND_INSTANCE_SIGNATURE"):
            return "Hyprland"

        return None

    def get_session_type(self) -> Optional[str]:
        """Get session type (Wayland or X11).

        Returns:
            "wayland", "x11", or None if unknown
        """
        session_type = os.environ.get("XDG_SESSION_TYPE", "").lower()
        if session_type in ("wayland", "x11"):
            return session_type

        # Fallback detection
        if os.environ.get("WAYLAND_DISPLAY"):
            return "wayland"
        if os.environ.get("DISPLAY"):
            return "x11"

        return None

    def get_adapter(self) -> Optional[DesktopAdapter]:
        """Get appropriate adapter for detected environment.

        Returns:
            DesktopAdapter instance or None if no adapter supports this environment
        """
        desktop = self.detect_environment()
        logger.debug(f"Detected desktop environment: {desktop}")

        # Try each adapter in order of specificity
        for adapter_class in self.ADAPTERS:
            adapter = adapter_class()
            if adapter.is_available():
                logger.info(f"Using adapter: {adapter.name}")
                return adapter

        logger.warning("No suitable desktop adapter found")
        return None
