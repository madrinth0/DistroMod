#!/usr/bin/env bash
#
# Build a standalone DistroMod executable with PyInstaller.
#
set -euo pipefail

cd "$(dirname "$0")"

PYTHON="${PYTHON:-python3}"

if ! "$PYTHON" -m PyInstaller --version >/dev/null 2>&1; then
    echo "PyInstaller is not installed." >&2
    echo "Install it with:  $PYTHON -m pip install pyinstaller" >&2
    exit 1
fi

rm -rf build dist

"$PYTHON" -m PyInstaller \
    --onefile \
    --name distromod \
    --paths . \
    --hidden-import distromod.adapters.gnome \
    --hidden-import distromod.adapters.kde \
    --hidden-import distromod.adapters.hyprland \
    --hidden-import distromod.adapters.xfce \
    --hidden-import distromod.adapters.cinnamon \
    --hidden-import distromod.adapters.mate \
    --hidden-import distromod.adapters.lxqt \
    --hidden-import distromod.adapters.generic \
    distromod/__main__.py

echo
echo "Built: dist/distromod"
echo "Tip:   install it with  sudo install -Dm755 dist/distromod /usr/local/bin/distromod"
