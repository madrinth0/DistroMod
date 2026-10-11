"""Tests for the backup manager."""

from __future__ import annotations

from distromod.backup import BackupManager


def test_create_and_list(tmp_path):
    manager = BackupManager(tmp_path / "backups")
    config = tmp_path / "settings.ini"
    config.write_text("hello\n")

    backup_id = manager.create_backup([config, tmp_path / "missing.ini"])
    assert backup_id is not None

    backups = manager.list_backups()
    assert len(backups) == 1
    assert backups[0]["id"] == backup_id
    assert backups[0]["files"] == 1


def test_nothing_to_backup(tmp_path):
    manager = BackupManager(tmp_path / "backups")
    assert manager.create_backup([tmp_path / "nope.ini"]) is None
    assert manager.list_backups() == []


def test_restore(tmp_path):
    manager = BackupManager(tmp_path / "backups")
    config = tmp_path / "settings.ini"
    config.write_text("original\n")
    backup_id = manager.create_backup([config])

    config.write_text("changed\n")
    manager.restore_backup(backup_id)
    assert config.read_text() == "original\n"


def test_delete(tmp_path):
    manager = BackupManager(tmp_path / "backups")
    config = tmp_path / "settings.ini"
    config.write_text("x\n")
    backup_id = manager.create_backup([config])
    manager.delete_backup(backup_id)
    assert manager.list_backups() == []


def test_prune(tmp_path):
    manager = BackupManager(tmp_path / "backups")
    config = tmp_path / "settings.ini"
    config.write_text("x\n")
    ids = []
    for i in range(3):
        config.write_text(f"v{i}\n")
        ids.append(manager.create_backup([config]))
    removed = manager.prune(keep=1)
    assert removed == 2
    assert len(manager.list_backups()) == 1
