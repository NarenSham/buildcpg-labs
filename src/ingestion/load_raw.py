import pandas as pd
import duckdb
from pathlib import Path

RAW_CSV = Path("data/raw/sales_2025_09.csv")
DB_PATH = Path("data/buildcpg.duckdb")

def load_raw_to_bronze():
    df_raw = pd.read_csv(RAW_CSV)
    con = duckdb.connect(DB_PATH)
    
    # create table if not exists
    con.execute("""
    CREATE TABLE IF NOT EXISTS bronze_sales AS
    SELECT * FROM df_raw
    LIMIT 0
    """)
    
    # insert data
    con.register("df_raw", df_raw)
    con.execute("INSERT INTO bronze_sales SELECT * FROM df_raw")
    con.close()
    print("✅ Raw data loaded into bronze_sales")

if __name__ == "__main__":
    load_raw_to_bronze()
