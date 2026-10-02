# Smart Fitness Session Analyzer (Assignment II)

## 1. Project Overview

In **Assignment II**, I extended the object-oriented fitness session analyzer from Assignment I into a complete, file-based Python application. 

Instead of generating simulated data in memory, the program now reads official CSV files, validates records, handles malformed inputs and corrupted measurements safely without crashing, groups observations by session, and writes detailed analysis reports to an `output/` directory.

The application satisfies all assignment criteria:
- **File-based Ingestion:** Safely reads `participants.csv`, `fitness_sessions.csv`, and `fitness_sessions_invalid.csv` using Python's `csv` module and `with open(..., encoding="utf-8", newline="")`.
- **Regex Validation:** Validates participant and session identifiers with anchored regular expressions (`^P\d{3}$` and `^FIT-\d{4}-\d{3}$`).
- **Custom Exceptions:** Defines and handles `InvalidIdentifierError` and `InvalidRecordError`.
- **Targeted Error Handling:** Catches specific exceptions (`FileNotFoundError`, `PermissionError`, `ValueError`, `KeyError`) and quarantines invalid records with full diagnostics rather than terminating.
- **Reporting:** Automatically creates an `output/` directory containing `analysis_summary.csv`, `analysis_report.txt`, and `rejected_records.txt`.
- **Standard Library Only:** Built strictly using Python built-in modules (`argparse`, `csv`, `re`, `pathlib`, `typing`, `math`, `unittest`) without any external dependencies.

---

## 2. Package and Module Architecture

I organized the codebase into a clean Python package named `fitness_analyzer` with dedicated modules:

```text
Smart_Fitness_Session_Analyzer/
|-- fitness_analyzer/                 # Python package
|   |-- __init__.py                   # Package exports
|   |-- exceptions.py                 # Custom exception classes
|   |-- validators.py                 # Regular expression and range validation
|   |-- models.py                     # Domain models: Participant, Observation, Sessions
|   |-- calculations.py               # Statistical and trend calculation helpers
|   `-- data_loader.py                # CSV ingestion, record validation, and output writers
|-- option_a_fitness/                 # Course data files
|   |-- participants.csv              # Official participant profiles
|   |-- fitness_sessions.csv          # Official valid session records
|   `-- fitness_sessions_invalid.csv  # Official corrupted session records
|-- main.py                           # CLI entry point with argparse
|-- tests.py                          # Comprehensive unit test suite
|-- requirements.txt                  # Standard library declaration
|-- .gitignore                        # Ignores __pycache__ and bytecode
`-- README.md                         # Project documentation
```

### Module Responsibilities

| Module | Core Responsibility |
|---|---|
| **`fitness_analyzer.exceptions`** | Defines `InvalidIdentifierError` and `InvalidRecordError` (subclassing `ValueError`). |
| **`fitness_analyzer.validators`** | Anchored regex patterns (`^P\d{3}$`, `^FIT-\d{4}-\d{3}$`, `^.+\.csv$`) and numerical boundary checks. |
| **`fitness_analyzer.models`** | Object-oriented domain classes demonstrating encapsulation (`Participant`), data cleaning (`Observation`), and composition/inheritance (`FitnessSession`, `AdvancedFitnessSession`). |
| **`fitness_analyzer.calculations`** | Standalone functions for summary stats (mean, min, max), cooldown recovery trend detection, and personal baseline deviations. |
| **`fitness_analyzer.data_loader`** | Reads CSV inputs with proper UTF-8 encoding, detects corrupted/missing rows, groups observations by session, and writes report files. |

---

## 3. Regular Expression Validation

Per Section 4.2 of the assignment specification, identifiers are validated using compiled, anchored regular expressions with full-match behavior:

```python
PARTICIPANT_ID_PATTERN = re.compile(r"^P\d{3}$")
SESSION_ID_PATTERN = re.compile(r"^FIT-\d{4}-\d{3}$")
CSV_FILENAME_PATTERN = re.compile(r"^.+\.csv$", re.IGNORECASE)
```

- **Participant ID:** Requires uppercase `'P'` followed by exactly three digits (e.g., `P001`, `P002`). Invalid formats like `001` or `P99` raise `InvalidIdentifierError`.
- **Fitness Session ID:** Requires `'FIT-'` followed by a 4-digit year and a 3-digit sequence (e.g., `FIT-2026-001`). Invalid formats like `FIT-26-102` raise `InvalidIdentifierError`.
- **CSV Filenames:** Ensures files have a `.csv` extension before attempting to open them.
- *Note:* In accordance with the assignment guidelines, regular expressions are **not** used for numerical range checks; ordinary Python comparisons (`value < min_val or value > max_val`) are used instead.

---

## 4. Custom Exceptions and Error Handling

Per Section 4.4, I created two custom exception classes:

```python
class InvalidIdentifierError(ValueError):
    """Raised when an identifier has an invalid format."""
    pass

