"""Entry point for the `harness` CLI command."""

import sys
from pathlib import Path

# Add src to path for imports
src_path = str(Path(__file__).parent / "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from harness_tui import main

if __name__ == "__main__":
    main()
