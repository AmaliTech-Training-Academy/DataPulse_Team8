# DataPulse Sample Data Generator

This directory contains `generate_samples.py`, a robust Python script designed to generate synthetic datasets for ETL pipeline testing and data quality evaluation within DataPulse.

## Overview

The `generate_samples.py` script uses the Python `faker` library to produce realistic employee records with configurable data quality issues. It is particularly useful for verifying data validation logic and testing pipeline resilience against malformed datasets.

## Requirements

The script requires the `faker` library:

```bash
pip install faker
```

## Structure of Generated Data

Generated CSV files include the following columns:

- `id`: Sequential integer (1 to N)
- `name`: Full name
- `email`: Email address (e.g., `first.last@company.com`)
- `age`: Integer between 22 and 65
- `department`: Categorical string (Engineering, Marketing, Sales, HR, Finance, Product)
- `salary`: Integer between 50000 and 150000
- `hire_date`: Date string (YYYY-MM-DD) past 10 years

## Usage Methods

### 1. Generating Standard Presets (Recommended)

To generate a predefined standard set of datasets with varying degrees of deliberately injected errors, run with the `--preset` flag:

```bash
python generate_samples.py --preset
```

This will automatically create a new timestamped folder under `generated_sample_data/sample_set_YYYYMMDD_HHMMSS/` containing three files, each with 1,000 rows:

1.  **`clean_data.csv`**: ~5% error rate (Expected Quality Score: ~95)
2.  **`mixed_data.csv`**: ~30% error rate (Expected Quality Score: ~70)
3.  **`messy_data.csv`**: ~60% error rate (Expected Quality Score: ~40)

### 2. Generating Custom Datasets

You can explicitly control the number of rows, the exact error rate, and the destination path:

```bash
python generate_samples.py --rows 500 --error-rate 0.2 --output custom.csv
```

**Parameters:**

- `--rows`: Total number of records to construct (default: 1000).
- `--error-rate`: A float from `0.0` (perfectly clean) to `1.0` (every row has an error). Determines what percentage of records contain exactly one defect (default: 0.1).
- `--output`: Filepath where the CSV will be saved (default: generated.csv).

## Injected Data Quality Errors

When the script evaluates that a specific row should contain an error (based on the requested `--error-rate`), it injects exactly **one** of the following common data anomalies:

1.  **Null Name**: Empty string instead of a valid name.
2.  **Invalid Email Format**: Missing domain in the email address (e.g., `name@missingdomain`).
3.  **Unrealistic Age**: Negative, zero, or highly improbable age (e.g., -5, 0, 150).
4.  **Categorical Mismatch**: "InvalidDept" assigned to the Department column.
5.  **Invalid Salary**: Negative value, zero, or a string ("Not a number") instead of numeric data.
6.  **Future Hire Date**: A date up to 1 year in the future.
7.  **Implicit Null/None Age**: Explicitly nullifying integer values.