class InvalidRecordError(ValueError):
    """Raised when a CSV record cannot be accepted."""
    pass
```

### Targeted Exception Handling Strategy
The program avoids broad `except Exception:` blocks. Instead, it catches specific errors:
- **`FileNotFoundError` / `PermissionError`:** Handled when opening files. If the profiles file cannot be read, the user receives an informative message. For session files, a missing file logs a warning and allows the program to process remaining files.
- **`ValueError` / `KeyError` / `csv.Error`:** Caught during CSV conversion when fields are empty, unparseable (`"fast"` or `"two"`), or when unexpected column lengths occur.
- **Quarantining Invalid Rows:** When a row in a session file is corrupted, the program does not crash. It records the source file, row number, faulty field, raw value, and reason into `rejected_records.txt` and continues to the next row.

---

## 5. Generated Output Files

When executed, the program automatically creates an `output/` directory (using `pathlib.Path.mkdir(parents=True, exist_ok=True)`) containing three report files:

### 1. `output/analysis_summary.csv`
Contains exactly one summary row for each processed workout session:
```csv
session_id,participant_id,participant_name,classification,valid_observations,total_observations,usable_percentage,avg_heart_rate,hr_difference_from_baseline,avg_temperature,avg_activity_level
FIT-2026-001,P001,Amina Noor,resting,6,6,100.0%,68.83,+0.8,32.43,0.09
FIT-2026-002,P002,Jonas Berg,moderate activity,6,6,100.0%,102.0,+28.0,33.13,0.5
FIT-2026-003,P003,Maya Chen,high activity,6,6,100.0%,132.5,+69.5,33.53,0.75
FIT-2026-004,P001,Amina Noor,recovering,6,6,100.0%,113.17,+45.2,33.28,0.55
FIT-2026-005,P002,Jonas Berg,insufficient data,0,5,0.0%,N/A,N/A,N/A,N/A
FIT-2026-101,P001,Amina Noor,insufficient data,1,1,100.0%,72.0,+4.0,32.5,0.1
```

### 2. `output/analysis_report.txt`
A detailed, human-readable report for each session, including participant baseline comparisons and classification reasoning.

### 3. `output/rejected_records.txt`
A formatted log detailing every quarantined CSV row:
```text
REJECTED CSV RECORDS LOG
========================================================================================
Source File                  | Row   | Field            | Value        | Reason
----------------------------------------------------------------------------------------
fitness_sessions_invalid.csv | 3     | heart_rate       | fast         | Cannot convert heart_rate 'fast' to integer
fitness_sessions_invalid.csv | 4     | participant_id   | 001          | Invalid Participant ID '001'. Must match format 'P' followed by 3 digits (e.g. 'P001').
fitness_sessions_invalid.csv | 5     | activity_level   | EMPTY        | Missing required field 'activity_level'
fitness_sessions_invalid.csv | 6     | signal_quality   | 1.4          | Signal quality value 1.4 is out of allowable range [0.0, 1.0]
fitness_sessions_invalid.csv | 7     | session_id       | FIT-26-102   | Invalid Session ID 'FIT-26-102'. Must match format 'FIT-YYYY-NNN' (e.g. 'FIT-2026-001').
fitness_sessions_invalid.csv | 8     | participant_id   | P999         | Unknown participant identifier 'P999' not found in profiles
fitness_sessions_invalid.csv | 9     | timestamp        | two          | Cannot convert timestamp 'two' to integer
fitness_sessions_invalid.csv | 10    | heart_rate       | -15          | Heart rate value -15 is out of allowable range [35, 205]
fitness_sessions_invalid.csv | 11    | skin_response    | -0.5         | Skin response value -0.5 is out of allowable range [0.0, 50.0]
fitness_sessions_invalid.csv | 12    | row_length       | 7 columns    | Expected 8 columns, found 7
========================================================================================
Total rejected rows: 10
```

---

## 6. How to Run the Program

### Running with Default Arguments
Simply run the script from the repository root; it automatically defaults to the course CSV files:
```bash
# On Windows:
python main.py

