import duckdb
import pandas as pd
import os

db_path = "data/lab1_sales_performance.duckdb"
print(f"📍 Connecting to DuckDB at: {db_path}\n")

conn = duckdb.connect(db_path)

# Step 1: Check current state
print("=" * 50)
print("CURRENT STATE")
print("=" * 50)
schemas = conn.execute("""
    SELECT DISTINCT schema_name 
    FROM information_schema.schemata 
    ORDER BY schema_name;
""").fetchall()
print("📁 Schemas:", [s[0] for s in schemas])

tables = conn.execute("""
    SELECT table_name, table_schema
    FROM information_schema.tables
    WHERE table_schema NOT IN ('information_schema', 'pg_catalog')
    ORDER BY table_schema, table_name;
""").fetchall()
print("📊 Existing tables:", tables if tables else "None")

# Step 2: Check if CSV exists
print("\n" + "=" * 50)
print("DATA SOURCE CHECK")
print("=" * 50)
csv_path = "data/raw/sales_data.csv"
if os.path.exists(csv_path):
    print(f"✅ CSV file found at: {csv_path}")
    print(f"   File size: {os.path.getsize(csv_path)} bytes")
    
    # Preview CSV
    try:
        df = pd.read_csv(csv_path)
        print(f"   Shape: {df.shape}")
        print(f"   Columns: {df.columns.tolist()}")
        print("\n   First 3 rows:")
        print(df.head(3))
    except Exception as e:
        print(f"   ⚠️ Error reading CSV: {e}")
else:
    print(f"❌ CSV file NOT found at: {csv_path}")

# Step 3: Create schema and ingest data
print("\n" + "=" * 50)
print("INGESTING DATA")
print("=" * 50)

try:
    # Create raw schema if it doesn't exist
    conn.execute("CREATE SCHEMA IF NOT EXISTS raw;")
    print("✅ Created 'raw' schema")
    
    # Read CSV and create table
    if os.path.exists(csv_path):
        sales_df = pd.read_csv(csv_path)
        
        # Create table from CSV
        conn.execute(f"""
            CREATE OR REPLACE TABLE raw.sales_data AS
            SELECT * FROM read_csv_auto('{csv_path}');
        """)
        print(f"✅ Created raw.sales_data table with {len(sales_df)} rows")
        
        # Verify
        result = conn.execute("SELECT COUNT(*) FROM raw.sales_data;").fetchall()
        print(f"   Verification: {result[0][0]} rows in raw.sales_data")
    else:
        print("❌ Cannot ingest - CSV file not found")

except Exception as e:
    print(f"❌ Error during ingestion: {e}")

# Step 4: Final verification
print("\n" + "=" * 50)
print("FINAL STATE")
print("=" * 50)
schemas = conn.execute("""
    SELECT DISTINCT schema_name 
    FROM information_schema.schemata 
    WHERE schema_name NOT IN ('information_schema', 'pg_catalog')
    ORDER BY schema_name;
""").fetchall()
print("📁 Schemas:", [s[0] for s in schemas])

tables = conn.execute("""
    SELECT table_schema, table_name
    FROM information_schema.tables
    WHERE table_schema NOT IN ('information_schema', 'pg_catalog')
    ORDER BY table_schema, table_name;
""").fetchall()
if tables:
    for schema, table in tables:
        count = conn.execute(f"SELECT COUNT(*) FROM {schema}.{table};").fetchall()[0][0]
        print(f"  {schema}.{table} ({count} rows)")
else:
    print("  No tables found")

try:
    df_sample = conn.execute("SELECT * FROM raw.sales_data LIMIT 3;").fetchdf()
    print("\n📊 Sample data:")
    print(df_sample)
except Exception as e:
    print(f"\n⚠️ Cannot fetch sample: {e}")

conn.close()
print("\n✅ Done!")