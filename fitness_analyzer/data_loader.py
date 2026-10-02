"""Data loading, CSV parsing, record validation, and output generation.

Handles:
- Reading participants.csv with open(..., encoding="utf-8", newline="")
- Reading session CSV files and grouping records by session_id
- Quarantining corrupted rows and recording them in rejected_records.txt
- Writing analysis_summary.csv, analysis_report.txt, and rejected_records.txt
"""

import csv
from pathlib import Path
from fitness_analyzer.exceptions import InvalidIdentifierError, InvalidRecordError
from fitness_analyzer.validators import (
    validate_participant_id,
    validate_session_id,
    validate_csv_filename,
    validate_numeric_range,
)
from fitness_analyzer.models import Participant, Observation, FitnessSession


def load_participants_csv(filepath):
    """Load participant profiles from CSV.

    Uses with open(..., encoding="utf-8", newline="") and csv.reader.
    Validates participant_id with regex and checks baseline ranges.
    Returns a dictionary mapping participant_id -> Participant instance.
    """
    path = Path(filepath)
    if not path.is_file():
        raise FileNotFoundError(f"Participants file not found: {path}")

    # Validate filename extension with regex
    validate_csv_filename(str(path))

    participants = {}
    try:
        with open(path, mode="r", encoding="utf-8", newline="") as f:
            reader = csv.reader(f)
            header = next(reader, None)
            if not header:
                raise InvalidRecordError(f"File {path.name} is empty")

            for row_idx, row in enumerate(reader, start=2):
                if not row or not any(field.strip() for field in row):
                    continue  # skip completely empty lines

                if len(row) != 5:
                    raise InvalidRecordError(
                        f"Row {row_idx} in {path.name} has {len(row)} columns, expected 5"
                    )

                p_id, name, hr_str, skin_str, temp_str = [cell.strip() for cell in row]

                # Validate participant ID with regex
                try:
                    validate_participant_id(p_id)
                except InvalidIdentifierError as e:
                    raise InvalidIdentifierError(f"Row {row_idx} in {path.name}: {e}")

                # Convert baseline numbers
                try:
                    hr = int(hr_str)
                    skin = float(skin_str)
                    temp = float(temp_str)
                except ValueError as e:
                    raise InvalidRecordError(
                        f"Row {row_idx} in {path.name}: Cannot parse numeric baselines ({e})"
                    )

                # Instantiate Participant (encapsulation property checks apply)
                participant = Participant(
                    participant_id=p_id,
                    baseline_heart_rate=hr,
                    baseline_skin_response=skin,
                    baseline_temperature=temp,
                    name=name,
                )
                participants[p_id] = participant

    except (PermissionError, FileNotFoundError):
        raise
    except csv.Error as e:
        raise InvalidRecordError(f"CSV error while reading {path.name}: {e}")

    return participants


