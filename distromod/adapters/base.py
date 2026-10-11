"""Base class for desktop environment adapters."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List, Optional

from distromod.utils.logging import logger
from distromod.utils.paths import home, xdg_config_home

# Feature identifiers used throughout the application.  An adapter advertises
# the subset it supports via :meth:`DesktopAdapter.get_supported_features`.
FEATURE_GTK_THEME = "gtk_theme"
FEATURE_ICON_THEME = "icon_theme"
FEATURE_CURSOR_THEME = "cursor_theme"
FEATURE_WALLPAPER = "wallpaper"
FEATURE_FONT = "font"
FEATURE_COLOR_SCHEME = "color_scheme"

_ALL_FEATURES = (
    FEATURE_GTK_THEME,
    FEATURE_ICON_THEME,
    FEATURE_CURSOR_THEME,
    FEATURE_WALLPAPER,
    FEATURE_FONT,
    FEATURE_COLOR_SCHEME,
)


class DesktopAdapter(ABC):
    """Abstract base class implemented by each desktop environment adapter.

    Subclasses implement :meth:`is_available` and
    :meth:`get_supported_features`, then override the getters/setters for the
    features they advertise.  The default implementations raise
    :class:`NotImplementedError`; callers must consult
    :meth:`get_supported_features` first (the core does this).
    """

    name: str = "base"
    display_name: str = "Base"

    def __init__(self) -> None:
        self.home = home()

    # -- capability discovery -------------------------------------------------

    @abstractmethod
    def is_available(self) -> bool:
        """Return ``True`` when this adapter can manage the current session."""

    @abstractmethod
    def get_supported_features(self) -> List[str]:
        """Return the list of feature identifiers this adapter supports."""

    def supports(self, feature: str) -> bool:
        """Return ``True`` when ``feature`` is supported."""
        return feature in self.get_supported_features()

    # -- configuration snapshot ----------------------------------------------

    def get_current_config(self) -> Dict[str, str]:
        """Return a mapping of supported feature -> current value."""
        config: Dict[str, str] = {}
        getters = {
            FEATURE_GTK_THEME: self.get_gtk_theme,
            FEATURE_ICON_THEME: self.get_icon_theme,
            FEATURE_CURSOR_THEME: self.get_cursor_theme,
            FEATURE_WALLPAPER: self.get_wallpaper,
            FEATURE_FONT: self.get_font,
            FEATURE_COLOR_SCHEME: self.get_color_scheme,
        }
        for feature in self.get_supported_features():
            getter = getters.get(feature)
            if getter is None:
                continue
            try:
                config[feature] = getter()
            except Exception as exc:  # defensive: never fail a status query
                logger.debug("Could not read %s for %s: %s", feature, self.name, exc)
                config[feature] = "Unknown"
        return config

    # -- configuration files (used for backups) -------------------------------

    def _gtk_settings_path(self, version: int = 3) -> Path:
        return xdg_config_home() / f"gtk-{version}.0" / "settings.ini"

    def get_gtk_config_file(self) -> str:
        return str(self._gtk_settings_path(3))

    def get_icon_config_file(self) -> str:
        return str(self._gtk_settings_path(3))

    def get_cursor_config_file(self) -> str:
        return str(self._gtk_settings_path(3))

    def get_font_config_file(self) -> str:
        return str(self._gtk_settings_path(3))

    def get_wallpaper_config_file(self) -> str:
        return str(self._gtk_settings_path(3))

    # -- feature getters (override as needed) ---------------------------------

    def get_gtk_theme(self) -> str:
        raise NotImplementedError("GTK theme not supported")

    def set_gtk_theme(self, theme_name: str) -> None:
        raise NotImplementedError("GTK theme not supported")

    def list_gtk_themes(self) -> List[str]:
        from distromod.utils.desktop import list_gtk_themes

        return list_gtk_themes()

    def get_icon_theme(self) -> str:
        raise NotImplementedError("Icon theme not supported")

    def set_icon_theme(self, theme_name: str) -> None:
        raise NotImplementedError("Icon theme not supported")

    def list_icon_themes(self) -> List[str]:
        from distromod.utils.desktop import list_icon_themes

        return list_icon_themes()

    def get_cursor_theme(self) -> str:
        raise NotImplementedError("Cursor theme not supported")

    def set_cursor_theme(self, theme_name: str) -> None:
        raise NotImplementedError("Cursor theme not supported")

    def list_cursor_themes(self) -> List[str]:
        from distromod.utils.desktop import list_cursor_themes

        return list_cursor_themes()

    def get_wallpaper(self) -> str:
        raise NotImplementedError("Wallpaper not supported")

    def set_wallpaper(self, path: str) -> None:
        raise NotImplementedError("Wallpaper not supported")

    def get_font(self) -> str:
        raise NotImplementedError("Font not supported")

    def set_font(self, font_name: str, size: Optional[int] = None) -> None:
        raise NotImplementedError("Font not supported")

    def list_fonts(self) -> List[str]:
        from distromod.utils.desktop import list_fonts

        return list_fonts()

    def get_color_scheme(self) -> str:
        raise NotImplementedError("Color scheme not supported")

    def set_color_scheme(self, scheme: str) -> None:
        raise NotImplementedError("Color scheme not supported")

    def list_color_schemes(self) -> List[str]:
        """Return available colour scheme names (empty when unsupported)."""
        return []

    # -- preset application ---------------------------------------------------

    def apply_config(self, config: Dict[str, str]) -> None:
        """Apply a preset ``config`` mapping, ignoring unsupported keys."""
        if not isinstance(config, dict):
            raise ValueError("Preset configuration must be a mapping")

        applied = 0
        for key, value in config.items():
            if key in (FEATURE_COLOR_SCHEME,) and self.supports(FEATURE_COLOR_SCHEME):
                self.set_color_scheme(str(value))
            elif key == FEATURE_GTK_THEME and self.supports(FEATURE_GTK_THEME):
                self.set_gtk_theme(str(value))
            elif key == FEATURE_ICON_THEME and self.supports(FEATURE_ICON_THEME):
                self.set_icon_theme(str(value))
            elif key == FEATURE_CURSOR_THEME and self.supports(FEATURE_CURSOR_THEME):
                self.set_cursor_theme(str(value))
            elif key == FEATURE_WALLPAPER and self.supports(FEATURE_WALLPAPER):
                self.set_wallpaper(str(value))
            elif key == FEATURE_FONT and self.supports(FEATURE_FONT):
                self.set_font(str(value))
            else:
                logger.debug("Skipping unsupported preset key: %s", key)
                continue
            applied += 1

        logger.info("Applied %d preset value(s) via %s", applied, self.name)

    # -- misc -----------------------------------------------------------------

    def refresh(self) -> None:
        """Ask the running desktop to reload settings (best effort)."""
        logger.debug("%s: no refresh action", self.name)

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"<{type(self).__name__} name={self.name!r}>"
