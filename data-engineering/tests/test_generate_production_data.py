import os
import csv
import pytest
import sys
import multiprocessing as mp
from datetime import datetime

# Add the scripts directory to sys.path to allow importing generate_production_data
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(os.path.dirname(current_dir), "scripts"))

from generate_production_data import (
    init_worker, 
    generate_row_batch, 
    generate_production_dataset, 
    CSV_HEADER
)

@pytest.fixture(scope="module", autouse=True)
def setup_faker():
    """Initialize Faker for the worker functions."""
    init_worker()

def test_generate_row_batch_count():
    """Verify generate_row_batch returns the correct number of rows."""
    batch_size = 10
    start_id = 1
    error_rate = 0.0
    
    rows = generate_row_batch((start_id, batch_size, error_rate))
    
    assert len(rows) == batch_size
    assert rows[0][0] == start_id
    assert rows[-1][0] == start_id + batch_size - 1

def test_generate_row_batch_columns():
    """Verify row batch has the correct number of columns."""
    rows = generate_row_batch((1, 5, 0.0))
    for row in rows:
        assert len(row) == len(CSV_HEADER)

def test_generate_row_batch_no_errors():
    """Verify that with 0% error rate, rows are valid (basic check)."""
    rows = generate_row_batch((1, 20, 0.0))
    for row in rows:
        # id, name, email, age, department, salary, hire_date
        assert row[1] != "" # Name
        assert "@company.com" in row[2] # Email
        assert int(row[3]) >= 22 # Age
        assert int(row[5]) >= 50000 # Salary
        # Date format
        datetime.strptime(row[6], "%Y-%m-%d")

def test_generate_row_batch_with_errors():
    """Verify that with 100% error rate, errors are injected."""
    batch_size = 50
    rows = generate_row_batch((1, batch_size, 1.0))
    
    errors_found = False
    for row in rows:
        # Check for any of the injected error patterns defined in generate_production_data.py
        # Null name, invalid email, unrealistic age, InvalidDept, etc.
        if (row[1] == "" or 
            "@missingdomain" in row[2] or 
            row[4] == "InvalidDept" or 
            row[5] in [-1000, 0, "Not a number"] or
            row[3] in [-5, 0, 150, None]):
            errors_found = True
            break
            
        # Future hire date check
        hire_date = datetime.strptime(row[6], "%Y-%m-%d")
        if hire_date > datetime.now():
            errors_found = True
            break
            
    assert errors_found, "Should have found at least one injected error with 100% error rate"

def test_generate_production_dataset_file_creation(tmp_path):
    """Verify that the end-to-end generator creates a file with correct rows and header."""
    output_path = tmp_path / "prod_test.csv"
    total_rows = 100
    error_rate = 0.1
    workers = 2 # Use 2 workers to test multiprocessing on a small scale
    chunk_size = 50
    
    generate_production_dataset(total_rows, error_rate, str(output_path), workers, chunk_size)
    
    assert output_path.exists()
    
    with open(output_path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader)
        rows = list(reader)
        
    assert header == CSV_HEADER
    assert len(rows) == total_rows
    
    # Check first row ID
    assert rows[0][0] == "1"
    # Check last row ID
    assert rows[-1][0] == str(total_rows)
