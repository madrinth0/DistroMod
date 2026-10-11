"""Discovery of installed themes and fonts.

These helpers work purely from the standard on-disk locations, so they behave
the same regardless of the desktop environment in use.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, List, Set

from distromod.utils.exec import run
from distromod.utils.paths import data_dirs_with_user, home


def _unique_sorted(names: Iterable[str]) -> List[str]:
    return sorted({name for name in names if name})


def _subdirectories(directory: Path) -> List[Path]:
    try:
        if not directory.is_dir():
            return []
        return [entry for entry in directory.iterdir() if entry.is_dir()]
    except OSError:
        return []


def gtk_theme_dirs() -> List[Path]:
    """Return directories that hold GTK themes."""
    dirs: List[Path] = [home() / ".themes"]
    for base in data_dirs_with_user():
        dirs.append(base / "themes")
    return dirs


def icon_theme_dirs() -> List[Path]:
    """Return directories that hold icon / cursor themes."""
    dirs: List[Path] = [home() / ".icons"]
    for base in data_dirs_with_user():
        dirs.append(base / "icons")
    return dirs


def _is_gtk_theme(path: Path) -> bool:
    markers = ("gtk-2.0", "gtk-3.0", "gtk-4.0", "gtk-4.0", "index.theme")
    if (path / "index.theme").is_file():
        return True
    return any((path / marker).is_dir() for marker in markers if marker != "index.theme")


def _is_icon_theme(path: Path) -> bool:
    return (path / "index.theme").is_file()


def _is_cursor_theme(path: Path) -> bool:
    return (path / "cursors").is_dir()


def list_gtk_themes() -> List[str]:
    """Return the names of all installed GTK themes."""
    found: Set[str] = set()
    for directory in gtk_theme_dirs():
        for theme in _subdirectories(directory):
            if _is_gtk_theme(theme):
                found.add(theme.name)
    return _unique_sorted(found)


def list_icon_themes() -> List[str]:
    """Return the names of all installed icon themes."""
    found: Set[str] = set()
    for directory in icon_theme_dirs():
        for theme in _subdirectories(directory):
            if _is_icon_theme(theme):
                found.add(theme.name)
    return _unique_sorted(found)


def list_cursor_themes() -> List[str]:
    """Return the names of all installed cursor themes."""
    found: Set[str] = set()
    for directory in icon_theme_dirs():
        for theme in _subdirectories(directory):
            if _is_cursor_theme(theme):
                found.add(theme.name)
    return _unique_sorted(found)


def list_qt_themes() -> List[str]:
    """Return the names of installed Kvantum (Qt) themes."""
    found: Set[str] = set()
    for directory in (home() / ".local" / "share" / "Kvantum", Path("/usr/share/Kvantum")):
        for theme in _subdirectories(directory):
            found.add(theme.name)
    return _unique_sorted(found)


def list_fonts() -> List[str]:
    """Return the names of installed font families.

    Uses ``fc-list`` when available (fast and accurate) and falls back to
    scanning the standard font directories.
    """
    result = run(["fc-list", "--format", "%{family[0]}\n"], timeout=20)
    names: Set[str] = set()
    if result.returncode == 0 and result.stdout:
        for line in result.stdout.splitlines():
            family = line.strip().split(",")[0].strip()
            if family:
                names.add(family)
    if names:
        return _unique_sorted(names)

    extensions = {".ttf", ".otf", ".ttc", ".otc"}
    font_dirs = [home() / ".fonts", home() / ".local" / "share" / "fonts"]
    for base in data_dirs_with_user():
        font_dirs.append(base / "fonts")
    for directory in font_dirs:
        try:
            if not directory.is_dir():
                continue
            for file in directory.rglob("*"):
                if file.is_file() and file.suffix.lower() in extensions:
                    names.add(file.stem)
        except OSError:
            continue
    return _unique_sorted(names)
