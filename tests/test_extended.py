"""Tests for the expanded adapter set and the broadened feature surface."""

from __future__ import annotations

import json
from subprocess import CompletedProcess

import pytest

import distromod.adapters.gsettings_common as gs
import distromod.adapters.kde as kde_module
import distromod.adapters.wallpaper_tools as wt
from distromod.adapters.base import (
    FEATURE_COLOR_SCHEME,
    FEATURE_CURSOR_SIZE,
    FEATURE_QT_THEME,
)
from distromod.adapters.cosmic import CosmicAdapter
from distromod.adapters.deepin import DeepinAdapter
from distromod.adapters.generic import GenericX11Adapter
from distromod.adapters.gnome import GnomeAdapter
from distromod.adapters.i3 import I3Adapter
from distromod.adapters.kde import KdeAdapter
from distromod.adapters.lxde import LxdeAdapter
from distromod.adapters.niri import NiriAdapter
from distromod.adapters.openbox import OpenboxAdapter
from distromod.adapters.sway import SwayAdapter
from distromod.adapters.wayfire import WayfireAdapter
from distromod.cli import main
from distromod.detection import DesktopDetector


# -- schema probing -----------------------------------------------------------


def test_schema_available_uses_cache(monkeypatch):
    monkeypatch.setattr(gs, "which", lambda name: "/usr/bin/gsettings")
    monkeypatch.setattr(gs, "_SCHEMA_CACHE", None)
    monkeypatch.setattr(
        gs,
        "capture",
        lambda cmd, timeout=15.0: {
            ("gsettings", "list-schemas"): "org.gnome.desktop.interface\norg.gnome.desktop.background",
            ("gsettings", "list-keys"): "gtk-theme\ncolor-scheme\ncursor-size",
        }.get(tuple(cmd[:2]), ""),
    )
    assert gs.schema_available("org.gnome.desktop.interface")
    assert gs.schema_available("org.gnome.desktop.interface", "cursor-size")
    assert not gs.schema_available("org.gnome.desktop.interface", "font-name")
    assert not gs.schema_available("com.example.missing")


def test_gsettings_features_reflect_schemas(monkeypatch):
    monkeypatch.setattr(gs, "which", lambda name: "/usr/bin/gsettings")
    monkeypatch.setattr(gs, "_SCHEMA_CACHE", {"org.gnome.desktop.interface"})
    monkeypatch.setattr(gs, "capture", lambda cmd, timeout=15.0: "color-scheme\ncursor-size")

    features = GnomeAdapter().get_supported_features()
    assert FEATURE_COLOR_SCHEME in features
    assert FEATURE_CURSOR_SIZE in features


def test_gsettings_cursor_size(monkeypatch):
    adapter = GnomeAdapter()
    monkeypatch.setattr(adapter, "_gs_get_int", lambda schema, key: 48)
    assert adapter.get_cursor_size() == 48

    recorded = {}
    monkeypatch.setattr(
        adapter, "_gs_set_raw", lambda schema, key, literal: recorded.update(args=(schema, key, literal))
    )
    adapter.set_cursor_size(31)
    assert recorded["args"] == ("org.gnome.desktop.interface", "cursor-size", "31")

    with pytest.raises(ValueError):
        adapter.set_cursor_size(500)


# -- new lightweight WM adapters ----------------------------------------------


@pytest.mark.parametrize(
    "adapter_cls,var,value",
    [
        (SwayAdapter, "XDG_CURRENT_DESKTOP", "sway"),
        (I3Adapter, "DESKTOP_SESSION", "i3"),
        (OpenboxAdapter, "XDG_CURRENT_DESKTOP", "Openbox"),
        (LxdeAdapter, "XDG_CURRENT_DESKTOP", "LXDE"),
        (NiriAdapter, "XDG_CURRENT_DESKTOP", "niri"),
        (WayfireAdapter, "XDG_CURRENT_DESKTOP", "wayfire"),
    ],
)
def test_lightweight_wm_detection(clean_desktop_env, adapter_cls, var, value):
    clean_desktop_env.setenv(var, value)
    assert adapter_cls().is_available() is True


