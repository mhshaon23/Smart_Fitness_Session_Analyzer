"""Standalone helper functions for the fitness session analyzer.

Contains functions for calculating statistics, detecting recovery trends,
calculating differences from baseline, and simple table formatting.
"""


def calculate_summary_statistics(values):
    """Calculate mean, min, and max for a list of numbers."""
    if not values:
        return {"mean": None, "min": None, "max": None, "count": 0}

    count = len(values)
    avg_val = round(sum(values) / count, 2)
    min_val = round(float(min(values)), 2)
    max_val = round(float(max(values)), 2)

    return {
        "mean": avg_val,
        "min": min_val,
        "max": max_val,
        "count": count,
    }


def detect_recovery_trend(observations):
    """Check if heart rate and activity drop near the end of the session.

    Compares the first third of observations to the last third of observations.
    If both heart rate and activity decrease significantly, it's considered recovery.
    """
    if len(observations) < 6:
        return False, "Not enough observations to reliably detect a temporal recovery trend (minimum 6 needed)."

    # Split into thirds
    chunk_size = max(2, len(observations) // 3)
    early_chunk = observations[:chunk_size]
    late_chunk = observations[-chunk_size:]

    early_hr = sum(obs.heart_rate for obs in early_chunk) / len(early_chunk)
    late_hr = sum(obs.heart_rate for obs in late_chunk) / len(late_chunk)

    early_act = sum(obs.activity_level for obs in early_chunk) / len(early_chunk)
    late_act = sum(obs.activity_level for obs in late_chunk) / len(late_chunk)

    hr_drop = early_hr - late_hr
    act_drop = early_act - late_act

    # A clear recovery should have a solid drop in both HR and movement
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


def calculate_baseline_deviations(avg_hr, avg_temp, baseline_hr, baseline_temp):
    """Calculate the difference between average session values and personal baseline."""
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


def format_console_table(headers, rows):
    """Format headers and rows into a readable ASCII table for terminal output."""
    if not headers:
        return ""

    # Figure out column widths based on contents
    widths = [len(h) for h in headers]
    for row in rows:
        for i, val in enumerate(row):
            if i < len(widths):
                widths[i] = max(widths[i], len(str(val)))

    # Build the horizontal divider and header line
    divider = "+" + "+".join("-" * (w + 2) for w in widths) + "+"
    header_str = "| " + " | ".join(h.ljust(widths[i]) for i, h in enumerate(headers)) + " |"

    table_lines = [divider, header_str, divider]
    for row in rows:
        row_cells = []
        for i, val in enumerate(row):
            w = widths[i]
            s = str(val)
            # Align numbers to the right, text to the left
            if s.replace(".", "", 1).replace("-", "", 1).isdigit():
                row_cells.append(s.rjust(w))
            else:
                row_cells.append(s.ljust(w))
        table_lines.append("| " + " | ".join(row_cells) + " |")
    table_lines.append(divider)

    return "\n".join(table_lines)


def validate_raw_observation_dict(raw):
    """Check that a raw dictionary has all the expected fields before creating an object."""
    if not isinstance(raw, dict):
        return ["Observation data must be a dictionary"]

    required_keys = [
        "timestamp",
        "heart_rate",
        "skin_response",
        "temperature",
        "activity_level",
        "signal_quality",
    ]

    errors = []
    for key in required_keys:
        if key not in raw:
            errors.append(f"Missing required field '{key}'")
    return errors
