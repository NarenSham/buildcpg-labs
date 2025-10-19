import pandas as pd
import duckdb
import logging
import os

# Make sure logs folder exists
os.makedirs('../logs', exist_ok=True)

# Set up logging
logging.basicConfig(filename='../logs/lab1.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logging.info("Starting ingestion script...")

# Read raw CSV
df = pd.read_csv('../data/raw/sales_data.csv')
logging.info(f"Loaded {len(df)} rows from raw data")

# Connect to DuckDB and write bronze table
con = duckdb.connect('../data/processed/lab1.duckdb')
con.execute("CREATE TABLE IF NOT EXISTS bronze_sales AS SELECT * FROM df")
logging.info(f"Bronze table created with {len(df)} rows")
