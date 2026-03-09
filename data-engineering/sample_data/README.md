# Sample Data Generator

This directory contains the `generate_samples.py` script, which is used to generate realistic employee datasets with configurable error rates for testing DataPulse ETL pipelines.

## Usage

You can run the script with the `--preset` flag to generate a standard set of "clean", "mixed", and "messy" data:

```bash
python3 generate_samples.py --preset
```

This will create a new timestamped folder under `generated_sample_data/` containing the three CSV files.

### Custom Generation

For more control, you can specify the number of rows, error rate, and output path:

```bash
python3 generate_samples.py --rows 500 --error-rate 0.2 --output my_custom_data.csv
```

## Datasets Generated (Preset Mode)

| File             | Error Rate | Expected Quality Score | Purpose                                                        |
| ---------------- | ---------- | ---------------------- | -------------------------------------------------------------- |
| `clean_data.csv` | ~5%        | ~95                    | Validates the "happy path" with high-quality data.             |
| `mixed_data.csv` | ~30%       | ~70                    | Simulates typical production data with moderate issues.        |
| `messy_data.csv` | ~60%       | ~40                    | Used for testing robust error handling and low-score triggers. |

## Column Schema

- `id`: Unique sequential identifier.
- `name`: Full name of the employee.
- `email`: Formatted email address.
- `age`: Employee age (valid: 22-65).
- `department`: One of several predefined company departments.
- `salary`: Annual salary (valid: 50,000-150,000).
- `hire_date`: Date of hire (valid: within the last 10 years).

## Requirements

- Python 3.10+
- `faker` library (`pip install faker`)
