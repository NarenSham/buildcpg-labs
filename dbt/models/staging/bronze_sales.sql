-- Bronze: read raw CSV with DuckDB's read_csv_auto
SELECT * FROM read_csv_auto('../data/raw/sales_2025_09.csv')  -- dbt-duckdb supports read_csv_auto
