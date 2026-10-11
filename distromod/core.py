"""Core DistroMod functionality."""

import os
from typing import Any, Dict, List, Optional

from distromod.adapters.base import (
    DesktopAdapter,
    FEATURE_CURSOR_SIZE,
    FEATURE_QT_THEME,
)
from distromod.detection import DesktopDetector
from distromod.backup import BackupManager
from distromod.presets import PresetManager
from distromod.utils.logging import logger
from distromod.utils.paths import which
from distromod.utils.validation import validate_font_size, validate_path, validate_theme_name


class DistroMod:
    """Main DistroMod application class."""

    def __init__(self):
        """Initialize DistroMod."""
        self.detector = DesktopDetector()
        self.backup_manager = BackupManager()
        self.preset_manager = PresetManager()
        self._adapter: Optional[DesktopAdapter] = None

    def get_desktop_environment(self) -> str:
        """Get detected desktop environment name.

        Returns:
            Desktop environment name or "Unknown"
        """
        return self.detector.detect_environment() or "Unknown"

    def get_session(self) -> str:
        """Get current session type.

        Returns:
            Session type (e.g., "x11", "wayland")
        """
        return self.detector.get_session_type() or "Unknown"

    def get_adapter(self) -> Optional[DesktopAdapter]:
        """Get the appropriate desktop adapter.

        Returns:
            DesktopAdapter instance or None if no adapter available
        """
        if not self._adapter:
            self._adapter = self.detector.get_adapter()
        return self._adapter

    def list_gtk_themes(self) -> List[str]:
        """List available GTK themes.

        Returns:
            List of theme names
        """
        adapter = self.get_adapter()
        if not adapter:
            return []
        return adapter.list_gtk_themes()

    def get_gtk_theme(self) -> str:
        """Get current GTK theme.

        Returns:
            Current GTK theme name
        """
        adapter = self.get_adapter()
        if not adapter:
            return "Unknown"
        return adapter.get_gtk_theme()

    def set_gtk_theme(self, theme_name: str) -> None:
        """Set GTK theme.

        Args:
            theme_name: Name of theme to set

        Raises:
            ValueError: If theme name is invalid
            RuntimeError: If setting theme fails
        """
        validate_theme_name(theme_name)
        adapter = self.get_adapter()
        if not adapter:
            raise RuntimeError("No desktop adapter available")
        
        # Create backup before change
        self.backup_manager.create_backup([adapter.get_gtk_config_file()])
        
        adapter.set_gtk_theme(theme_name)
        logger.info(f"GTK theme set to {theme_name}")

    def list_icon_themes(self) -> List[str]:
        """List available icon themes.

        Returns:
            List of theme names
        """
        adapter = self.get_adapter()
        if not adapter:
            return []
        return adapter.list_icon_themes()

    def get_icon_theme(self) -> str:
        """Get current icon theme.

        Returns:
            Current icon theme name
        """
        adapter = self.get_adapter()
        if not adapter:
            return "Unknown"
        return adapter.get_icon_theme()

    def set_icon_theme(self, theme_name: str) -> None:
        """Set icon theme.

        Args:
            theme_name: Name of theme to set

        Raises:
            ValueError: If theme name is invalid
            RuntimeError: If setting theme fails
        """
        validate_theme_name(theme_name)
        adapter = self.get_adapter()
        if not adapter:
            raise RuntimeError("No desktop adapter available")
        
        self.backup_manager.create_backup([adapter.get_icon_config_file()])
        adapter.set_icon_theme(theme_name)
        logger.info(f"Icon theme set to {theme_name}")

    def list_cursor_themes(self) -> List[str]:
        """List available cursor themes.

        Returns:
            List of theme names
        """
        adapter = self.get_adapter()
        if not adapter:
            return []
        return adapter.list_cursor_themes()

    def get_cursor_theme(self) -> str:
        """Get current cursor theme.

        Returns:
            Current cursor theme name
        """
        adapter = self.get_adapter()
        if not adapter:
            return "Unknown"
        return adapter.get_cursor_theme()

    def set_cursor_theme(self, theme_name: str, size: Optional[int] = None) -> None:
        """Set cursor theme (and optionally its size).

        Args:
            theme_name: Name of theme to set
            size: Optional cursor size in pixels

        Raises:
            ValueError: If theme name or size is invalid
            RuntimeError: If setting theme fails or size is unsupported
        """
        validate_theme_name(theme_name)
        size = validate_font_size(size, 16, 128)
        adapter = self.get_adapter()
        if not adapter:
            raise RuntimeError("No desktop adapter available")
        if size is not None and not adapter.supports(FEATURE_CURSOR_SIZE):
            raise RuntimeError("Cursor size customization not supported on this environment.")

        self.backup_manager.create_backup([adapter.get_cursor_config_file()])
        adapter.set_cursor_theme(theme_name)
        if size is not None:
            adapter.set_cursor_size(size)
        logger.info(f"Cursor theme set to {theme_name}")

    def get_cursor_size(self) -> int:
        """Return the current cursor size in pixels."""
        adapter = self.get_adapter()
        if not adapter or not adapter.supports(FEATURE_CURSOR_SIZE):
            raise RuntimeError("Cursor size customization not supported on this environment.")
        return adapter.get_cursor_size()

    def set_cursor_size(self, size: int) -> None:
        """Set the cursor size in pixels."""
        size = validate_font_size(size, 16, 128)
        adapter = self.get_adapter()
        if not adapter or not adapter.supports(FEATURE_CURSOR_SIZE):
            raise RuntimeError("Cursor size customization not supported on this environment.")
        adapter.set_cursor_size(size)
        logger.info(f"Cursor size set to {size}")

    # -- Qt / Kvantum theme ---------------------------------------------------

    def list_qt_themes(self) -> List[str]:
        """List available Qt/Kvantum themes."""
        adapter = self.get_adapter()
        if not adapter or not adapter.supports(FEATURE_QT_THEME):
            return []
        return adapter.list_qt_themes()

    def get_qt_theme(self) -> str:
        """Return the current Qt/Kvantum theme."""
        adapter = self.get_adapter()
        if not adapter or not adapter.supports(FEATURE_QT_THEME):
            return "Unknown"
        return adapter.get_qt_theme()

    def set_qt_theme(self, theme_name: str) -> None:
        """Set the Qt/Kvantum theme."""
        theme_name = validate_theme_name(theme_name, "Qt theme")
        adapter = self.get_adapter()
        if not adapter or not adapter.supports(FEATURE_QT_THEME):
            raise RuntimeError("Qt theme customization not supported on this environment.")
        self.backup_manager.create_backup([adapter.get_qt_config_file()])
        adapter.set_qt_theme(theme_name)
        logger.info(f"Qt theme set to {theme_name}")

    def get_wallpaper(self) -> str:
        """Get current wallpaper.

        Returns:
            Current wallpaper path
        """
        adapter = self.get_adapter()
        if not adapter:
            return "Unknown"
        return adapter.get_wallpaper()

    def set_wallpaper(self, path: str) -> None:
        """Set wallpaper.

        Args:
            path: Path to wallpaper image

        Raises:
            ValueError: If path is invalid or image doesn't exist
            RuntimeError: If setting wallpaper fails
        """
        path = validate_path(path, must_exist=True)
        adapter = self.get_adapter()
        if not adapter:
            raise RuntimeError("No desktop adapter available")
        
        self.backup_manager.create_backup([adapter.get_wallpaper_config_file()])
        adapter.set_wallpaper(path)
        logger.info(f"Wallpaper set to {path}")

    def list_fonts(self) -> List[str]:
        """List available fonts.

        Returns:
            List of font names
        """
        adapter = self.get_adapter()
        if not adapter:
            return []
        return adapter.list_fonts()

    def get_font(self) -> str:
        """Get current font.

        Returns:
            Current font name
        """
        adapter = self.get_adapter()
        if not adapter:
            return "Unknown"
        return adapter.get_font()

    def set_font(self, font_name: str, size: Optional[int] = None) -> None:
        """Set font.

        Args:
            font_name: Name of font to set
            size: Font size in points

        Raises:
            ValueError: If font name is invalid
            RuntimeError: If setting font fails
        """
        validate_theme_name(font_name)
        size = validate_font_size(size)
        
        adapter = self.get_adapter()
        if not adapter:
            raise RuntimeError("No desktop adapter available")
        
        self.backup_manager.create_backup([adapter.get_font_config_file()])
        adapter.set_font(font_name, size)
        logger.info(f"Font set to {font_name}")

    def get_color_scheme(self) -> str:
        """Get the current colour scheme."""
        adapter = self.get_adapter()
        if not adapter:
            return "Unknown"
        return adapter.get_color_scheme()

    def set_color_scheme(self, scheme: str) -> None:
        """Set the colour scheme.

        Args:
            scheme: Colour scheme name

        Raises:
            ValueError: If the name is invalid
            RuntimeError: If no adapter is available or the change fails
        """
        scheme = validate_theme_name(scheme, "color scheme")
        adapter = self.get_adapter()
        if not adapter:
            raise RuntimeError("No desktop adapter available")
        adapter.set_color_scheme(scheme)
        logger.info(f"Color scheme set to {scheme}")

    def list_color_schemes(self) -> List[str]:
        """List available colour schemes."""
        adapter = self.get_adapter()
        if not adapter:
            return []
        return adapter.list_color_schemes()

    def export_preset(self, output_path: str) -> None:
        """Export current configuration as preset.

        Args:
            output_path: Path to save preset file

        Raises:
            ValueError: If output path is invalid
        """
        output_path = validate_path(output_path, must_exist=False)
        adapter = self.get_adapter()
        if not adapter:
            raise RuntimeError("No desktop adapter available")
        
        config = adapter.get_current_config()
        self.preset_manager.export_preset(config, output_path)
        logger.info(f"Preset exported to {output_path}")

    def import_preset(self, input_path: str) -> Dict[str, Any]:
        """Import preset configuration.

        Args:
            input_path: Path to preset file

        Returns:
            Preset configuration dictionary

        Raises:
            ValueError: If preset file is invalid or malformed
        """
        input_path = validate_path(input_path, must_exist=True)
        return self.preset_manager.import_preset(input_path)

    def apply_preset(self, input_path: str) -> None:
        """Apply preset configuration.

        Args:
            input_path: Path to preset file

        Raises:
            ValueError: If preset is invalid or incompatible
            RuntimeError: If applying preset fails
        """
        input_path = validate_path(input_path, must_exist=True)
        adapter = self.get_adapter()
        if not adapter:
            raise RuntimeError("No desktop adapter available")
        
        config = self.preset_manager.import_preset(input_path)
        
        # Create backup before applying
        config_files = [
            adapter.get_gtk_config_file(),
            adapter.get_icon_config_file(),
            adapter.get_cursor_config_file(),
            adapter.get_font_config_file(),
            adapter.get_wallpaper_config_file(),
        ]
        if adapter.supports(FEATURE_QT_THEME):
            config_files.append(adapter.get_qt_config_file())
        self.backup_manager.create_backup(config_files)
        
        adapter.apply_config(config)
        logger.info(f"Preset applied from {input_path}")

    def list_backups(self) -> List[Dict[str, Any]]:
        """List available backups.

        Returns:
            List of backup information dictionaries
        """
        return self.backup_manager.list_backups()

    def restore_backup(self, backup_id: str) -> None:
        """Restore from backup.

        Args:
            backup_id: ID of backup to restore

        Raises:
            ValueError: If backup ID is invalid
            RuntimeError: If restoration fails
        """
        self.backup_manager.restore_backup(backup_id)
        logger.info(f"Backup {backup_id} restored")

    def delete_backup(self, backup_id: str) -> None:
        """Delete a backup by ID.

        Args:
            backup_id: ID of backup to delete

        Raises:
            ValueError: If backup ID is invalid or does not exist
        """
        self.backup_manager.delete_backup(backup_id)
        logger.info(f"Backup {backup_id} deleted")

    # -- diagnostics ----------------------------------------------------------

    def status(self) -> Dict[str, Any]:
        """Return the current environment and configuration as a dictionary."""
        adapter = self.get_adapter()
        return {
            "desktop_environment": self.get_desktop_environment(),
            "session": self.get_session(),
            "adapter": adapter.name if adapter else None,
            "adapter_name": adapter.display_name if adapter else None,
            "features": adapter.get_supported_features() if adapter else [],
            "configuration": adapter.get_current_config() if adapter else {},
        }

    def doctor(self) -> Dict[str, Any]:
        """Return diagnostic information about the environment and tools."""
        tools = [
            "gsettings",
            "dconf",
            "kwriteconfig6",
            "kreadconfig6",
            "plasma-apply-colorscheme",
            "plasma-apply-wallpaperimage",
            "xfconf-query",
            "hyprctl",
            "hyprpaper",
            "swaymsg",
            "swaybg",
            "awww",
            "niri",
            "feh",
            "nitrogen",
            "xwallpaper",
            "pcmanfm-qt",
            "pcmanfm",
            "cosmic-bg",
            "fc-list",
        ]
        adapter = self.get_adapter()
        return {
            "desktop_environment": self.get_desktop_environment(),
            "session": self.get_session(),
            "xdg_current_desktop": os.environ.get("XDG_CURRENT_DESKTOP", ""),
            "desktop_session": os.environ.get("DESKTOP_SESSION", ""),
            "adapter": adapter.name if adapter else None,
            "adapter_name": adapter.display_name if adapter else None,
            "tools": {tool: bool(which(tool)) for tool in tools},
            "adapters": self.detector.describe_adapters(),
        }
