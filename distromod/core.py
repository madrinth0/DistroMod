"""Core DistroMod functionality."""

import json
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from distromod.adapters.base import DesktopAdapter
from distromod.detection import DesktopDetector
from distromod.backup import BackupManager
from distromod.presets import PresetManager
from distromod.utils.logging import logger
from distromod.utils.validation import validate_path, validate_theme_name


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

    def set_cursor_theme(self, theme_name: str) -> None:
        """Set cursor theme.

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
        
        self.backup_manager.create_backup([adapter.get_cursor_config_file()])
        adapter.set_cursor_theme(theme_name)
        logger.info(f"Cursor theme set to {theme_name}")

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
        validate_path(path, must_exist=True)
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
        if size is not None and (size < 6 or size > 72):
            raise ValueError("Font size must be between 6 and 72")
        
        adapter = self.get_adapter()
        if not adapter:
            raise RuntimeError("No desktop adapter available")
        
        self.backup_manager.create_backup([adapter.get_font_config_file()])
        adapter.set_font(font_name, size)
        logger.info(f"Font set to {font_name}")

    def export_preset(self, output_path: str) -> None:
        """Export current configuration as preset.

        Args:
            output_path: Path to save preset file

        Raises:
            ValueError: If output path is invalid
        """
        validate_path(output_path, must_exist=False)
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
        validate_path(input_path, must_exist=True)
        return self.preset_manager.import_preset(input_path)

    def apply_preset(self, input_path: str) -> None:
        """Apply preset configuration.

        Args:
            input_path: Path to preset file

        Raises:
            ValueError: If preset is invalid or incompatible
            RuntimeError: If applying preset fails
        """
        validate_path(input_path, must_exist=True)
        adapter = self.get_adapter()
        if not adapter:
            raise RuntimeError("No desktop adapter available")
        
        config = self.preset_manager.import_preset(input_path)
        
        # Create backup before applying
        config_files = [
            adapter.get_gtk_config_file(),
            adapter.get_icon_config_file(),
            adapter.get_cursor_config_file(),
        ]
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
