#!/usr/bin/env python3
"""Command-line interface for DistroMod."""

from __future__ import annotations

import argparse
import sys
from typing import Dict, List, Optional

from distromod import __version__
from distromod.core import DistroMod
from distromod.utils.logging import logger, setup_logging


class DistroModCLI:
    """CLI handler for DistroMod."""

    def __init__(self) -> None:
        self._distromod: Optional[DistroMod] = None
        self._subparsers: Dict[str, argparse.ArgumentParser] = {}

    @property
    def distromod(self) -> DistroMod:
        if self._distromod is None:
            self._distromod = DistroMod()
        return self._distromod

    # -- entry point ----------------------------------------------------------

    def run(self, args: Optional[List[str]] = None) -> int:
        """Run the CLI with ``args`` (defaults to ``sys.argv[1:]``)."""
        parser = self._build_parser()
        parsed = parser.parse_args(args)

        level = "DEBUG" if getattr(parsed, "debug", False) else (
            "INFO" if getattr(parsed, "verbose", False) else "WARNING"
        )
        setup_logging(level=level)

        if not hasattr(parsed, "func"):
            parser.print_help()
            return 0

        try:
            return parsed.func(parsed) or 0
        except KeyboardInterrupt:
            logger.info("Interrupted by user")
            print("\nCancelled.")
            return 130
        except Exception as exc:  # noqa: BLE001 - top level guard
            logger.error("Fatal error: %s", exc)
            print(f"✗ Error: {exc}")
            return 1

    # -- parser ---------------------------------------------------------------

    def _build_parser(self) -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser(
            prog="distromod",
            description="Linux Desktop Customization Tool",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  distromod status                    Show current desktop configuration
  distromod gtk set Adwaita           Change GTK theme
  distromod icons list                List installed icon themes
  distromod cursor set breeze_cursors Change cursor theme
  distromod wallpaper set ~/bg.png    Set wallpaper
  distromod font set "Noto Sans" --size 11
  distromod color set BreezeDark      Set colour scheme
  distromod preset export config.json Export current settings
  distromod preset import config.json Import a preset
  distromod backup list               List available backups
  distromod backup restore <id>       Restore from a backup
            """,
        )

        parser.add_argument(
            "--version", action="version", version=f"%(prog)s {__version__}"
        )
        parser.add_argument(
            "-v", "--verbose", action="store_true", help="Show informational messages"
        )
        parser.add_argument(
            "--debug", action="store_true", help="Show debug messages"
        )

        subparsers = parser.add_subparsers(dest="command", help="Available commands")

        # status
        status_parser = subparsers.add_parser(
            "status", help="Show current desktop configuration"
        )
        status_parser.set_defaults(func=self.cmd_status)

        # gtk
        self._subparsers["gtk"] = self._theme_command(
            subparsers, "gtk", "Manage GTK theme and settings", "theme", self.cmd_gtk
        )

        # icons
        self._subparsers["icons"] = self._theme_command(
            subparsers, "icons", "Manage icon theme", "theme", self.cmd_icons,
            allow_list=True,
        )

        # cursor
        self._subparsers["cursor"] = self._theme_command(
            subparsers, "cursor", "Manage cursor theme", "theme", self.cmd_cursor,
            allow_list=True,
        )

        # wallpaper
        wallpaper_parser = subparsers.add_parser("wallpaper", help="Manage wallpaper")
        wallpaper_sub = wallpaper_parser.add_subparsers(dest="wallpaper_command")
        wallpaper_sub.add_parser("current", help="Show current wallpaper")
        wallpaper_set = wallpaper_sub.add_parser("set", help="Set wallpaper")
        wallpaper_set.add_argument("path", help="Path to wallpaper image")
        wallpaper_parser.set_defaults(func=self.cmd_wallpaper)
        self._subparsers["wallpaper"] = wallpaper_parser

        # font
        font_parser = subparsers.add_parser("font", help="Manage fonts")
        font_sub = font_parser.add_subparsers(dest="font_command")
        font_sub.add_parser("list", help="List available fonts")
        font_sub.add_parser("current", help="Show current font")
        font_set = font_sub.add_parser("set", help="Set font")
        font_set.add_argument("font", help="Font family name")
        font_set.add_argument("--size", type=int, help="Font size in points")
        font_parser.set_defaults(func=self.cmd_font)
        self._subparsers["font"] = font_parser

        # color scheme
        color_parser = subparsers.add_parser("color", help="Manage colour scheme")
        color_sub = color_parser.add_subparsers(dest="color_command")
        color_sub.add_parser("list", help="List available colour schemes")
        color_sub.add_parser("current", help="Show current colour scheme")
        color_set = color_sub.add_parser("set", help="Set colour scheme")
        color_set.add_argument("scheme", help="Colour scheme name")
        color_parser.set_defaults(func=self.cmd_color)
        self._subparsers["color"] = color_parser

        # preset
        preset_parser = subparsers.add_parser("preset", help="Manage presets")
        preset_sub = preset_parser.add_subparsers(dest="preset_command")
        preset_export = preset_sub.add_parser("export", help="Export current configuration")
        preset_export.add_argument("output", help="Output file path")
        preset_import = preset_sub.add_parser("import", help="Import preset")
        preset_import.add_argument("input", help="Input file path")
        preset_import.add_argument(
            "--force", action="store_true", help="Apply without confirmation"
        )
        preset_parser.set_defaults(func=self.cmd_preset)
        self._subparsers["preset"] = preset_parser

        # backup
        backup_parser = subparsers.add_parser("backup", help="Manage backups")
        backup_sub = backup_parser.add_subparsers(dest="backup_command")
        backup_sub.add_parser("list", help="List available backups")
        backup_restore = backup_sub.add_parser("restore", help="Restore from backup")
        backup_restore.add_argument("backup_id", help="Backup ID")
        backup_delete = backup_sub.add_parser("delete", help="Delete a backup")
        backup_delete.add_argument("backup_id", help="Backup ID")
        backup_parser.set_defaults(func=self.cmd_backup)
        self._subparsers["backup"] = backup_parser

        return parser

    def _theme_command(
        self,
        subparsers,
        name: str,
        help_text: str,
        arg_name: str,
        handler,
        allow_list: bool = False,
    ) -> argparse.ArgumentParser:
        parser = subparsers.add_parser(name, help=help_text)
        sub = parser.add_subparsers(dest=f"{name}_command")
        if allow_list or name == "gtk":
            sub.add_parser("list", help="List available themes")
        sub.add_parser("current", help="Show current selection")
        set_parser = sub.add_parser("set", help="Set the theme")
        set_parser.add_argument(arg_name, help="Theme name")
        parser.set_defaults(func=handler)
        return parser

    # -- helpers --------------------------------------------------------------

    def _sub_required(self, name: str, command: Optional[str]) -> bool:
        """Print subcommand help when none was supplied. Returns True if handled."""
        if command:
            return False
        parser = self._subparsers.get(name)
        if parser is not None:
            parser.print_help()
        return True

    def _require_feature(self, feature: str, message: str) -> Optional[object]:
        adapter = self.distromod.get_adapter()
        if not adapter or feature not in adapter.get_supported_features():
            print(f"Error: {message}")
            return None
        return adapter

    # -- commands -------------------------------------------------------------

    def cmd_status(self, args: argparse.Namespace) -> int:
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

        print(f"Adapter: {adapter.display_name} ({adapter.name})")
        print("\nSupported Features:")
        for feature in adapter.get_supported_features():
            print(f"  ✓ {feature}")

        print("\nCurrent Configuration:")
        config = adapter.get_current_config()
        if not config:
            print("  (none)")
        for key, value in config.items():
            print(f"  {key}: {value}")

        return 0

    def cmd_gtk(self, args: argparse.Namespace) -> int:
        if self._sub_required("gtk", getattr(args, "gtk_command", None)):
            return 2
        if self._require_feature("gtk_theme", "GTK theme customization not supported on this environment.") is None:
            return 1

        if args.gtk_command == "list":
            print("\nAvailable GTK Themes:")
            for theme in self.distromod.list_gtk_themes():
                print(f"  • {theme}")
            return 0
        if args.gtk_command == "current":
            print(f"Current GTK Theme: {self.distromod.get_gtk_theme()}")
            return 0
        if args.gtk_command == "set":
            print(f"Setting GTK theme to: {args.theme}")
            self.distromod.set_gtk_theme(args.theme)
            print("✓ GTK theme updated successfully")
            return 0
        return 0

    def cmd_icons(self, args: argparse.Namespace) -> int:
        if self._sub_required("icons", getattr(args, "icons_command", None)):
            return 2
        if self._require_feature("icon_theme", "Icon theme customization not supported on this environment.") is None:
            return 1

        if args.icons_command == "list":
            print("\nAvailable Icon Themes:")
            for theme in self.distromod.list_icon_themes():
                print(f"  • {theme}")
            return 0
        if args.icons_command == "current":
            print(f"Current Icon Theme: {self.distromod.get_icon_theme()}")
            return 0
        if args.icons_command == "set":
            print(f"Setting icon theme to: {args.theme}")
            self.distromod.set_icon_theme(args.theme)
            print("✓ Icon theme updated successfully")
            return 0
        return 0

    def cmd_cursor(self, args: argparse.Namespace) -> int:
        if self._sub_required("cursor", getattr(args, "cursor_command", None)):
            return 2
        if self._require_feature("cursor_theme", "Cursor theme customization not supported on this environment.") is None:
            return 1

        if args.cursor_command == "list":
            print("\nAvailable Cursor Themes:")
            for theme in self.distromod.list_cursor_themes():
                print(f"  • {theme}")
            return 0
        if args.cursor_command == "current":
            print(f"Current Cursor Theme: {self.distromod.get_cursor_theme()}")
            return 0
        if args.cursor_command == "set":
            print(f"Setting cursor theme to: {args.theme}")
            self.distromod.set_cursor_theme(args.theme)
            print("✓ Cursor theme updated successfully")
            return 0
        return 0

    def cmd_wallpaper(self, args: argparse.Namespace) -> int:
        if self._sub_required("wallpaper", getattr(args, "wallpaper_command", None)):
            return 2
        if self._require_feature("wallpaper", "Wallpaper customization not supported on this environment.") is None:
            return 1

        if args.wallpaper_command == "current":
            print(f"Current Wallpaper: {self.distromod.get_wallpaper()}")
            return 0
        if args.wallpaper_command == "set":
            print(f"Setting wallpaper to: {args.path}")
            self.distromod.set_wallpaper(args.path)
            print("✓ Wallpaper updated successfully")
            return 0
        return 0

    def cmd_font(self, args: argparse.Namespace) -> int:
        if self._sub_required("font", getattr(args, "font_command", None)):
            return 2
        if self._require_feature("font", "Font customization not supported on this environment.") is None:
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
            print(f"Current Font: {self.distromod.get_font()}")
            return 0
        if args.font_command == "set":
            print(f"Setting font to: {args.font}")
            self.distromod.set_font(args.font, args.size)
            print("✓ Font updated successfully")
            return 0
        return 0

    def cmd_color(self, args: argparse.Namespace) -> int:
        if self._sub_required("color", getattr(args, "color_command", None)):
            return 2
        if self._require_feature("color_scheme", "Colour scheme customization not supported on this environment.") is None:
            return 1

        if args.color_command == "list":
            schemes = self.distromod.list_color_schemes()
            print("\nAvailable Colour Schemes:")
            for scheme in schemes:
                print(f"  • {scheme}")
            if not schemes:
                print("  (none found)")
            return 0
        if args.color_command == "current":
            print(f"Current Colour Scheme: {self.distromod.get_color_scheme()}")
            return 0
        if args.color_command == "set":
            print(f"Setting colour scheme to: {args.scheme}")
            self.distromod.set_color_scheme(args.scheme)
            print("✓ Colour scheme updated successfully")
            return 0
        return 0

    def cmd_preset(self, args: argparse.Namespace) -> int:
        if self._sub_required("preset", getattr(args, "preset_command", None)):
            return 2

        if args.preset_command == "export":
            print(f"Exporting current configuration to: {args.output}")
            self.distromod.export_preset(args.output)
            print(f"✓ Preset exported to {args.output}")
            return 0
        if args.preset_command == "import":
            print(f"Importing preset from: {args.input}")
            config = self.distromod.import_preset(args.input)
            print("\nPreset contains:")
            for key, value in config.items():
                print(f"  {key}: {value}")

            if not args.force:
                try:
                    confirm = input("\nApply these settings? (y/n): ")
                except EOFError:
                    confirm = "n"
                if confirm.strip().lower() not in ("y", "yes"):
                    print("Cancelled.")
                    return 0

            self.distromod.apply_preset(args.input)
            print("✓ Preset applied successfully")
            return 0
        return 0

    def cmd_backup(self, args: argparse.Namespace) -> int:
        if self._sub_required("backup", getattr(args, "backup_command", None)):
            return 2

        if args.backup_command == "list":
            backups = self.distromod.list_backups()
            if not backups:
                print("No backups available.")
                return 0
            print("\nAvailable Backups:")
            for backup in backups:
                print(
                    f"  {backup['id']}: {backup['timestamp']} "
                    f"({backup['files']} files)"
                )
            return 0
        if args.backup_command == "restore":
            print(f"Restoring from backup: {args.backup_id}")
            self.distromod.restore_backup(args.backup_id)
            print("✓ Backup restored successfully")
            return 0
        if args.backup_command == "delete":
            print(f"Deleting backup: {args.backup_id}")
            self.distromod.delete_backup(args.backup_id)
            print("✓ Backup deleted successfully")
            return 0
        return 0


def main(argv: Optional[List[str]] = None) -> int:
    """Main entry point."""
    return DistroModCLI().run(argv)


if __name__ == "__main__":
    sys.exit(main())