def test_lightweight_wm_env_signature(clean_desktop_env):
    clean_desktop_env.setenv("SWAYSOCK", "/run/user/1000/sway-ipc.sock")
    assert SwayAdapter().is_available() is True


def test_lightweight_wm_offers_expected_features(clean_desktop_env):
    features = SwayAdapter().get_supported_features()
    assert "gtk_theme" in features
    assert "wallpaper" in features
    assert FEATURE_COLOR_SCHEME in features


def test_detector_selects_cosmic(clean_desktop_env):
    clean_desktop_env.setenv("XDG_CURRENT_DESKTOP", "COSMIC")
    adapter = DesktopDetector().get_adapter()
    assert adapter is not None and adapter.name == "cosmic"


def test_detector_selects_sway(clean_desktop_env):
    clean_desktop_env.setenv("XDG_CURRENT_DESKTOP", "sway")
    adapter = DesktopDetector().get_adapter()
    assert adapter is not None and adapter.name == "sway"


def test_detector_selects_i3_from_session(clean_desktop_env):
    clean_desktop_env.setenv("DESKTOP_SESSION", "i3")
    adapter = DesktopDetector().get_adapter()
    assert adapter is not None and adapter.name == "i3"


def test_detector_prefers_budgie_over_gnome(clean_desktop_env, monkeypatch):
    monkeypatch.setattr(gs, "which", lambda name: "/usr/bin/gsettings")
    clean_desktop_env.setenv("XDG_CURRENT_DESKTOP", "Budgie:GNOME")
    adapter = DesktopDetector().get_adapter()
    assert adapter is not None and adapter.name == "budgie"


def test_detect_environment_uses_env_fallback(clean_desktop_env):
    clean_desktop_env.setenv("SWAYSOCK", "/run/user/1000/sway-ipc.sock")
    assert DesktopDetector().detect_environment() == "Sway"


# -- wallpaper toolbox --------------------------------------------------------


def test_apply_wallpaper_prefers_installed_tool(monkeypatch):
    monkeypatch.setattr(wt, "is_wayland_session", lambda: False)
    monkeypatch.setattr(wt, "which", lambda name: "/usr/bin/feh" if name == "feh" else None)
    calls = []

    def fake_run(cmd, timeout=15.0):
        calls.append(cmd)
        return CompletedProcess(cmd, 0, "", "")

    monkeypatch.setattr(wt, "run", fake_run)
    assert wt.apply_wallpaper("/tmp/opencode/wall.png") == "feh"
    assert calls and calls[-1][0].endswith("feh")


def test_apply_wallpaper_spawns_swaybg_on_wayland(monkeypatch):
    monkeypatch.setattr(wt, "is_wayland_session", lambda: True)
    monkeypatch.setattr(wt, "which", lambda name: f"/usr/bin/{name}")
    monkeypatch.setattr(wt, "run", lambda cmd, timeout=15.0: CompletedProcess(cmd, 0, "", ""))
    spawned = []
    monkeypatch.setattr(wt, "spawn", lambda cmd: spawned.append(cmd) or True)

    assert wt.apply_wallpaper("/tmp/opencode/wall.png") == "swaybg"
    assert spawned and spawned[0][0].endswith("swaybg")


def test_apply_wallpaper_falls_back_to_awww(monkeypatch):
    monkeypatch.setattr(wt, "is_wayland_session", lambda: True)
    monkeypatch.setattr(
        wt, "which", lambda name: "/usr/bin/awww" if name == "awww" else None
    )
    calls = []
    monkeypatch.setattr(
        wt, "ok", lambda cmd, timeout=15.0: calls.append(list(cmd)) or True
    )
    assert wt.apply_wallpaper("/tmp/opencode/wall.png") == "awww"
    assert calls and calls[-1][:2] == ["awww", "img"]


def test_wallpaper_state_roundtrip(tmp_home, monkeypatch):
    monkeypatch.setattr(wt, "apply_wallpaper", lambda path: "feh")
    adapter = GenericX11Adapter()
    adapter.set_wallpaper("/tmp/opencode/wall.png")
    assert adapter.get_wallpaper() == "/tmp/opencode/wall.png"


