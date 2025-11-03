import duckdb

conn = duckdb.connect('/Users/narensham/Documents/Projects/Cursor/buildcpg-labs/lab2_market_sentiment/data/lab2_market_sentiment.duckdb')

query = """
SELECT 
    content_id,
    published_at,
    brand,
    source,
    COUNT(*) as dup_count
FROM main.sentiment_unified
GROUP BY content_id, published_at, brand, source
HAVING COUNT(*) > 1
ORDER BY dup_count DESC
LIMIT 20
"""

results = conn.execute(query).fetchall()

print("\n=== DUPLICATES FOUND ===")
for row in results:
    print(f"ID: {row[0]} | Published: {row[1]} | Brand: {row[2]} | Source: {row[3]} | Count: {row[4]}")

conn.close()