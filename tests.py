"""Unit tests for the Smart Fitness Session Analyzer.

Covers the required OOP concepts and the five mandatory scenarios:
- Encapsulation in Participant
- Data validation and classmethod in Observation
- Composition in FitnessSession
- Inheritance and method overriding in AdvancedFitnessSession
- Five scenarios: resting, moderate activity, high activity, recovery, and poor quality
"""

import unittest
from models import Participant, Observation, FitnessSession, AdvancedFitnessSession
from sample_data import load_scenario_dataset


class TestFitnessAnalyzer(unittest.TestCase):
    """Test suite covering the required OOP features and the five scenarios."""

    # 1. Test Encapsulation in Participant
    def test_participant_encapsulation(self):
        p = Participant("P001", baseline_heart_rate=70, baseline_skin_response=1.5, baseline_temperature=32.5)
        self.assertEqual(p.baseline_heart_rate, 70)
        # Check that invalid resting heart rate raises ValueError
        with self.assertRaises(ValueError):
            p.baseline_heart_rate = 20

    # 2. Test Observation validation and from_dict classmethod
    def test_observation_validation(self):
        # Valid observation
        good_raw = {
            "timestamp": 0,
            "heart_rate": 80,
            "skin_response": 1.5,
            "temperature": 33.0,
            "activity_level": 0.2,
            "signal_quality": 0.95,
        }
        good_obs = Observation.from_dict(good_raw)
        self.assertTrue(good_obs.is_valid)

        # Corrupted observation: missing heart rate and poor signal quality
        bad_raw = {
            "timestamp": 1,
            "heart_rate": None,
            "skin_response": 1.5,
            "temperature": 33.0,
            "activity_level": 0.2,
            "signal_quality": 0.30,
        }
        bad_obs = Observation.from_dict(bad_raw)
        self.assertFalse(bad_obs.is_valid)
        self.assertGreater(len(bad_obs.rejection_reasons), 0)

    # 3. Test FitnessSession composition and summary calculation
    def test_session_composition_and_summary(self):
        p = Participant("P001", 70, 1.5, 32.5)
        session = FitnessSession(p, "Test Session")
        session.add_observation(Observation(0, 80, 1.5, 32.5, 0.2, 0.95))
        session.add_observation(Observation(1, 90, 1.5, 32.5, 0.3, 0.95))

        self.assertEqual(len(session.observations), 2)
        summary = session.calculate_summaries()
        self.assertEqual(summary["heart_rate"]["mean"], 85.0)

    # 4. Test AdvancedFitnessSession inheritance and method overriding
    def test_inheritance_and_overriding(self):
        p = Participant("P001", 60, 1.5, 32.5)
        adv_session = AdvancedFitnessSession(p, "Advanced Cardio")
        for _ in range(6):
            adv_session.add_observation(Observation(0, 90, 1.8, 33.0, 0.45, 0.95))

        summaries = adv_session.calculate_summaries()
        self.assertIn("cardiovascular_strain", summaries)
        self.assertIsNotNone(summaries["cardiovascular_strain"]["hr_reserve_utilization_pct"])

    # 5. Scenario 1: Resting session
    def test_scenario_resting(self):
        prof, obs = load_scenario_dataset("resting", seed=101)
        p = Participant(prof["participant_id"], prof["baseline_heart_rate"], prof["baseline_skin_response"], prof["baseline_temperature"])
        session = FitnessSession(p, "Resting")
        session.add_raw_observations(obs)
        cls_name, _ = session.classify()
        self.assertEqual(cls_name, "resting")

    # 6. Scenario 2: Moderate activity
    def test_scenario_moderate_activity(self):
        prof, obs = load_scenario_dataset("moderate_activity", seed=202)
        p = Participant(prof["participant_id"], prof["baseline_heart_rate"], prof["baseline_skin_response"], prof["baseline_temperature"])
        session = FitnessSession(p, "Moderate")
        session.add_raw_observations(obs)
        cls_name, _ = session.classify()
        self.assertEqual(cls_name, "moderate activity")

    # 7. Scenario 3: High activity
    def test_scenario_high_activity(self):
        prof, obs = load_scenario_dataset("high_activity", seed=303)
        p = Participant(prof["participant_id"], prof["baseline_heart_rate"], prof["baseline_skin_response"], prof["baseline_temperature"])
        session = FitnessSession(p, "High")
        session.add_raw_observations(obs)
        cls_name, _ = session.classify()
        self.assertEqual(cls_name, "high activity")

    # 8. Scenario 4: Activity followed by recovery
    def test_scenario_recovery(self):
        prof, obs = load_scenario_dataset("recovery", seed=404, number_of_windows=14)
        p = Participant(prof["participant_id"], prof["baseline_heart_rate"], prof["baseline_skin_response"], prof["baseline_temperature"])
        session = FitnessSession(p, "Recovery")
        session.add_raw_observations(obs)
        cls_name, _ = session.classify()
        self.assertEqual(cls_name, "recovering")

    # 9. Scenario 5: Poor-quality or invalid sensor data
    def test_scenario_poor_quality(self):
        prof, obs = load_scenario_dataset("poor_quality", seed=505)
        p = Participant(prof["participant_id"], prof["baseline_heart_rate"], prof["baseline_skin_response"], prof["baseline_temperature"])
        session = FitnessSession(p, "Poor Quality")
        session.add_raw_observations(obs)
        cls_name, _ = session.classify()
        self.assertEqual(cls_name, "insufficient data")


if __name__ == "__main__":
    unittest.main()
