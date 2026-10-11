"""KDE Plasma adapter (Plasma 5 and Plasma 6)."""

from __future__ import annotations

import os
from pathlib import Path
from typing import List, Optional
from urllib.parse import unquote, urlparse

from distromod.adapters.base import (
    DesktopAdapter,
    FEATURE_COLOR_SCHEME,
    FEATURE_CURSOR_THEME,
    FEATURE_FONT,
    FEATURE_GTK_THEME,
    FEATURE_ICON_THEME,
    FEATURE_WALLPAPER,
)
from distromod.adapters.gtk_common import GtkSettingsMixin
from distromod.utils.exec import run
from distromod.utils.ini import read_value, set_value
from distromod.utils.logging import logger
from distromod.utils.paths import which, xdg_config_home, xdg_state_home
from distromod.utils.validation import validate_font_size, validate_theme_name

# KDE keyfile locations.
KDEGLOBALS = xdg_config_home() / "kdeglobals"
KCMINPUTRC = xdg_config_home() / "kcminputrc"
PLASMA_APPLETSRC = xdg_config_home() / "plasma-org.kde.plasma.desktop-appletsrc"

# KDE's font values look like ``Family,pointSize,-1,weight,italic,...``.
_FONT_TEMPLATE = "{family},{size},-1,5,50,0,0,0,0,0"
_WALLPAPER_STATE = xdg_state_home() / "distromod" / "wallpaper"


