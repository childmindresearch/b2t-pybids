"""
Query helpers for filtering BIDS entities.

Provides sentinel values for special filtering behavior:
- Query.OPTIONAL: Allow entity to be missing or have any value
- Query.NONE: Match only when entity is explicitly missing
- Query.ANY: Match any value (don't filter on this entity)
"""


class Query:
    """Special query values for entity filtering."""

    # Sentinel objects for special filtering behavior
    OPTIONAL = object()  # Allow missing or any value
    NONE = object()      # Match explicit null/missing
    ANY = object()       # Match any value (don't filter)

    def __repr__(self):
        return "Query"
