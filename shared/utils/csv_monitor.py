"""
CSV Monitor: Check if CSV files have been updated
Used by labs to detect when new data arrives
"""
import os
import json
from datetime import datetime
from pathlib import Path


class CSVMonitor:
    def __init__(self, state_file='.csv_state.json'):
        """Initialize monitor with state file location"""
        self.state_file = state_file
        self.state = self._load_state()
    
    def _load_state(self):
        """Load previous state from JSON file"""
        if os.path.exists(self.state_file):
            with open(self.state_file, 'r') as f:
                return json.load(f)
        return {}
    
    def _save_state(self):
        """Save current state to JSON file"""
        with open(self.state_file, 'w') as f:
            json.dump(self.state, f, indent=2)
    
    def check_csv(self, csv_path):
        """
        Check if CSV has been updated since last check
        Returns: (has_changed: bool, new_rows: int, file_size: int)
        """
        csv_path = str(csv_path)
        
        if not os.path.exists(csv_path):
            return False, 0, 0
        
        # Get current file stats
        current_size = os.path.getsize(csv_path)
        current_mtime = os.path.getmtime(csv_path)
        
        # Get previous stats
        if csv_path not in self.state:
            self.state[csv_path] = {
                'size': current_size,
                'mtime': current_mtime,
                'last_check': datetime.now().isoformat(),
                'row_count': self._count_rows(csv_path)
            }
            self._save_state()
            return True, self.state[csv_path]['row_count'], current_size
        
        previous_state = self.state[csv_path]
        previous_size = previous_state['size']
        previous_rows = previous_state.get('row_count', 0)
        
        # Check if file changed
        has_changed = current_size != previous_size
        
        if has_changed:
            current_rows = self._count_rows(csv_path)
            new_rows = max(0, current_rows - previous_rows)
            
            # Update state
            self.state[csv_path] = {
                'size': current_size,
                'mtime': current_mtime,
                'last_check': datetime.now().isoformat(),
                'row_count': current_rows
            }
            self._save_state()
            
            return True, new_rows, current_size
        
        return False, 0, current_size
    
    def _count_rows(self, csv_path):
        """Count rows in CSV file"""
        try:
            with open(csv_path, 'r') as f:
                return sum(1 for _ in f) - 1  # Subtract 1 for header
        except:
            return 0


# Example usage:
if __name__ == "__main__":
    monitor = CSVMonitor('lab1_sales_performance/.csv_state.json')
    has_changed, new_rows, size = monitor.check_csv('lab1_sales_performance/data/raw/sales_data.csv')
    print(f"CSV updated: {has_changed}, New rows: {new_rows}, Size: {size}")