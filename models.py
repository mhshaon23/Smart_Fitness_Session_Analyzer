"""Domain classes for the Smart Fitness Session Analyzer.

This module defines the core object-oriented architecture:
- Participant: Encapsulates user profile data and resting baseline values.
- Observation: Models single sensor windows, parsing dictionaries and validating data.
- FitnessSession: Coordinates observations for a participant (demonstrating composition).
- AdvancedFitnessSession: Extends FitnessSession with cardiovascular strain analytics (inheritance & overriding).
"""

from typing import List, Dict, Any, Tuple, Optional
from calculations import (
    calculate_summary_statistics,
    detect_recovery_trend,
    calculate_baseline_deviations,
    format_console_table,
)


class Participant:
    """Represents a gym participant and their personal physiological reference baselines.

    Demonstrates encapsulation by managing resting heart rate, skin response,
    and body temperature through protected attributes with property getters and setters
    that enforce biological sanity checks.
    """

    def __init__(
        self,
        participant_id: str,
        baseline_heart_rate: int,
        baseline_skin_response: float,
        baseline_temperature: float,
    ) -> None:
        if not isinstance(participant_id, str) or not participant_id.strip():
            raise ValueError("participant_id must be a non-empty string")

        self.participant_id = participant_id.strip()

        # Initialize via properties to ensure validation rules run on initialization
        self._baseline_heart_rate: int = 0
        self._baseline_skin_response: float = 0.0
        self._baseline_temperature: float = 0.0

        self.baseline_heart_rate = baseline_heart_rate
        self.baseline_skin_response = baseline_skin_response
        self.baseline_temperature = baseline_temperature

    # --- Encapsulation: Baseline Heart Rate ---
    @property
    def baseline_heart_rate(self) -> int:
        """Personal resting heart rate baseline in beats per minute."""
        return self._baseline_heart_rate

    @baseline_heart_rate.setter
    def baseline_heart_rate(self, value: int) -> None:
        if not isinstance(value, (int, float)):
            raise TypeError("Baseline heart rate must be a numeric value")
        if value < 35 or value > 110:
            raise ValueError(
                f"Resting baseline heart rate {value} bpm is outside plausible human resting limits (35-110 bpm)"
            )
        self._baseline_heart_rate = int(round(value))

    # --- Encapsulation: Baseline Skin Response ---
    @property
    def baseline_skin_response(self) -> float:
        """Personal reference skin response in simulated conductance units."""
        return self._baseline_skin_response

    @baseline_skin_response.setter
    def baseline_skin_response(self, value: float) -> None:
        if not isinstance(value, (int, float)):
            raise TypeError("Baseline skin response must be numeric")
        if value < 0.0:
            raise ValueError("Baseline skin response cannot be negative")
        self._baseline_skin_response = round(float(value), 2)

    # --- Encapsulation: Baseline Skin Temperature ---
    @property
    def baseline_temperature(self) -> float:
        """Personal reference skin temperature in degrees Celsius."""
        return self._baseline_temperature

    @baseline_temperature.setter
    def baseline_temperature(self, value: float) -> None:
        if not isinstance(value, (int, float)):
            raise TypeError("Baseline temperature must be numeric")
        if value < 28.0 or value > 38.0:
            raise ValueError(
                f"Baseline temperature {value} deg C is outside plausible skin temperature range (28-38 deg C)"
            )
        self._baseline_temperature = round(float(value), 2)

    def to_dict(self) -> Dict[str, Any]:
        """Convert participant profile into a standard dictionary format."""
        return {
            "participant_id": self.participant_id,
            "baseline_heart_rate": self.baseline_heart_rate,
            "baseline_skin_response": self.baseline_skin_response,
            "baseline_temperature": self.baseline_temperature,
        }

    def __repr__(self) -> str:
        return (
            f"Participant(id='{self.participant_id}', baseline_hr={self.baseline_heart_rate}, "
            f"baseline_skin={self.baseline_skin_response}, baseline_temp={self.baseline_temperature})"
        )


