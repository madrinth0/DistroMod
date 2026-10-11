"""Shared wallpaper handling for lightweight window managers.

Full desktop environments expose a wallpaper API (Plasma script, GSettings,
xfconf).  Tiling WMs and minimal sessions instead rely on external tools such as
``swaybg``, ``awww``, ``feh`` or ``nitrogen``.  This module centralises that
tool selection and the "last applied wallpaper" state used for read-back.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from distromod.utils.exec import ok, run, spawn
from distromod.utils.logging import logger
from distromod.utils.paths import which, xdg_state_home


def is_wayland_session() -> bool:
    """Return ``True`` when the current session is Wayland."""
    if os.environ.get("WAYLAND_DISPLAY"):
        return True
    return os.environ.get("XDG_SESSION_TYPE", "").lower() == "wayland"


def _kill_resident(program: str) -> None:
    """Terminate a resident wallpaper process (best effort)."""
    if which("pkill"):
        run(["pkill", "-x", program], timeout=5)


def apply_wallpaper(path: str) -> Optional[str]:
    """Apply ``path`` using the best available wallpaper tool.

    Returns:
        The name of the tool that succeeded, or ``None`` if none worked.
    """
    path = str(Path(path).expanduser())

    if is_wayland_session():
        if which("swaybg"):
            _kill_resident("swaybg")
            if spawn(["swaybg", "-i", path, "-m", "fill"]):
                return "swaybg"
        if which("awww") and ok(["awww", "img", path]):
            return "awww"

    candidates = [
        ["pcmanfm-qt", "--set-wallpaper", path],
        ["pcmanfm", "--set-wallpaper", path],
        ["feh", "--bg-fill", path],
        ["xwallpaper", "--zoom", path],
        ["nitrogen", "--set-zoom-fill", "--save", path],
        ["hsetroot", "-fill", path],
    ]
    for argv in candidates:
        if which(argv[0]) and run(argv).returncode == 0:
            return argv[0]

    # Final Wayland fallbacks, in case the session type was misdetected.
    if which("swaybg"):
        _kill_resident("swaybg")
        if spawn(["swaybg", "-i", path, "-m", "fill"]):
            return "swaybg"
    if which("awww") and ok(["awww", "img", path]):
        return "awww"
    return None


class WallpaperToolsMixin:
    """Wallpaper support backed by external tools + a state file.

    Subclasses can override :meth:`get_wallpaper_native` /
    :meth:`set_wallpaper_native` to use a compositor-specific mechanism first.
    """

    def _wallpaper_state(self) -> Path:
        return xdg_state_home() / "distromod" / f"{self.name}-wallpaper"

    def get_wallpaper_native(self) -> Optional[str]:
        """Return the wallpaper from a compositor-specific source, if any."""
        return None

    def set_wallpaper_native(self, path: str) -> bool:
        """Apply the wallpaper natively. Return ``True`` on success."""
        return False

    def get_wallpaper(self) -> str:
        native = self.get_wallpaper_native()
        if native:
            return native
        try:
            return self._wallpaper_state().read_text(encoding="utf-8").strip() or "Unknown"
        except (OSError, UnicodeError):
            return "Unknown"

    def set_wallpaper(self, path: str) -> None:
        expanded = str(Path(path).expanduser())
        if self.set_wallpaper_native(expanded):
            self._remember_wallpaper(expanded)
            return

        tool = apply_wallpaper(expanded)
        if tool is None:
            raise RuntimeError(
                "No supported wallpaper tool found (tried swaybg, awww, pcmanfm, "
                "feh, xwallpaper, nitrogen, hsetroot)"
            )
        logger.debug("Set wallpaper via %s", tool)
        self._remember_wallpaper(expanded)

    def _remember_wallpaper(self, path: str) -> None:
        try:
            state = self._wallpaper_state()
            state.parent.mkdir(parents=True, exist_ok=True)
            state.write_text(path + "\n", encoding="utf-8")
        except OSError as exc:  # pragma: no cover - best effort
            logger.debug("Could not record wallpaper state: %s", exc)

    def get_wallpaper_config_file(self) -> str:
        return str(self._wallpaper_state())
