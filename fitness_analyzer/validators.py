"""Validation functions and regular expressions for the Fitness Session Analyzer.

Validates identifiers using anchored regular expressions per Section 4.2 of the assignment.
Ordinary numerical range checks use standard Python comparisons, as instructed.
"""

import re
from fitness_analyzer.exceptions import InvalidIdentifierError


# Regular expressions with anchored patterns / full-match behavior
PARTICIPANT_ID_PATTERN = re.compile(r"^P\d{3}$")
SESSION_ID_PATTERN = re.compile(r"^FIT-\d{4}-\d{3}$")
CSV_FILENAME_PATTERN = re.compile(r"^.+\.csv$", re.IGNORECASE)


def validate_participant_id(identifier):
    """Validate that participant ID follows 'P' followed by 3 digits (e.g. 'P001').

    Raises InvalidIdentifierError if the format is invalid.
    """
    if not isinstance(identifier, str) or not PARTICIPANT_ID_PATTERN.fullmatch(identifier.strip()):
        raise InvalidIdentifierError(
            f"Invalid Participant ID '{identifier}'. Must match format 'P' followed by 3 digits (e.g. 'P001')."
        )
    return identifier.strip()


def validate_session_id(identifier):
    """Validate that fitness session ID matches 'FIT-YYYY-NNN' (e.g. 'FIT-2026-001').

    Raises InvalidIdentifierError if the format is invalid.
    """
    if not isinstance(identifier, str) or not SESSION_ID_PATTERN.fullmatch(identifier.strip()):
        raise InvalidIdentifierError(
            f"Invalid Session ID '{identifier}'. Must match format 'FIT-YYYY-NNN' (e.g. 'FIT-2026-001')."
        )
    return identifier.strip()


def validate_csv_filename(filename):
    """Validate that a given path or filename ends with .csv extension using regex."""
    if not isinstance(filename, str) or not CSV_FILENAME_PATTERN.fullmatch(filename.strip()):
        raise ValueError(f"Expected a CSV filename ending in '.csv', got '{filename}'")
    return filename.strip()


def validate_numeric_range(value, lower_bound, upper_bound, metric_name):
    """Check if a numeric measurement is within physiological/sensor limits.

    Uses ordinary comparisons (not regex, per assignment guidelines).
    Returns an error description if out of range, or None if valid.
    """
    if value is None:
        return f"Missing value for {metric_name}"
    if not isinstance(value, (int, float)):
        return f"{metric_name} must be numeric, got {type(value).__name__}"
    if value < lower_bound or value > upper_bound:
        return f"{metric_name} value {value} is out of allowable range [{lower_bound}, {upper_bound}]"
    return None