class Observation:
    """Represents a single time window reading captured from a wearable device.

    Validates physiological bounds and sensor quality, recording reasons for rejection
    if the observation cannot be trusted.
    """

    # Quality and physiological boundary constants
    MIN_SIGNAL_QUALITY = 0.60
    MIN_HR, MAX_HR = 35, 205
    MIN_TEMP, MAX_TEMP = 25.0, 42.0
    MIN_ACTIVITY, MAX_ACTIVITY = 0.0, 1.0

    def __init__(
        self,
        timestamp: int,
        heart_rate: Optional[int],
        skin_response: Optional[float],
        temperature: Optional[float],
        activity_level: Optional[float],
        signal_quality: Optional[float],
    ) -> None:
        self.timestamp = timestamp
        self.heart_rate = heart_rate
        self.skin_response = skin_response
        self.temperature = temperature
        self.activity_level = activity_level
        self.signal_quality = signal_quality

        self.rejection_reasons: List[str] = []
        self._validate()

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Observation":
        """Factory class method to create an Observation directly from a raw dictionary.

        Safely parses expected fields, handling potential type casts or missing keys.
        """
        return cls(
            timestamp=data.get("timestamp", 0),
            heart_rate=data.get("heart_rate"),
            skin_response=data.get("skin_response"),
            temperature=data.get("temperature"),
            activity_level=data.get("activity_level"),
            signal_quality=data.get("signal_quality"),
        )

    @staticmethod
    def validate_metric_range(
        value: Optional[float | int],
        lower_bound: float,
        upper_bound: float,
        metric_name: str,
    ) -> Optional[str]:
        """Static helper to verify if a numeric metric falls within an expected range.

        Returns an error description string if out of bounds or None, else None.
        """
        if value is None:
            return f"Missing value for {metric_name}"
        if not isinstance(value, (int, float)):
            return f"Invalid non-numeric type for {metric_name}"
        if value < lower_bound or value > upper_bound:
            return (
                f"{metric_name} value {value} is out of allowable range [{lower_bound}, {upper_bound}]"
            )
        return None

    def _validate(self) -> None:
        """Run all data hygiene checks and populate rejection reasons."""
        # 1. Signal quality check
        if self.signal_quality is None:
            self.rejection_reasons.append("Missing signal_quality")
        elif not isinstance(self.signal_quality, (int, float)):
            self.rejection_reasons.append("Non-numeric signal_quality")
        elif self.signal_quality < self.MIN_SIGNAL_QUALITY:
            self.rejection_reasons.append(
                f"Signal quality {self.signal_quality:.2f} is below reliability threshold ({self.MIN_SIGNAL_QUALITY:.2f})"
            )

        # 2. Heart rate check
        hr_err = self.validate_metric_range(self.heart_rate, self.MIN_HR, self.MAX_HR, "heart_rate")
        if hr_err:
            self.rejection_reasons.append(hr_err)

        # 3. Skin response check
        if self.skin_response is None:
            self.rejection_reasons.append("Missing value for skin_response")
        elif not isinstance(self.skin_response, (int, float)) or self.skin_response < 0:
            self.rejection_reasons.append(f"Skin response {self.skin_response} must be >= 0")

        # 4. Temperature check
        temp_err = self.validate_metric_range(self.temperature, self.MIN_TEMP, self.MAX_TEMP, "temperature")
        if temp_err:
            self.rejection_reasons.append(temp_err)

        # 5. Activity level check
        act_err = self.validate_metric_range(self.activity_level, self.MIN_ACTIVITY, self.MAX_ACTIVITY, "activity_level")
        if act_err:
            self.rejection_reasons.append(act_err)

    @property
    def is_valid(self) -> bool:
        """Indicates whether the observation passed all data quality and validity checks."""
        return len(self.rejection_reasons) == 0

    def to_dict(self) -> Dict[str, Any]:
        """Serialize observation state into a dictionary."""
        return {
            "timestamp": self.timestamp,
            "heart_rate": self.heart_rate,
            "skin_response": self.skin_response,
            "temperature": self.temperature,
            "activity_level": self.activity_level,
            "signal_quality": self.signal_quality,
            "is_valid": self.is_valid,
            "rejection_reasons": list(self.rejection_reasons),
        }

    def __repr__(self) -> str:
        status = "VALID" if self.is_valid else f"INVALID ({len(self.rejection_reasons)} issues)"
        return f"Observation(t={self.timestamp}, hr={self.heart_rate}, act={self.activity_level}, status={status})"


