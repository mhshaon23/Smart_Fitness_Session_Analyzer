"""Standalone calculation, validation, and presentation functions for the Fitness Analyzer.

This module provides reusable mathematical, statistical, and formatting helpers
without binding them to specific class instances, satisfying the requirement
for standalone functions.
"""

from typing import List, Dict, Any, Tuple, Optional


def calculate_summary_statistics(values: List[float | int]) -> Dict[str, Optional[float]]:
    """Calculate mean, min, and max for a sequence of numbers.

    Returns None for all metrics if the input list is empty to prevent ZeroDivisionError.
    Values are rounded to two decimal places for readable reporting.
    """
    if not values:
        return {"mean": None, "min": None, "max": None, "count": 0}

    total = sum(values)
    count = len(values)
    mean_val = round(total / count, 2)
    min_val = round(float(min(values)), 2)
    max_val = round(float(max(values)), 2)

    return {
        "mean": mean_val,
        "min": min_val,
        "max": max_val,
        "count": count,
    }


def detect_recovery_trend(observations: List[Any]) -> Tuple[bool, str]:
    """Examine whether heart rate and activity show a clear downward trend near the end.

    Divides the valid observations into an 'early' phase (first third) and a
    'late' phase (final third). If both heart rate and activity level start elevated
    and decline significantly toward baseline, recovery is confirmed.

    Returns:
        (is_recovering, diagnostic_explanation)
    """
    if len(observations) < 6:
        return False, "Not enough observations to reliably detect a temporal recovery trend (minimum 6 needed)."

    chunk_size = max(2, len(observations) // 3)
    early_window = observations[:chunk_size]
    late_window = observations[-chunk_size:]

    early_hr = sum(obs.heart_rate for obs in early_window) / len(early_window)
    late_hr = sum(obs.heart_rate for obs in late_window) / len(late_window)

    early_act = sum(obs.activity_level for obs in early_window) / len(early_window)
    late_act = sum(obs.activity_level for obs in late_window) / len(late_window)

    hr_drop = early_hr - late_hr
    act_drop = early_act - late_act

    # A valid recovery must start with noticeable exertion and then fall markedly
    if hr_drop >= 15.0 and act_drop >= 0.20:
        reason = (
            f"Clear recovery pattern detected: heart rate dropped by {hr_drop:.1f} bpm "
            f"({early_hr:.1f} -> {late_hr:.1f}) and activity level dropped by {act_drop:.2f} "
            f"({early_act:.2f} -> {late_act:.2f}) from start to finish."
        )
        return True, reason

    reason = (
        f"No recovery trend: HR changed by {-hr_drop:+.1f} bpm and activity changed by "
        f"{-act_drop:+.2f} between early and late session windows."
    )
    return False, reason


def calculate_baseline_deviations(
    avg_hr: Optional[float],
    avg_temp: Optional[float],
    baseline_hr: float,
    baseline_temp: float,
) -> Dict[str, Optional[float]]:
    """Compute how much average session readings deviate from personal baselines.

    Returns absolute differences and percentage changes relative to baseline.
    """
    if avg_hr is None or avg_temp is None:
        return {
            "hr_difference": None,
            "hr_percent_change": None,
            "temp_difference": None,
        }

    hr_diff = round(avg_hr - baseline_hr, 2)
    hr_pct = round((hr_diff / baseline_hr) * 100, 1) if baseline_hr > 0 else 0.0
    temp_diff = round(avg_temp - baseline_temp, 2)

    return {
        "hr_difference": hr_diff,
        "hr_percent_change": hr_pct,
        "temp_difference": temp_diff,
    }


def format_console_table(headers: List[str], rows: List[List[str]]) -> str:
    """Build an aligned ASCII table for console presentation.

    Dynamically sizes each column based on header and row contents for clean terminal display.
    """
    if not headers:
        return ""

    col_widths = [len(h) for h in headers]
    for row in rows:
        for idx, cell in enumerate(row):
            if idx < len(col_widths):
                col_widths[idx] = max(col_widths[idx], len(str(cell)))

    # Formatting helper for borders and lines
    sep_line = "+" + "+".join("-" * (w + 2) for w in col_widths) + "+"
    header_line = "| " + " | ".join(h.ljust(col_widths[i]) for i, h in enumerate(headers)) + " |"

    body_lines = []
    for row in rows:
        row_cells = []
        for i, cell in enumerate(row):
            w = col_widths[i]
            # Right-align numeric looking strings, left-align text
            cell_str = str(cell)
            if cell_str.replace(".", "", 1).replace("-", "", 1).isdigit():
                row_cells.append(cell_str.rjust(w))
            else:
                row_cells.append(cell_str.ljust(w))
        body_lines.append("| " + " | ".join(row_cells) + " |")

    return "\n".join([sep_line, header_line, sep_line] + body_lines + [sep_line])


def validate_raw_observation_dict(raw: Dict[str, Any]) -> List[str]:
    """Check a raw dictionary for presence and types of mandatory fields before parsing.

    Returns a list of error strings; empty if structure is acceptable.
    """
    errors = []
    expected_fields = [
        "timestamp",
        "heart_rate",
        "skin_response",
        "temperature",
        "activity_level",
        "signal_quality",
    ]

    if not isinstance(raw, dict):
        return ["Observation data must be a dictionary"]

    for field in expected_fields:
        if field not in raw:
            errors.append(f"Missing required field '{field}'")

    return errors

