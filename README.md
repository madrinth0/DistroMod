# DistroMod

A modular Linux desktop customization tool that adapts to your desktop
environment automatically. Change themes, icon sets, cursors, fonts, wallpapers
and colour schemes from one consistent command-line interface — with automatic
backups so you can always roll back.

## Features

- **Broad environment support**: KDE Plasma, GNOME, COSMIC, Deepin (DDE),
  Budgie, Pantheon, Cinnamon, MATE, XFCE, LXQt, LXDE, plus the Hyprland, Sway,
  niri, Wayfire and i3/Openbox window managers, and a generic X11/Wayland
  fallback.
- **Automatic detection** of your desktop environment and session type; only
  supported options are offered.
- **Customization** of GTK themes, icon themes, cursor themes (and sizes),
  fonts, wallpapers, colour schemes and (on KDE) the Qt/Kvantum widget theme.
- **Capability-aware**: adapters advertise only the features their environment
  actually supports, and GSettings adapters probe installed schemas before
  offering colour-scheme or cursor-size control.
- **Presets**: export/import your setup as portable, validated JSON.
- **Automatic backups**: every change snapshots the affected config files first;
  restore any snapshot with a single command.
- **Diagnostics**: `distromod doctor` shows the detected environment, the chosen
  adapter and which helper tools are present; `status --json` is script-friendly.
- **No root required**: everything runs at the user level.
- **Safety**: all theme names and paths are validated before use; config writes
  are atomic and format-preserving.
- **Standalone executable**: build a single self-contained binary with
  PyInstaller.

## Requirements

- Python 3.10+
- A supported desktop environment (or any X11/Wayland session)
- Optional helper tools are used when present and gracefully skipped when not:
  `gsettings`/`dconf`, `xfconf-query`, `kwriteconfig6`/`kreadconfig6`,
  `plasma-apply-*`, `hyprctl`/`hyprpaper`, `swaybg`/`swww`, `niri`,
  `cosmic-bg`, `pcmanfm`/`pcmanfm-qt`, `feh`, `xwallpaper`, `nitrogen`,
  `hsetroot`, `fc-list`. Run `distromod doctor` to see what is available.

## Installation

### From source (development)

```bash
git clone https://github.com/madrinth0/DistroMod.git
cd DistroMod
python3 -m pip install -e .
```

This installs a `distromod` command on your `PATH`.

### Run without installing

```bash
./distromod.sh --help
# or
python3 -m distromod --help
```

### Build a standalone executable

```bash
python3 -m pip install pyinstaller
./build.sh
```

The resulting `dist/distromod` binary is self-contained:

```bash
sudo install -Dm755 dist/distromod /usr/local/bin/distromod
```

## Usage

### Show current state

```bash
distromod status
distromod status --json   # machine-readable
distromod doctor          # environment + helper-tool diagnostics
```

### Themes, icons, cursors

```bash
distromod gtk list
distromod gtk current
distromod gtk set Adwaita

distromod icons list
distromod icons set Papirus

distromod cursor list
distromod cursor set Bibata
distromod cursor set Bibata --size 48   # theme + size
distromod cursor size                   # show current size
distromod cursor size 48                # change size only

# Qt/Kvantum widget theme (KDE)
distromod qt list
distromod qt current
distromod qt set Kvantum
```

### Wallpaper

```bash
distromod wallpaper current
distromod wallpaper set ~/Pictures/wallpaper.png
```

### Fonts and colour schemes

```bash
distromod font current
distromod font list
distromod font set "Noto Sans" --size 11

distromod color list
distromod color current
distromod color set BreezeDark
```

### Presets

```bash
# Save the current setup
distromod preset export my-setup.json

# Inspect and apply a saved setup
distromod preset import my-setup.json
distromod preset import my-setup.json --force   # skip confirmation
```

### Backups

DistroMod snapshots the affected config files automatically before every
change.

```bash
distromod backup list
distromod backup restore <backup-id>
distromod backup delete <backup-id>
```

### Verbose output

```bash
distromod --verbose status
distromod --debug gtk set Adwaita
```

## How it works

Each desktop environment has an *adapter* that knows where its settings live.
`distromod status` reports which adapter was selected. Settings are read and
written using the native mechanism for that environment:

