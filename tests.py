"""Unit test suite for Assignment II.

Covers:
- Regex validation for participant ID, session ID, and filenames
- Custom exceptions (InvalidIdentifierError, InvalidRecordError) raised and handled
- Missing-file error handling (FileNotFoundError)
- Valid CSV ingestion (participants.csv, fitness_sessions.csv)
- Invalid CSV record rejection and quarantining (fitness_sessions_invalid.csv)
- Boundary cases (acceptable boundary limits, empty files, unexpected row lengths)
- Output files creation in output directory
"""

import unittest
from pathlib import Path
import tempfile
import csv

from fitness_analyzer.exceptions import InvalidIdentifierError, InvalidRecordError
from fitness_analyzer.validators import (
    validate_participant_id,
    validate_session_id,
    validate_csv_filename,
    validate_numeric_range,
)
from fitness_analyzer.models import Participant, Observation, FitnessSession
from fitness_analyzer.data_loader import (
    load_participants_csv,
    load_sessions_csv,
    save_reports,
)


class TestValidatorsAndRegex(unittest.TestCase):
    """Test regular expression validation per Section 4.2."""

    def test_valid_participant_id(self):
        self.assertEqual(validate_participant_id("P001"), "P001")
        self.assertEqual(validate_participant_id("P999"), "P999")

    def test_invalid_participant_id(self):
        # Missing 'P', wrong length, or letters in number part
        with self.assertRaises(InvalidIdentifierError):
            validate_participant_id("001")
        with self.assertRaises(InvalidIdentifierError):
            validate_participant_id("P01")
        with self.assertRaises(InvalidIdentifierError):
            validate_participant_id("P1234")
        with self.assertRaises(InvalidIdentifierError):
            validate_participant_id("X001")

    def test_valid_session_id(self):
        self.assertEqual(validate_session_id("FIT-2026-001"), "FIT-2026-001")
        self.assertEqual(validate_session_id("FIT-2025-999"), "FIT-2025-999")

    def test_invalid_session_id(self):
        # 2-digit year, wrong prefix, or missing digits
        with self.assertRaises(InvalidIdentifierError):
            validate_session_id("FIT-26-102")
        with self.assertRaises(InvalidIdentifierError):
            validate_session_id("SES-2026-001")
        with self.assertRaises(InvalidIdentifierError):
            validate_session_id("FIT-2026-1")

    def test_validate_csv_filename(self):
        self.assertEqual(validate_csv_filename("data.csv"), "data.csv")
        self.assertEqual(validate_csv_filename("path/to/sessions.CSV"), "path/to/sessions.CSV")
        with self.assertRaises(ValueError):
            validate_csv_filename("data.txt")


class TestCustomExceptions(unittest.TestCase):
    """Test that custom exceptions are properly raised and handled per Section 4.4."""

    def test_invalid_identifier_error_is_value_error(self):
        self.assertTrue(issubclass(InvalidIdentifierError, ValueError))

    def test_invalid_record_error_is_value_error(self):
        self.assertTrue(issubclass(InvalidRecordError, ValueError))

    def test_raising_and_catching_exceptions(self):
        # Catch InvalidIdentifierError
        caught_id_err = False
        try:
            validate_participant_id("BAD_ID")
        except InvalidIdentifierError:
            caught_id_err = True
        self.assertTrue(caught_id_err)

        # Catch InvalidRecordError
        caught_rec_err = False
        try:
            raise InvalidRecordError("Corrupted record format")
        except InvalidRecordError:
            caught_rec_err = True
        self.assertTrue(caught_rec_err)


