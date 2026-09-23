"""Unit tests for the Smart Fitness Session Analyzer.

Tests:
- Participant class and property validation (encapsulation)
- Observation class, from_dict classmethod, and validation checks
- FitnessSession composition, statistics, and reports
- AdvancedFitnessSession inheritance and method overriding
- Standalone helper functions in calculations.py
- The 5 scenarios: resting, moderate, high, recovery, poor quality
"""

import unittest
from models import Participant, Observation, FitnessSession, AdvancedFitnessSession
from calculations import (
    calculate_summary_statistics,
    detect_recovery_trend,
    calculate_baseline_deviations,
    format_console_table,
    validate_raw_observation_dict,
)
from sample_data import load_scenario_dataset


class TestParticipant(unittest.TestCase):
    """Test Participant model, focusing on encapsulation and property setters."""

    def setUp(self):
        self.p = Participant("P001", baseline_heart_rate=70, baseline_skin_response=1.5, baseline_temperature=32.5)

    def test_valid_initialization(self):
        self.assertEqual(self.p.participant_id, "P001")
        self.assertEqual(self.p.baseline_heart_rate, 70)
        self.assertEqual(self.p.baseline_skin_response, 1.5)
        self.assertEqual(self.p.baseline_temperature, 32.5)

    def test_baseline_heart_rate_setter_valid(self):
        self.p.baseline_heart_rate = 60
        self.assertEqual(self.p.baseline_heart_rate, 60)

    def test_baseline_heart_rate_setter_invalid_range(self):
        # Human resting heart rates below 35 or above 110 should be rejected
        with self.assertRaises(ValueError):
            self.p.baseline_heart_rate = 20
        with self.assertRaises(ValueError):
            self.p.baseline_heart_rate = 140

    def test_baseline_heart_rate_setter_invalid_type(self):
        with self.assertRaises(TypeError):
            self.p.baseline_heart_rate = "seventy"

    def test_baseline_skin_response_negative(self):
        with self.assertRaises(ValueError):
            self.p.baseline_skin_response = -0.5

    def test_baseline_temperature_out_of_bounds(self):
        with self.assertRaises(ValueError):
            self.p.baseline_temperature = 41.0
        with self.assertRaises(ValueError):
            self.p.baseline_temperature = 25.0

    def test_to_dict(self):
        d = self.p.to_dict()
        self.assertEqual(d["participant_id"], "P001")
        self.assertEqual(d["baseline_heart_rate"], 70)


class TestObservation(unittest.TestCase):
    """Test Observation model, factory class method, static helper, and validation rules."""

    def test_from_dict_factory(self):
        raw = {
            "timestamp": 1,
            "heart_rate": 95,
            "skin_response": 2.1,
            "temperature": 33.2,
            "activity_level": 0.5,
            "signal_quality": 0.95,
        }
        obs = Observation.from_dict(raw)
        self.assertTrue(obs.is_valid)
        self.assertEqual(len(obs.rejection_reasons), 0)
        self.assertEqual(obs.heart_rate, 95)

    def test_static_validate_metric_range(self):
        self.assertIsNone(Observation.validate_metric_range(100, 35, 205, "heart_rate"))
        self.assertIsNotNone(Observation.validate_metric_range(250, 35, 205, "heart_rate"))
        self.assertIsNotNone(Observation.validate_metric_range(None, 35, 205, "heart_rate"))

    def test_rejection_low_signal_quality(self):
        obs = Observation(
            timestamp=0,
            heart_rate=80,
            skin_response=1.5,
            temperature=33.0,
            activity_level=0.1,
            signal_quality=0.45,  # below 0.60
        )
        self.assertFalse(obs.is_valid)
        self.assertTrue(any("reliability threshold" in r for r in obs.rejection_reasons))

    def test_rejection_impossible_heart_rate(self):
        obs = Observation(
            timestamp=1,
            heart_rate=265,  # above 205
            skin_response=1.5,
            temperature=33.0,
            activity_level=0.5,
            signal_quality=0.90,
        )
        self.assertFalse(obs.is_valid)
        self.assertTrue(any("heart_rate" in r for r in obs.rejection_reasons))

    def test_rejection_negative_activity_level(self):
        obs = Observation(
            timestamp=2,
            heart_rate=75,
            skin_response=1.5,
            temperature=33.0,
            activity_level=-0.20,  # negative
            signal_quality=0.90,
        )
        self.assertFalse(obs.is_valid)
        self.assertTrue(any("activity_level" in r for r in obs.rejection_reasons))

    def test_rejection_missing_values(self):
        obs = Observation(
            timestamp=3,
            heart_rate=None,  # missing
            skin_response=None,  # missing
            temperature=33.0,
            activity_level=0.2,
            signal_quality=0.90,
        )
        self.assertFalse(obs.is_valid)
        self.assertGreaterEqual(len(obs.rejection_reasons), 2)