def load_sessions_csv(session_filepaths, participants_dict):
    """Load session CSV files, validate each row, and group by session_id.

    Records every rejected row with source file, row number, field, and reason.
    Returns:
        (sessions_dict, rejected_records_list, stats_summary)
    """
    if isinstance(session_filepaths, (str, Path)):
        session_filepaths = [session_filepaths]

    sessions = {}
    rejected_records = []
    total_rows = 0
    accepted_rows = 0

    # Measurement acceptable ranges (ordinary comparisons, not regex)
    RANGE_RULES = {
        "heart_rate": (35, 205, "Heart rate"),
        "skin_response": (0.0, 50.0, "Skin response"),
        "temperature": (25.0, 42.0, "Temperature"),
        "activity_level": (0.0, 1.0, "Activity level"),
        "signal_quality": (0.0, 1.0, "Signal quality"),
    }

    for file_item in session_filepaths:
        path = Path(file_item)
        if not path.is_file():
            print(f"Warning: Session file not found: {path}")
            continue

        try:
            validate_csv_filename(str(path))
        except ValueError as e:
            print(f"Warning: Skipping non-csv file {path}: {e}")
            continue

        try:
            with open(path, mode="r", encoding="utf-8", newline="") as f:
                reader = csv.reader(f)
                header = next(reader, None)
                if not header:
                    continue

                for row_idx, row in enumerate(reader, start=2):
                    if not row or not any(c.strip() for c in row):
                        continue

                    total_rows += 1
                    clean_row = [c.strip() for c in row]

                    # 1. Detect unexpected row length
                    if len(clean_row) != 8:
                        rejected_records.append({
                            "source_file": path.name,
                            "row_number": row_idx,
                            "field": "row_length",
                            "raw_value": f"{len(clean_row)} columns",
                            "reason": f"Expected 8 columns, found {len(clean_row)}",
                        })
                        continue

                    (
                        sess_id,
                        part_id,
                        t_str,
                        hr_str,
                        skin_str,
                        temp_str,
                        act_str,
                        sig_str,
                    ) = clean_row

                    # 2. Check for missing required fields
                    missing_field = None
                    for col_name, val in [
                        ("session_id", sess_id),
                        ("participant_id", part_id),
                        ("timestamp", t_str),
                        ("heart_rate", hr_str),
                        ("skin_response", skin_str),
                        ("temperature", temp_str),
                        ("activity_level", act_str),
                        ("signal_quality", sig_str),
                    ]:
                        if val == "":
                            missing_field = col_name
                            break

                    if missing_field:
                        rejected_records.append({
                            "source_file": path.name,
                            "row_number": row_idx,
                            "field": missing_field,
                            "raw_value": "EMPTY",
                            "reason": f"Missing required field '{missing_field}'",
                        })
                        continue

                    # 3. Validate Session ID format with regex
                    try:
                        validate_session_id(sess_id)
                    except InvalidIdentifierError as e:
                        rejected_records.append({
                            "source_file": path.name,
                            "row_number": row_idx,
                            "field": "session_id",
                            "raw_value": sess_id,
                            "reason": str(e),
                        })
                        continue

                    # 4. Validate Participant ID format with regex
                    try:
                        validate_participant_id(part_id)
                    except InvalidIdentifierError as e:
                        rejected_records.append({
                            "source_file": path.name,
                            "row_number": row_idx,
                            "field": "participant_id",
                            "raw_value": part_id,
                            "reason": str(e),
                        })
                        continue

                    # 5. Check if participant exists in profiles
                    if part_id not in participants_dict:
                        rejected_records.append({
                            "source_file": path.name,
                            "row_number": row_idx,
                            "field": "participant_id",
                            "raw_value": part_id,
                            "reason": f"Unknown participant identifier '{part_id}' not found in profiles",
                        })
                        continue

                    # 6. Type conversions with targeted try/except ValueError
                    try:
                        timestamp = int(t_str)
                    except ValueError:
                        rejected_records.append({
                            "source_file": path.name,
                            "row_number": row_idx,
                            "field": "timestamp",
                            "raw_value": t_str,
                            "reason": f"Cannot convert timestamp '{t_str}' to integer",
                        })
                        continue

                    try:
                        heart_rate = int(hr_str)
                    except ValueError:
                        rejected_records.append({
                            "source_file": path.name,
                            "row_number": row_idx,
                            "field": "heart_rate",
                            "raw_value": hr_str,
                            "reason": f"Cannot convert heart_rate '{hr_str}' to integer",
                        })
                        continue

                    try:
                        skin_response = float(skin_str)
                    except ValueError:
                        rejected_records.append({
                            "source_file": path.name,
                            "row_number": row_idx,
                            "field": "skin_response",
                            "raw_value": skin_str,
                            "reason": f"Cannot convert skin_response '{skin_str}' to float",
                        })
                        continue

                    try:
                        temperature = float(temp_str)
                    except ValueError:
                        rejected_records.append({
                            "source_file": path.name,
                            "row_number": row_idx,
                            "field": "temperature",
                            "raw_value": temp_str,
                            "reason": f"Cannot convert temperature '{temp_str}' to float",
                        })
                        continue

                    try:
                        activity_level = float(act_str)
                    except ValueError:
                        rejected_records.append({
                            "source_file": path.name,
                            "row_number": row_idx,
                            "field": "activity_level",
                            "raw_value": act_str,
                            "reason": f"Cannot convert activity_level '{act_str}' to float",
                        })
                        continue

                    try:
                        signal_quality = float(sig_str)
                    except ValueError:
                        rejected_records.append({
                            "source_file": path.name,
                            "row_number": row_idx,
                            "field": "signal_quality",
                            "raw_value": sig_str,
                            "reason": f"Cannot convert signal_quality '{sig_str}' to float",
                        })
                        continue

                    # 7. Check for impossible / out-of-range measurements
                    range_violation = None
                    measurements = [
                        ("heart_rate", heart_rate, RANGE_RULES["heart_rate"]),
                        ("skin_response", skin_response, RANGE_RULES["skin_response"]),
                        ("temperature", temperature, RANGE_RULES["temperature"]),
                        ("activity_level", activity_level, RANGE_RULES["activity_level"]),
                        ("signal_quality", signal_quality, RANGE_RULES["signal_quality"]),
                    ]

                    for f_name, f_val, (low, high, label) in measurements:
                        err = validate_numeric_range(f_val, low, high, label)
                        if err:
                            range_violation = (f_name, f_val, err)
                            break

                    if range_violation:
                        f_name, f_val, err_msg = range_violation
                        rejected_records.append({
                            "source_file": path.name,
                            "row_number": row_idx,
                            "field": f_name,
                            "raw_value": str(f_val),
                            "reason": err_msg,
                        })
                        continue

                    # Record is valid! Create Observation
                    observation = Observation(
                        timestamp=timestamp,
                        heart_rate=heart_rate,
                        skin_response=skin_response,
                        temperature=temperature,
                        activity_level=activity_level,
                        signal_quality=signal_quality,
                        session_id=sess_id,
                        participant_id=part_id,
                    )

                    # Group by session_id and connect to participant
                    if sess_id not in sessions:
                        participant = participants_dict[part_id]
                        sessions[sess_id] = FitnessSession(
                            participant=participant,
                            session_id=sess_id,
                        )

                    sessions[sess_id].add_observation(observation)
                    accepted_rows += 1

        except (PermissionError, FileNotFoundError) as e:
            print(f"Error accessing file {path}: {e}")
        except csv.Error as e:
            print(f"CSV format error in {path}: {e}")

    stats_summary = {
        "total_rows": total_rows,
        "accepted_rows": accepted_rows,
        "rejected_rows": len(rejected_records),
    }

    return sessions, rejected_records, stats_summary


