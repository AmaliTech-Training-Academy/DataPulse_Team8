import os
import sys
import csv
import pytest
from unittest.mock import patch, MagicMock

# Add scripts directory to path to import generate_production_data
scripts_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../scripts'))
if scripts_dir not in sys.path:
    sys.path.insert(0, scripts_dir)

import generate_production_data

# Ensure fake is initialized for worker testing
@pytest.fixture(autouse=True)
def init_faker_fixture():
    generate_production_data.init_worker()

def test_generate_row_batch_all_clean():
    # start_id=1, batch_size=10, error_rate=0.0
    batch = generate_production_data.generate_row_batch((1, 10, 0.0))
    
    assert len(batch) == 10
    for i, row in enumerate(batch):
        assert row[0] == i + 1  # id
        assert row[1] != ""     # name
        assert "@" in row[2]    # email
        assert isinstance(row[3], int) # age
        assert row[4] in generate_production_data.DEPARTMENTS # dept
        assert isinstance(row[5], int) # salary
        assert "-" in row[6]    # hire_date

def test_generate_row_batch_all_errors():
    # start_id=100, batch_size=50, error_rate=1.0
    batch = generate_production_data.generate_row_batch((100, 50, 1.0))
    
    assert len(batch) == 50
    error_count = 0
    for i, row in enumerate(batch):
        assert row[0] == 100 + i
        
        has_error = False
        if row[1] == "":
            has_error = True
        elif "@missingdomain" in row[2]:
            has_error = True
        elif row[3] == "" or row[3] in [-5, 0, 150]:
            has_error = True
        elif row[4] == "InvalidDept":
            has_error = True
        elif row[5] in [-1000, 0, "Not a number"]:
            has_error = True
        else:
            # Assume future hire date
            has_error = True
            
        if has_error:
            error_count += 1
            
    assert error_count == 50

def test_generate_production_dataset_integration(tmp_path):
    output_file = tmp_path / "prod_test.csv"
    
    # We run full generation for a tiny payload to avoid actual heavy lifting but traverse the parallel code
    generate_production_data.generate_production_dataset(
        total_rows=15, 
        error_rate=0.2, 
        output_path=str(output_file), 
        workers=2, 
        chunk_size=5
    )
    
    assert output_file.exists()
    
    with open(output_file, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        header = next(reader)
        assert header == generate_production_data.CSV_HEADER
        
        rows = list(reader)
        assert len(rows) == 15
        assert int(rows[0][0]) == 1
        assert int(rows[-1][0]) == 15

@patch('generate_production_data.generate_production_dataset')
def test_main_preset(mock_generator):
    with patch('sys.argv', ['generate_production_data.py', '--preset']):
        generate_production_data.main()
        
    # The preset is called 3 times (good, mixed, messy)
    assert mock_generator.call_count == 3
