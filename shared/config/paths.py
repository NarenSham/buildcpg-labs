"""
Path helper: Centralized way to get paths for any lab
"""
import yaml
from pathlib import Path


ROOT = Path(__file__).parent.parent


def load_labs_config():
    """Load the labs configuration"""
    with open(ROOT / 'config' / 'labs_config.yaml') as f:
        return yaml.safe_load(f)


def get_lab_config(lab_name):
    """Get configuration for a specific lab"""
    config = load_labs_config()
    if lab_name not in config['labs']:
        raise ValueError(f"Lab '{lab_name}' not found in config")
    return config['labs'][lab_name]


def get_lab_path(lab_name):
    """Get root path of a lab"""
    cfg = get_lab_config(lab_name)
    return ROOT / cfg['path']


def get_lab_db_path(lab_name):
    """Get DuckDB database path for a lab"""
    cfg = get_lab_config(lab_name)
    return ROOT / cfg['db_path']


def get_lab_dbt_path(lab_name):
    """Get dbt project path for a lab"""
    cfg = get_lab_config(lab_name)
    return ROOT / cfg['dbt_path']


def get_lab_raw_data_path(lab_name):
    """Get raw data path for a lab"""
    cfg = get_lab_config(lab_name)
    return ROOT / cfg['raw_data_path']


# Example usage:
if __name__ == "__main__":
    # Get config for lab1
    config = get_lab_config('lab1_sales_performance')
    print("Lab1 config:", config)
    
    # Get specific paths
    db_path = get_lab_db_path('lab1_sales_performance')
    print("Lab1 DB:", db_path)