class TestFitnessSession(unittest.TestCase):
    """Test FitnessSession composition, observation filtering, summaries, and reports."""

    def setUp(self):
        self.participant = Participant("P001", 70, 1.5, 32.5)
        self.session = FitnessSession(self.participant, "Test Session")

    def test_composition(self):
        # Session has-a Participant
        self.assertEqual(self.session.participant.participant_id, "P001")
        # Session has observations
        obs = Observation(0, 75, 1.5, 32.5, 0.1, 0.95)
        self.session.add_observation(obs)
        self.assertEqual(len(self.session.observations), 1)

    def test_filtering_valid_and_rejected(self):
        good = Observation(0, 75, 1.5, 32.5, 0.1, 0.95)
        bad = Observation(1, 260, 1.5, 32.5, 0.1, 0.95)
        self.session.add_observation(good)
        self.session.add_observation(bad)

        self.assertEqual(len(self.session.get_valid_observations()), 1)
        self.assertEqual(len(self.session.get_rejected_observations()), 1)

    def test_summaries_calculation(self):
        for hr in [70, 80, 90]:
            self.session.add_observation(Observation(0, hr, 1.5, 33.0, 0.2, 0.95))

        summaries = self.session.calculate_summaries()
        self.assertEqual(summaries["valid_observations"], 3)
        self.assertEqual(summaries["heart_rate"]["mean"], 80.0)
        self.assertEqual(summaries["heart_rate"]["min"], 70.0)
        self.assertEqual(summaries["heart_rate"]["max"], 90.0)
        self.assertEqual(summaries["baseline_deviations"]["hr_difference"], 10.0)

    def test_to_dict_structure(self):
        self.session.add_observation(Observation(0, 75, 1.5, 32.5, 0.1, 0.95))
        d = self.session.to_dict()
        self.assertIn("session_name", d)
        self.assertIn("participant", d)
        self.assertIn("classification", d)
        self.assertIn("summaries", d)
        self.assertIn("observation_counts", d)

    def test_generate_report_string(self):
        self.session.add_observation(Observation(0, 75, 1.5, 32.5, 0.1, 0.95))
        report = self.session.generate_report()
        self.assertIn("FITNESS SESSION REPORT", report)
        self.assertIn("P001", report)


class TestAdvancedFitnessSession(unittest.TestCase):
    """Test inheritance and method overriding in AdvancedFitnessSession."""

    def test_inheritance_and_overriding(self):
        p = Participant("P001", 60, 1.5, 32.5)
        adv_session = AdvancedFitnessSession(p, "Cardio Lab")

        # Confirm inheritance
        self.assertIsInstance(adv_session, FitnessSession)

        # Add observations with moderate intensity (HR 90 vs baseline 60 -> +30 bpm delta)
        for _ in range(8):
            adv_session.add_observation(Observation(0, 90, 1.8, 33.0, 0.45, 0.95))

        # Check overridden calculate_summaries
        summaries = adv_session.calculate_summaries()
        self.assertIn("cardiovascular_strain", summaries)
        self.assertIsNotNone(summaries["cardiovascular_strain"]["hr_reserve_utilization_pct"])

        # Check overridden classify
        cls_name, reason = adv_session.classify()
        self.assertEqual(cls_name, "moderate activity")
        self.assertIn("Advanced Metric:", reason)

        # Check overridden to_dict
        d = adv_session.to_dict()
        self.assertEqual(d.get("session_type"), "AdvancedFitnessSession")


