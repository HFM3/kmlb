"""Shared test setup.

kmlb is pure standard library, so there is nothing to stub at import time. The
only setup needed is to place the ``src`` layout on the path so the package is
importable without an install.
"""

import sys
from pathlib import Path

# Make the src-layout package importable without installation.
SRC = Path(__file__).resolve().parents[1] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
