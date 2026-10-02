"""Custom exceptions for the Fitness Session Analyzer application.

Per the assignment specification:
- InvalidIdentifierError: Raised when participant or session ID fails regex format.
- InvalidRecordError: Raised when a CSV record has missing values, bad types, or wrong length.
"""


class InvalidIdentifierError(ValueError):
    """Raised when an identifier has an invalid format."""
    pass


class InvalidRecordError(ValueError):
    """Raised when a CSV record cannot be accepted."""
    pass
