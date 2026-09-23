# Smart Fitness Session Analyzer
---

## 1. Project Overview

In this individual assignment, I developed an object-oriented Python application to process, validate, and analyze sensor data collected from wearable fitness devices during gym workouts.

In practical fitness monitoring, raw sensor streams are frequently noisy. Wearable devices often drop readings (`None` values), produce sensor errors (such as impossible heart rates like 265 bpm or negative activity levels), or suffer from poor signal quality. My program takes the raw dictionary data for a participant and their session readings, filters out invalid or corrupted observations, calculates summary statistics (mean, min, max), compares measurements against the participant's personal resting baselines, and classifies the workout session into one of five categories:
- `resting`
- `moderate activity`
- `high activity`
- `recovering`
- `insufficient data`

Following the assignment requirements, I built the entire application using only Python's standard library (`typing`, `json`, `math`, `pathlib`, `sys`, and `unittest`) without using third-party libraries like pandas, numpy, or scikit-learn.

---

## 2. Project Structure and Class Design

I organized the codebase into modular Python files to maintain clear separation of responsibilities:

```text
Smart_Fitness_Session_Analyzer/
|-- option_a_fitness/       # Instructor-provided data generator
|   |-- DATA_DESCRIPTION.md
|   |-- data_generator.py
|   `-- example_usage.py
|-- models.py               # Domain classes: Participant, Observation, and Sessions
|-- calculations.py         # Standalone helper functions for math, trend detection, and formatting
|-- sample_data.py          # Data loader interfacing with the scenario generator
|-- main.py                 # Main runner script demonstrating all five scenarios
|-- tests.py                # Unit test suite testing all classes and scenarios (31 tests)
|-- requirements.txt        # Notes that only the Python standard library is used
|-- .gitignore              # Ignores __pycache__ and bytecode files
`-- README.md               # Project documentation
```

### Class Responsibilities

| Class | Location | Purpose |
|---|---|---|
| **`Participant`** | `models.py` | Stores participant profile data and resting baselines (heart rate, skin response, and skin temperature). Uses property getters and setters to protect and validate these values. |
| **`Observation`** | `models.py` | Represents a single sensor reading window. Validates measurement values against acceptable ranges and records specific error reasons if data is invalid. |
| **`FitnessSession`** | `models.py` | Represents a complete workout session. Demonstrates composition by containing a `Participant` object and a list of `Observation` objects. Calculates summaries, handles session classification, and builds reports. |
| **`AdvancedFitnessSession`** | `models.py` | A subclass of `FitnessSession` demonstrating inheritance and method overriding. It adds heart rate reserve calculations to evaluate cardiovascular strain. |

---

## 3. Object-Oriented Programming Requirements

### A. Encapsulation
- **Where:** Inside the `Participant` class in `models.py`.
- **How I implemented it:** Personal resting baselines are stored in private/protected variables (`_baseline_heart_rate`, `_baseline_skin_response`, and `_baseline_temperature`). Access is controlled through `@property` getters and setters. For example, `baseline_heart_rate` validates that the input is a number between 35 and 110 bpm; invalid types raise a `TypeError` and out-of-range values raise a `ValueError`. Skin response is guarded against negative numbers, and skin temperature is restricted to plausible human skin limits (28–38 deg C).

### B. Composition
- **Where:** Inside the `FitnessSession` class in `models.py`.
- **How I implemented it:** A `FitnessSession` has a `Participant` instance (`self.participant`) and maintains a list of `Observation` instances (`self.observations`). The session manages these objects directly, filters valid readings from rejected ones, and computes aggregate statistics across them.

### C. Inheritance and Method Overriding
- **Where:** `AdvancedFitnessSession` inherits from `FitnessSession` in `models.py`.
- **How I implemented it:**
  - `calculate_summaries()`: Calls `super().calculate_summaries()` to obtain the base statistics, then calculates the participant's Heart Rate Reserve utilization percentage using the Karvonen formula.
  - `classify()`: Calls `super().classify()` to get the base category, then appends the heart rate reserve percentage to provide extra context in the explanation.
  - `to_dict()`: Overrides the method to add `"session_type": "AdvancedFitnessSession"` to the returned dictionary.

### D. Class Method and Static Method
- **Class Method:** `Observation.from_dict(cls, data)` in `models.py`. This is an alternative constructor that takes a raw dictionary from the data generator and turns it into a validated `Observation` instance.
- **Static Method:** `Observation.validate_metric_range(value, lower_bound, upper_bound, metric_name)` in `models.py`. A utility helper that checks if a numeric metric falls within expected bounds without needing access to instance state.

---

## 4. Standalone Functions

In `calculations.py`, I created five standalone functions to handle calculations, validation, and presentation:

1. **`calculate_summary_statistics(values)`**  
   Calculates the average, minimum, maximum, and count of a list of numbers. Handles empty lists safely by returning `None` instead of causing a division-by-zero error.
2. **`detect_recovery_trend(observations)`**  
   Splits the session into early and late windows (first third vs. last third). Checks if both heart rate and activity dropped noticeably, confirming whether the participant was cooling down.
3. **`calculate_baseline_deviations(avg_hr, avg_temp, baseline_hr, baseline_temp)`**  
   Calculates the difference and percentage change between session averages and the participant's personal baselines.
4. **`format_console_table(headers, rows)`**  
   A presentation helper that formats data into a clean, aligned ASCII table for terminal display.
