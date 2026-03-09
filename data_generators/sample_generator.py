"""
Sample Data Generator
=====================
Generates lightweight, reproducible sample/test datasets for use in
development, unit-testing, and QA test plans for the DataPulse platform.

Usage (CLI):
    python -m data_generators.sample_generator --rows 500 --output data/samples

Usage (Python):
    from data_generators.sample_generator import SampleDataGenerator

    gen = SampleDataGenerator(seed=42)
    df = gen.generate_sales(rows=200)
    gen.save(df, "sales", output_dir="data/samples")
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import random
import string
from datetime import datetime, timedelta
from typing import Dict, List, Optional


class SampleDataGenerator:
    """Generates deterministic sample datasets for testing and development."""

    # ------------------------------------------------------------------ #
    #  Construction                                                        #
    # ------------------------------------------------------------------ #

    def __init__(self, seed: int = 42) -> None:
        """
        Parameters
        ----------
        seed:
            Random seed that makes all generated datasets fully reproducible.
        """
        self._seed = seed
        random.seed(seed)

    # ------------------------------------------------------------------ #
    #  Public generators                                                   #
    # ------------------------------------------------------------------ #

    def generate_sales(self, rows: int = 100) -> List[Dict]:
        """Return a list of sale-record dicts.

        Fields: id, date, product, category, quantity, unit_price, total,
                region, customer_id, status.
        """
        categories = ["Electronics", "Clothing", "Food", "Books", "Home"]
        regions = ["North", "South", "East", "West", "Central"]
        statuses = ["completed", "pending", "refunded", "cancelled"]

        records: List[Dict] = []
        base_date = datetime(2024, 1, 1)

        for i in range(1, rows + 1):
            qty = random.randint(1, 50)
            price = round(random.uniform(5.0, 500.0), 2)
            records.append(
                {
                    "id": i,
                    "date": (
                        base_date + timedelta(days=random.randint(0, 364))
                    ).strftime("%Y-%m-%d"),
                    "product": f"Product_{self._rand_str(6)}",
                    "category": random.choice(categories),
                    "quantity": qty,
                    "unit_price": price,
                    "total": round(qty * price, 2),
                    "region": random.choice(regions),
                    "customer_id": f"CUST_{random.randint(1000, 9999)}",
                    "status": random.choice(statuses),
                }
            )
        return records

    def generate_users(self, rows: int = 50) -> List[Dict]:
        """Return a list of user-record dicts.

        Fields: id, username, email, role, active, created_at.
        """
        roles = ["admin", "analyst", "viewer", "editor"]
        records: List[Dict] = []
        base_date = datetime(2023, 1, 1)

        for i in range(1, rows + 1):
            username = f"user_{self._rand_str(5)}"
            records.append(
                {
                    "id": i,
                    "username": username,
                    "email": f"{username}@datapulse.example.com",
                    "role": random.choice(roles),
                    "active": random.choice([True, False]),
                    "created_at": (
                        base_date + timedelta(days=random.randint(0, 700))
                    ).strftime("%Y-%m-%dT%H:%M:%S"),
                }
            )
        return records

    def generate_quality_checks(self, rows: int = 80) -> List[Dict]:
        """Return a list of data-quality check result dicts.

        Fields: id, dataset_id, rule_id, check_date, passed, score,
                error_count, warning_count.
        """
        records: List[Dict] = []
        base_date = datetime(2024, 1, 1)

        for i in range(1, rows + 1):
            passed = random.random() > 0.2
            records.append(
                {
                    "id": i,
                    "dataset_id": random.randint(1, 20),
                    "rule_id": random.randint(1, 10),
                    "check_date": (
                        base_date + timedelta(days=random.randint(0, 364))
                    ).strftime("%Y-%m-%dT%H:%M:%S"),
                    "passed": passed,
                    "score": round(random.uniform(0.5, 1.0) if passed else random.uniform(0.0, 0.5), 4),
                    "error_count": 0 if passed else random.randint(1, 50),
                    "warning_count": random.randint(0, 10),
                }
            )
        return records

    def generate_datasets_metadata(self, rows: int = 20) -> List[Dict]:
        """Return metadata records describing uploaded datasets.

        Fields: id, name, description, file_type, row_count, column_count,
                uploaded_by, uploaded_at, status.
        """
        file_types = ["csv", "excel", "json", "parquet"]
        statuses = ["active", "archived", "processing", "failed"]
        records: List[Dict] = []
        base_date = datetime(2024, 1, 1)

        for i in range(1, rows + 1):
            records.append(
                {
                    "id": i,
                    "name": f"dataset_{self._rand_str(8)}",
                    "description": f"Sample dataset {i} for testing purposes",
                    "file_type": random.choice(file_types),
                    "row_count": random.randint(100, 100_000),
                    "column_count": random.randint(3, 30),
                    "uploaded_by": f"CUST_{random.randint(1000, 9999)}",
                    "uploaded_at": (
                        base_date + timedelta(days=random.randint(0, 364))
                    ).strftime("%Y-%m-%dT%H:%M:%S"),
                    "status": random.choice(statuses),
                }
            )
        return records

    # ------------------------------------------------------------------ #
    #  Persistence helpers                                                 #
    # ------------------------------------------------------------------ #

    def save(
        self,
        records: List[Dict],
        name: str,
        output_dir: str = "data/samples",
        fmt: str = "csv",
    ) -> str:
        """Persist *records* to *output_dir* as CSV or JSON.

        Returns the full path of the written file.
        """
        os.makedirs(output_dir, exist_ok=True)
        filepath = os.path.join(output_dir, f"{name}.{fmt}")

        if fmt == "csv":
            self._write_csv(records, filepath)
        elif fmt == "json":
            self._write_json(records, filepath)
        else:
            raise ValueError(f"Unsupported format '{fmt}'. Choose 'csv' or 'json'.")

        print(f"[SampleGenerator] Wrote {len(records)} records → {filepath}")
        return filepath

    # ------------------------------------------------------------------ #
    #  Internal helpers                                                    #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _rand_str(length: int) -> str:
        return "".join(random.choices(string.ascii_lowercase + string.digits, k=length))

    @staticmethod
    def _write_csv(records: List[Dict], filepath: str) -> None:
        if not records:
            return
        with open(filepath, "w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=records[0].keys())
            writer.writeheader()
            writer.writerows(records)

    @staticmethod
    def _write_json(records: List[Dict], filepath: str) -> None:
        with open(filepath, "w", encoding="utf-8") as fh:
            json.dump(records, fh, indent=2, default=str)


# --------------------------------------------------------------------------- #
#  CLI entry-point                                                             #
# --------------------------------------------------------------------------- #

def _parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate sample datasets for DataPulse development/testing."
    )
    parser.add_argument("--rows", type=int, default=100, help="Rows per dataset (default: 100)")
    parser.add_argument("--output", default="data/samples", help="Output directory (default: data/samples)")
    parser.add_argument("--format", choices=["csv", "json"], default="csv", help="Output format (default: csv)")
    parser.add_argument("--seed", type=int, default=42, help="Random seed (default: 42)")
    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> None:
    args = _parse_args(argv)
    gen = SampleDataGenerator(seed=args.seed)

    datasets = {
        "sales": gen.generate_sales(rows=args.rows),
        "users": gen.generate_users(rows=max(10, args.rows // 5)),
        "quality_checks": gen.generate_quality_checks(rows=args.rows),
        "datasets_metadata": gen.generate_datasets_metadata(rows=max(10, args.rows // 10)),
    }

    for name, records in datasets.items():
        gen.save(records, name, output_dir=args.output, fmt=args.format)

    print(f"[SampleGenerator] Done — {len(datasets)} datasets written to '{args.output}'.")


if __name__ == "__main__":
    main()
