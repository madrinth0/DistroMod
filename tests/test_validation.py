"""Tests for input validation helpers."""

from __future__ import annotations

import pytest

from distromod.utils.validation import (
    validate_backup_id,
    validate_font_size,
    validate_path,
    validate_theme_name,
)


@pytest.mark.parametrize("name", ["Adwaita", "Breeze-Dark", "Noto Sans", "capitaine_cursors"])
def test_valid_theme_names(name):
    assert validate_theme_name(name) == name.strip()


@pytest.mark.parametrize(
    "name",
    ["", "   ", "../evil", "a/b", "a\\b", ".", "..", "-flag", "bad\x00name", "x" * 200],
)
def test_invalid_theme_names(name):
    with pytest.raises(ValueError):
        validate_theme_name(name)


def test_validate_path_existing(tmp_path):
    target = tmp_path / "file.txt"
    target.write_text("hi")
    assert validate_path(target, must_exist=True) == str(target)


def test_validate_path_missing(tmp_path):
    with pytest.raises(ValueError):
        validate_path(tmp_path / "nope.txt", must_exist=True)


def test_validate_path_directory_rejected(tmp_path):
    with pytest.raises(ValueError):
        validate_path(tmp_path, must_exist=True, kind="file")


def test_validate_path_output_requires_parent(tmp_path):
    with pytest.raises(ValueError):
        validate_path(tmp_path / "missing" / "out.json", must_exist=False)


def test_validate_path_output_can_create_parent(tmp_path):
    result = validate_path(
        tmp_path / "created" / "out.json", must_exist=False, allow_create_parent=True
    )
    assert (tmp_path / "created").is_dir()
    assert result.endswith("out.json")


def test_validate_path_null_byte():
    with pytest.raises(ValueError):
        validate_path("bad\x00path")


@pytest.mark.parametrize("value", ["20260101-120000", "abc_123", "a.b-c"])
def test_valid_backup_ids(value):
    assert validate_backup_id(value) == value


@pytest.mark.parametrize("value", ["", "..", "../x", "a/b", "a b", "a\\b"])
def test_invalid_backup_ids(value):
    with pytest.raises(ValueError):
        validate_backup_id(value)


def test_font_size():
    assert validate_font_size(None) is None
    assert validate_font_size(11) == 11
    with pytest.raises(ValueError):
        validate_font_size(1)
    with pytest.raises(ValueError):
        validate_font_size(100)