def save_reports(sessions, rejected_records, output_dir):
    """Write analysis_summary.csv, analysis_report.txt, and rejected_records.txt.

    Creates the output directory if it does not already exist.
    Returns list of created file paths.
    """
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    summary_csv_path = out_path / "analysis_summary.csv"
    report_txt_path = out_path / "analysis_report.txt"
    rejected_txt_path = out_path / "rejected_records.txt"

    created_files = []

    # 1. Write analysis_summary.csv (one row per processed session)
    try:
        with open(summary_csv_path, mode="w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                "session_id",
                "participant_id",
                "participant_name",
                "classification",
                "valid_observations",
                "total_observations",
                "usable_percentage",
                "avg_heart_rate",
                "hr_difference_from_baseline",
                "avg_temperature",
                "avg_activity_level",
            ])

            for sess_id in sorted(sessions.keys()):
                sess = sessions[sess_id]
                cls_label, _ = sess.classify()
                summaries = sess.calculate_summaries()
                hr_mean = summaries["heart_rate"]["mean"]
                temp_mean = summaries["temperature"]["mean"]
                act_mean = summaries["activity_level"]["mean"]
                hr_diff = summaries["baseline_deviations"]["hr_difference"]

                writer.writerow([
                    sess.session_id,
                    sess.participant.participant_id,
                    sess.participant.name,
                    cls_label,
                    summaries["valid_observations"],
                    summaries["total_observations"],
                    f"{summaries['usable_percentage']}%",
                    hr_mean if hr_mean is not None else "N/A",
                    f"{hr_diff:+.1f}" if hr_diff is not None else "N/A",
                    temp_mean if temp_mean is not None else "N/A",
                    act_mean if act_mean is not None else "N/A",
                ])

        created_files.append(summary_csv_path)
    except (PermissionError, OSError) as e:
        print(f"Error writing {summary_csv_path}: {e}")

    # 2. Write analysis_report.txt (human-readable report for each session)
    try:
        with open(report_txt_path, mode="w", encoding="utf-8") as f:
            f.write("SMART FITNESS SESSION ANALYZER - COMPLETE ANALYSIS REPORT\n")
            f.write("=" * 72 + "\n\n")

            if not sessions:
                f.write("No sessions were successfully processed.\n")
            else:
                for sess_id in sorted(sessions.keys()):
                    sess = sessions[sess_id]
                    f.write(sess.generate_report())
                    f.write("\n\n")

        created_files.append(report_txt_path)
    except (PermissionError, OSError) as e:
        print(f"Error writing {report_txt_path}: {e}")

    # 3. Write rejected_records.txt (detailed log of rejected CSV rows)
    try:
        with open(rejected_txt_path, mode="w", encoding="utf-8") as f:
            f.write("REJECTED CSV RECORDS LOG\n")
            f.write("=" * 88 + "\n")
            f.write(
                f"{'Source File':<28} | {'Row':<5} | {'Field':<16} | {'Value':<12} | {'Reason'}\n"
            )
            f.write("-" * 88 + "\n")

            if not rejected_records:
                f.write("No rows were rejected.\n")
            else:
                for rec in rejected_records:
                    f.write(
                        f"{rec['source_file']:<28} | "
                        f"{rec['row_number']:<5} | "
                        f"{rec['field']:<16} | "
                        f"{str(rec['raw_value'])[:12]:<12} | "
                        f"{rec['reason']}\n"
                    )

            f.write("=" * 88 + "\n")
            f.write(f"Total rejected rows: {len(rejected_records)}\n")

        created_files.append(rejected_txt_path)
    except (PermissionError, OSError) as e:
        print(f"Error writing {rejected_txt_path}: {e}")

    return created_files
