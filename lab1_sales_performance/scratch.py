import duckdb

# Connect to the database file
con = duckdb.connect("lab1_sales_performance.db")

# Run queries
con.execute("SELECT * FROM raw.sales_data LIMIT 5").fetchall()