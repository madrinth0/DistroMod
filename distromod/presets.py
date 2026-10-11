"""Preset import/export with validation.

A preset is a portable JSON document describing a set of appearance settings.
Only a fixed set of keys are recognised; unknown keys are ignored and malformed
values are rejected.
"""

from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from distromod import __version__
from distromod.utils.logging import logger

SCHEMA_VERSION = 1
MAX_PRESET_BYTES = 1024 * 1024  # 1 MiB is plenty for a settings file

KNOWN_KEYS = {
    "gtk_theme",
    "icon_theme",
    "cursor_theme",
    "wallpaper",
    "font",
    "color_scheme",
}


class PresetManager:
    """Export and import DistroMod presets."""

    def export_preset(self, config: Dict[str, Any], output_path: str) -> str:
        """Write ``config`` to ``output_path`` as a preset document.

        Args:
            config: Feature name -> value mapping.
            output_path: Destination file path.

        Returns:
            The absolute path written.

        Raises:
            ValueError: If ``config`` is not a mapping or the path is invalid.
        """
        if not isinstance(config, dict):
            raise ValueError("Configuration must be a mapping")

        cleaned: Dict[str, str] = {}
        for key, value in config.items():
            if not isinstance(key, str):
                continue
            if value is None:
                continue
            if isinstance(value, (dict, list, tuple)):
                raise ValueError(f"Cannot export complex value for key {key!r}")
            cleaned[key] = str(value)

        payload = {
            "distromod_preset": True,
            "version": SCHEMA_VERSION,
            "generator": f"distromod {__version__}",
            "created": datetime.now().isoformat(timespec="seconds"),
            "environment": _detect_environment(),
            "config": cleaned,
        }

        path = Path(output_path).expanduser()
        if not path.is_absolute():
            path = Path.cwd() / path
        path.parent.mkdir(parents=True, exist_ok=True)

        data = json.dumps(payload, indent=2, sort_keys=True) + "\n"
        fd, tmp_name = tempfile.mkstemp(prefix=path.name + ".", dir=str(path.parent))
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                handle.write(data)
            os.replace(tmp_name, path)
        except BaseException:
            try:
                os.unlink(tmp_name)
            except OSError:
                pass
            raise

        logger.info("Exported preset to %s", path)
        return str(path)

    def import_preset(self, input_path: str) -> Dict[str, str]:
        """Load and validate a preset document.

        Args:
            input_path: Preset file path.

        Returns:
            The validated feature -> value mapping.

        Raises:
            ValueError: If the file is missing, too large, not valid JSON, or
                contains no recognised settings.
        """
        path = Path(input_path).expanduser()
        try:
            raw = path.read_text(encoding="utf-8")
        except OSError as exc:
            raise ValueError(f"Cannot read preset {path}: {exc}") from exc

        if len(raw.encode("utf-8", errors="replace")) > MAX_PRESET_BYTES:
            raise ValueError("Preset file is too large")

        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Preset is not valid JSON: {exc}") from exc

        if not isinstance(data, dict):
            raise ValueError("Preset must be a JSON object")

        version = data.get("version")
        if isinstance(version, int) and version > SCHEMA_VERSION:
            logger.warning(
                "Preset was created by a newer DistroMod (version %s); "
                "continuing anyway",
                version,
            )

        config = data.get("config", data)
        if not isinstance(config, dict):
            raise ValueError("Preset 'config' must be a JSON object")

        result: Dict[str, str] = {}
        for key, value in config.items():
            if not isinstance(key, str):
                logger.debug("Ignoring non-string preset key: %r", key)
                continue
            if key not in KNOWN_KEYS:
                logger.debug("Ignoring unknown preset key: %s", key)
                continue
            if isinstance(value, (dict, list, tuple)):
                raise ValueError(f"Invalid value for preset key {key!r}")
            if value is None:
                continue
            result[key] = str(value)

        if not result:
            raise ValueError("Preset contains no recognised settings")
        return result


def _detect_environment() -> str:
    try:
        from distromod.detection import DesktopDetector

        return DesktopDetector().detect_environment() or "unknown"
    except Exception:  # pragma: no cover - metadata only
        return "unknown"
