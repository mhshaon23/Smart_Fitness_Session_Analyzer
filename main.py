"""Main application entry point for the Smart Fitness Session Analyzer.

Processes five distinct simulated exercise sessions:
1. Resting session
2. Moderate activity
3. High activity
4. Recovery session
5. Corrupted / poor-quality sensor data

For each session, this script:
- Instantiates Participant and Session objects (composition).
- Ingests and validates all observation windows.
- Calculates summary statistics and baseline comparisons.
- Classifies session intensity with clear explanations.
- Prints human-readable console reports and displays structured dictionary results.
"""

import json
from models import Participant, FitnessSession, AdvancedFitnessSession
from sample_data import get_all_test_scenarios


def process_scenario(scenario_info: dict, use_advanced_model: bool = False) -> dict:
    """Run full ingestion, validation, analysis, and reporting for a single scenario."""
    profile_data = scenario_info["profile"]
    observations_raw = scenario_info["observations"]
    title = scenario_info["title"]

    # 1. Create domain Participant object (demonstrating encapsulation)
    participant = Participant(
        participant_id=profile_data["participant_id"],
        baseline_heart_rate=profile_data["baseline_heart_rate"],
        baseline_skin_response=profile_data["baseline_skin_response"],
        baseline_temperature=profile_data["baseline_temperature"],
    )

    # 2. Instantiate Session object (demonstrating composition and inheritance)
    if use_advanced_model:
        session = AdvancedFitnessSession(participant=participant, session_name=title)
    else:
        session = FitnessSession(participant=participant, session_name=title)

    # 3. Ingest observations (factory class method & validation logic)
    session.add_raw_observations(observations_raw)

    # 4. Generate and display the human-readable console report
    report_text = session.generate_report()
    print(report_text)
    print()

    # 5. Extract structured dictionary representation
    structured_result = session.to_dict()
    return structured_result


def main():
    print("\n" + "#" * 76)
    print("#" + " SMART FITNESS SESSION ANALYZER - DEMONSTRATION ".center(74) + "#")
    print("#" + " ACT4420: Object-Oriented Analysis Systems ".center(74) + "#")
    print("#" * 76 + "\n")

    scenarios = get_all_test_scenarios()
    session_results = []

    for idx, scenario_info in enumerate(scenarios, 1):
        print(f"\n>>> Running Scenario {idx} of {len(scenarios)}: {scenario_info['title']} <<<")

        # Demonstrate AdvancedFitnessSession (subclass with method overriding) on scenario 4 (recovery)
        use_advanced = (scenario_info["scenario"] == "recovery")
        result_dict = process_scenario(scenario_info, use_advanced_model=use_advanced)
        session_results.append(result_dict)

    # Summary table comparing all 5 scenarios
    print("\n" + "=" * 76)
    print(" ALL SCENARIOS COMPARISON SUMMARY")
    print("=" * 76)
    header = f"{'Scenario Name':<32} | {'Usable Obs':<10} | {'Classification':<18} | {'HR vs Base'}"
    print(header)
    print("-" * 76)
    for res in session_results:
        s_name = res["session_name"][:30]
        usable = f"{res['observation_counts']['valid']}/{res['observation_counts']['total']}"
        cls_label = res["classification"]
        diff = res["summaries"]["baseline_deviations"]["hr_difference"]
        diff_str = f"{diff:+.1f} bpm" if diff is not None else "N/A"
        print(f"{s_name:<32} | {usable:<10} | {cls_label:<18} | {diff_str}")
    print("=" * 76)

    # Sample structured dictionary output demonstration
    print("\n>>> Sample Structured Dictionary Output (Scenario 1 JSON snippet): <<<")
    sample_snippet = {
        "session_name": session_results[0]["session_name"],
        "participant_id": session_results[0]["participant"]["participant_id"],
        "classification": session_results[0]["classification"],
        "explanation": session_results[0]["explanation"],
        "heart_rate_summary": session_results[0]["summaries"]["heart_rate"],
        "usable_percentage": session_results[0]["summaries"]["usable_percentage"],
    }
    print(json.dumps(sample_snippet, indent=2))
    print("\nDemonstration completed successfully.\n")


if __name__ == "__main__":
    main()

