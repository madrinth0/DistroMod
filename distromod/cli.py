#!/usr/bin/env python3
"""Command-line interface for DistroMod."""

import argparse
import sys
from typing import Optional

from distromod import __version__
from distromod.core import DistroMod
from distromod.utils.logging import setup_logging, logger


class DistroModCLI:
    """CLI handler for DistroMod."""

    def __init__(self):
        """Initialize CLI handler."""
        self.distromod = DistroMod()
        setup_logging()

    def run(self, args: Optional[list] = None) -> int:
        """Run CLI with given arguments.

        Args:
            args: Command-line arguments (defaults to sys.argv[1:])

        Returns:
            Exit code (0 for success, non-zero for failure)
        """
        parser = self._build_parser()
        parsed = parser.parse_args(args)

        if not hasattr(parsed, "func"):
            parser.print_help()
            return 0

        try:
            return parsed.func(parsed) or 0
        except KeyboardInterrupt:
            logger.info("Interrupted by user")
            return 130
        except Exception as e:
            logger.error(f"Fatal error: {e}")
            return 1

    def _build_parser(self) -> argparse.ArgumentParser:
        """Build argument parser.

        Returns:
            ArgumentParser with all subcommands configured
        """
        parser = argparse.ArgumentParser(
            prog="distromod",
            description="Linux Desktop Customization Tool",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  distromod status              Show current desktop configuration
  distromod gtk --theme Adwaita Change GTK theme
  distromod wallpaper --set <path> Set wallpaper
  distromod preset export config.json Export current settings
  distromod preset import config.json Import preset configuration
  distromod backup list         List available backups
  distromod backup restore <id> Restore from backup
            """,
        )

        parser.add_argument(
            "--version",
            action="version",
            version=f"%(prog)s {__version__}",
        )

        subparsers = parser.add_subparsers(dest="command", help="Available commands")

        # Status command
        status_parser = subparsers.add_parser(
            "status", help="Show current desktop configuration"
        )
        status_parser.set_defaults(func=self.cmd_status)

        # GTK command
        gtk_parser = subparsers.add_parser("gtk", help="Manage GTK theme and settings")
        gtk_subparsers = gtk_parser.add_subparsers(dest="gtk_command")
        gtk_subparsers.add_parser("list", help="List available GTK themes")
        gtk_subparsers.add_parser("current", help="Show current GTK theme")
        gtk_theme = gtk_subparsers.add_parser("set", help="Set GTK theme")
        gtk_theme.add_argument("theme", help="Theme name")
        gtk_parser.set_defaults(func=self.cmd_gtk)

        # Icons command
        icons_parser = subparsers.add_parser("icons", help="Manage icon theme")
        icons_subparsers = icons_parser.add_subparsers(dest="icons_command")
        icons_subparsers.add_parser("list", help="List available icon themes")
        icons_subparsers.add_parser("current", help="Show current icon theme")
        icons_set = icons_subparsers.add_parser("set", help="Set icon theme")
        icons_set.add_argument("theme", help="Theme name")
        icons_parser.set_defaults(func=self.cmd_icons)

        # Cursor command
        cursor_parser = subparsers.add_parser("cursor", help="Manage cursor theme")
        cursor_subparsers = cursor_parser.add_subparsers(dest="cursor_command")
        cursor_subparsers.add_parser("list", help="List available cursor themes")
        cursor_subparsers.add_parser("current", help="Show current cursor theme")
        cursor_set = cursor_subparsers.add_parser("set", help="Set cursor theme")
        cursor_set.add_argument("theme", help="Theme name")
        cursor_parser.set_defaults(func=self.cmd_cursor)

        # Wallpaper command
        wallpaper_parser = subparsers.add_parser(
            "wallpaper", help="Manage wallpaper"
        )
        wallpaper_subparsers = wallpaper_parser.add_subparsers(
            dest="wallpaper_command"
        )
        wallpaper_subparsers.add_parser("current", help="Show current wallpaper")
        wallpaper_set = wallpaper_subparsers.add_parser("set", help="Set wallpaper")
        wallpaper_set.add_argument("path", help="Path to wallpaper image")
        wallpaper_parser.set_defaults(func=self.cmd_wallpaper)

        # Font command
        font_parser = subparsers.add_parser("font", help="Manage fonts")
        font_subparsers = font_parser.add_subparsers(dest="font_command")
        font_subparsers.add_parser("list", help="List available fonts")
        font_subparsers.add_parser("current", help="Show current font")
        font_set = font_subparsers.add_parser("set", help="Set font")
        font_set.add_argument("font", help="Font name")
        font_set.add_argument("--size", type=int, help="Font size")
        font_parser.set_defaults(func=self.cmd_font)

        # Preset command
        preset_parser = subparsers.add_parser("preset", help="Manage presets")
        preset_subparsers = preset_parser.add_subparsers(dest="preset_command")
        preset_export = preset_subparsers.add_parser(
            "export", help="Export current configuration"
        )
        preset_export.add_argument("output", help="Output file path")
        preset_import = preset_subparsers.add_parser("import", help="Import preset")
        preset_import.add_argument("input", help="Input file path")
        preset_import.add_argument(
            "--force", action="store_true", help="Override without confirmation"
        )
        preset_parser.set_defaults(func=self.cmd_preset)

        # Backup command
        backup_parser = subparsers.add_parser("backup", help="Manage backups")
        backup_subparsers = backup_parser.add_subparsers(dest="backup_command")
        backup_subparsers.add_parser("list", help="List available backups")
        backup_restore = backup_subparsers.add_parser(
            "restore", help="Restore from backup"
        )
        backup_restore.add_argument("backup_id", help="Backup ID")
        backup_parser.set_defaults(func=self.cmd_backup)

        return parser

    def cmd_status(self, args: argparse.Namespace) -> int:
        """Status command: show current configuration."""
        print("\n=== DistroMod Status ===")
        print(f"Version: {__version__}")
        print(f"\nDesktop Environment: {self.distromod.get_desktop_environment()}")
        print(f"Desktop Session: {self.distromod.get_session()}")

        adapter = self.distromod.get_adapter()
        if not adapter:
            print("\nStatus: No supported desktop environment detected.")
            print(
                "DistroMod works best with: GNOME, KDE Plasma, Hyprland, XFCE, "
                "Cinnamon, MATE, or LXQt."
            )
            return 1

        print(f"Adapter: {adapter.name}")
        print(f"\nSupported Features:")
        features = adapter.get_supported_features()
        for feature in features:
            print(f"  ✓ {feature}")

        print("\nCurrent Configuration:")
        config = adapter.get_current_config()
        for key, value in config.items():
            print(f"  {key}: {value}")

        return 0

    def cmd_gtk(self, args: argparse.Namespace) -> int:
        """GTK theme command."""
        adapter = self.distromod.get_adapter()
        if not adapter or "gtk_theme" not in adapter.get_supported_features():
            print("Error: GTK theme customization not supported on this environment.")
            return 1

        if args.gtk_command == "list":
            themes = self.distromod.list_gtk_themes()
            print("\nAvailable GTK Themes:")
            for theme in themes:
                print(f"  • {theme}")
            return 0

        if args.gtk_command == "current":
            current = self.distromod.get_gtk_theme()
            print(f"Current GTK Theme: {current}")
            return 0

        if args.gtk_command == "set":
            print(f"Setting GTK theme to: {args.theme}")
            try:
                self.distromod.set_gtk_theme(args.theme)
                print("✓ GTK theme updated successfully")
                return 0
            except Exception as e:
                print(f"✗ Error: {e}")
                return 1

        return 0

    def cmd_icons(self, args: argparse.Namespace) -> int:
        """Icon theme command."""
        adapter = self.distromod.get_adapter()
        if not adapter or "icon_theme" not in adapter.get_supported_features():
            print("Error: Icon theme customization not supported on this environment.")
            return 1

        if args.icons_command == "list":
            themes = self.distromod.list_icon_themes()
            print("\nAvailable Icon Themes:")
            for theme in themes:
                print(f"  • {theme}")
            return 0

        if args.icons_command == "current":
            current = self.distromod.get_icon_theme()
            print(f"Current Icon Theme: {current}")
            return 0

        if args.icons_command == "set":
            print(f"Setting icon theme to: {args.theme}")
            try:
                self.distromod.set_icon_theme(args.theme)
                print("✓ Icon theme updated successfully")
                return 0
            except Exception as e:
                print(f"✗ Error: {e}")
                return 1

        return 0

    def cmd_cursor(self, args: argparse.Namespace) -> int:
        """Cursor theme command."""
        adapter = self.distromod.get_adapter()
        if not adapter or "cursor_theme" not in adapter.get_supported_features():
            print("Error: Cursor theme customization not supported on this environment.")
            return 1

        if args.cursor_command == "list":
            themes = self.distromod.list_cursor_themes()
            print("\nAvailable Cursor Themes:")
            for theme in themes:
                print(f"  • {theme}")
            return 0

        if args.cursor_command == "current":
            current = self.distromod.get_cursor_theme()
            print(f"Current Cursor Theme: {current}")
            return 0

        if args.cursor_command == "set":
            print(f"Setting cursor theme to: {args.theme}")
            try:
                self.distromod.set_cursor_theme(args.theme)
                print("✓ Cursor theme updated successfully")
                return 0
            except Exception as e:
                print(f"✗ Error: {e}")
                return 1

        return 0

    def cmd_wallpaper(self, args: argparse.Namespace) -> int:
        """Wallpaper command."""
        adapter = self.distromod.get_adapter()
        if not adapter or "wallpaper" not in adapter.get_supported_features():
            print("Error: Wallpaper customization not supported on this environment.")
            return 1

        if args.wallpaper_command == "current":
            current = self.distromod.get_wallpaper()
            print(f"Current Wallpaper: {current}")
            return 0

        if args.wallpaper_command == "set":
            print(f"Setting wallpaper to: {args.path}")
            try:
                self.distromod.set_wallpaper(args.path)
                print("✓ Wallpaper updated successfully")
                return 0
            except Exception as e:
                print(f"✗ Error: {e}")
                return 1

        return 0

    def cmd_font(self, args: argparse.Namespace) -> int:
        """Font command."""
        adapter = self.distromod.get_adapter()
        if not adapter or "font" not in adapter.get_supported_features():
            print("Error: Font customization not supported on this environment.")
            return 1

        if args.font_command == "list":
            fonts = self.distromod.list_fonts()
            print("\nAvailable Fonts (sample):")
            for font in fonts[:20]:
                print(f"  • {font}")
            if len(fonts) > 20:
                print(f"  ... and {len(fonts) - 20} more")
            return 0

        if args.font_command == "current":
            current = self.distromod.get_font()
            print(f"Current Font: {current}")
            return 0

        if args.font_command == "set":
            print(f"Setting font to: {args.font}")
            try:
                self.distromod.set_font(args.font, args.size)
                print("✓ Font updated successfully")
                return 0
            except Exception as e:
                print(f"✗ Error: {e}")
                return 1

        return 0

    def cmd_preset(self, args: argparse.Namespace) -> int:
        """Preset command."""
        if args.preset_command == "export":
            print(f"Exporting current configuration to: {args.output}")
            try:
                self.distromod.export_preset(args.output)
                print(f"✓ Preset exported to {args.output}")
                return 0
            except Exception as e:
                print(f"✗ Error: {e}")
                return 1

        if args.preset_command == "import":
            print(f"Importing preset from: {args.input}")
            try:
                config = self.distromod.import_preset(args.input)
                print(f"\nPreset contains:")
                for key, value in config.items():
                    print(f"  {key}: {value}")

                if not args.force:
                    confirm = input("\nApply these settings? (y/n): ")
                    if confirm.lower() != "y":
                        print("Cancelled.")
                        return 0

                self.distromod.apply_preset(args.input)
                print("✓ Preset applied successfully")
                return 0
            except Exception as e:
                print(f"✗ Error: {e}")
                return 1

        return 0

    def cmd_backup(self, args: argparse.Namespace) -> int:
        """Backup command."""
        if args.backup_command == "list":
            backups = self.distromod.list_backups()
            if not backups:
                print("No backups available.")
                return 0

            print("\nAvailable Backups:")
            for backup in backups:
                print(f"  {backup['id']}: {backup['timestamp']} ({backup['files']} files)")
            return 0

        if args.backup_command == "restore":
            print(f"Restoring from backup: {args.backup_id}")
            try:
                self.distromod.restore_backup(args.backup_id)
                print("✓ Backup restored successfully")
                return 0
            except Exception as e:
                print(f"✗ Error: {e}")
                return 1

        return 0


def main() -> int:
    """Main entry point."""
    cli = DistroModCLI()
    return cli.run()


if __name__ == "__main__":
    sys.exit(main())
