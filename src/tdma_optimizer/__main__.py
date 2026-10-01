"""
__main__.py
-----------
Allows running the package directly with:

    python -m tdma_optimizer [arguments]

This file is the conventional entry-point for Python packages that
support ``python -m`` invocation.
"""

import sys

from .cli import main

if __name__ == "__main__":
    sys.exit(main())