# On macOS/Linux:
python3 main.py
```

### Running with Custom Command-Line Flags
Per Section 7, the application supports command-line arguments using `argparse`:
```bash
# Windows
python main.py --profiles option_a_fitness/participants.csv --sessions option_a_fitness/fitness_sessions.csv option_a_fitness/fitness_sessions_invalid.csv --output output

# macOS/Linux
python3 main.py --profiles option_a_fitness/participants.csv --sessions option_a_fitness/fitness_sessions.csv option_a_fitness/fitness_sessions_invalid.csv --output output
```

### Running Automated Tests
```bash
# Windows:
python -m unittest tests.py -v

# macOS/Linux:
python3 -m unittest tests.py -v
```

---

## 7. Console Completion Summary Sample

When executed, the program prints a clean summary to the terminal:

```text
============================================================================
               SMART FITNESS SESSION ANALYZER - ASSIGNMENT II               
============================================================================
Profiles file   : option_a_fitness/participants.csv
Sessions files  : option_a_fitness/fitness_sessions.csv, option_a_fitness/fitness_sessions_invalid.csv
Output folder   : output
----------------------------------------------------------------------------
Loaded 3 participant profile(s) successfully.

============================================================================
                             COMPLETION SUMMARY                             
============================================================================
Total rows examined      : 40
Accepted rows            : 30
Rejected rows quarantined: 10
Processed workout sessions: 6
----------------------------------------------------------------------------
Session ID     | Participant      | Classification     | Usable Obs
----------------------------------------------------------------------------
FIT-2026-001   | Amina Noor       | resting            | 6/6
FIT-2026-002   | Jonas Berg       | moderate activity  | 6/6
FIT-2026-003   | Maya Chen        | high activity      | 6/6
FIT-2026-004   | Amina Noor       | recovering         | 6/6
FIT-2026-005   | Jonas Berg       | insufficient data  | 0/5
FIT-2026-101   | Amina Noor       | insufficient data  | 1/1
----------------------------------------------------------------------------
Created report files:
  - output\analysis_summary.csv
  - output\analysis_report.txt
  - output\rejected_records.txt
============================================================================
```

---

## 8. Limitations & Design Considerations

1. **Header Assumption:** The program assumes CSV files include standard header rows. If a headerless CSV is passed, the first data row is treated as the column names.
2. **Missing Point Recovery:** Currently, rows with missing or corrupted fields are completely quarantined. In a production telemetry pipeline, isolated missing data points could be estimated using linear interpolation if the overall signal quality is high.
3. **Encoding:** All file operations explicitly use `encoding="utf-8"` and `newline=""` to guarantee consistent cross-platform behavior across Windows, macOS, and Linux.
