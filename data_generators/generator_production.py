"""
Production Data Generator
==========================
Production-grade ETL data generator for the DataPulse platform.

Features:
- Configurable schema definitions via a simple dict/JSON spec.
- Batch-oriented generation with progress reporting.
- Built-in data-quality validation (null checks, range checks, uniqueness).
- PostgreSQL seeding via SQLAlchemy (DATABASE_URL env var) or dry-run mode.
- Idempotent: re-running with the same seed/config always yields the same data.

Usage (CLI):
    python -m data_generators.generator_production --config config/prod_schema.json --rows 10000

Usage (Python):
    from data_generators.generator_production import ProductionDataGenerator

    gen = ProductionDataGenerator(seed=0)
    result = gen.run(schema_name="sales", rows=5000, dry_run=True)
    print(result.summary())
"""

from __future__ import annotations

import argparse
import csv
import json
import logging
import os
import random
import string
import sys
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# --------------------------------------------------------------------------- #
#  Schema definitions                                                          #
# --------------------------------------------------------------------------- #

#: Built-in schemas shipped with the package.  Custom schemas can be loaded
#: from JSON files via :meth:`ProductionDataGenerator.load_schema`.
BUILTIN_SCHEMAS: Dict[str, List[Dict[str, Any]]] = {
    "sales": [
        {"name": "id",          "type": "sequence"},
        {"name": "date",        "type": "date",    "start": "2023-01-01", "end": "2024-12-31"},
        {"name": "product",     "type": "str",     "prefix": "PROD_",    "length": 8},
        {"name": "category",    "type": "choice",  "choices": ["Electronics", "Clothing", "Food", "Books", "Home", "Sports"]},
        {"name": "quantity",    "type": "int",     "min": 1,   "max": 500},
        {"name": "unit_price",  "type": "float",   "min": 1.0, "max": 999.99, "decimals": 2},
        {"name": "region",      "type": "choice",  "choices": ["North", "South", "East", "West", "Central"]},
        {"name": "customer_id", "type": "str",     "prefix": "CUST_",    "length": 6},
        {"name": "status",      "type": "choice",  "choices": ["completed", "pending", "refunded", "cancelled"],
                                "weights": [0.70, 0.15, 0.10, 0.05]},
    ],
    "users": [
        {"name": "id",          "type": "sequence"},
        {"name": "username",    "type": "str",     "prefix": "user_",  "length": 8},
        {"name": "email",       "type": "email"},
        {"name": "role",        "type": "choice",  "choices": ["admin", "analyst", "viewer", "editor"],
                                "weights": [0.05, 0.30, 0.50, 0.15]},
        {"name": "active",      "type": "bool",    "true_rate": 0.85},
        {"name": "created_at",  "type": "datetime","start": "2022-01-01", "end": "2024-12-31"},
    ],
    "datasets_metadata": [
        {"name": "id",           "type": "sequence"},
        {"name": "name",         "type": "str",    "prefix": "ds_",  "length": 10},
        {"name": "description",  "type": "str",    "prefix": "Dataset ", "length": 5},
        {"name": "file_type",    "type": "choice", "choices": ["csv", "excel", "json", "parquet"]},
        {"name": "row_count",    "type": "int",    "min": 100, "max": 10_000_000},
        {"name": "column_count", "type": "int",    "min": 2,   "max": 100},
        {"name": "status",       "type": "choice", "choices": ["active", "archived", "processing", "failed"],
                                 "weights": [0.80, 0.10, 0.05, 0.05]},
        {"name": "uploaded_at",  "type": "datetime","start": "2023-01-01", "end": "2024-12-31"},
    ],
    "quality_checks": [
        {"name": "id",            "type": "sequence"},
        {"name": "dataset_id",    "type": "int",  "min": 1, "max": 500},
        {"name": "rule_id",       "type": "int",  "min": 1, "max": 50},
        {"name": "check_date",    "type": "datetime", "start": "2023-01-01", "end": "2024-12-31"},
        {"name": "passed",        "type": "bool", "true_rate": 0.85},
        {"name": "score",         "type": "float","min": 0.0, "max": 1.0, "decimals": 4},
        {"name": "error_count",   "type": "int",  "min": 0, "max": 200},
        {"name": "warning_count", "type": "int",  "min": 0, "max": 50},
    ],
}


