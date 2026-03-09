import os
import csv
import pytest
import sys
from datetime import datetime

# Add the sample_data directory to sys.path to allow importing generate_samples
# Adjusting to point to the correct absolute path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(os.path.dirname(current_dir), "sample_data"))

from generate_samples import generate_robust_dataset

def test_generate_robust_dataset_creates_file(tmp_path):
    """Verify that the generator creates a file at the specified path."""
    output_path = tmp_path / "test_output.csv"
    generate_robust_dataset(num_rows=10, error_rate=0.0, output_path=str(output_path))
    assert output_path.exists()

def test_generate_robust_dataset_row_count(tmp_path):
    """Verify that the generator produces the requested number of rows and a correct header."""
    num_rows = 50
    output_path = tmp_path / "row_count.csv"
    generate_robust_dataset(num_rows=num_rows, error_rate=0.0, output_path=str(output_path))
    
    with open(output_path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader)
        rows = list(reader)
        
    assert len(rows) == num_rows
    assert header == ["id", "name", "email", "age", "department", "salary", "hire_date"]

def test_generate_robust_dataset_no_errors(tmp_path):
    """Verify that with 0% error rate, all rows are realistic and valid."""
    num_rows = 20
    output_path = tmp_path / "no_errors.csv"
    generate_robust_dataset(num_rows=num_rows, error_rate=0.0, output_path=str(output_path))
    
    with open(output_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            assert row["name"] != ""
            assert "@company.com" in row["email"]
            assert int(row["age"]) >= 22 and int(row["age"]) <= 65
            assert int(row["salary"]) >= 50000
            # Basic date format check
            try:
                datetime.strptime(row["hire_date"], "%Y-%m-%d")
            except ValueError:
                pytest.fail(f"Invalid date format: {row['hire_date']}")

def test_generate_robust_dataset_with_errors(tmp_path):
    """Verify that with 100% error rate, errors are injected as expected."""
    num_rows = 100
    error_rate = 1.0 
    output_path = tmp_path / "with_errors.csv"
    generate_robust_dataset(num_rows=num_rows, error_rate=error_rate, output_path=str(output_path))
    
    errors_found = False
    with open(output_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Check for any of the injected error patterns defined in generate_samples.py
            if (row["name"] == "" or 
                "@missingdomain" in row["email"] or 
                row["department"] == "InvalidDept" or 
                row["salary"] in ["-1000", "0", "Not a number"] or
                row["age"] in ["-5", "0", "150", ""]):
                errors_found = True
                break
            
            # Future hire date check
            hire_date = datetime.strptime(row["hire_date"], "%Y-%m-%d")
            if hire_date > datetime.now():
                errors_found = True
                break
    
    assert errors_found, "Should have found at least one injected error with 100% error rate"
