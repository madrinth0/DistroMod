from __future__ import annotations

import os
from pathlib import Path

from distromod.adapters.base import DesktopAdapter


class GenericX11Adapter(DesktopAdapter):
    name = "generic"

    def is_available(self) -> bool:
        return os.environ.get("DISPLAY") is not None or os.environ.get("XDG_SESSION_TYPE") == "x11"

    def get_supported_features(self) -> list[str]:
        return ["wallpaper"]

    def get_current_config(self) -> dict[str, str]:
        return {"wallpaper": self.get_wallpaper()}

    def get_wallpaper(self) -> str:
        return os.environ.get("WALLPAPER", "Unknown")

    def set_wallpaper(self, path: str) -> None:
        os.environ["WALLPAPER"] = path
