import duckdb
from pathlib import Path
from tabulate import tabulate  # optional, for pretty printing

# Database path
DB_PATH = Path("/Users/narensham/Documents/Projects/Cursor/buildcpg-labs/lab2_market_sentiment/data/lab2_market_sentiment.duckdb")

# Connect to DuckDB
conn = duckdb.connect(str(DB_PATH))

# Get all tables
tables = conn.execute("SHOW TABLES").fetchall()
table_names = [t[0] for t in tables]

print(f"\nDatabase: {DB_PATH}\n")
print(f"Found {len(table_names)} tables: {', '.join(table_names)}\n")

for table in table_names:
    print("="*80)
    print(f"Table: {table}")
    print("-"*80)
    
    # Get column names
    columns = [desc[0] for desc in conn.execute(f"SELECT * FROM {table} LIMIT 1").description]
    print("Columns:", ", ".join(columns))
    
    # Get first 10 rows
    rows = conn.execute(f"SELECT * FROM {table} LIMIT 10").fetchall()
    if rows:
        print(tabulate(rows, headers=columns, tablefmt="grid"))
    else:
        print("No rows found.")
    
    # Show total row count
    count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    print(f"Total rows: {count}\n")
