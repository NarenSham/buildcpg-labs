"""
Lab1: Check if new data was added to CSV
Uses shared CSVMonitor utility
"""
import sys
from pathlib import Path

# Add root to path
lab_root = Path(__file__).parent.parent
project_root = lab_root.parent
sys.path.insert(0, str(project_root))

from shared.utils.csv_monitor import CSVMonitor
from shared.config.paths import get_lab_raw_data_path, get_lab_config

def main():
    # Get lab1 config
    config = get_lab_config('lab1_sales_performance')
    lab_path = Path(__file__).parent.parent
    
    # Create monitor with lab1-specific state file
    monitor = CSVMonitor(str(lab_path / '.csv_state.json'))
    
    # Check for CSV updates
    csv_file = lab_path / 'data' / 'raw' / 'sales_data.csv'
    
    print(f"Checking: {csv_file}")
    has_changed, new_rows, size = monitor.check_csv(str(csv_file))
    
    if has_changed:
        print(f"✅ CSV updated!")
        print(f"   New rows: {new_rows}")
        print(f"   Total size: {size} bytes")
        return True
    else:
        print("No new data detected")
        return False

if __name__ == "__main__":
    should_run_pipeline = main()
    sys.exit(0 if should_run_pipeline else 1)