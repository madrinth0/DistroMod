"""Allow running DistroMod as ``python -m distromod``."""

import sys

from distromod.cli import main

if __name__ == "__main__":
    sys.exit(main())
