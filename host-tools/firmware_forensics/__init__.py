"""Offline firmware forensics helpers.

The package deliberately has no device transport integration.  It reads local
files, produces metadata, and optionally writes extracted components to an
explicit host-side directory.
"""

__all__ = ["core"]
__version__ = "0.1"
