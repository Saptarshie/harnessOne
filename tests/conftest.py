"""Test configuration to resolve import conflicts.

The harness.py CLI file conflicts with the harness package.
This conftest ensures the harness package is found first.
"""

import sys
from pathlib import Path

# Ensure src directory is first in sys.path
src_path = str(Path(__file__).parent.parent / "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)
