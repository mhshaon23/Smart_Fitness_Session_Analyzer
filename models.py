"""Domain classes for the fitness session analyzer.

Includes:
- Participant: Stores user info and baseline values (encapsulation).
- Observation: Stores single sensor readings and validates them (classmethod & staticmethod).
- FitnessSession: Manages observations for a participant (composition).
- AdvancedFitnessSession: Subclass adding cardiovascular strain metrics (inheritance & overriding).
"""

from calculations import (
    calculate_summary_statistics,
    detect_recovery_trend,
    calculate_baseline_deviations,
    format_console_table,
)


class Participant:
    """Represents a gym participant and their personal baseline resting values."""

    def __init__(self, participant_id, baseline_heart_rate, baseline_skin_response, baseline_temperature):
        if not isinstance(participant_id, str) or not participant_id.strip():
            raise ValueError("participant_id must be a non-empty string")

        self.participant_id = participant_id.strip()

        # Set up private variables for encapsulation
        self._baseline_heart_rate = 0
        self._baseline_skin_response = 0.0
        self._baseline_temperature = 0.0

        # Use properties to validate inputs on creation
        self.baseline_heart_rate = baseline_heart_rate
        self.baseline_skin_response = baseline_skin_response
        self.baseline_temperature = baseline_temperature

    # --- Property and setter for baseline heart rate (Encapsulation) ---
    @property
    def baseline_heart_rate(self):
        return self._baseline_heart_rate

    @baseline_heart_rate.setter
    def baseline_heart_rate(self, value):
        if not isinstance(value, (int, float)):
            raise TypeError("Baseline heart rate must be a numeric value")
        # Check against normal resting heart rate limits
        if value < 35 or value > 110:
            raise ValueError(
                f"Resting baseline heart rate {value} bpm is outside plausible human resting limits (35-110 bpm)"
            )
        self._baseline_heart_rate = int(round(value))

    # --- Property and setter for baseline skin response ---
    @property
    def baseline_skin_response(self):
        return self._baseline_skin_response

    @baseline_skin_response.setter
    def baseline_skin_response(self, value):
        if not isinstance(value, (int, float)):
            raise TypeError("Baseline skin response must be numeric")
        if value < 0.0:
            raise ValueError("Baseline skin response cannot be negative")
        self._baseline_skin_response = round(float(value), 2)

    # --- Property and setter for baseline temperature ---
    @property
    def baseline_temperature(self):
        return self._baseline_temperature

    @baseline_temperature.setter
    def baseline_temperature(self, value):
        if not isinstance(value, (int, float)):
            raise TypeError("Baseline temperature must be numeric")
        if value < 28.0 or value > 38.0:
            raise ValueError(
                f"Baseline temperature {value} deg C is outside plausible skin temperature range (28-38 deg C)"
            )
        self._baseline_temperature = round(float(value), 2)

    def to_dict(self):
        """Return participant details as a dictionary."""
        return {
            "participant_id": self.participant_id,
            "baseline_heart_rate": self.baseline_heart_rate,
            "baseline_skin_response": self.baseline_skin_response,
            "baseline_temperature": self.baseline_temperature,
        }

    def __repr__(self):
        return (
            f"Participant(id='{self.participant_id}', baseline_hr={self.baseline_heart_rate}, "
            f"baseline_skin={self.baseline_skin_response}, baseline_temp={self.baseline_temperature})"
        )


class Observation:
    """Represents a single sensor reading window from the wearable device."""

    # Sensor ranges and minimum signal quality threshold
    MIN_SIGNAL_QUALITY = 0.60
    MIN_HR, MAX_HR = 35, 205
    MIN_TEMP, MAX_TEMP = 25.0, 42.0
    MIN_ACTIVITY, MAX_ACTIVITY = 0.0, 1.0

    def __init__(self, timestamp, heart_rate, skin_response, temperature, activity_level, signal_quality):
        self.timestamp = timestamp
        self.heart_rate = heart_rate
        self.skin_response = skin_response
        self.temperature = temperature
        self.activity_level = activity_level
        self.signal_quality = signal_quality

        self.rejection_reasons = []
        self._validate()

    @classmethod
    def from_dict(cls, data):
        """Class method to create an Observation directly from a raw dictionary."""
        return cls(
            timestamp=data.get("timestamp", 0),
            heart_rate=data.get("heart_rate"),
            skin_response=data.get("skin_response"),
            temperature=data.get("temperature"),
            activity_level=data.get("activity_level"),
            signal_quality=data.get("signal_quality"),
        )

    @staticmethod
    def validate_metric_range(value, lower_bound, upper_bound, metric_name):
        """Static method to check if a numeric reading falls within acceptable bounds."""
        if value is None:
            return f"Missing value for {metric_name}"
        if not isinstance(value, (int, float)):
            return f"Invalid non-numeric type for {metric_name}"
        if value < lower_bound or value > upper_bound:
            return (
                f"{metric_name} value {value} is out of allowable range [{lower_bound}, {upper_bound}]"
            )
        return None

    def _validate(self):
        """Check for missing or impossible values, and weak signal quality."""
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
            self.rejection_reasons.append("Skin response must be >= 0")

        # 4. Temperature check
        temp_err = self.validate_metric_range(self.temperature, self.MIN_TEMP, self.MAX_TEMP, "temperature")
        if temp_err:
            self.rejection_reasons.append(temp_err)

        # 5. Activity level check
        act_err = self.validate_metric_range(self.activity_level, self.MIN_ACTIVITY, self.MAX_ACTIVITY, "activity_level")
        if act_err:
            self.rejection_reasons.append(act_err)

    @property
    def is_valid(self):
        """True if there were no rejection reasons."""
        return len(self.rejection_reasons) == 0

    def to_dict(self):
        """Convert observation to dictionary."""
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

    def __repr__(self):
        status = "VALID" if self.is_valid else f"INVALID ({len(self.rejection_reasons)} issues)"
        return f"Observation(t={self.timestamp}, hr={self.heart_rate}, act={self.activity_level}, status={status})"


