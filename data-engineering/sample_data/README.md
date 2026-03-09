# Sample Datasets for DataPulse

Three pre-generated datasets for testing and demonstrating the quality scoring system.  
All CSV files are stored in the `datasets/` subfolder.

## Datasets

| File             | Rows | Error Rate | Expected Score | Purpose                                                         |
| ---------------- | ---- | ---------- | -------------- | --------------------------------------------------------------- |
| `clean_data.csv` | 1000 | ~5%        | ~95            | Baseline — minimal errors, validates high-quality path          |
| `mixed_data.csv` | 1000 | ~30%       | ~70            | Realistic — moderate issues, typical production-like data       |
| `messy_data.csv` | 1000 | ~60%       | ~40            | Stress test — heavy errors for edge-case and scoring validation |

## Column Schema

| Column       | Type   | Description                                                 |
| ------------ | ------ | ----------------------------------------------------------- |
| `id`         | int    | Unique row identifier (1-based, sequential)                 |
| `name`       | string | Full name (first + last)                                    |
| `email`      | string | Email address in `first.last@company.com` format            |
| `age`        | int    | Employee age (valid range: 22–65)                           |
| `department` | string | One of: Engineering, Marketing, Sales, HR, Finance, Product |
| `salary`     | int    | Annual salary in USD (valid range: 50,000–150,000)          |
| `hire_date`  | date   | Hire date in `YYYY-MM-DD` format (within last 10 years)     |

## Injected Error Types

The generator injects realistic data quality issues at the configured error rate:

| #   | Error Type         | Example                                 |
| --- | ------------------ | --------------------------------------- |
| 0   | Null name          | Empty string in `name` column           |
| 1   | Invalid email      | Missing TLD (e.g. `john@missingdomain`) |
| 2   | Out-of-range age   | `-5`, `0`, or `150`                     |
| 3   | Invalid department | `InvalidDept` — not in the valid set    |
| 4   | Bad salary         | `-1000`, `0`, or `"Not a number"`       |
| 5   | Future hire date   | Date after today                        |
| 6   | Null age           | Empty string in `age` column            |

## Regenerating

```bash
pip install faker
python generate_samples.py --preset
```
