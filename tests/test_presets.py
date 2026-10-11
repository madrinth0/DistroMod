"""Tests for preset import/export."""

from __future__ import annotations

import json

import pytest

from distromod.presets import PresetManager


def test_export_import_round_trip(tmp_path):
    manager = PresetManager()
    out = tmp_path / "preset.json"
    manager.export_preset({"gtk_theme": "Adwaita", "icon_theme": "Papirus"}, out)

    data = json.loads(out.read_text())
    assert data["distromod_preset"] is True
    assert data["version"] == 1

    config = manager.import_preset(out)
    assert config == {"gtk_theme": "Adwaita", "icon_theme": "Papirus"}


def test_import_flat_object(tmp_path):
    path = tmp_path / "flat.json"
    path.write_text(json.dumps({"gtk_theme": "Breeze", "unknown": "ignored"}))
    assert PresetManager().import_preset(path) == {"gtk_theme": "Breeze"}


def test_import_invalid_json(tmp_path):
    path = tmp_path / "bad.json"
    path.write_text("{not json")
    with pytest.raises(ValueError):
        PresetManager().import_preset(path)


def test_import_rejects_complex_values(tmp_path):
    path = tmp_path / "bad.json"
    path.write_text(json.dumps({"config": {"gtk_theme": {"nested": True}}}))
    with pytest.raises(ValueError):
        PresetManager().import_preset(path)


def test_import_empty_config(tmp_path):
    path = tmp_path / "empty.json"
    path.write_text(json.dumps({"config": {}}))
    with pytest.raises(ValueError):
        PresetManager().import_preset(path)


def test_export_rejects_complex_value(tmp_path):
    with pytest.raises(ValueError):
        PresetManager().export_preset({"gtk_theme": ["a", "b"]}, tmp_path / "x.json")