class KdeAdapter(GtkSettingsMixin, DesktopAdapter):
    """Adapter for the KDE Plasma desktop."""

    name = "kde"
    display_name = "KDE Plasma"

    # -- detection ------------------------------------------------------------

    def is_available(self) -> bool:
        desktop = os.environ.get("XDG_CURRENT_DESKTOP", "").lower()
        session = os.environ.get("DESKTOP_SESSION", "").lower()
        if "kde" in desktop or "plasma" in desktop or "plasma" in session:
            return True
        if os.environ.get("KDE_FULL_SESSION") or os.environ.get("KDE_SESSION_VERSION"):
            return True
        return False

    def get_supported_features(self) -> List[str]:
        return [
            FEATURE_GTK_THEME,
            FEATURE_ICON_THEME,
            FEATURE_CURSOR_THEME,
            FEATURE_WALLPAPER,
            FEATURE_FONT,
            FEATURE_COLOR_SCHEME,
        ]

    # -- config files for backups --------------------------------------------

    def get_icon_config_file(self) -> str:
        return str(KDEGLOBALS)

    def get_cursor_config_file(self) -> str:
        return str(KCMINPUTRC)

    def get_font_config_file(self) -> str:
        return str(KDEGLOBALS)

    def get_wallpaper_config_file(self) -> str:
        return str(PLASMA_APPLETSRC)

    # -- icon theme -----------------------------------------------------------

    def get_icon_theme(self) -> str:
        return read_value(KDEGLOBALS, "Icons", "Theme") or "Unknown"

    def set_icon_theme(self, theme_name: str) -> None:
        theme_name = validate_theme_name(theme_name, "icon theme")
        set_value(KDEGLOBALS, "Icons", "Theme", theme_name)
        self.refresh()

    # -- cursor theme ---------------------------------------------------------

    def get_cursor_theme(self) -> str:
        return read_value(KCMINPUTRC, "Mouse", "cursorTheme") or "breeze_cursors"

    def set_cursor_theme(self, theme_name: str) -> None:
        theme_name = validate_theme_name(theme_name, "cursor theme")
        apply_tool = which("plasma-apply-cursortheme")
        if apply_tool:
            result = run([apply_tool, theme_name])
            if result.returncode == 0:
                self.refresh()
                return
            logger.debug("plasma-apply-cursortheme failed: %s", result.stderr)
        set_value(KCMINPUTRC, "Mouse", "cursorTheme", theme_name)
        self.refresh()

    def get_cursor_size(self) -> int:
        raw = read_value(KCMINPUTRC, "Mouse", "cursorSize")
        try:
            return int(raw) if raw is not None else 24
        except ValueError:
            return 24

    def set_cursor_size(self, size: int) -> None:
        size = validate_font_size(size, 16, 128)
        set_value(KCMINPUTRC, "Mouse", "cursorSize", str(size))

    # -- color scheme ---------------------------------------------------------

    def get_color_scheme(self) -> str:
        return read_value(KDEGLOBALS, "General", "ColorScheme") or "Unknown"

    def set_color_scheme(self, scheme: str) -> None:
        scheme = validate_theme_name(scheme, "color scheme")
        apply_tool = which("plasma-apply-colorscheme")
        if apply_tool:
            result = run([apply_tool, scheme])
            if result.returncode == 0:
                return
            logger.debug("plasma-apply-colorscheme failed: %s", result.stderr)
        set_value(KDEGLOBALS, "General", "ColorScheme", scheme)
        self.refresh()

    def list_color_schemes(self) -> List[str]:
        names = set()
        for directory in (Path("/usr/share/color-schemes"), Path.home() / ".local/share/color-schemes"):
            try:
                if directory.is_dir():
                    for file in directory.glob("*.colors"):
                        names.add(file.stem)
            except OSError:
                continue
        return sorted(names)

    # -- fonts ----------------------------------------------------------------

    @staticmethod
    def _parse_kde_font(value: str) -> str:
        """Normalise KDE's ``Family,size,...`` value to ``"Family size"``."""
        if not value or value == "Unknown":
            return "Unknown"
        parts = value.split(",")
        family = parts[0].strip()
        size = parts[1].strip() if len(parts) > 1 else ""
        return f"{family} {size}".strip()

    def get_font(self) -> str:
        raw = read_value(KDEGLOBALS, "General", "font")
        if not raw:
            return "Unknown"
        return self._parse_kde_font(raw)

    def set_font(self, font_name: str, size: Optional[int] = None) -> None:
        size = validate_font_size(size)
        family, embedded = _split_family_size(font_name)
        if size is None and embedded is not None:
            # ``set_font`` may receive a combined "Family 10" value from a
            # preset; split it back apart.
            font_name, size = family, embedded
        font_name = validate_theme_name(font_name, "font")
        if size is None:
            current = self._parse_kde_font(read_value(KDEGLOBALS, "General", "font") or "")
            _, size = _split_family_size(current)
            size = size or 10

        value = _FONT_TEMPLATE.format(family=font_name, size=size)
        for key in ("font", "fixed", "menuFont", "toolBarFont", "smallestReadableFont"):
            set_value(KDEGLOBALS, "General", key, value)
        set_value(KDEGLOBALS, "WM", "activeFont", value)
        self.refresh()

    # -- wallpaper ------------------------------------------------------------

    def get_wallpaper(self) -> str:
        for line in _iter_appletsrc_lines():
            stripped = line.strip()
            if stripped.startswith("Image="):
                value = stripped.split("=", 1)[1].strip()
                path = _file_url_to_path(value)
                if path:
                    return path
        try:
            return _WALLPAPER_STATE.read_text(encoding="utf-8").strip() or "Unknown"
        except (OSError, UnicodeError):
            return "Unknown"

    def set_wallpaper(self, path: str) -> None:
        apply_tool = which("plasma-apply-wallpaperimage")
        if apply_tool:
            result = run([apply_tool, path], timeout=30)
            if result.returncode == 0:
                _remember_wallpaper(path)
                return
            logger.debug("plasma-apply-wallpaperimage failed: %s", result.stderr)

        # Fallback: rewrite the Image= entries directly and ask Plasma to reload.
        updated = self._update_appletsrc_wallpaper(path)
        if not updated:
            raise RuntimeError(
                "Could not set the Plasma wallpaper: install "
                "'plasma-apply-wallpaperimage' or configure a wallpaper manually first"
            )
        _remember_wallpaper(path)
        self.refresh()

    @staticmethod
    def _update_appletsrc_wallpaper(path: str) -> bool:
        target = PLASMA_APPLETSRC
        try:
            lines = target.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            return False
        url = Path(path).expanduser().as_uri()
        changed = False
        for index, line in enumerate(lines):
            if line.strip().startswith("Image=file:") or line.strip().startswith("Image=/"):
                prefix = line[: len(line) - len(line.lstrip())]
                lines[index] = f"{prefix}Image={url}"
                changed = True
        if not changed:
            return False
        try:
            target.write_text("\n".join(lines) + "\n", encoding="utf-8")
        except OSError as exc:
            logger.debug("Could not write %s: %s", target, exc)
            return False
        return True

    # -- refresh --------------------------------------------------------------

    def refresh(self) -> None:
        for tool, args in (
            ("qdbus6", ["org.kde.KWin", "/KWin", "reconfigure"]),
            ("qdbus", ["org.kde.KWin", "/KWin", "reconfigure"]),
        ):
            if which(tool):
                run([tool, *args], timeout=10)
                break


def _split_family_size(value: str) -> tuple[str, Optional[int]]:
    """Split ``"Family 11"`` into ``("Family", 11)``."""
    value = (value or "").strip()
    if not value:
        return "", None
    parts = value.rsplit(" ", 1)
    if len(parts) == 2 and parts[1].isdigit():
        return parts[0], int(parts[1])
    return value, None


def _file_url_to_path(value: str) -> Optional[str]:
    """Convert ``file:///path`` (or a plain path) to a filesystem path."""
    if not value:
        return None
    if value.startswith("file:"):
        parsed = urlparse(value)
        return unquote(parsed.path) or None
    if value.startswith("/"):
        return value
    return None


def _iter_appletsrc_lines():
    try:
        return PLASMA_APPLETSRC.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return []


def _remember_wallpaper(path: str) -> None:
    try:
        _WALLPAPER_STATE.parent.mkdir(parents=True, exist_ok=True)
        _WALLPAPER_STATE.write_text(str(Path(path).expanduser()) + "\n", encoding="utf-8")
    except OSError as exc:  # pragma: no cover - best effort
        logger.debug("Could not record wallpaper state: %s", exc)