# --------------------------------------------------------------------------- #
#  Result dataclass                                                            #
# --------------------------------------------------------------------------- #

@dataclass
class GenerationResult:
    schema_name: str
    rows_requested: int
    rows_generated: int
    validation_errors: List[str] = field(default_factory=list)
    output_path: Optional[str] = None
    db_table: Optional[str] = None
    duration_seconds: float = 0.0

    def summary(self) -> str:
        lines = [
            f"Schema        : {self.schema_name}",
            f"Rows requested: {self.rows_requested:,}",
            f"Rows generated: {self.rows_generated:,}",
            f"Validation OK : {not self.validation_errors}",
            f"Duration (s)  : {self.duration_seconds:.2f}",
        ]
        if self.output_path:
            lines.append(f"Output file   : {self.output_path}")
        if self.db_table:
            lines.append(f"DB table      : {self.db_table}")
        if self.validation_errors:
            lines.append("Validation errors:")
            for err in self.validation_errors[:10]:
                lines.append(f"  - {err}")
            if len(self.validation_errors) > 10:
                lines.append(f"  … and {len(self.validation_errors) - 10} more")
        return "\n".join(lines)

    @property
    def success(self) -> bool:
        return not self.validation_errors


# --------------------------------------------------------------------------- #
#  Core generator                                                              #
# --------------------------------------------------------------------------- #