5. **`validate_raw_observation_dict(raw)`**  
   A validation helper that checks whether an incoming raw dictionary contains all required keys before parsing.

---

## 5. Assumptions and Classification Rules

### Data Validation Rules
An observation is rejected and marked as invalid if:
- `signal_quality` is below 0.60 or missing (`None`): Sensor readings are unreliable.
- `heart_rate` is missing (`None`) or outside 35–205 bpm.
- `skin_response` is missing (`None`) or negative.
- `temperature` is missing (`None`) or outside 25.0–42.0 deg C.
- `activity_level` is missing (`None`) or outside 0.0–1.0.

### Session Classification Logic
The program classifies a session using the following rules in order:
1. **`insufficient data`**: If there are fewer than 5 valid observations, or if valid observations make up less than 50% of the total session.
2. **`recovering`**: If `detect_recovery_trend()` detects that heart rate dropped by at least 15.0 bpm and activity dropped by at least 0.20 between the start and end of the session.
3. **`resting`**: If average heart rate was within 10.0 bpm of baseline and average activity was under 0.25.
4. **`high activity`**: If average heart rate was 45.0+ bpm above baseline or activity averaged 0.65 or higher.
5. **`moderate activity`**: Any session that falls between resting and high activity levels.

---

## 6. How to Run the Program

### Prerequisites
- Python 3.10 or newer (tested on Python 3.13).
- Uses only Python's built-in standard library.

### Commands

1. **Clone the repository:**
   ```bash
   git clone https://github.com/mhshaon23/Smart_Fitness_Session_Analyzer.git
   cd Smart_Fitness_Session_Analyzer
   ```

2. **Run the main application:**
   ```bash
   # On Windows:
   python main.py

   # On macOS/Linux:
   python3 main.py
   ```

3. **Run the unit tests:**
   ```bash
   # On Windows:
   python -m unittest tests.py -v

   # On macOS/Linux:
   python3 -m unittest tests.py -v
   ```

---

## 7. Example Output

### Console Report (Scenario 2: Moderate Activity)

```text
========================================================================
 FITNESS SESSION REPORT: MODERATE CARDIO SESSION
========================================================================
Participant ID       : P-MOD-02
Personal Baselines   : HR 82 bpm | Temp 32.3 deg C | Skin 1.58
------------------------------------------------------------------------
SESSION CLASSIFICATION: MODERATE ACTIVITY
Reason: Average heart rate was 113.0 bpm (+31.0 bpm from baseline) and activity averaged 0.51, indicating moderate workout intensity.
------------------------------------------------------------------------
Observations Overview: 12 usable out of 12 total (100.0% valid)

Summary Statistics (Usable Data Only):
+---------------------+-------+-------+-------+--------------------+
| Metric              | Mean  | Min   | Max   | vs Baseline        |
+---------------------+-------+-------+-------+--------------------+
| Heart Rate (bpm)    | 113.0 | 107.0 | 122.0 | +31.0 bpm (+37.8%) |
| Activity (0-1)      |  0.51 |  0.41 |  0.63 | N/A                |
| Temperature (deg C) | 32.49 | 32.29 | 32.65 | +0.19 deg C        |
+---------------------+-------+-------+-------+--------------------+
========================================================================
```

### Sensor Rejection Table (Scenario 5: Corrupted Data)

```text
Rejected Sensor Observations (12 flagged):
+-----------+------------+----------+-------------+---------------------------------------------------------------------------------------------------------------------------+
| Timestamp | Heart Rate | Activity | Signal Qual | Rejection Reasons                                                                                                         |
+-----------+------------+----------+-------------+---------------------------------------------------------------------------------------------------------------------------+
|         0 | None       |     0.48 |        0.46 | Signal quality 0.46 is below reliability threshold (0.60); Missing value for heart_rate                                   |
|         1 |        265 |     0.54 |         0.5 | Signal quality 0.50 is below reliability threshold (0.60); heart_rate value 265 is out of allowable range [35, 205]       |
|         2 |         71 |     -0.2 |        0.11 | Signal quality 0.11 is below reliability threshold (0.60); activity_level value -0.2 is out of allowable range [0.0, 1.0] |
+-----------+------------+----------+-------------+---------------------------------------------------------------------------------------------------------------------------+
```

### Structured Dictionary Output Sample (`session.to_dict()`)

```json
{
  "session_name": "Resting Session",
  "participant_id": "P-REST-01",
  "classification": "resting",
  "explanation": "Average heart rate was 77.92 bpm (+1.9 bpm from baseline) with minimal activity (0.12), consistent with rest.",
  "heart_rate_summary": {
    "mean": 77.92,
    "min": 75.0,
    "max": 81.0,
    "count": 12
  },
  "usable_percentage": 100.0
}
```

---

## 8. Limitations & Possible Improvements

1. **Recovery window splitting:**  
   My recovery detection splits observations into thirds (early vs. late). While this works well for steady recovery after a workout, an interval training session with multiple recovery periods would require a rolling average or slope calculation.
2. **Estimated maximum heart rate:**  
   `AdvancedFitnessSession` uses a standard estimate of 195 bpm because age and gender are not included in the participant profile. In a real system, age and fitness level would be used to calculate a personalized max heart rate.
3. **Discarding vs. interpolating bad data:**  
   Currently, any window with missing or corrupted values is completely discarded. In a production app, short gaps with missing points could be interpolated from surrounding valid readings if the signal quality is otherwise good.
