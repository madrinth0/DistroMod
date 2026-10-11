"""Tests for the command-line interface."""

from __future__ import annotations

import pytest

from distromod.cli import main


def test_version_exits_zero(capsys):
    with pytest.raises(SystemExit) as excinfo:
        main(["--version"])
    assert excinfo.value.code == 0
    assert "distromod" in capsys.readouterr().out


def test_help_exits_zero(capsys):
    with pytest.raises(SystemExit) as excinfo:
        main(["--help"])
    assert excinfo.value.code == 0
    assert "Linux Desktop Customization Tool" in capsys.readouterr().out


def test_status_without_adapter(clean_desktop_env, capsys):
    code = main(["status"])
    assert code == 1
    out = capsys.readouterr().out
    assert "No supported desktop environment" in out


def test_subcommand_help(clean_desktop_env, capsys):
    # ``gtk`` with no action prints its own help and returns 2.
    code = main(["gtk"])
    assert code == 2
    assert "usage:" in capsys.readouterr().out.lower()
