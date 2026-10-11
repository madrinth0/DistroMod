"""Minimal, format-preserving INI / keyfile helpers.

Desktop environments such as KDE and GTK store settings in INI-like "keyfiles".
Using :mod:`configparser` would normalise away comments, ordering and case, so
instead we surgically edit the specific ``key=value`` pair we care about while
leaving the rest of the file byte-for-byte intact.  Writes are atomic.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import List, Optional, Union

from distromod.utils.logging import logger


def parse_group_header(line: str) -> Optional[str]:
    """Return the group name if ``line`` is a ``[Group]`` header, else ``None``."""
    stripped = line.strip()
    if len(stripped) >= 2 and stripped.startswith("[") and stripped.endswith("]"):
        return stripped[1:-1]
    return None


def read_value(
    path: Union[str, Path],
    group: str,
    key: str,
    default: Optional[str] = None,
) -> Optional[str]:
    """Read ``key`` from ``[group]`` in ``path``.

    Args:
        path: Keyfile path.
        group: Group name (case-sensitive).
        key: Key name (case-sensitive).
        default: Value returned when the file/group/key is missing.

    Returns:
        The raw value (without surrounding whitespace) or ``default``.
    """
    file_path = Path(path).expanduser()
    try:
        content = file_path.read_text(encoding="utf-8", errors="replace")
    except (OSError, UnicodeError):
        return default

    current: Optional[str] = None
    for line in content.splitlines():
        header = parse_group_header(line)
        if header is not None:
            current = header
            continue
        if current != group:
            continue
        stripped = line.strip()
        if not stripped or stripped[0] in "#;":
            continue
        if "=" not in stripped:
            continue
        found_key, _, value = stripped.partition("=")
        if found_key.strip() == key:
            return value.strip()
    return default


def set_value(path: Union[str, Path], group: str, key: str, value: str) -> None:
    """Set ``key=value`` inside ``[group]`` of ``path``.

    The file (and parent directories) are created if needed.  Existing keys are
    updated in place; otherwise the key is appended to the group, and the group
    is appended to the file if it does not exist yet.  The write is atomic.
    """
    file_path = Path(path).expanduser()
    try:
        content = file_path.read_text(encoding="utf-8", errors="replace")
        lines: List[str] = content.splitlines()
    except FileNotFoundError:
        lines = []
    except (OSError, UnicodeError) as exc:
        raise RuntimeError(f"Cannot read {file_path}: {exc}") from exc

    group_start: Optional[int] = None
    group_end: Optional[int] = None
    for index, line in enumerate(lines):
        header = parse_group_header(line)
        if header is None:
            continue
        if header == group:
            group_start = index
        elif group_start is not None and group_end is None:
            group_end = index
            break

    replacement = f"{key}={value}"

    if group_start is None:
        if lines and lines[-1].strip() != "":
            lines.append("")
        lines.append(f"[{group}]")
        lines.append(replacement)
    else:
        insert_at: Optional[int] = None
        search_end = group_end if group_end is not None else len(lines)
        for index in range(group_start + 1, search_end):
            stripped = lines[index].strip()
            if not stripped or stripped[0] in "#;":
                continue
            if "=" not in stripped:
                continue
            found_key, _, _ = stripped.partition("=")
            if found_key.strip() == key:
                # Preserve indentation of the original line.
                indent = lines[index][: len(lines[index]) - len(lines[index].lstrip())]
                lines[index] = f"{indent}{replacement}"
                insert_at = -1
                break
        if insert_at != -1:
            # Append after the last meaningful line of the group (skip trailing
            # blank lines so we do not leave stray gaps).
            target = search_end
            while target > group_start + 1 and lines[target - 1].strip() == "":
                target -= 1
            lines.insert(target, replacement)

    _atomic_write(file_path, lines)
    logger.debug("Set [%s] %s in %s", group, key, file_path)


def _atomic_write(path: Path, lines: List[str]) -> None:
    """Atomically write ``lines`` to ``path`` (one line per element)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    data = "\n".join(lines) + "\n"
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


def delete_value(path: Union[str, Path], group: str, key: str) -> None:
    """Remove ``key`` from ``[group]`` if present."""
    file_path = Path(path).expanduser()
    try:
        lines = file_path.read_text(encoding="utf-8", errors="replace").splitlines()
    except (OSError, UnicodeError):
        return

    current: Optional[str] = None
    kept: List[str] = []
    removed = False
    for line in lines:
        header = parse_group_header(line)
        if header is not None:
            current = header
            kept.append(line)
            continue
        if current == group and not removed:
            stripped = line.strip()
            if stripped and stripped[0] not in "#;" and "=" in stripped:
                found_key, _, _ = stripped.partition("=")
                if found_key.strip() == key:
                    removed = True
                    continue
        kept.append(line)
    if removed:
        _atomic_write(file_path, kept)