class FitnessSession:
    """Represents a complete workout/recording session for a specific participant.

    Demonstrates composition: A FitnessSession 'has-a' Participant instance and
    'has-many' Observation instances.
    """

    # Minimum valid observations needed to reliably classify a workout session
    MIN_USABLE_OBSERVATIONS = 5
    MIN_USABLE_RATIO = 0.50

    def __init__(self, participant: Participant, session_name: str = "Training Session") -> None:
        if not isinstance(participant, Participant):
            raise TypeError("participant must be an instance of Participant")
        self.participant: Participant = participant
        self.session_name: str = session_name
        self.observations: List[Observation] = []

    def add_observation(self, observation: Observation) -> None:
        """Add a single Observation object to this session."""
        if not isinstance(observation, Observation):
            raise TypeError("observation must be an instance of Observation")
        self.observations.append(observation)

    def add_raw_observations(self, raw_data_list: List[Dict[str, Any]]) -> None:
        """Batch add observations from raw dictionaries using Observation.from_dict."""
        for item in raw_data_list:
            self.add_observation(Observation.from_dict(item))

    def get_valid_observations(self) -> List[Observation]:
        """Return only observations that passed data validation."""
        return [obs for obs in self.observations if obs.is_valid]

    def get_rejected_observations(self) -> List[Observation]:
        """Return observations that failed data validation."""
        return [obs for obs in self.observations if not obs.is_valid]

    def calculate_summaries(self) -> Dict[str, Any]:
        """Calculate statistical summaries and baseline comparisons across valid observations."""
        valid_obs = self.get_valid_observations()
        total_count = len(self.observations)
        valid_count = len(valid_obs)

        if not valid_obs:
            return {
                "total_observations": total_count,
                "valid_observations": 0,
                "rejected_observations": total_count,
                "usable_percentage": 0.0,
                "heart_rate": calculate_summary_statistics([]),
                "activity_level": calculate_summary_statistics([]),
                "temperature": calculate_summary_statistics([]),
                "skin_response": calculate_summary_statistics([]),
                "baseline_deviations": calculate_baseline_deviations(
                    None, None, self.participant.baseline_heart_rate, self.participant.baseline_temperature
                ),
            }

        hr_vals = [obs.heart_rate for obs in valid_obs if obs.heart_rate is not None]
        act_vals = [obs.activity_level for obs in valid_obs if obs.activity_level is not None]
        temp_vals = [obs.temperature for obs in valid_obs if obs.temperature is not None]
        skin_vals = [obs.skin_response for obs in valid_obs if obs.skin_response is not None]

        hr_stats = calculate_summary_statistics(hr_vals)
        act_stats = calculate_summary_statistics(act_vals)
        temp_stats = calculate_summary_statistics(temp_vals)
        skin_stats = calculate_summary_statistics(skin_vals)

        baseline_devs = calculate_baseline_deviations(
            hr_stats["mean"],
            temp_stats["mean"],
            self.participant.baseline_heart_rate,
            self.participant.baseline_temperature,
        )

        usable_pct = round((valid_count / total_count) * 100, 1) if total_count > 0 else 0.0

        return {
            "total_observations": total_count,
            "valid_observations": valid_count,
            "rejected_observations": total_count - valid_count,
            "usable_percentage": usable_pct,
            "heart_rate": hr_stats,
            "activity_level": act_stats,
            "temperature": temp_stats,
            "skin_response": skin_stats,
            "baseline_deviations": baseline_devs,
        }

    def classify(self) -> Tuple[str, str]:
        """Classify session intensity and physiological response.

        Returns:
            (classification_label, explanation_text)
            Possible labels: 'insufficient data', 'recovering', 'resting',
                             'moderate activity', 'high activity'
        """
        valid_obs = self.get_valid_observations()
        total_count = len(self.observations)
        valid_count = len(valid_obs)

        # 1. Check data sufficiency
        if (
            valid_count < self.MIN_USABLE_OBSERVATIONS
            or (total_count > 0 and (valid_count / total_count) < self.MIN_USABLE_RATIO)
        ):
            reason = (
                f"Only {valid_count}/{total_count} observations are valid "
                f"(minimum {self.MIN_USABLE_OBSERVATIONS} and {int(self.MIN_USABLE_RATIO * 100)}% required). "
                f"Data quality is insufficient for analysis."
            )
            return "insufficient data", reason

        # 2. Check for recovery trend
        is_recovering, recovery_msg = detect_recovery_trend(valid_obs)
        if is_recovering:
            return "recovering", recovery_msg

        # 3. Analyze steady-state intensity
        summaries = self.calculate_summaries()
        avg_hr = summaries["heart_rate"]["mean"]
        avg_act = summaries["activity_level"]["mean"]
        hr_diff = summaries["baseline_deviations"]["hr_difference"]

        # Resting: minimal elevation above personal baseline and very low movement
        if hr_diff <= 10.0 and avg_act < 0.25:
            reason = (
                f"Average heart rate was {avg_hr} bpm ({hr_diff:+.1f} bpm from baseline) "
                f"with minimal activity ({avg_act:.2f}), consistent with rest."
            )
            return "resting", reason

        # High Activity: elevated heart rate and sustained vigorous movement
        if hr_diff >= 45.0 or avg_act >= 0.65:
            reason = (
                f"Average heart rate was {avg_hr} bpm ({hr_diff:+.1f} bpm from baseline) "
                f"with elevated activity ({avg_act:.2f}), indicating high exertion."
            )
            return "high activity", reason

        # Moderate Activity: intermediate heart rate rise and moderate movement
        reason = (
            f"Average heart rate was {avg_hr} bpm ({hr_diff:+.1f} bpm from baseline) "
            f"and activity averaged {avg_act:.2f}, indicating moderate workout intensity."
        )
        return "moderate activity", reason

    def to_dict(self) -> Dict[str, Any]:
        """Produce the required structured dictionary representation of the session results."""
        classification, explanation = self.classify()
        summaries = self.calculate_summaries()

        return {
            "session_name": self.session_name,
            "participant": self.participant.to_dict(),
            "classification": classification,
            "explanation": explanation,
            "summaries": summaries,
            "observation_counts": {
                "total": len(self.observations),
                "valid": summaries["valid_observations"],
                "rejected": summaries["rejected_observations"],
            },
        }

    def generate_report(self) -> str:
        """Generate a readable, well-formatted console report describing the session."""
        classification, explanation = self.classify()
        summaries = self.calculate_summaries()

        lines = []
        lines.append("=" * 72)
        lines.append(f" FITNESS SESSION REPORT: {self.session_name.upper()}")
        lines.append("=" * 72)
        lines.append(f"Participant ID       : {self.participant.participant_id}")
        lines.append(
            f"Personal Baselines   : HR {self.participant.baseline_heart_rate} bpm | "
            f"Temp {self.participant.baseline_temperature} deg C | "
            f"Skin {self.participant.baseline_skin_response}"
        )
        lines.append("-" * 72)
        lines.append(f"SESSION CLASSIFICATION: {classification.upper()}")
        lines.append(f"Reason: {explanation}")
        lines.append("-" * 72)
        lines.append(
            f"Observations Overview: {summaries['valid_observations']} usable out of "
            f"{summaries['total_observations']} total ({summaries['usable_percentage']}% valid)"
        )

        if summaries["valid_observations"] > 0:
            hr_stats = summaries["heart_rate"]
            act_stats = summaries["activity_level"]
            temp_stats = summaries["temperature"]
            devs = summaries["baseline_deviations"]

            table_headers = ["Metric", "Mean", "Min", "Max", "vs Baseline"]
            table_rows = [
                [
                    "Heart Rate (bpm)",
                    str(hr_stats["mean"]),
                    str(hr_stats["min"]),
                    str(hr_stats["max"]),
                    f"{devs['hr_difference']:+.1f} bpm ({devs['hr_percent_change']:+.1f}%)",
                ],
                [
                    "Activity (0-1)",
                    str(act_stats["mean"]),
                    str(act_stats["min"]),
                    str(act_stats["max"]),
                    "N/A",
                ],
                [
                    "Temperature (deg C)",
                    str(temp_stats["mean"]),
                    str(temp_stats["min"]),
                    str(temp_stats["max"]),
                    f"{devs['temp_difference']:+.2f} deg C",
                ],
            ]
            lines.append("\nSummary Statistics (Usable Data Only):")
            lines.append(format_console_table(table_headers, table_rows))

        rejected = self.get_rejected_observations()
        if rejected:
            lines.append(f"\nRejected Sensor Observations ({len(rejected)} flagged):")
            rej_headers = ["Timestamp", "Heart Rate", "Activity", "Signal Qual", "Rejection Reasons"]
            rej_rows = []
            for obs in rejected[:5]:  # show first 5 for clarity
                rej_rows.append([
                    str(obs.timestamp),
                    str(obs.heart_rate),
                    str(obs.activity_level),
                    str(obs.signal_quality),
                    "; ".join(obs.rejection_reasons),
                ])
            lines.append(format_console_table(rej_headers, rej_rows))
            if len(rejected) > 5:
                lines.append(f"... and {len(rejected) - 5} more rejected observations.")

        lines.append("=" * 72)
        return "\n".join(lines)


