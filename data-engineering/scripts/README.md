# Production Data Generator (High-Performance)

This directory contains `generate_production_data.py`, a high-performance tool designed to generate millions of rows of realistic data for scale and load testing of the DataPulse ETL pipeline.

## Features

- **High Performance**: Uses Python's `multiprocessing` to saturate available CPU cores.
- **Memory Efficient**: Implements chunked writing (buffered I/O) to handle millions of rows without exhausting RAM.
- **Realistic Data**: Leverages the `faker` library to generate plausible employee records.
- **Configurable Error Injection**: Specifically designed to test data quality scoring systems by injecting controlled anomalies.
- **Preset Mode**: Quickly generates three massive standard datasets (Good, Mixed, Messy).

## Usage

### 1. Generating Presets (Recommendation)

Use the `--preset` flag to generate three massive 1,000,000-row files:

```bash
python3 generate_production_data.py --preset
```

- **Output Location**: `data-engineering/generated_csv_data/production_set_TIMESTAMP/`
- **Files**: `good_data.csv` (~95% score), `mixed_data.csv` (~70% score), `messy_data.csv` (~40% score).

### 2. Custom Generation

For specific requirements:

```bash
python3 generate_production_data.py --rows 5000000 --error-rate 0.15 --output ../generated_csv_data/large_batch.csv
```

## Dataset Configuration

| Parameter      | Default  | Description                                        |
| -------------- | -------- | -------------------------------------------------- |
| `--rows`       | -        | Total rows to generate.                            |
| `--error-rate` | 0.1      | Fraction of rows (0.0 - 1.0) containing anomalies. |
| `--workers`    | Max CPUs | Number of parallel processes to use.               |
| `--chunk-size` | 10,000   | Rows held in memory before flushing to disk.       |

## Column Schema

- `id`: Sequential primary key.
- `name`: Full name.
- `email`: Company-specific email format or invalid format (error).
- `age`: Valid (22-65) or anomalies (0, 150, etc.).
- `department`: Valid company departments or "InvalidDept".
- `salary`: Realistic ranges or invalid types/negative values.
- `hire_date`: Past 10 years or future dates (error).

## Testing

Run the dedicated test suite to verify generator logic:

```bash
pytest ../tests/test_generate_production_data.py
```

## Notes

- The `generated_csv_data/` directory is used for output storage. Large generated CSVs should typically not be committed to version control.
