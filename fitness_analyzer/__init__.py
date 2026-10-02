"""Smart Fitness Session Analyzer Package.

Provides modules for:
- models: Participant, Observation, FitnessSession, AdvancedFitnessSession
- exceptions: InvalidIdentifierError, InvalidRecordError
- validators: Regular expression and range validation
- calculations: Summary statistics and recovery analysis
- data_loader: CSV file parsing and record tracking
"""

from fitness_analyzer.exceptions import InvalidIdentifierError, InvalidRecordError
from fitness_analyzer.models import Participant, Observation, FitnessSession, AdvancedFitnessSession
from fitness_analyzer.validators import (
    validate_participant_id,
    validate_session_id,
    validate_csv_filename,
)
from fitness_analyzer.calculations import (
    calculate_summary_statistics,
    detect_recovery_trend,
    calculate_baseline_deviations,
)
from fitness_analyzer.data_loader import (
    load_participants_csv,
    load_sessions_csv,
    save_reports,
)

__all__ = [
    "InvalidIdentifierError",
    "InvalidRecordError",
    "Participant",
    "Observation",
    "FitnessSession",
    "AdvancedFitnessSession",
    "validate_participant_id",
    "validate_session_id",
    "validate_csv_filename",
    "calculate_summary_statistics",
    "detect_recovery_trend",
    "calculate_baseline_deviations",
    "load_participants_csv",
    "load_sessions_csv",
    "save_reports",
]