class FitnessSession:
    """Represents a workout session for a participant.

    Demonstrates composition: A FitnessSession has a Participant and a list of Observations.
    """

    # We need at least 5 valid observations and 50% usable data
    MIN_USABLE_OBSERVATIONS = 5
    MIN_USABLE_RATIO = 0.50

    def __init__(self, participant, session_name="Training Session"):
        if not isinstance(participant, Participant):
            raise TypeError("participant must be an instance of Participant")
        self.participant = participant
        self.session_name = session_name
        self.observations = []

    def add_observation(self, observation):
        """Add one Observation object to the session."""
        if not isinstance(observation, Observation):
            raise TypeError("observation must be an instance of Observation")
        self.observations.append(observation)

    def add_raw_observations(self, raw_data_list):
        """Convert a list of raw dictionaries into Observation objects and add them."""
        for item in raw_data_list:
            self.add_observation(Observation.from_dict(item))

    def get_valid_observations(self):
        """Return list of usable observations."""
        return [obs for obs in self.observations if obs.is_valid]

    def get_rejected_observations(self):
        """Return list of rejected observations."""
        return [obs for obs in self.observations if not obs.is_valid]

    def calculate_summaries(self):
        """Calculate averages, minimums, maximums, and baseline comparison."""
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

    def classify(self):
        """Classify session intensity based on baseline deviations and activity."""
        valid_obs = self.get_valid_observations()
        total_count = len(self.observations)
        valid_count = len(valid_obs)

        # 1. Check if we have enough usable data
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

        # 3. Analyze steady-state workout intensity
        summaries = self.calculate_summaries()
        avg_hr = summaries["heart_rate"]["mean"]
        avg_act = summaries["activity_level"]["mean"]
        hr_diff = summaries["baseline_deviations"]["hr_difference"]

        # Resting: minimal elevation above baseline and low movement
        if hr_diff <= 10.0 and avg_act < 0.25:
            reason = (
                f"Average heart rate was {avg_hr} bpm ({hr_diff:+.1f} bpm from baseline) "
                f"with minimal activity ({avg_act:.2f}), consistent with rest."
            )
            return "resting", reason

        # High Activity: high heart rate increase or high activity level
        if hr_diff >= 45.0 or avg_act >= 0.65:
            reason = (
                f"Average heart rate was {avg_hr} bpm ({hr_diff:+.1f} bpm from baseline) "
                f"with elevated activity ({avg_act:.2f}), indicating high exertion."
            )
            return "high activity", reason

        # Moderate Activity: between resting and high activity
        reason = (
            f"Average heart rate was {avg_hr} bpm ({hr_diff:+.1f} bpm from baseline) "
            f"and activity averaged {avg_act:.2f}, indicating moderate workout intensity."
        )
        return "moderate activity", reason

    def to_dict(self):
        """Return structured results as a dictionary."""
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

    def generate_report(self):
        """Generate a readable text report of the session."""
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
            for obs in rejected[:5]:  # show first 5
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

    Extends FitnessSession to calculate extra cardiovascular reserve metrics.
    """

    def __init__(self, participant, session_name="Advanced Session"):
        super().__init__(participant, session_name)
        # Using 195 bpm as a standard max heart rate ceiling for training load
        self.estimated_max_hr = 195

    def calculate_summaries(self):
        """Override calculate_summaries to add cardiovascular strain percentage."""
        summaries = super().calculate_summaries()

        if summaries["valid_observations"] > 0 and summaries["heart_rate"]["mean"] is not None:
            avg_hr = summaries["heart_rate"]["mean"]
            base_hr = self.participant.baseline_heart_rate

            # Calculate heart rate reserve utilization
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

    def classify(self):
        """Override classify to add cardiovascular reserve info to the explanation."""
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

    def to_dict(self):
        """Override to_dict to add the session type."""
        result = super().to_dict()
        result["session_type"] = "AdvancedFitnessSession"
        return result
