"""
Lab1: Inspect data quality
Uses shared DataInspector utility
"""
import sys
from pathlib import Path

# Add root to path so we can import shared/
lab_root = Path(__file__).parent.parent
project_root = lab_root.parent
sys.path.insert(0, str(project_root))

print(f"DEBUG: lab_root = {lab_root}")
print(f"DEBUG: project_root = {project_root}")
print(f"DEBUG: sys.path[0] = {sys.path[0]}")


from shared.utils.data_inspector import DataInspector
from shared.config.paths import get_lab_db_path

def main():
    # Get lab1's database path from config
    db_path = lab_root / 'data' / 'lab1_sales_performance.duckdb'
    
    print(f"Inspecting: {db_path}\n")
    
    # Create inspector for lab1's database
    inspector = DataInspector(str(db_path))
    
    # Get all schemas
    schemas = inspector.get_all_schemas()
    print(f"Schemas: {schemas}")
    
    # For each schema, list tables
    for schema in schemas:
        tables = inspector.get_tables_by_schema(schema)
        print(f"\nSchema '{schema}' tables: {tables}")
        
        # Get stats for each table
        for table in tables:
            stats = inspector.get_table_stats(schema, table)
            print(f"  {table}: {stats['rows']} rows, {stats['cols']} columns")
            
            # Check quality
            try:
                quality = inspector.get_quality_score(schema, table, key_column='order_id')
                print(f"    Quality score: {quality}%")
            except:
                pass
    
    inspector.close()

if __name__ == "__main__":
    main()