| Environment | Mechanism |
|---|---|
| KDE Plasma | `kdeglobals`, `kcminputrc`, `Kvantum/kvantum.kvconfig`, `plasma-apply-*`, GTK `settings.ini` |
| GNOME | `gsettings` (dconf) |
| COSMIC | RON config under `~/.config/cosmic/` + GTK `settings.ini` |
| Deepin (DDE) | `gsettings` schema `com.deepin.dde.appearance` |
| Budgie / Pantheon | `gsettings` (GNOME schemas) |
| Cinnamon / MATE | `gsettings` with their own schemas |
| XFCE | `xfconf-query` |
| LXQt | `lxqt.conf` + GTK `settings.ini`, `pcmanfm-qt` wallpaper |
| LXDE | GTK `settings.ini`, PCManFM wallpaper |
| Hyprland | GTK `settings.ini`, `hyprpaper` / `swww` |
| Sway / niri / Wayfire | GTK `settings.ini`, `swaybg` / `swww` / `wf-shell.ini` |
| i3 / Openbox | GTK `settings.ini`, `feh` / `nitrogen` / `xwallpaper` |
| Generic X11/Wayland | GTK `settings.ini`, common wallpaper tools |

### Files and directories

- Logs: `$XDG_STATE_HOME/distromod/distromod.log` (override with
  `DISTROMOD_LOG_FILE`; set to `-` to disable).
- Backups: `$XDG_DATA_HOME/distromod/backups` (usually
  `~/.local/share/distromod/backups`).
- Environment variables: `DISTROMOD_LOG_LEVEL`, `DISTROMOD_LOG_FILE`.

## Supported environments

| Environment | Themes | Icons | Cursors | Cursor size | Fonts | Wallpaper | Colour scheme | Qt/Kvantum |
|---|---|---|---|---|---|---|---|---|
| KDE Plasma | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| GNOME | ✓ | ✓ | ✓ | ✓ᵍ | ✓ | ✓ | ✓ | – |
| COSMIC | ✓ | ✓ | ✓ | – | ✓ | ✓ | ✓ (light/dark) | – |
| Deepin (DDE) | ✓ | ✓ | ✓ | – | ✓ | ✓ | – | – |
| Budgie | ✓ | ✓ | ✓ | ✓ᵍ | ✓ | ✓ | ✓ᵍ | – |
| Pantheon | ✓ | ✓ | ✓ | ✓ᵍ | ✓ | ✓ | ✓ᵍ | – |
| Cinnamon | ✓ | ✓ | ✓ | ✓ᵍ | ✓ | ✓ | ✓ᵍ | – |
| MATE | ✓ | ✓ | ✓ | ✓ᵍ | ✓ | ✓ | ✓ᵍ | – |
| XFCE | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | – | – |
| LXQt | ✓ | ✓ | ✓ | – | ✓ | ✓ | – | – |
| LXDE | ✓ | ✓ | ✓ | – | ✓ | ✓ | ✓ | – |
| Hyprland | ✓ | ✓ | ✓ | – | ✓ | ✓ | ✓ | – |
| Sway / niri / Wayfire | ✓ | ✓ | ✓ | – | ✓ | ✓ | ✓ | – |
| i3 / Openbox | ✓ | ✓ | ✓ | – | ✓ | ✓ | ✓ | – |
| Generic X11/Wayland | ✓ | ✓ | ✓ | – | ✓ | ✓ | ✓ | – |

✓ᵍ = offered only when the installed GSettings schema provides the key (this is
probed automatically).

## Development

```bash
python3 -m pip install -e ".[dev]"

# Run the test suite
python3 -m pytest -v

# With coverage
python3 -m pytest --cov=distromod --cov-report=html
```

### Project layout

```
distromod/
├── __main__.py        # python -m distromod
├── cli.py             # argument parsing and command handlers
├── core.py            # high-level operations (backups, presets, delegation)
├── detection.py       # desktop environment detection + adapter selection
├── backup.py          # snapshot/restore of config files
├── presets.py         # validated preset import/export
├── adapters/          # one module per desktop environment (+ base/mixins)
└── utils/             # logging, paths, validation, INI editing, discovery
```

## Known limitations

- Some changes require the desktop to be restarted or re-logged-in to fully
  apply; `distromod` asks the running desktop to reload where it can.
- On GNOME/MATE/Cinnamon/Budgie/Pantheon/Deepin, settings are stored in dconf;
  the backup snapshots the dconf user database rather than individual text files.
- GTK4 applications may need a theme portal to pick up some changes.
- The COSMIC and Deepin adapters are provided on a best-effort basis because
  those desktops use newer, less-documented configuration formats; the KDE,
  GNOME, XFCE and GTK-based paths are the most exercised.
- KDE's `plasma-apply-*` tools talk to the running session over D-Bus and ignore
  `HOME`, so they affect the live desktop even inside a sandboxed test
  environment. Prefer `distromod backup` before experimenting.
- On window managers, `distromod` records the wallpaper it applied so it can
  report the current value on later runs (the compositor itself does not store
  it).

## License

GPL-3.0-or-later. See [LICENSE](LICENSE).

## Contributing

1. Create a feature branch
2. Add tests for new functionality
3. Ensure `python3 -m pytest` and `python3 -m pyflakes distromod tests` pass
4. Open a pull request with a clear description
