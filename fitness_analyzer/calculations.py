"""Standalone calculation, analysis, and formatting helpers.

Contains statistical functions, recovery trend detection, and baseline difference logic.
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
    if len(observations) < 4:
        return False, "Not enough observations to reliably detect a recovery trend."

    # Split observations into thirds (early, mid, late)
    chunk_size = max(1, len(observations) // 3)
    early_chunk = observations[:chunk_size]
    late_chunk = observations[-chunk_size:]

    early_hr = sum(obs.heart_rate for obs in early_chunk) / len(early_chunk)
    late_hr = sum(obs.heart_rate for obs in late_chunk) / len(late_chunk)

    early_act = sum(obs.activity_level for obs in early_chunk) / len(early_chunk)
    late_act = sum(obs.activity_level for obs in late_chunk) / len(late_chunk)

    hr_drop = early_hr - late_hr
    act_drop = early_act - late_act

    # Check 1: Direct early-to-late drop
    if hr_drop >= 15.0 and act_drop >= 0.15:
        reason = (
            f"Recovery pattern detected: heart rate dropped by {hr_drop:.1f} bpm "
            f"({early_hr:.1f} -> {late_hr:.1f}) and activity level dropped by {act_drop:.2f} "
            f"({early_act:.2f} -> {late_act:.2f})."
        )
        return True, reason

    # Check 2: Peak workout followed by cooldown near the end of session
    first_half = observations[: len(observations) // 2 + 1]
    peak_hr = max(obs.heart_rate for obs in first_half)
    peak_act = max(obs.activity_level for obs in first_half)
    drop_from_peak_hr = peak_hr - late_hr
    drop_from_peak_act = peak_act - late_act

    if drop_from_peak_hr >= 25.0 and drop_from_peak_act >= 0.35 and late_act <= 0.35:
        reason = (
            f"Activity followed by recovery: heart rate peaked at {peak_hr} bpm and declined to "
            f"{late_hr:.1f} bpm (-{drop_from_peak_hr:.1f} bpm) with activity dropping from "
            f"{peak_act:.2f} to {late_act:.2f} near the end."
        )
        return True, reason

    reason = (
        f"No recovery trend: HR changed by {-hr_drop:+.1f} bpm and activity changed by "
        f"{-act_drop:+.2f}."
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
    """Format headers and rows into an aligned text table."""
    if not headers:
        return ""

    widths = [len(h) for h in headers]
    for row in rows:
        for i, val in enumerate(row):
            if i < len(widths):
                widths[i] = max(widths[i], len(str(val)))

    divider = "+" + "+".join("-" * (w + 2) for w in widths) + "+"
    header_str = "| " + " | ".join(h.ljust(widths[i]) for i, h in enumerate(headers)) + " |"

    lines = [divider, header_str, divider]
    for row in rows:
        row_cells = []
        for i, val in enumerate(row):
            w = widths[i]
            s = str(val)
            if s.replace(".", "", 1).replace("-", "", 1).isdigit():
                row_cells.append(s.rjust(w))
            else:
                row_cells.append(s.ljust(w))
        lines.append("| " + " | ".join(row_cells) + " |")
    lines.append(divider)

    return "\n".join(lines)
