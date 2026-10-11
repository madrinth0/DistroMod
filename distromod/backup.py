"""Backup and restore of configuration files."""

from __future__ import annotations

import json
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Union

from distromod.utils.logging import logger
from distromod.utils.paths import xdg_data_home
from distromod.utils.validation import validate_backup_id


def default_backup_dir() -> Path:
    """Return the directory where backups are stored."""
    return xdg_data_home() / "distromod" / "backups"


class BackupManager:
    """Create, list and restore snapshots of configuration files.

    Each backup is a directory containing a ``manifest.json`` plus a numbered
    copy of every file that existed at backup time.  The manifest records the
    original location so files can be restored atomically.
    """

    def __init__(self, backup_dir: Optional[Union[str, Path]] = None) -> None:
        self.backup_dir = Path(backup_dir) if backup_dir else default_backup_dir()

    # -- creation -------------------------------------------------------------

    def create_backup(self, files: Iterable[Union[str, Path]]) -> Optional[str]:
        """Back up ``files`` and return the new backup ID.

        Non-existent files are skipped; when nothing can be backed up ``None``
        is returned and no directory is created.

        Args:
            files: Paths to configuration files.

        Returns:
            The backup ID, or ``None`` if there was nothing to back up.
        """
        paths: List[Path] = []
        seen: set[Path] = set()
        for item in files:
            if not item:
                continue
            path = Path(str(item)).expanduser()
            if path in seen:
                continue
            seen.add(path)
            if path.is_file():
                paths.append(path)

        if not paths:
            logger.debug("Nothing to back up (no existing config files)")
            return None

        self.backup_dir.mkdir(parents=True, exist_ok=True)
        backup_id = self._new_id()
        folder = self.backup_dir / backup_id
        folder.mkdir(parents=True, exist_ok=False)

        entries: List[Dict[str, str]] = []
        for index, path in enumerate(paths, start=1):
            stored = f"{index:03d}_{path.name}"
            shutil.copy2(path, folder / stored)
            entries.append({"original": str(path), "stored": stored})

        manifest = {
            "id": backup_id,
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "files": entries,
        }
        (folder / "manifest.json").write_text(
            json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
        )
        logger.info("Created backup %s (%d file(s))", backup_id, len(entries))
        return backup_id

    def _new_id(self) -> str:
        base = datetime.now().strftime("%Y%m%d-%H%M%S")
        candidate = base
        counter = 1
        while (self.backup_dir / candidate).exists():
            candidate = f"{base}-{counter}"
            counter += 1
        return candidate

    # -- listing --------------------------------------------------------------

    def list_backups(self) -> List[Dict[str, Any]]:
        """Return backup metadata, newest first."""
        if not self.backup_dir.is_dir():
            return []
        result: List[Dict[str, Any]] = []
        for folder in sorted(self.backup_dir.iterdir(), reverse=True):
            if not folder.is_dir():
                continue
            manifest = self._load_manifest(folder)
            if manifest is None:
                logger.debug("Skipping backup without manifest: %s", folder)
                continue
            result.append(
                {
                    "id": manifest.get("id", folder.name),
                    "timestamp": manifest.get("timestamp", ""),
                    "files": len(manifest.get("files", [])),
                    "path": str(folder),
                }
            )
        return result

    def get_backup(self, backup_id: str) -> Optional[Dict[str, Any]]:
        """Return the manifest for ``backup_id`` or ``None``."""
        backup_id = validate_backup_id(backup_id)
        folder = self.backup_dir / backup_id
        return self._load_manifest(folder) if folder.is_dir() else None

    # -- restore --------------------------------------------------------------

    def restore_backup(self, backup_id: str) -> int:
        """Restore the files stored in ``backup_id``.

        Returns:
            The number of files restored.

        Raises:
            ValueError: If the backup does not exist.
            RuntimeError: If the manifest is missing or unreadable.
        """
        backup_id = validate_backup_id(backup_id)
        folder = self.backup_dir / backup_id
        if not folder.is_dir():
            raise ValueError(f"Backup not found: {backup_id}")

        manifest = self._load_manifest(folder)
        if manifest is None:
            raise RuntimeError(f"Backup {backup_id} is missing a valid manifest")

        restored = 0
        for entry in manifest.get("files", []):
            try:
                original = Path(str(entry["original"])).expanduser()
                stored = folder / str(entry["stored"])
            except (KeyError, TypeError):
                logger.warning("Malformed manifest entry in %s", backup_id)
                continue
            if not stored.is_file():
                logger.warning("Backup file missing: %s", stored)
                continue
            original.parent.mkdir(parents=True, exist_ok=True)
            temporary = original.with_name(original.name + ".distromod-restore")
            shutil.copy2(stored, temporary)
            os.replace(temporary, original)
            restored += 1

        logger.info("Restored %d file(s) from backup %s", restored, backup_id)
        return restored

    # -- maintenance ----------------------------------------------------------

    def delete_backup(self, backup_id: str) -> None:
        """Delete a backup directory."""
        backup_id = validate_backup_id(backup_id)
        folder = self.backup_dir / backup_id
        if not folder.is_dir():
            raise ValueError(f"Backup not found: {backup_id}")
        shutil.rmtree(folder)
        logger.info("Deleted backup %s", backup_id)

    def prune(self, keep: int = 10) -> int:
        """Keep only the ``keep`` most recent backups; return how many were removed."""
        backups = self.list_backups()
        removed = 0
        for backup in backups[keep:]:
            try:
                shutil.rmtree(self.backup_dir / backup["id"])
                removed += 1
            except OSError as exc:  # pragma: no cover
                logger.debug("Could not prune %s: %s", backup["id"], exc)
        return removed

    # -- internals ------------------------------------------------------------

    @staticmethod
    def _load_manifest(folder: Path) -> Optional[Dict[str, Any]]:
        try:
            data = json.loads((folder / "manifest.json").read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError, UnicodeError):
            return None
        return data if isinstance(data, dict) else None
