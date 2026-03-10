"""
High-Performance Production Data Generator for DataPulse ETL.
Generates millions of realistic rows efficiently using multiprocessing and chunked I/O.
"""

import argparse
import csv
import os
import random
import sys
import multiprocessing as mp
from datetime import datetime
from functools import partial

try:
    from faker import Faker
    from tqdm import tqdm
except ImportError:
    print("Error: Required libraries missing.")
    print("Please run: pip install faker tqdm")
    sys.exit(1)

# Constants
DEPARTMENTS = ["Engineering", "Marketing", "Sales", "HR", "Finance", "Product", "Operations", "Legal"]
CSV_HEADER = ["id", "name", "email", "age", "department", "salary", "hire_date"]

# Global Faker instance per worker process
fake = None

def init_worker():
    """Initialize a global Faker instance for each multiprocessing worker."""
    global fake
    fake = Faker()

def generate_row_batch(batch_args):
    """
    Worker function to generate a batch of rows.
    batch_args is a tuple: (start_id, batch_size, error_rate)
    """
    start_id, batch_size, error_rate = batch_args
    rows = []
    
    num_errors = int(batch_size * error_rate)
    error_indices = set(random.sample(range(start_id, start_id + batch_size), num_errors))

    for current_id in range(start_id, start_id + batch_size):
        # Base realistic accurate row
        name = fake.name()
        email = f"{name.split()[0].lower()}.{name.split()[-1].lower()}@company.com"
        age = random.randint(22, 65)
        dept = random.choice(DEPARTMENTS)
        salary = random.randint(50000, 150000)
        hire_date = fake.date_between(start_date="-10y", end_date="today").strftime("%Y-%m-%d")

        # Inject specific data quality errors
        if current_id in error_indices:
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
                hire_date = fake.date_between(start_date="today", end_date="+1y").strftime("%Y-%m-%d") # Future hire
            elif choice == 6:
                age = None  # Actual None/Null injection explicitly

        row = [
            current_id, 
            name if name is not None else "",
            email if email is not None else "",
            age if age is not None else "",
            dept if dept is not None else "",
            salary if salary is not None else "",
            hire_date if hire_date is not None else ""
        ]
        rows.append(row)
        
    return rows

def generate_production_dataset(total_rows, error_rate, output_path, workers, chunk_size):
    """Generate production-scale dataset using multiprocessing and chunked writes."""
    
    # Ensure directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    print(f"Initializing generation of {total_rows:,} rows...")
    print(f"Output       : {output_path}")
    print(f"Workers      : {workers}")
    print(f"Target Error : {error_rate * 100:.1f}%")
    
    # Prepare work batches
    batches = []
    current_id = 1
    while current_id <= total_rows:
        batch_size = min(chunk_size, total_rows - current_id + 1)
        batches.append((current_id, batch_size, error_rate))
        current_id += batch_size

    # Write header and process batches
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(CSV_HEADER)

        # Use Imap for ordered writing and realtime progress bar
        with mp.Pool(processes=workers, initializer=init_worker) as pool:
            # imap is lazy but ordered, perfect for chunked File I/O
            results = pool.imap(generate_row_batch, batches)
            
            with tqdm(total=total_rows, desc="Generating", unit="rows") as pbar:
                for batch_result in results:
                    writer.writerows(batch_result)
                    pbar.update(len(batch_result))

    print(f"\n✓ Successfully generated {total_rows:,} rows.")
    file_size_mb = os.path.getsize(output_path) / (1024 * 1024)
    print(f"✓ Final File Size: {file_size_mb:.2f} MB")

def main():
    parser = argparse.ArgumentParser(description="DataPulse Production Scale CSV Generator")
    parser.add_argument("--rows", type=int, help="Total number of rows to generate (e.g., 1000000)")
    parser.add_argument("--error-rate", type=float, default=0.1, help="Percentage of rows with errors (0.0 to 1.0)")
    parser.add_argument("--output", type=str, help="Absolute or relative path to output CSV file")
    parser.add_argument("--preset", action="store_true", help="Generate 3 massive preset files (good, mixed, messy) in a numbered folder.")
    
    # Performance tuning parameters
    parser.add_argument("--workers", type=int, default=mp.cpu_count(), help="Number of CPU cores to use (default: max)")
    parser.add_argument("--chunk-size", type=int, default=10000, help="Rows per batch. Do not change unless tuning RAM.")
    
    args = parser.parse_args()

    start_time = datetime.now()
    try:
        if args.preset:
            # Generate 1,000,000 rows per file for the production preset if not specified
            preset_rows = 1000000 if not args.rows else args.rows
            print(f"Generating massive production presets ({preset_rows:,} rows each)...")
            
            # Resolve data-engineering/sample_data directory correctly
            d = os.path.dirname(os.path.abspath(__file__))
            sample_data_dir = os.path.join(os.path.dirname(os.path.dirname(d)), "sample_data")
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            set_folder_name = f"production_set_{timestamp}"
            set_dir = os.path.join(sample_data_dir, set_folder_name)
            os.makedirs(set_dir, exist_ok=True)
            
            print(f"Creating massive files in: {set_dir}/")
            generate_production_dataset(preset_rows, 0.05, os.path.join(set_dir, "good_data.csv"), args.workers, args.chunk_size)
            generate_production_dataset(preset_rows, 0.30, os.path.join(set_dir, "mixed_data.csv"), args.workers, args.chunk_size)
            generate_production_dataset(preset_rows, 0.60, os.path.join(set_dir, "messy_data.csv"), args.workers, args.chunk_size)
            
        else:
            if not args.rows or not args.output:
                parser.error("The following arguments are required unless using --preset: --rows, --output")
                
            # Safety checks
            if args.rows <= 0:
                print("Error: --rows must be greater than 0")
                sys.exit(1)
            if not (0.0 <= args.error_rate <= 1.0):
                print("Error: --error-rate must be between 0.0 and 1.0")
                sys.exit(1)

            generate_production_dataset(
                args.rows, 
                args.error_rate, 
                args.output, 
                args.workers, 
                args.chunk_size
            )
    except KeyboardInterrupt:
        print("\n⚠ Generation cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n✘ Fatal error during generation: {e}")
        sys.exit(1)
        
    duration = datetime.now() - start_time
    print(f"✓ Total Execution Time: {duration}")

if __name__ == "__main__":
    # Required for Windows multiprocessing compatibility, safe on Mac/Linux
    mp.freeze_support()
    main()