class ProductionDataGenerator:
    """
    Production-grade, schema-driven data generator for DataPulse.

    Parameters
    ----------
    seed:
        Random seed for full reproducibility.
    batch_size:
        Number of rows to generate per internal batch (affects memory usage).
    log_level:
        Python logging level string (e.g. ``"INFO"``, ``"DEBUG"``).
    """

    def __init__(
        self,
        seed: int = 0,
        batch_size: int = 1_000,
        log_level: str = "INFO",
    ) -> None:
        self._seed = seed
        self._batch_size = batch_size
        random.seed(seed)
        logging.basicConfig(
            level=getattr(logging, log_level.upper(), logging.INFO),
            format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        )

    # ------------------------------------------------------------------ #
    #  Public API                                                          #
    # ------------------------------------------------------------------ #

    def run(
        self,
        schema_name: str,
        rows: int = 1_000,
        output_dir: Optional[str] = None,
        fmt: str = "csv",
        db_url: Optional[str] = None,
        dry_run: bool = False,
        custom_schema: Optional[List[Dict[str, Any]]] = None,
    ) -> GenerationResult:
        """
        Generate *rows* rows for *schema_name* and optionally persist them.

        Parameters
        ----------
        schema_name:
            Key in :data:`BUILTIN_SCHEMAS` or a label for *custom_schema*.
        rows:
            Number of rows to generate.
        output_dir:
            Write output file here.  If ``None`` and *dry_run* is ``False``,
            defaults to ``"data/production"``.
        fmt:
            ``"csv"`` or ``"json"``.
        db_url:
            SQLAlchemy connection string.  If provided the generated data is
            inserted into a table named *schema_name*.
        dry_run:
            If ``True``, generate data in-memory only (no I/O).
        custom_schema:
            Provide your own field spec list instead of a built-in schema.

        Returns
        -------
        GenerationResult
        """
        import time
        t0 = time.monotonic()

        schema = custom_schema or BUILTIN_SCHEMAS.get(schema_name)
        if schema is None:
            raise ValueError(
                f"Unknown schema '{schema_name}'. "
                f"Available built-ins: {list(BUILTIN_SCHEMAS.keys())}"
            )

        logger.info("Starting generation: schema=%s rows=%d", schema_name, rows)
        records = self._generate_batched(schema, rows)
        logger.info("Generation complete. Validating …")

        errors = self._validate(records, schema)
        if errors:
            logger.warning("%d validation error(s) found.", len(errors))

        result = GenerationResult(
            schema_name=schema_name,
            rows_requested=rows,
            rows_generated=len(records),
            validation_errors=errors,
        )

        if not dry_run:
            out_dir = output_dir or "data/production"
            result.output_path = self._write(records, schema_name, out_dir, fmt)

            if db_url:
                result.db_table = self._seed_database(records, schema_name, db_url)

        result.duration_seconds = time.monotonic() - t0
        logger.info("Done. %s", result.summary())
        return result

    @staticmethod
    def load_schema(path: str) -> Tuple[str, List[Dict[str, Any]]]:
        """Load a custom schema JSON file.

        The JSON file must contain an object with two keys:
        ``"name"`` (str) and ``"fields"`` (list of field specs).

        Returns ``(name, fields)`` tuple.
        """
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
        name: str = data["name"]
        fields: List[Dict[str, Any]] = data["fields"]
        return name, fields

    # ------------------------------------------------------------------ #
    #  Internal — data generation                                         #
    # ------------------------------------------------------------------ #

    def _generate_batched(
        self, schema: List[Dict[str, Any]], rows: int
    ) -> List[Dict]:
        records: List[Dict] = []
        sequence_counters: Dict[str, int] = {}

        for start in range(0, rows, self._batch_size):
            count = min(self._batch_size, rows - start)
            batch = self._generate_batch(schema, count, sequence_counters)
            records.extend(batch)
            logger.debug("Generated %d / %d rows …", len(records), rows)

        return records

    def _generate_batch(
        self,
        schema: List[Dict[str, Any]],
        count: int,
        seq: Dict[str, int],
    ) -> List[Dict]:
        rows = []
        for _ in range(count):
            row: Dict[str, Any] = {}
            for field_spec in schema:
                name = field_spec["name"]
                row[name] = self._generate_value(field_spec, seq)
            rows.append(row)
        return rows

    def _generate_value(
        self, spec: Dict[str, Any], seq: Dict[str, int]
    ) -> Any:
        ftype = spec["type"]

        if ftype == "sequence":
            name = spec["name"]
            seq[name] = seq.get(name, 0) + 1
            return seq[name]

        if ftype == "int":
            return random.randint(spec.get("min", 0), spec.get("max", 1_000))

        if ftype == "float":
            value = random.uniform(spec.get("min", 0.0), spec.get("max", 1.0))
            decimals = spec.get("decimals", 2)
            return round(value, decimals)

        if ftype == "str":
            prefix = spec.get("prefix", "")
            length = spec.get("length", 6)
            suffix = "".join(
                random.choices(string.ascii_lowercase + string.digits, k=length)
            )
            return f"{prefix}{suffix}"

        if ftype == "email":
            user = "".join(random.choices(string.ascii_lowercase, k=6))
            domain = random.choice(["datapulse.io", "example.com", "corp.net"])
            return f"{user}@{domain}"

        if ftype == "choice":
            choices = spec["choices"]
            weights = spec.get("weights")
            return random.choices(choices, weights=weights, k=1)[0]

        if ftype == "bool":
            true_rate = spec.get("true_rate", 0.5)
            return random.random() < true_rate

        if ftype in ("date", "datetime"):
            start = datetime.strptime(spec.get("start", "2020-01-01"), "%Y-%m-%d")
            end = datetime.strptime(spec.get("end", "2024-12-31"), "%Y-%m-%d")
            delta_days = (end - start).days
            dt = start + timedelta(days=random.randint(0, delta_days))
            if ftype == "date":
                return dt.strftime("%Y-%m-%d")
            return dt.strftime("%Y-%m-%dT%H:%M:%S")

        raise ValueError(f"Unknown field type: '{ftype}'")

    # ------------------------------------------------------------------ #
    #  Internal — validation                                              #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _validate(
        records: List[Dict], schema: List[Dict[str, Any]]
    ) -> List[str]:
        errors: List[str] = []
        required_fields = {s["name"] for s in schema}
        seen_sequences: Dict[str, set] = {}

        for idx, row in enumerate(records):
            # Null / missing check
            for fname in required_fields:
                if row.get(fname) is None:
                    errors.append(f"Row {idx}: field '{fname}' is null")

            # Uniqueness check for sequence fields
            for spec in schema:
                if spec["type"] == "sequence":
                    name = spec["name"]
                    value = row.get(name)
                    bucket = seen_sequences.setdefault(name, set())
                    if value in bucket:
                        errors.append(f"Duplicate sequence value {value} in field '{name}' at row {idx}")
                    bucket.add(value)

            # Range checks
            for spec in schema:
                name = spec["name"]
                value = row.get(name)
                if spec["type"] in ("int", "float") and value is not None:
                    lo = spec.get("min")
                    hi = spec.get("max")
                    if lo is not None and value < lo:
                        errors.append(f"Row {idx}: '{name}'={value} < min={lo}")
                    if hi is not None and value > hi:
                        errors.append(f"Row {idx}: '{name}'={value} > max={hi}")

        return errors

    # ------------------------------------------------------------------ #
    #  Internal — persistence                                             #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _write(
        records: List[Dict],
        name: str,
        output_dir: str,
        fmt: str,
    ) -> str:
        os.makedirs(output_dir, exist_ok=True)
        filepath = os.path.join(output_dir, f"{name}.{fmt}")

        if fmt == "csv":
            if records:
                with open(filepath, "w", newline="", encoding="utf-8") as fh:
                    writer = csv.DictWriter(fh, fieldnames=records[0].keys())
                    writer.writeheader()
                    writer.writerows(records)
        elif fmt == "json":
            with open(filepath, "w", encoding="utf-8") as fh:
                json.dump(records, fh, indent=2, default=str)
        else:
            raise ValueError(f"Unsupported format '{fmt}'.")

        logger.info("Wrote %d records → %s", len(records), filepath)
        return filepath

    @staticmethod
    def _seed_database(
        records: List[Dict], table_name: str, db_url: str
    ) -> str:
        """Insert *records* into *table_name* using SQLAlchemy.

        The table is created automatically if it does not exist (text columns
        for all fields).  For production use, define a proper migration with
        Alembic.
        """
        try:
            from sqlalchemy import Column, MetaData, String, Table, create_engine, text
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError(
                "SQLAlchemy is required for database seeding. "
                "Install it with: pip install sqlalchemy"
            ) from exc

        engine = create_engine(db_url)
        metadata = MetaData()

        if not records:
            logger.warning("No records to insert into '%s'.", table_name)
            return table_name

        columns = [Column(k, String) for k in records[0]]
        table = Table(table_name, metadata, *columns, extend_existing=True)

        with engine.begin() as conn:
            # Create table if absent
            metadata.create_all(conn)
            # Truncate then re-insert for idempotency
            conn.execute(text(f"DELETE FROM {table_name}"))
            conn.execute(table.insert(), [{str(k): str(v) for k, v in row.items()} for row in records])

        logger.info("Seeded %d rows into DB table '%s'.", len(records), table_name)
        return table_name


