# DistroMod - Linux Desktop Customization Tool

A comprehensive, modular Linux customization tool that adapts to your desktop environment automatically.

## Features

- **Multi-Environment Support**: Works with GNOME, KDE Plasma, Hyprland, XFCE, Cinnamon, MATE, LXQt, and other desktop environments
- **Automatic Detection**: Detects your desktop environment and shows only applicable options
- **Customization**: GTK themes, icon themes, cursor themes, wallpapers, fonts, and color schemes
- **Presets**: Export and import customization profiles as portable JSON
- **Backups & Restoration**: Safe backup and restore of configuration files
- **Terminal Interface**: Interactive CLI or direct command support
- **Standalone Executable**: Build into a self-contained Linux binary with PyInstaller

## Installation

### From Source (Development)

```bash
git clone https://github.com/madrinth0/DistroMod.git
cd DistroMod
python3 -m pip install -e .
```

### Build Standalone Executable

```bash
chmod +x build.sh
./build.sh
```

The resulting `distromod` executable will be in the `dist/` directory.

## Usage

### Interactive Terminal Interface

```bash
./distromod.sh
# or
distromod
```

### Direct Commands

```bash
# Show current configuration status
distromod status

# Customize GTK theme
distromod gtk

# Change wallpaper
distromod wallpaper

# Manage backups
distromod backup list
distromod backup restore <backup-id>

# Manage presets
distromod preset export <file.json>
distromod preset import <file.json>

# Get help
distromod --help
```

## Architecture

- **CLI Module**: Command-line interface and argument parsing
- **Desktop Environment Adapters**: Environment-specific implementations
- **Theme Engine**: GTK, icon, cursor, and font management
- **Backup System**: Safe file backup and restoration
- **Preset System**: Configuration import/export with validation
- **Utilities**: Path handling, validation, logging

## Supported Environments

| Environment | Status | Features |
|---|---|---|
| GNOME | ✓ | Themes, icons, wallpaper, font, color scheme |
| KDE Plasma | ✓ | Themes, icons, wallpaper, font |
| Hyprland | ✓ | Configuration, wallpaper |
| XFCE | ✓ | Themes, icons, wallpaper |
| Cinnamon | ✓ | Themes, icons, wallpaper |
| MATE | ✓ | Themes, icons, wallpaper |
| LXQt | ✓ | Themes, icons |
| Generic X11 | ✓ | Wallpaper, basic X11 settings |

## Safety & Reliability

- **No Root Required**: All operations work at user level
- **Safe Backups**: Automatic backups before modifications
- **Atomic Operations**: Configuration changes are atomic where possible
- **Validation**: All imports and paths validated against attacks
- **Error Handling**: Graceful failures with clear error messages
- **Testing**: Comprehensive test suite with mocked system operations

## Testing

```bash
# Run all tests
python3 -m pytest tests/ -v

# Run specific test module
python3 -m pytest tests/test_detection.py -v

# Run with coverage
python3 -m pytest tests/ --cov=distromod --cov-report=html
```

## Build Requirements

- Python 3.10+
- For standalone executable: PyInstaller
- For development: pytest, pytest-cov

## Known Limitations

- Some settings may require desktop restart to apply
- Hyprland wallpaper changes require systemd user service support
- Icon theme changes may not apply immediately in all environments
- GTK4 application theming may require GTK theme portals

## License

GPL v3.0

## Contributing

Contributions are welcome! Please:

1. Create a feature branch
2. Add tests for new functionality
3. Ensure all tests pass
4. Submit a pull request with a clear description

## Troubleshooting

### Command Not Found

If `distromod` is not found after building, ensure the `dist/` directory is in your PATH:

```bash
export PATH=$PATH:./dist
distromod --help
```

### Desktop Environment Not Detected

Check what DistroMod detects:

```bash
distromod status
```

This shows your environment, available features, and current configuration.

### Theme Changes Not Applied

Some environments require a logout or desktop restart. Try:

```bash
# Restart GNOME Shell (GNOME only)
killall -3 gnome-shell

# Restart KDE Plasma (KDE only)
killall kwin_x11 && kwin_x11 &
```

### Backup/Restore Issues

List all available backups:

```bash
distromod backup list
```

Restore a specific backup by ID:

```bash
distromod backup restore <backup-id>
```
