"""Robust Sample Dataset Generator for DataPulse ETL.

Generates three sample datasets with different quality levels:
  - clean_data.csv  : ~5% error rate  → expected quality score ~95
  - mixed_data.csv  : ~30% error rate → expected quality score ~70
  - messy_data.csv  : ~60% error rate → expected quality score ~40

Usage:
  python generate_samples.py --preset          # Generate standard preset files
  python generate_samples.py --rows 500 --error-rate 0.2 --output custom.csv
"""

import argparse
import csv
import os
import random
import logging
import sys
from datetime import datetime, timedelta

# Configure Logging
LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "sample_generator.log")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

try:
    from faker import Faker
except ImportError:
    logger.error("The 'faker' library is required to generate realistic data. Please run: pip install faker")
    exit(1)

# Initialize Faker
fake = Faker()

DEPARTMENTS = ["Engineering", "Marketing", "Sales", "HR", "Finance", "Product"]

def generate_robust_dataset(num_rows=1000, error_rate=0.1, output_path="generated.csv"):
    """
    Generate a dataset using Faker with a specified error rate.
    Errors injected align with typical Data Engineering data quality checks.
    """
    rows = []
    
    # Pre-calculate how many exact errors to inject based on error_rate
    num_errors = int(num_rows * error_rate)
    error_indices = set(random.sample(range(1, num_rows + 1), num_errors))

    for i in range(1, num_rows + 1):
        # 1. Base realistic accurate row
        name = fake.name()
        email = f"{name.split()[0].lower()}.{name.split()[-1].lower()}@company.com"
        age = random.randint(22, 65)
        dept = random.choice(DEPARTMENTS)
        salary = random.randint(50000, 150000)
        
        # Hire date between 10 years ago and today
        hire_date = fake.date_between(start_date="-10y", end_date="today").strftime("%Y-%m-%d")

        # 2. Inject specific data quality errors if this index was selected
        if i in error_indices:
            choice = random.randint(0, 6)
            if choice == 0:
                name = ""  # Nullability failure
            elif choice == 1:
                email = f"{name.split()[0]}@missingdomain"  # Invalid format failure
            elif choice == 2:
                age = random.choice([-5, 0, 150])  # Out of bounds / Unrealistic failure
            elif choice == 3:
                dept = "InvalidDept"  # Categorical mismatch failure
            elif choice == 4:
                salary = random.choice([-1000, 0, "Not a number"])  # Type/Range failure
            elif choice == 5:
                # Future hire date failure
                hire_date = fake.date_between(start_date="today", end_date="+1y").strftime("%Y-%m-%d")
            elif choice == 6:
                age = None  # Actual None/Null injection explicitly

        # Handle None conversions for CSV writing gracefully
        row = [
            i, 
            name if name is not None else "",
            email if email is not None else "",
            age if age is not None else "",
            dept if dept is not None else "",
            salary if salary is not None else "",
            hire_date if hire_date is not None else ""
        ]
        rows.append(row)

    # 3. Write to CSV
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "name", "email", "age", "department", "salary", "hire_date"])
        writer.writerows(rows)
        
    logger.info(f"✓ Generated {num_rows} rows mapped to '{output_path}'")
    logger.info(f"  └─ Expected Error Rate: {error_rate * 100:.1f}% (~{num_errors} rows with injected errors)")


def main():
    parser = argparse.ArgumentParser(description="DataPulse Robust CSV Generator")
    parser.add_argument("--rows", type=int, default=1000, help="Number of rows to generate")
    parser.add_argument("--error-rate", type=float, default=0.1, help="Percentage of rows with errors (0.0 to 1.0)")
    parser.add_argument("--output", type=str, default="generated.csv", help="Path to output CSV file")
    parser.add_argument("--preset", action="store_true", help="Generate standard preset files (clean, dirty, mixed)")
    
    args = parser.parse_args()

    # Determine script directory to save files relatively if utilizing preset
    d = os.path.dirname(os.path.abspath(__file__))

    if args.preset:
        logger.info("Generating standard presets...")
        
        # New folder structure: sample_data/generated_sample_data/sample_set_TIMESTAMP/
        sample_data_dir = d
        generated_root = os.path.join(sample_data_dir, "generated_sample_data")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        set_dir = os.path.join(generated_root, f"sample_set_{timestamp}")
        os.makedirs(set_dir, exist_ok=True)
        
        logger.info(f"Creating files in directory: {set_dir}/")
        
        # 95% clean data -> 5% error rate  → expected score ~95
        generate_robust_dataset(1000, 0.05, os.path.join(set_dir, "clean_data.csv"))
        # 70% clean data -> 30% error rate → expected score ~70
        generate_robust_dataset(1000, 0.30, os.path.join(set_dir, "mixed_data.csv"))
        # 40% clean data -> 60% error rate → expected score ~40
        generate_robust_dataset(1000, 0.60, os.path.join(set_dir, "messy_data.csv"))
    else:
        generate_robust_dataset(args.rows, args.error_rate, args.output)


if __name__ == "__main__":
    # Alias for backward compatibility with stashed calls
    generate_dataset = generate_robust_dataset
    
    d = os.path.dirname(os.path.abspath(__file__))
    base_output_dir = os.path.join(d, "generated_sample_data")
    os.makedirs(base_output_dir, exist_ok=True)
    
    # Create a timestamped subdirectory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = os.path.join(base_output_dir, f"sample_set_{timestamp}")
    os.makedirs(output_dir, exist_ok=True)
    
    logger.info(f"Generating samples in: {output_dir}/")
    generate_dataset(100, 0.0, os.path.join(output_dir, "large_clean.csv"))
    generate_dataset(100, 0.15, os.path.join(output_dir, "large_dirty.csv"))
    generate_dataset(200, 0.08, os.path.join(output_dir, "large_mixed.csv"))
