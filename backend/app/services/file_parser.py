"""File parsing service - IMPLEMENTED."""

import pandas as pd


def parse_csv(file_path: str) -> dict:
    """Parse a CSV file and return metadata.
    
    Args:
        file_path: Absolute path to the CSV file
        
    Returns:
        Dictionary containing:
        - dataframe: pandas DataFrame
        - row_count: number of rows
        - column_count: number of columns
        - column_names: list of column names
        - dtypes: dict mapping column names to data types
        
    Raises:
        pd.errors.EmptyDataError: If file is empty
        pd.errors.ParserError: If CSV is malformed
        ValueError: If file format is invalid
    """
    df = pd.read_csv(file_path)
    
    # Validate DataFrame has data
    if df.empty:
        raise pd.errors.EmptyDataError("CSV file contains no data rows")
    
    # Validate DataFrame has columns
    if len(df.columns) == 0:
        raise ValueError("CSV file contains no columns")
    
    return {
        "dataframe": df,
        "row_count": len(df),
        "column_count": len(df.columns),
        "column_names": list(df.columns),
        "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
    }


def parse_json(file_path: str) -> dict:
    """Parse a JSON file and return metadata.
    
    Args:
        file_path: Absolute path to the JSON file
        
    Returns:
        Dictionary containing:
        - dataframe: pandas DataFrame
        - row_count: number of rows
        - column_count: number of columns
        - column_names: list of column names
        - dtypes: dict mapping column names to data types
        
    Raises:
        ValueError: If JSON format is invalid or file is empty
    """
    df = pd.read_json(file_path)
    
    # Validate DataFrame has data
    if df.empty:
        raise ValueError("JSON file contains no data rows")
    
    # Validate DataFrame has columns
    if len(df.columns) == 0:
        raise ValueError("JSON file contains no columns")
    
    return {
        "dataframe": df,
        "row_count": len(df),
        "column_count": len(df.columns),
        "column_names": list(df.columns),
        "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
    }
