"""pytest configuration and shared fixtures."""

import sys
from pathlib import Path

# Add backend/ to sys.path so imports work from tests/
sys.path.insert(0, str(Path(__file__).parent.parent))
