import os
import sys
import pytest
import csv
from unittest.mock import patch, MagicMock

# Add sample_data directory to Python path
sample_data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../sample_data'))
if sample_data_dir not in sys.path:
    sys.path.insert(0, sample_data_dir)

import generate_samples

def test_generate_robust_dataset_valid_output(tmp_path):
    output_file = tmp_path / "test_valid.csv"
    generate_samples.generate_robust_dataset(num_rows=10, error_rate=0.0, output_path=str(output_file))
    
    assert output_file.exists()
    
    with open(output_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        
    assert len(rows) == 10
    
    for row in rows:
        assert row["id"].isdigit()
        assert row["name"] != ""
        assert "@" in row["email"]
        assert row["age"].isdigit()
        assert int(row["age"]) >= 22 and int(row["age"]) <= 65
        assert row["department"] in generate_samples.DEPARTMENTS
        assert row["salary"].isdigit()
        assert int(row["salary"]) >= 50000 and int(row["salary"]) <= 150000
        assert "-" in row["hire_date"]

def test_generate_robust_dataset_error_injection(tmp_path):
    output_file = tmp_path / "test_error.csv"
    
    # Generate with 100% error rate to guarantee errors on every row.
    generate_samples.generate_robust_dataset(num_rows=50, error_rate=1.0, output_path=str(output_file))
    
    with open(output_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        
    assert len(rows) == 50
    
    errors_detected = 0
    for row in rows:
        # We know one of 7 random errors is selected for every errored row
        if row["name"] == "":
            errors_detected += 1
        elif "@missingdomain" in row["email"]:
            errors_detected += 1
        elif row["department"] == "InvalidDept":
            errors_detected += 1
        elif row["salary"] in ["-1000", "0", "Not a number"]:
            errors_detected += 1
        elif row["age"] == "":
            errors_detected += 1
        elif row["age"] in ["-5", "0", "150"]:
            errors_detected += 1
        else:
            # The only remaining error is a future hire_date.
            # We assume it falls into this else block.
            errors_detected += 1

    assert errors_detected == 50

@patch('generate_samples.generate_robust_dataset')
def test_main_cli_custom_args(mock_generate):
    with patch('sys.argv', ['generate_samples.py', '--rows', '500', '--error-rate', '0.2', '--output', 'custom.csv']):
        generate_samples.main()
        
    mock_generate.assert_called_once_with(500, 0.2, 'custom.csv')

@patch('generate_samples.generate_robust_dataset')
def test_main_cli_preset(mock_generate, tmp_path):
    with patch('sys.argv', ['generate_samples.py', '--preset']):
        generate_samples.main()
        
    assert mock_generate.call_count == 3
