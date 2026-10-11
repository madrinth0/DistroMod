# DistroMod

A modular Linux desktop customization tool that adapts to your desktop
environment automatically. Change themes, icon sets, cursors, fonts, wallpapers
and colour schemes from one consistent command-line interface — with automatic
backups so you can always roll back.

## Features

- **Multi-environment support**: GNOME, KDE Plasma, Hyprland, XFCE, Cinnamon,
  MATE, LXQt, plus a generic X11/Wayland fallback.
- **Automatic detection** of your desktop environment and session type; only
  supported options are offered.
- **Customization** of GTK themes, icon themes, cursor themes, fonts,
  wallpapers and colour schemes.
- **Presets**: export/import your setup as portable, validated JSON.
- **Automatic backups**: every change snapshots the affected config files first;
  restore any snapshot with a single command.
- **No root required**: everything runs at the user level.
- **Safety**: all theme names and paths are validated before use; config writes
  are atomic and format-preserving.
- **Standalone executable**: build a single self-contained binary with
  PyInstaller.

## Requirements

- Python 3.10+
- A supported desktop environment (or any X11/Wayland session)
- Optional helper tools are used when present and gracefully skipped when not:
  `gsettings`, `xfconf-query`, `kwriteconfig6`/`kreadconfig6`,
  `plasma-apply-*`, `hyprctl`, `swww`, `feh`, `xwallpaper`, `nitrogen`,
  `hsetroot`, `fc-list`.

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
| GNOME | `gsettings` (dconf) |
| KDE Plasma | `kdeglobals`, `kcminputrc`, `plasma-apply-*`, GTK `settings.ini` |
| Hyprland | GTK `settings.ini`, `hyprpaper` / `swww` |
| XFCE | `xfconf-query` |
| Cinnamon / MATE | `gsettings` with their own schemas |
| LXQt | `lxqt.conf` + GTK `settings.ini` |
| Generic X11/Wayland | GTK `settings.ini`, common wallpaper tools |

### Files and directories

- Logs: `$XDG_STATE_HOME/distromod/distromod.log` (override with
  `DISTROMOD_LOG_FILE`; set to `-` to disable).
- Backups: `$XDG_DATA_HOME/distromod/backups` (usually
  `~/.local/share/distromod/backups`).
- Environment variables: `DISTROMOD_LOG_LEVEL`, `DISTROMOD_LOG_FILE`.

## Supported environments

| Environment | Themes | Icons | Cursors | Fonts | Wallpaper | Colour scheme |
|---|---|---|---|---|---|---|
| GNOME | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| KDE Plasma | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Hyprland | ✓ | ✓ | ✓ | ✓ | ✓ | – |
| XFCE | ✓ | ✓ | ✓ | ✓ | ✓ | – |
| Cinnamon | ✓ | ✓ | ✓ | ✓ | ✓ | – |
| MATE | ✓ | ✓ | ✓ | ✓ | ✓ | – |
| LXQt | ✓ | ✓ | ✓ | ✓ | – | – |
| Generic X11/Wayland | ✓ | ✓ | ✓ | ✓ | ✓ | – |

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
- On GNOME/MATE/Cinnamon, settings are stored in dconf; the backup snapshots the
  dconf user database rather than individual text files.
- GTK4 applications may need a theme portal to pick up some changes.

## License

GPL-3.0-or-later. See [LICENSE](LICENSE).

## Contributing

1. Create a feature branch
2. Add tests for new functionality
3. Ensure `python3 -m pytest` and `python3 -m pyflakes distromod tests` pass
4. Open a pull request with a clear description
