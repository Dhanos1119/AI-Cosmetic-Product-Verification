"""
AI Cosmetic Verification Application Package
"""

import sys
from pathlib import Path

# Add project root directory to sys.path so root packages like 'database' are importable
BASE_DIR = Path(__file__).parent.parent.parent.resolve()
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

__version__ = "1.0.0"
