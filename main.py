"""Command-line entry point for the Smart Fitness Session Analyzer.

Usage:
    python main.py
    python main.py --profiles option_a_fitness/participants.csv \
                   --sessions option_a_fitness/fitness_sessions.csv option_a_fitness/fitness_sessions_invalid.csv \
                   --output output

Loads participant profiles and session telemetry from CSV files,
validates rows, classifies each session, and writes reports to the output folder.
"""

import sys
import argparse
from pathlib import Path

from fitness_analyzer.data_loader import (
    load_participants_csv,
    load_sessions_csv,
    save_reports,
)
from fitness_analyzer.exceptions import InvalidIdentifierError, InvalidRecordError


def parse_arguments():
    """Parse command line arguments with sensible defaults."""
    parser = argparse.ArgumentParser(
        description="Smart Fitness Session Analyzer - File-based telemetry analysis."
    )
    parser.add_argument(
        "--profiles",
        type=str,
        default="option_a_fitness/participants.csv",
        help="Path to participant profiles CSV file (default: option_a_fitness/participants.csv)",
    )
    parser.add_argument(
        "--sessions",
        nargs="+",
        default=[
            "option_a_fitness/fitness_sessions.csv",
            "option_a_fitness/fitness_sessions_invalid.csv",
        ],
        help="One or more session CSV files to analyze",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="output",
        help="Output directory for generated reports (default: output)",
    )
    return parser.parse_args()


def main():
    args = parse_arguments()

    print("\n" + "=" * 76)
    print(" SMART FITNESS SESSION ANALYZER - ASSIGNMENT II ".center(76))
    print("=" * 76)
    print(f"Profiles file   : {args.profiles}")
    print(f"Sessions files  : {', '.join(args.sessions)}")
    print(f"Output folder   : {args.output}")
    print("-" * 76)

    # 1. Load Participant Profiles (targeted try/except for file and format errors)
    try:
        participants = load_participants_csv(args.profiles)
        print(f"Loaded {len(participants)} participant profile(s) successfully.")
    except FileNotFoundError as e:
        print(f"Error: Profiles file not found: {e}")
        sys.exit(1)
    except PermissionError as e:
        print(f"Error: Permission denied accessing profiles file: {e}")
        sys.exit(1)
    except (InvalidIdentifierError, InvalidRecordError) as e:
        print(f"Error in profiles file data format: {e}")
        sys.exit(1)

    # 2. Load and Validate Session Records
    sessions, rejected_records, stats = load_sessions_csv(args.sessions, participants)

    # 3. Save Reports to Output Directory
    created_files = save_reports(sessions, rejected_records, args.output)

    # 4. Print Completion Summary (Required by Section 7)
    print("\n" + "=" * 76)
    print(" COMPLETION SUMMARY ".center(76))
    print("=" * 76)
    print(f"Total rows examined      : {stats['total_rows']}")
    print(f"Accepted rows            : {stats['accepted_rows']}")
    print(f"Rejected rows quarantined: {stats['rejected_rows']}")
    print(f"Processed workout sessions: {len(sessions)}")
    print("-" * 76)

    print(f"{'Session ID':<14} | {'Participant':<16} | {'Classification':<18} | {'Usable Obs'}")
    print("-" * 76)
    for s_id in sorted(sessions.keys()):
        sess = sessions[s_id]
        cls_label, _ = sess.classify()
        valid_cnt = len(sess.get_valid_observations())
        total_cnt = len(sess.observations)
        print(
            f"{s_id:<14} | {sess.participant.name[:15]:<16} | {cls_label:<18} | {valid_cnt}/{total_cnt}"
        )
    print("-" * 76)

    print("Created report files:")
    for file_path in created_files:
        print(f"  - {file_path}")
    print("=" * 76 + "\n")


if __name__ == "__main__":
    main()