class TestCSVDataLoader(unittest.TestCase):
    """Test reading official CSV files, error handling, and record validation."""

    def setUp(self):
        self.profiles_path = "option_a_fitness/participants.csv"
        self.valid_sessions_path = "option_a_fitness/fitness_sessions.csv"
        self.invalid_sessions_path = "option_a_fitness/fitness_sessions_invalid.csv"

    def test_load_participants_valid(self):
        participants = load_participants_csv(self.profiles_path)
        self.assertEqual(len(participants), 3)
        self.assertIn("P001", participants)
        self.assertEqual(participants["P001"].name, "Amina Noor")
        self.assertEqual(participants["P001"].baseline_heart_rate, 68)

    def test_missing_file_raises_file_not_found_error(self):
        with self.assertRaises(FileNotFoundError):
            load_participants_csv("non_existent_profiles.csv")

    def test_load_valid_sessions(self):
        participants = load_participants_csv(self.profiles_path)
        sessions, rejected, stats = load_sessions_csv(self.valid_sessions_path, participants)

        # fitness_sessions.csv has 5 sessions: FIT-2026-001 through FIT-2026-005
        self.assertEqual(len(sessions), 5)
        self.assertEqual(len(rejected), 0)
        self.assertEqual(stats["accepted_rows"], 29)  # 29 rows in valid CSV

        # Check classifications
        self.assertEqual(sessions["FIT-2026-001"].classify()[0], "resting")
        self.assertEqual(sessions["FIT-2026-002"].classify()[0], "moderate activity")
        self.assertEqual(sessions["FIT-2026-003"].classify()[0], "high activity")
        self.assertEqual(sessions["FIT-2026-004"].classify()[0], "recovering")
        self.assertEqual(sessions["FIT-2026-005"].classify()[0], "insufficient data")

    def test_load_invalid_sessions_quarantines_rows(self):
        participants = load_participants_csv(self.profiles_path)
        sessions, rejected, stats = load_sessions_csv(self.invalid_sessions_path, participants)

        # fitness_sessions_invalid.csv has 11 data rows: 1 valid, 10 rejected
        self.assertEqual(len(rejected), 10)
        self.assertEqual(stats["accepted_rows"], 1)

        # Check that specific failure reasons are captured
        fields_with_errors = {r["field"] for r in rejected}
        self.assertIn("heart_rate", fields_with_errors)
        self.assertIn("participant_id", fields_with_errors)
        self.assertIn("activity_level", fields_with_errors)
        self.assertIn("session_id", fields_with_errors)
        self.assertIn("row_length", fields_with_errors)


class TestBoundaryAndEdgeCases(unittest.TestCase):
    """Test boundary numerical limits and unexpected file formats."""

    def test_heart_rate_boundary_limits(self):
        # 35 and 205 are valid physiological limits
        self.assertIsNone(validate_numeric_range(35, 35, 205, "heart_rate"))
        self.assertIsNone(validate_numeric_range(205, 35, 205, "heart_rate"))
        # 34 and 206 are out of bounds
        self.assertIsNotNone(validate_numeric_range(34, 35, 205, "heart_rate"))
        self.assertIsNotNone(validate_numeric_range(206, 35, 205, "heart_rate"))

    def test_activity_level_boundary_limits(self):
        # 0.0 and 1.0 are valid
        self.assertIsNone(validate_numeric_range(0.0, 0.0, 1.0, "activity_level"))
        self.assertIsNone(validate_numeric_range(1.0, 0.0, 1.0, "activity_level"))
        # negative or above 1.0 are invalid
        self.assertIsNotNone(validate_numeric_range(-0.01, 0.0, 1.0, "activity_level"))
        self.assertIsNotNone(validate_numeric_range(1.01, 0.0, 1.0, "activity_level"))

    def test_empty_csv_file_handling(self):
        with tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False) as f:
            temp_path = f.name

        try:
            with self.assertRaises(InvalidRecordError):
                load_participants_csv(temp_path)
        finally:
            Path(temp_path).unlink(missing_ok=True)


class TestOutputGeneration(unittest.TestCase):
    """Test creating output files in output directory per Section 4.6."""

    def test_save_reports_creates_required_files(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            p = Participant("P001", 70, 1.5, 32.5, name="Test User")
            session = FitnessSession(p, "FIT-2026-001")
            session.add_observation(Observation(0, 75, 1.5, 32.5, 0.1, 0.95))

            sessions = {"FIT-2026-001": session}
            rejected = [
                {
                    "source_file": "test.csv",
                    "row_number": 2,
                    "field": "heart_rate",
                    "raw_value": "bad",
                    "reason": "Cannot convert to int",
                }
            ]

            created = save_reports(sessions, rejected, temp_dir)
            self.assertEqual(len(created), 3)

            # Check that files exist on disk
            out_dir = Path(temp_dir)
            self.assertTrue((out_dir / "analysis_summary.csv").is_file())
            self.assertTrue((out_dir / "analysis_report.txt").is_file())
            self.assertTrue((out_dir / "rejected_records.txt").is_file())


if __name__ == "__main__":
    unittest.main()