class TestStandaloneFunctions(unittest.TestCase):
    """Test standalone functions in calculations.py."""

    def test_calculate_summary_statistics_empty(self):
        stats = calculate_summary_statistics([])
        self.assertIsNone(stats["mean"])
        self.assertIsNone(stats["min"])
        self.assertIsNone(stats["max"])
        self.assertEqual(stats["count"], 0)

    def test_calculate_summary_statistics_values(self):
        stats = calculate_summary_statistics([10, 20, 30])
        self.assertEqual(stats["mean"], 20.0)
        self.assertEqual(stats["min"], 10.0)
        self.assertEqual(stats["max"], 30.0)
        self.assertEqual(stats["count"], 3)

    def test_detect_recovery_trend_true(self):
        # Simulate downward sloping HR (140 -> 70) and activity (0.8 -> 0.1)
        obs_list = [
            Observation(0, 140, 2.0, 33.0, 0.85, 0.95),
            Observation(1, 135, 2.0, 33.0, 0.80, 0.95),
            Observation(2, 110, 1.8, 33.0, 0.50, 0.95),
            Observation(3, 90, 1.6, 33.0, 0.30, 0.95),
            Observation(4, 75, 1.5, 33.0, 0.15, 0.95),
            Observation(5, 70, 1.5, 33.0, 0.10, 0.95),
        ]
        is_rec, msg = detect_recovery_trend(obs_list)
        self.assertTrue(is_rec)
        self.assertIn("Clear recovery pattern", msg)

    def test_detect_recovery_trend_false(self):
        # Flat session
        obs_list = [
            Observation(i, 80, 1.5, 33.0, 0.2, 0.95) for i in range(6)
        ]
        is_rec, msg = detect_recovery_trend(obs_list)
        self.assertFalse(is_rec)

    def test_calculate_baseline_deviations(self):
        devs = calculate_baseline_deviations(80.0, 33.0, 70.0, 32.0)
        self.assertEqual(devs["hr_difference"], 10.0)
        self.assertAlmostEqual(devs["hr_percent_change"], 14.3, places=1)
        self.assertEqual(devs["temp_difference"], 1.0)

    def test_format_console_table(self):
        headers = ["Col A", "Col B"]
        rows = [["1", "Apple"], ["2", "Banana"]]
        tbl = format_console_table(headers, rows)
        self.assertIn("Col A", tbl)
        self.assertIn("Banana", tbl)

    def test_validate_raw_observation_dict(self):
        valid_dict = {
            "timestamp": 0,
            "heart_rate": 70,
            "skin_response": 1.0,
            "temperature": 32.0,
            "activity_level": 0.1,
            "signal_quality": 0.9,
        }
        self.assertEqual(len(validate_raw_observation_dict(valid_dict)), 0)

        missing_dict = {"timestamp": 0}
        errs = validate_raw_observation_dict(missing_dict)
        self.assertGreater(len(errs), 0)


class TestFiveScenarios(unittest.TestCase):
    """Test the five required business scenarios using simulated generator data."""

    def _build_and_classify_session(self, scenario_name: str, seed: int = 42, windows: int = 12):
        prof_data, obs_data = load_scenario_dataset(scenario_name, seed=seed, number_of_windows=windows)
        p = Participant(
            prof_data["participant_id"],
            prof_data["baseline_heart_rate"],
            prof_data["baseline_skin_response"],
            prof_data["baseline_temperature"],
        )
        session = FitnessSession(p, scenario_name)
        session.add_raw_observations(obs_data)
        classification, reason = session.classify()
        return session, classification, reason

    def test_resting_scenario(self):
        _, classification, _ = self._build_and_classify_session("resting", seed=101)
        self.assertEqual(classification, "resting")

    def test_moderate_activity_scenario(self):
        _, classification, _ = self._build_and_classify_session("moderate_activity", seed=202)
        self.assertEqual(classification, "moderate activity")

    def test_high_activity_scenario(self):
        _, classification, _ = self._build_and_classify_session("high_activity", seed=303)
        self.assertEqual(classification, "high activity")

    def test_recovery_scenario(self):
        _, classification, _ = self._build_and_classify_session("recovery", seed=404, windows=14)
        self.assertEqual(classification, "recovering")

    def test_poor_quality_scenario(self):
        session, classification, _ = self._build_and_classify_session("poor_quality", seed=505)
        self.assertEqual(classification, "insufficient data")
        # Ensure corrupted observations were flagged and rejected
        rejected = session.get_rejected_observations()
        self.assertEqual(len(rejected), 12)


if __name__ == "__main__":
    unittest.main()
