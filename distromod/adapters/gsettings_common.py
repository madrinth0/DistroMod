"""Reusable GSettings behaviour for GNOME-family desktops.

GNOME, Cinnamon and MATE all store their appearance settings in GSettings /
dconf, with slightly different schema and key names.  This mixin implements the
common logic; subclasses configure the schema/key names through class
attributes.
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional
from urllib.parse import unquote, urlparse

from distromod.utils.exec import capture, run
from distromod.utils.logging import logger
from distromod.utils.paths import which, xdg_config_home
from distromod.utils.validation import validate_font_size, validate_theme_name


def _decode_gvariant_string(raw: str) -> Optional[str]:
    """Decode a ``gsettings get`` string result such as ``'Adwaita'``."""
    if raw is None:
        return None
    value = raw.strip()
    if len(value) >= 2 and value[0] == "'" and value[-1] == "'":
        inner = value[1:-1]
        return inner.replace("\\'", "'").replace("\\\\", "\\")
    if value.startswith("@") or value.startswith("["):
        return value
    return value or None


def _encode_gvariant_string(value: str) -> str:
    """Encode a Python string as a GVariant string literal argument."""
    escaped = value.replace("\\", "\\\\").replace("'", "\\'")
    return f"'{escaped}'"


_SCHEMA_CACHE: Optional[set] = None


def all_schemas() -> set:
    """Return the set of installed GSettings schema names (cached)."""
    global _SCHEMA_CACHE
    if _SCHEMA_CACHE is None:
        _SCHEMA_CACHE = set(capture(["gsettings", "list-schemas"]).splitlines())
    return _SCHEMA_CACHE


def schema_available(schema: str, key: Optional[str] = None) -> bool:
    """Return ``True`` when ``schema`` (and optionally ``key``) is installed.

    Used to make adapters degrade gracefully instead of advertising features
    whose backing schema is absent.
    """
    if which("gsettings") is None:
        return False
    if schema not in all_schemas():
        return False
    if key is None:
        return True
    keys = capture(["gsettings", "list-keys", schema]).splitlines()
    return key in set(keys)


class GSettingsMixin:
    """GTK/appearance settings backed by ``gsettings``.

    Subclasses set the schema/key attributes below to match their desktop.
    """

    interface_schema = "org.gnome.desktop.interface"
    background_schema = "org.gnome.desktop.background"
    background_key = "picture-uri"
    background_is_uri = True
    cursor_schema = "org.gnome.desktop.interface"
    cursor_key = "cursor-theme"
    supports_color_scheme = True

    # -- low level helpers ----------------------------------------------------

    @staticmethod
    def gsettings_available() -> bool:
        return which("gsettings") is not None

    def _gs_get(self, schema: str, key: str) -> Optional[str]:
        result = run(["gsettings", "get", schema, key])
        if result.returncode != 0:
            logger.debug("gsettings get %s %s failed: %s", schema, key, result.stderr)
            return None
        return _decode_gvariant_string(result.stdout)

    def _gs_set(self, schema: str, key: str, value: str) -> None:
        result = run(["gsettings", "set", schema, key, _encode_gvariant_string(value)])
        if result.returncode != 0:
            raise RuntimeError(
                f"gsettings set {schema} {key} failed: {result.stderr.strip()}"
            )

    def _gs_set_raw(self, schema: str, key: str, literal: str) -> None:
        """Set a key using a raw GVariant literal (e.g. ``['uri']`` or ``24``)."""
        result = run(["gsettings", "set", schema, key, literal])
        if result.returncode != 0:
            raise RuntimeError(
                f"gsettings set {schema} {key} failed: {result.stderr.strip()}"
            )

    def _gs_get_int(self, schema: str, key: str) -> Optional[int]:
        raw = self._gs_get(schema, key)
        if raw is None:
            return None
        try:
            return int(raw)
        except ValueError:
            return None

    def _gsettings_features(self, extra: Optional[List[str]] = None) -> List[str]:
        """Return the features actually backed by installed schemas."""
        features = ["gtk_theme", "icon_theme", "cursor_theme", "wallpaper", "font"]
        if schema_available(self.interface_schema, "cursor-size"):
            features.append("cursor_size")
        if self.supports_color_scheme and schema_available(
            self.interface_schema, "color-scheme"
        ):
            features.append("color_scheme")
        if extra:
            features.extend(extra)
        return features

    def dconf_user_db(self) -> str:
        """Return the path to the dconf user database (used for backups)."""
        return str(xdg_config_home() / "dconf" / "user")

    # -- feature implementations ---------------------------------------------

    def get_gtk_theme(self) -> str:
        return self._gs_get(self.interface_schema, "gtk-theme") or "Unknown"

    def set_gtk_theme(self, theme_name: str) -> None:
        theme_name = validate_theme_name(theme_name, "GTK theme")
        self._gs_set(self.interface_schema, "gtk-theme", theme_name)

    def get_icon_theme(self) -> str:
        return self._gs_get(self.interface_schema, "icon-theme") or "Unknown"

    def set_icon_theme(self, theme_name: str) -> None:
        theme_name = validate_theme_name(theme_name, "icon theme")
        self._gs_set(self.interface_schema, "icon-theme", theme_name)

    def get_cursor_theme(self) -> str:
        return self._gs_get(self.cursor_schema, self.cursor_key) or "Unknown"

    def set_cursor_theme(self, theme_name: str) -> None:
        theme_name = validate_theme_name(theme_name, "cursor theme")
        self._gs_set(self.cursor_schema, self.cursor_key, theme_name)

    def get_font(self) -> str:
        return self._gs_get(self.interface_schema, "font-name") or "Unknown"

    def set_font(self, font_name: str, size: Optional[int] = None) -> None:
        size = validate_font_size(size)
        family, embedded = _split_family_size(font_name)
        if size is None and embedded is not None:
            font_name, size = family, embedded
        font_name = validate_theme_name(font_name, "font")
        if size is None:
            current = self.get_font()
            _, size = _split_family_size(current)
            size = size or 11
        self._gs_set(self.interface_schema, "font-name", f"{font_name} {size}")

    def get_wallpaper(self) -> str:
        raw = self._gs_get(self.background_schema, self.background_key)
        if not raw:
            return "Unknown"
        if self.background_is_uri:
            path = _uri_to_path(raw)
            return path or raw
        return raw

    def set_wallpaper(self, path: str) -> None:
        value = Path(path).expanduser().as_uri() if self.background_is_uri else str(Path(path).expanduser())
        self._gs_set(self.background_schema, self.background_key, value)
        if self.background_is_uri and schema_available(self.background_schema, "picture-uri-dark"):
            # Keep the dark wallpaper in sync when the desktop supports it.
            self._gs_set_raw(
                self.background_schema,
                "picture-uri-dark",
                _encode_gvariant_string(value),
            )

    def get_color_scheme(self) -> str:
        if not self.supports_color_scheme:
            return "Unknown"
        return self._gs_get(self.interface_schema, "color-scheme") or "Unknown"

    def set_color_scheme(self, scheme: str) -> None:
        if not self.supports_color_scheme:
            raise NotImplementedError("Color scheme not supported")
        self._gs_set(self.interface_schema, "color-scheme", scheme)

    # -- cursor size ----------------------------------------------------------

    def get_cursor_size(self) -> int:
        value = self._gs_get_int(self.interface_schema, "cursor-size")
        return value if value is not None else 24

    def set_cursor_size(self, size: int) -> None:
        size = validate_font_size(size, 16, 128)
        self._gs_set_raw(self.interface_schema, "cursor-size", str(size))

    def list_color_schemes(self) -> List[str]:
        if not self.supports_color_scheme:
            return []
        return ["default", "prefer-dark", "prefer-light"]

    # -- config files for backups --------------------------------------------

    def get_gtk_config_file(self) -> str:
        return self.dconf_user_db()

    def get_icon_config_file(self) -> str:
        return self.dconf_user_db()

    def get_cursor_config_file(self) -> str:
        return self.dconf_user_db()

    def get_font_config_file(self) -> str:
        return self.dconf_user_db()

    def get_wallpaper_config_file(self) -> str:
        return self.dconf_user_db()


def _split_family_size(value: str) -> tuple[str, Optional[int]]:
    value = (value or "").strip()
    if not value:
        return "", None
    parts = value.rsplit(" ", 1)
    if len(parts) == 2 and parts[1].isdigit():
        return parts[0], int(parts[1])
    return value, None


def _uri_to_path(value: str) -> Optional[str]:
    if not value:
        return None
    if value.startswith("file:"):
        return unquote(urlparse(value).path) or None
    if value.startswith("/"):
        return value
    return None