# --------------------------------------------------------------------------- #
#  CLI entry-point                                                             #
# --------------------------------------------------------------------------- #

def _parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Production data generator for DataPulse."
    )
    parser.add_argument(
        "--schema",
        default="sales",
        choices=list(BUILTIN_SCHEMAS.keys()),
        help="Built-in schema to generate (default: sales).",
    )
    parser.add_argument(
        "--config",
        metavar="PATH",
        help="Path to a custom JSON schema file (overrides --schema).",
    )
    parser.add_argument(
        "--rows", type=int, default=1_000,
        help="Number of rows to generate (default: 1000).",
    )
    parser.add_argument(
        "--output", default="data/production",
        help="Output directory (default: data/production).",
    )
    parser.add_argument(
        "--format", choices=["csv", "json"], default="csv",
        help="Output format (default: csv).",
    )
    parser.add_argument(
        "--db-url", default=os.environ.get("DATABASE_URL"),
        help="SQLAlchemy DB URL for seeding (default: $DATABASE_URL).",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Generate data in-memory only; do not write files or seed DB.",
    )
    parser.add_argument(
        "--seed", type=int, default=0,
        help="Random seed (default: 0).",
    )
    parser.add_argument(
        "--batch-size", type=int, default=1_000,
        help="Rows per internal batch (default: 1000).",
    )
    parser.add_argument(
        "--log-level", default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level (default: INFO).",
    )
    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> None:
    args = _parse_args(argv)

    gen = ProductionDataGenerator(
        seed=args.seed,
        batch_size=args.batch_size,
        log_level=args.log_level,
    )

    schema_name = args.schema
    custom_schema = None

    if args.config:
        schema_name, custom_schema = ProductionDataGenerator.load_schema(args.config)
        logger.info("Loaded custom schema '%s' from %s", schema_name, args.config)

    result = gen.run(
        schema_name=schema_name,
        rows=args.rows,
        output_dir=args.output,
        fmt=args.format,
        db_url=args.db_url,
        dry_run=args.dry_run,
        custom_schema=custom_schema,
    )

    print(result.summary())
    sys.exit(0 if result.success else 1)


if __name__ == "__main__":
    main()
