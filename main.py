"""Main script to run and test the fitness session analyzer.

Runs the five scenarios required by the assignment:
1. Resting session
2. Moderate activity
3. High activity
4. Recovery session
5. Corrupted sensor data (poor quality)

Prints console reports and structured dictionary output for each session.
"""

import json
from models import Participant, FitnessSession, AdvancedFitnessSession
from sample_data import get_all_test_scenarios


def process_scenario(scenario_info, use_advanced_model=False):
    """Create objects, validate data, and print report for a scenario."""
    profile_data = scenario_info["profile"]
    observations_raw = scenario_info["observations"]
    title = scenario_info["title"]

    # Create participant object
    participant = Participant(
        participant_id=profile_data["participant_id"],
        baseline_heart_rate=profile_data["baseline_heart_rate"],
        baseline_skin_response=profile_data["baseline_skin_response"],
        baseline_temperature=profile_data["baseline_temperature"],
    )

    # Create session (using AdvancedFitnessSession for recovery to show inheritance)
    if use_advanced_model:
        session = AdvancedFitnessSession(participant=participant, session_name=title)
    else:
        session = FitnessSession(participant=participant, session_name=title)

    # Ingest raw observation dictionaries
    session.add_raw_observations(observations_raw)

    # Print the console report
    report_text = session.generate_report()
    print(report_text)
    print()

    # Return the dictionary format
    return session.to_dict()


def main():
    print("\n" + "=" * 76)
    print(" SMART FITNESS SESSION ANALYZER - ASSIGNMENT 1 ".center(76))
    print("=" * 76 + "\n")

    scenarios = get_all_test_scenarios()
    session_results = []

    for idx, scenario_info in enumerate(scenarios, 1):
        print(f"\n--- Running Scenario {idx}/{len(scenarios)}: {scenario_info['title']} ---")

        # Use AdvancedFitnessSession for the recovery scenario
        use_advanced = (scenario_info["scenario"] == "recovery")
        result_dict = process_scenario(scenario_info, use_advanced_model=use_advanced)
        session_results.append(result_dict)

    # Print a quick comparison table at the end
    print("\n" + "=" * 76)
    print(" OVERALL SCENARIOS SUMMARY")
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

    # Print a sample structured dictionary output
    print("\n--- Sample Structured Dictionary Output (Scenario 1 JSON snippet) ---")
    sample_snippet = {
        "session_name": session_results[0]["session_name"],
        "participant_id": session_results[0]["participant"]["participant_id"],
        "classification": session_results[0]["classification"],
        "explanation": session_results[0]["explanation"],
        "heart_rate_summary": session_results[0]["summaries"]["heart_rate"],
        "usable_percentage": session_results[0]["summaries"]["usable_percentage"],
    }
    print(json.dumps(sample_snippet, indent=2))
    print("\nAll scenarios processed successfully.\n")


if __name__ == "__main__":
    main()
