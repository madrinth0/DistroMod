#!/usr/bin/env bash
#
# Run DistroMod straight from a source checkout.
#
set -euo pipefail

cd "$(dirname "$0")"
exec "${PYTHON:-python3}" -m distromod "$@"