# -- COSMIC -------------------------------------------------------------------


def test_cosmic_wallpaper_and_scheme(tmp_path, monkeypatch):
    import distromod.adapters.cosmic as cosmic

    monkeypatch.setattr(cosmic, "xdg_config_home", lambda: tmp_path)
    monkeypatch.setattr(cosmic, "which", lambda name: None)

    adapter = CosmicAdapter()
    assert adapter.get_wallpaper() == "Unknown"
    adapter.set_wallpaper("/tmp/opencode/wall.png")
    assert adapter.get_wallpaper() == "/tmp/opencode/wall.png"
    assert adapter.get_wallpaper_config_file().endswith("com.system76.CosmicBackground/v1/all")

    assert adapter.get_color_scheme() == "Unknown"
    adapter.set_color_scheme("dark")
    assert adapter.get_color_scheme() == "prefer-dark"
    adapter.set_color_scheme("light")
    assert adapter.get_color_scheme() == "default"


# -- Wayfire ------------------------------------------------------------------


def test_wayfire_wallpaper_writes_ini(tmp_path, monkeypatch):
    import distromod.adapters.wayfire as wayfire

    ini = tmp_path / "wf-shell.ini"
    monkeypatch.setattr(wayfire, "WFSHELL_INI", ini)
    monkeypatch.setattr(wayfire, "apply_wallpaper", lambda path: None)
    monkeypatch.setattr(wayfire, "which", lambda name: None)

    adapter = WayfireAdapter()
    adapter.set_wallpaper("/tmp/opencode/wall.png")
    assert adapter.get_wallpaper() == "/tmp/opencode/wall.png"
    assert "wallpaper=/tmp/opencode/wall.png" in ini.read_text()


# -- Deepin -------------------------------------------------------------------


def test_deepin_first_uri():
    assert (
        DeepinAdapter._first_uri("['file:///home/u/a.png', 'file:///home/u/a.png']")
        == "file:///home/u/a.png"
    )
    assert DeepinAdapter._first_uri("[]") is None
    assert DeepinAdapter._first_uri("") is None


def test_deepin_detection(clean_desktop_env):
    clean_desktop_env.setenv("XDG_CURRENT_DESKTOP", "DDE")
    assert DeepinAdapter().is_available() is True


# -- KDE Qt/Kvantum theme -----------------------------------------------------


def test_kde_qt_theme(tmp_path, monkeypatch):
    kvantum = tmp_path / "Kvantum" / "kvantum.kvconfig"
    monkeypatch.setattr(kde_module, "KVANTUM_CONFIG", kvantum)
    monkeypatch.setattr(kde_module, "which", lambda name: None)

    adapter = KdeAdapter()
    assert adapter.get_qt_theme() == "Unknown"
    adapter.set_qt_theme("Kvantum")
    assert adapter.get_qt_theme() == "Kvantum"
    assert FEATURE_QT_THEME in adapter.get_supported_features()


# -- CLI integration ----------------------------------------------------------


def test_cli_doctor_runs(clean_desktop_env, capsys):
    assert main(["doctor"]) == 0
    assert "DistroMod Doctor" in capsys.readouterr().out


def test_cli_status_json_without_adapter(clean_desktop_env, capsys):
    code = main(["status", "--json"])
    assert code == 1
    data = json.loads(capsys.readouterr().out)
    assert data["adapter"] is None
    assert data["configuration"] == {}


def test_cli_cursor_size_unsupported(clean_desktop_env, capsys):
    clean_desktop_env.setenv("DISPLAY", ":0")
    code = main(["cursor", "size"])
    assert code == 1
    assert "not supported" in capsys.readouterr().out.lower()


def test_cli_qt_unsupported(clean_desktop_env, capsys):
    clean_desktop_env.setenv("DISPLAY", ":0")
    code = main(["qt", "current"])
    assert code == 1
    assert "not supported" in capsys.readouterr().out.lower()
