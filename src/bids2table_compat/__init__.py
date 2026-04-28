"""
PyBIDS compatibility layer for bids2table.

This module provides a drop-in replacement for common PyBIDS patterns,
allowing easy migration while teaching better DataFrame-based approaches.

Example:
    # Change this:
    from bids.layout import BIDSLayout

    # To this:
    from bids2table_compat import BIDSLayout

    # Everything else stays the same!
    layout = BIDSLayout('/path/to/dataset', validate=False)
    files = layout.get(subject='01', suffix='T1w')
"""

from .layout import BIDSLayout
from .query import Query
from .bidsfile import BIDSFile

__version__ = "0.1.0"

__all__ = [
    "BIDSLayout",
    "Query",
    "BIDSFile",
]
