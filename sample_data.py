"""Sample data loader and generator for the Smart Fitness Session Analyzer.

Provides datasets for the five required test scenarios:
- resting session
- moderate activity
- high activity
- activity followed by recovery
- poor-quality or invalid sensor data

Imports and wraps the course generator from option_a_fitness/data_generator.py.
"""

import sys
from pathlib import Path

# Add option_a_fitness to path to import data_generator.py
CURRENT_DIR = Path(__file__).resolve().parent
GENERATOR_DIR = CURRENT_DIR / "option_a_fitness"
if str(GENERATOR_DIR) not in sys.path:
    sys.path.insert(0, str(GENERATOR_DIR))

try:
    from data_generator import generate_fitness_data, available_scenarios
except ImportError:
    raise ImportError(
        "Could not find 'data_generator.py' in 'option_a_fitness' folder. "
        "Make sure the option_a_fitness directory is present in the repository root."
    )


# Predefined configurations for the 5 scenarios with fixed seeds for reproducibility
SCENARIOS_CONFIG = [
    {
        "scenario": "resting",
        "title": "Resting Session",
        "participant_id": "P-REST-01",
        "seed": 101,
        "windows": 12,
    },
    {
        "scenario": "moderate_activity",
        "title": "Moderate Cardio Session",
        "participant_id": "P-MOD-02",
        "seed": 202,
        "windows": 12,
    },
    {
        "scenario": "high_activity",
        "title": "High-Intensity Interval Session",
        "participant_id": "P-HIGH-03",
        "seed": 303,
        "windows": 12,
    },
    {
        "scenario": "recovery",
        "title": "Post-Workout Recovery Session",
        "participant_id": "P-REC-04",
        "seed": 404,
        "windows": 14,
    },
    {
        "scenario": "poor_quality",
        "title": "Sensor Malfunction & Corrupted Data Session",
        "participant_id": "P-CORRUPT-05",
        "seed": 505,
        "windows": 12,
    },
]


def load_scenario_dataset(scenario_name, participant_id="P001", seed=42, number_of_windows=12):
    """Generate raw data dictionaries for a specific scenario using data_generator.py."""
    return generate_fitness_data(
        participant_id=participant_id,
        scenario=scenario_name,
        seed=seed,
        number_of_windows=number_of_windows,
    )


def get_all_test_scenarios():
    """Return all 5 predefined scenario datasets with metadata for demonstration and testing."""
    scenarios_data = []
    for cfg in SCENARIOS_CONFIG:
        profile, observations = load_scenario_dataset(
            scenario_name=cfg["scenario"],
            participant_id=cfg["participant_id"],
            seed=cfg["seed"],
            number_of_windows=cfg["windows"],
        )
        scenarios_data.append({
            "scenario": cfg["scenario"],
            "title": cfg["title"],
            "profile": profile,
            "observations": observations,
        })
    return scenarios_data


if __name__ == "__main__":
    print("Available Generator Scenarios:", available_scenarios())
    print("\nGenerating sample for 'moderate_activity'...")
    prof, obs = load_scenario_dataset("moderate_activity", seed=42)
    print("Participant Profile:", prof)
    print(f"Total Observations Generated: {len(obs)}")
    print("First Observation Sample:", obs[0])