class AdvancedFitnessSession(FitnessSession):
    """Subclass of FitnessSession demonstrating Inheritance and Method Overriding.

    Extends basic session classification and summaries by calculating cardiovascular
    strain indices and estimating training stress.
    """

    def __init__(self, participant: Participant, session_name: str = "Advanced Session") -> None:
        super().__init__(participant, session_name)
        # Assumed standard estimation formula for maximal heart rate (220 - estimated age)
        # Using 195 bpm as a standard reference ceiling for training load calculations
        self.estimated_max_hr: int = 195

    def calculate_summaries(self) -> Dict[str, Any]:
        """Override calculate_summaries to append cardiovascular reserve metrics."""
        # Call base class method
        summaries = super().calculate_summaries()

        if summaries["valid_observations"] > 0 and summaries["heart_rate"]["mean"] is not None:
            avg_hr = summaries["heart_rate"]["mean"]
            base_hr = self.participant.baseline_heart_rate

            # Heart Rate Reserve (Karvonen method): (HR_avg - HR_rest) / (HR_max - HR_rest)
            hr_reserve = max(1, self.estimated_max_hr - base_hr)
            strain_ratio = max(0.0, min(1.0, (avg_hr - base_hr) / hr_reserve))

            summaries["cardiovascular_strain"] = {
                "estimated_max_hr": self.estimated_max_hr,
                "hr_reserve_utilization_pct": round(strain_ratio * 100, 1),
            }
        else:
            summaries["cardiovascular_strain"] = {
                "estimated_max_hr": self.estimated_max_hr,
                "hr_reserve_utilization_pct": None,
            }

        return summaries

    def classify(self) -> Tuple[str, str]:
        """Override classify to enrich base classification with cardiovascular load context."""
        base_class, base_reason = super().classify()

        if base_class == "insufficient data":
            return base_class, base_reason

        summaries = self.calculate_summaries()
        strain_info = summaries.get("cardiovascular_strain", {})
        utilization = strain_info.get("hr_reserve_utilization_pct")

        if utilization is not None:
            enriched_reason = (
                f"{base_reason} [Advanced Metric: utilized {utilization}% of cardiovascular reserve]"
            )
            return base_class, enriched_reason

        return base_class, base_reason

    def to_dict(self) -> Dict[str, Any]:
        """Override to_dict to include the session type and cardiovascular strain metrics."""
        result = super().to_dict()
        result["session_type"] = "AdvancedFitnessSession"
        return result
