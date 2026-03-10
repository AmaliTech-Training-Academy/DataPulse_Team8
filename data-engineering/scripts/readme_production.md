# Production Data Generator (DataPulse ETL)

This folder contains `generate_production_data.py`, an optimized script designed to generate massive volumes of synthetic data efficiently. It takes advantage of multiprocessing and chunked file I/O to quickly write millions of rows while maintaining a manageable memory footprint.

## Performance

Leveraging Python's `multiprocessing` and streaming data directly to disk:

- Generates 1,000,000 rows in seconds.
- Memory usage is kept low regardless of the total size, as data is written in small batches (`chunk-size`).
- Tracks progress dynamically using `tqdm`.

## Usage

The script is highly customizable through its command-line interface.

### Generating a Specific Target Size

You can generate a custom CSV file by defining row counts and output properties:

```bash
python generate_production_data.py --rows 5000000 --error-rate 0.1 --output ../sample_data/large_dataset.csv
```

**Custom Arguments:**

- `--rows` : Exact number of total rows requested.
- `--output` : Filepath for the generated CSV.
- `--error-rate` : Float between 0.0 and 1.0 (Default 0.1).
- `--workers` : Number of CPU cores to utilize (Default: Max available on your machine).
- `--chunk-size` : The number of rows calculated in a single process batch before writing to disk (Default: 10,000).

### Generating DataPulse Presets

Simulates staging large datasets with distinct data qualities (Excellent, Mixed, Poor) in a single run:

```bash
python generate_production_data.py --preset
```

_Note: Presets automatically generate 1,000,000 rows by default unless `--rows` is explicitly stated otherwise._

The presets command generates three massive CSVs nested within `sample_data/production_set_YYYYMMDD_HHMMSS/`:

1. `good_data.csv` (5% errors)
2. `mixed_data.csv` (30% errors)
3. `messy_data.csv` (60% errors)
