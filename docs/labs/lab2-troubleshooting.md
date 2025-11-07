# Lab 2: Troubleshooting Guide

Common issues and solutions for the Market Sentiment Analysis pipeline.

## Table of Contents

1. [API Issues](#api-issues)
2. [Database Issues](#database-issues)
3. [dbt Issues](#dbt-issues)
4. [Dashboard Issues](#dashboard-issues)
5. [GitHub Actions Issues](#github-actions-issues)
6. [Performance Issues](#performance-issues)
7. [Data Quality Issues](#data-quality-issues)

---

## API Issues

### Reddit API: 401 Unauthorized

**Symptoms**:
```
prawcore.exceptions.ResponseException: received 401 HTTP response
```

**Causes**:
- Invalid credentials
- Credentials not loaded from `.env`

**Solutions**:

```bash
# 1. Verify .env file exists and has correct values
cat .env | grep REDDIT

# 2. Test credentials directly
python << 'EOF'
import praw
import os
from dotenv import load_dotenv

load_dotenv()

reddit = praw.Reddit(
    client_id=os.getenv('REDDIT_CLIENT_ID'),
    client_secret=os.getenv('REDDIT_CLIENT_SECRET'),
    user_agent=os.getenv('REDDIT_USER_AGENT')
)

print(f"Read only: {reddit.read_only}")  # Should be True
print("✅ Credentials valid")
EOF

# 3. If still failing, regenerate credentials at:
# https://www.reddit.com/prefs/apps
```

### Reddit API: 429 Too Many Requests

**Symptoms**:
```
prawcore.exceptions.TooManyRequests: received 429 HTTP response
```

**Causes**:
- Exceeded rate limit (60 requests per minute)

**Solutions**:

```python
# Option 1: Reduce requests in ingest_real_data.py
LIMIT_PER_BRAND = 10  # Instead of 20

# Option 2: Add delays between requests
import time
for brand in BRANDS:
    # ... fetch logic ...
    time.sleep(1)  # 1 second delay

# Option 3: Use PRAW's built-in rate limiting (automatic)
# PRAW handles this by default, but you can be explicit:
reddit = praw.Reddit(
    client_id=os.getenv('REDDIT_CLIENT_ID'),
    client_secret=os.getenv('REDDIT_CLIENT_SECRET'),
    user_agent=os.getenv('REDDIT_USER_AGENT'),
    ratelimit_seconds=600  # Wait 10 min if rate limited
)
```

### News API: 426 Upgrade Required

**Symptoms**:
```
newsapi.newsapi_exception.NewsAPIException: 426 - Upgrade Required
```

**Causes**:
- Exceeded free tier limit (100 requests/day)
- Trying to access articles older than 30 days

**Solutions**:

```python
# Option 1: Reduce requests per brand
articles_per_brand = 10  # Instead of 20

# Option 2: Only ingest on certain days
from datetime import datetime
if datetime.utcnow().weekday() == 6:  # Only on Sundays
    ingest_news_data()

# Option 3: Upgrade to paid plan
# See: https://newsapi.org/pricing
```

### News API: No Results Found

**Symptoms**:
- API returns successfully but `articles` list is empty

**Causes**:
- Search query too specific
- Date range has no matching articles
- Language filter too restrictive

**Solutions**:

```python
# 1. Broaden search query
q = brand  # Instead of f"{brand} AND (product OR launch)"

# 2. Increase date range
from_date = (datetime.utcnow() - timedelta(days=30)).strftime('%Y-%m-%d')

# 3. Add debug logging
response = newsapi.get_everything(q=brand, from_param=from_date, language='en')
logger.info(f"Articles found for {brand}: {len(response.get('articles', []))}")
if len(response.get('articles', [])) == 0:
    logger.warning(f"No articles for {brand} - try adjusting search")
```

---

## Database Issues

### DuckDB: File Locked Error

**Symptoms**:
```
IO Error: Could not set lock on file "lab2_market_sentiment.duckdb": Resource temporarily unavailable
```

**Causes**:
- Another process has the database open
- Stale lock file from crashed process

**Solutions**:

```bash
# 1. Close all connections
# - Stop Streamlit dashboard
# - Stop any Python scripts
# - Close any database clients

# 2. Remove lock file
rm data/lab2_market_sentiment.duckdb.wal

# 3. If issue persists, find and kill process
lsof data/lab2_market_sentiment.duckdb
# Then: kill -9 <PID>

# 4. Last resort: Create new database
cd dbt
dbt build --profiles-dir . --full-refresh
```

### DuckDB: Out of Memory

**Symptoms**:
```
Error: Out of Memory Error: failed to allocate data of size X
```

**Causes**:
- Dataset too large for available RAM
- Memory leak in query

**Solutions**:

```python
# 1. Set memory limits in connection
import duckdb
conn = duckdb.connect('data/lab2_market_sentiment.duckdb')
conn.execute("SET memory_limit='2GB';")
conn.execute("SET max_memory='2GB';")

# 2. Process data in chunks
chunk_size = 1000
for offset in range(0, total_rows, chunk_size):
    df = conn.execute(f"SELECT * FROM table LIMIT {chunk_size} OFFSET {offset}").df()
    # Process chunk...

# 3. Use streaming in Streamlit
@st.cache_data(ttl=300)
def load_data_chunked():
    return conn.execute("SELECT * FROM table LIMIT 10000").df()
```

### DuckDB: Corrupt Database

**Symptoms**:
```
Catalog Error: Table with name X does not exist
```
OR tables missing after successful dbt run

**Solutions**:

```bash
# 1. Backup existing database (if partially working)
cp data/lab2_market_sentiment.duckdb data/lab2_market_sentiment.duckdb.backup

# 2. Full refresh rebuild
cd dbt
dbt clean
dbt deps
dbt build --profiles-dir . --full-refresh

# 3. If still failing, delete and recreate
rm data/lab2_market_sentiment.duckdb*
dbt build --profiles-dir . --full-refresh

# 4. Restore from GitHub Actions artifact (if available)
# Download artifact from successful workflow run
unzip duckdb-database.zip
mv lab2_market_sentiment.duckdb data/
```

---

## dbt Issues

### dbt: Compilation Error - Column Not Found

**Symptoms**:
```
Compilation Error in model X
  column "Y" does not exist
```

**Causes**:
- Upstream model changed schema
- Typo in column name
- Missing column in raw data

**Solutions**:

```bash
# 1. Check upstream model output
dbt run --select int_sentiment_unified --profiles-dir .
dbt show --select int_sentiment_unified --profiles-dir .

# 2. Verify raw data has expected columns
python << 'EOF'
import pandas as pd
df = pd.read_csv('data/raw/reddit_brands.csv')
print("Columns:", df.columns.tolist())
EOF

# 3. Fix column reference in SQL
# Check schema.yml for correct column names

# 4. Full refresh if schema changed
dbt build --select +model_name+ --profiles-dir . --full-refresh
```

### dbt: Test Failed - Uniqueness Violation

**Symptoms**:
```
Failure in test unique_sentiment_event_id (models/schema.yml)
  Got 5 results, configured to fail if != 0
```

**Causes**:
- Duplicate data in source files
- Surrogate key generation not unique enough
- Incremental logic issue

**Solutions**:

```bash
# 1. Identify duplicates
cd dbt
dbt test --select fct_sentiment_events --store-failures

# 2. Query failed test results
python << 'EOF'
import duckdb
conn = duckdb.connect('data/lab2_market_sentiment.duckdb')
dupes = conn.execute("""
    SELECT sentiment_event_id, COUNT(*) as cnt
    FROM fct_sentiment_events
    GROUP BY sentiment_event_id
    HAVING COUNT(*) > 1
""").df()
print(dupes)
EOF

# 3. Fix surrogate key generation
# Add more fields to make unique: row_num, ingested_at, etc.

# 4. Full refresh to clear duplicates
dbt run --select fct_sentiment_events --profiles-dir . --full-refresh
```

### dbt: Package Not Found

**Symptoms**:
```
Package dbt_expectations not found
```

**Causes**:
- `dbt_packages/` directory missing
- Package not installed

**Solutions**:

```bash
cd dbt

# 1. Install packages
dbt deps

# 2. Verify packages installed
ls dbt_packages/

# Should see:
# - dbt_expectations/
# - dbt_utils/
# etc.

# 3. If deps fails, check packages.yml
cat packages.yml

# 4. Try clean install
rm -rf dbt_packages/
dbt deps
```

### dbt: Incremental Model Not Updating

**Symptoms**:
- New data ingested but mart tables don't update

**Causes**:
- Incremental logic filtering out new data
- Missing `--full-refresh` after schema change

**Solutions**:

```bash
# 1. Check incremental logic
# Look for WHERE clause in model

# 2. Force full refresh
dbt run --select model_name --profiles-dir . --full-refresh

# 3. Check max date in table
python << 'EOF'
import duckdb
conn = duckdb.connect('data/lab2_market_sentiment.duckdb')
max_date = conn.execute("SELECT MAX(published_at) FROM fct_sentiment_events").fetchone()[0]
print(f"Max date in table: {max_date}")
EOF

# 4. Verify new data exists in raw files
head -n 5 data/raw/reddit_brands.csv
```

---

## Dashboard Issues

### Streamlit: Port Already in Use

**Symptoms**:
```
OSError: [Errno 48] Address already in use
```

**Solutions**:

```bash
# Option 1: Use different port
streamlit run app/streamlit_app.py --server.port 8502

# Option 2: Kill process using port 8501
lsof -ti:8501 | xargs kill -9

# Option 3: Find and kill specific process
ps aux | grep streamlit
kill -9 <PID>
```

### Streamlit: No Data Showing

**Symptoms**:
- Dashboard loads but shows "No data found" or empty charts

**Causes**:
- Database empty or missing tables
- Database path incorrect
- Caching issue

**Solutions**:

```python
# 1. Verify database path in streamlit_app.py
DB_PATH = Path(__file__).parent.parent / "data" / "lab2_market_sentiment.duckdb"
print(f"Looking for DB at: {DB_PATH}")
print(f"DB exists: {DB_PATH.exists()}")

# 2. Check table exists
import duckdb
conn = duckdb.connect(str(DB_PATH))
tables = conn.execute("SHOW TABLES").fetchall()
print("Tables:", tables)

# 3. Clear Streamlit cache
# In browser: C (clear cache)
# Or add to code:
st.cache_data.clear()

# 4. Verify data in database
count = conn.execute("SELECT COUNT(*) FROM fct_sentiment_events").fetchone()[0]
print(f"Events count: {count}")
```

### Streamlit: Slow Performance

**Symptoms**:
- Dashboard takes 10+ seconds to load
- Filters lag when updating

**Solutions**:

```python
# 1. Increase cache TTL
@st.cache_data(ttl=600)  # 10 minutes instead of 5
def load_data():
    # ...

# 2. Limit data loaded
def load_data():
    # Only load last 90 days
    query = """
        SELECT * FROM fct_sentiment_events
        WHERE published_at >= CURRENT_DATE - INTERVAL '90 days'
    """
    return conn.execute(query).df()

# 3. Use aggregated data for charts
def load_daily_data():
    # Use mart_daily_sentiment instead of fact table
    return conn.execute("SELECT * FROM mart_daily_sentiment").df()

# 4. Add pagination to tables
df_display = df.head(100)  # Only show first 100 rows
```

### Streamlit: Module Not Found

**Symptoms**:
```
ModuleNotFoundError: No module named 'plotly'
```

**Solutions**:

```bash
# 1. Verify virtual environment is activated
which python
# Should show venv/bin/python

# 2. Install missing module
pip install plotly

# 3. Or reinstall all requirements
pip install -r requirements.txt --upgrade

# 4. Check installed packages
pip list | grep plotly
```

---

## GitHub Actions Issues

### Workflow: Failing on Dependency Installation

**Symptoms**:
```
ERROR: Could not find a version that satisfies the requirement X
```

**Solutions**:

```yaml
# 1. Update actions versions in workflow
- uses: actions/checkout@v4  # Not v3
- uses: actions/setup-python@v5  # Not v4

# 2. Pin Python version
python-version: '3.11'  # Explicit version

# 3. Upgrade pip before installing
- name: Install dependencies
  run: |
    python -m pip install --upgrade pip
    pip install -r requirements.txt

# 4. Add system dependencies if needed (for ARM/M1)
- name: Install dependencies
  run: |
    brew install gcc  # macOS only
    pip install -r requirements.txt
```

### Workflow: Secrets Not Found

**Symptoms**:
```
Error: REDDIT_CLIENT_ID not set
```

**Solutions**:

1. **Add secrets to repository**:
   - Go to Settings → Secrets and variables → Actions
   - Click "New repository secret"
   - Add each secret

2. **Verify secret names match**:
   ```yaml
   env:
     REDDIT_CLIENT_ID: ${{ secrets.REDDIT_CLIENT_ID }}
     # Make sure secret name matches exactly
   ```

3. **Check secret values**:
   - No quotes around values in GitHub UI
   - No trailing spaces
   - Copy-paste carefully

### Workflow: dbt Build Fails

**Symptoms**:
```
dbt: command not found
```
OR
```
Could not find profile named 'lab2_market_sentiment'
```

**Solutions**:

```yaml
# 1. Ensure dbt is in requirements.txt
# Already should be:
# dbt-core==1.7.0
# dbt-duckdb==1.7.0

# 2. Fix dbt command
run: |
  cd dbt
  dbt deps  # Install packages first
  dbt build --profiles-dir .

# 3. Verify profiles.yml exists
# Should be in dbt/ directory

# 4. Use absolute path if needed
run: |
  cd dbt
  python -m dbt build --profiles-dir .
```

### Workflow: Timeout

**Symptoms**:
```
The job was canceled because it exceeded the maximum execution time
```

**Solutions**:

```yaml
# 1. Increase job timeout (default is 360 minutes)
jobs:
  run-pipeline:
    runs-on: ubuntu-latest
    timeout-minutes: 60  # 1 hour

# 2. Reduce data ingested
# In ingest_real_data.py:
limit_per_brand = 10  # Instead of 20

# 3. Add timeout to individual steps
- name: Run pipeline
  timeout-minutes: 30
  run: python orchestrate_weekly.py
```

---

## Performance Issues

### Ingestion: Taking Too Long

**Symptoms**:
- Ingestion script runs for 20+ minutes

**Solutions**:

```python
# 1. Reduce posts per brand
limit_per_brand = 10  # Default was 20

# 2. Use concurrent requests (careful with rate limits)
from concurrent.futures import ThreadPoolExecutor

def fetch_brand(brand):
    # ... fetch logic ...

with ThreadPoolExecutor(max_workers=3) as executor:
    results = list(executor.map(fetch_brand, BRANDS))

# 3. Skip already-ingested data
existing_ids = set(pd.read_csv('data/raw/reddit_brands.csv')['post_id'])
if post.id not in existing_ids:
    # Process...

# 4. Limit time filter
subreddit.search(brand, limit=20, time_filter='week')  # Not 'month'
```

### dbt: Slow Build Times

**Symptoms**:
- `dbt build` takes 5+ minutes

**Solutions**:

```bash
# 1. Run only changed models
dbt build --select state:modified+ --profiles-dir .

# 2. Use threads
dbt build --profiles-dir . --threads 4

# 3. Skip tests during development
dbt run --profiles-dir .  # No tests

# 4. Profile slow models
dbt run --select model_name --profiles-dir . --debug

# Look for slow SQL operations in logs
```

### Query: Slow Dashboard Queries

**Symptoms**:
- Streamlit charts take 5+ seconds to render

**Solutions**:

```python
# 1. Add indexes (DuckDB automatically optimizes, but explicit helps)
conn.execute("CREATE INDEX IF NOT EXISTS idx_brand ON fct_sentiment_events(brand)")
conn.execute("CREATE INDEX IF NOT EXISTS idx_date ON fct_sentiment_events(published_at)")

# 2. Use aggregated marts
# Instead of querying fact table, use mart_daily_sentiment

# 3. Filter data early
query = """
    SELECT * FROM fct_sentiment_events
    WHERE published_at >= CURRENT_DATE - INTERVAL '30 days'
      AND brand IN ('Coca-Cola', 'PepsiCo')
"""

# 4. Use columnar selection
query = """
    SELECT brand, sentiment_score, published_at  -- Only needed columns
    FROM fct_sentiment_events
    WHERE ...
"""
```

---

## Data Quality Issues

### Issue: Sentiment Scores Out of Range

**Symptoms**:
- Test failure: `sentiment_score` not between -1 and 1

**Solutions**:

```python
# 1. Check VADER output
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
analyzer = SentimentIntensityAnalyzer()
scores = analyzer.polarity_scores("This is terrible!")
print(scores)  # compound should be -1 to 1

# 2. Add normalization in staging
ROUND(
    CASE 
        WHEN sentiment_score > 1 THEN 1.0
        WHEN sentiment_score < -1 THEN -1.0
        ELSE sentiment_score
    END,
    3
) as sentiment_score

# 3. Add validation in Python
def normalize_sentiment(score):
    return max(-1.0, min(1.0, score))
```

### Issue: Missing Brand Data

**Symptoms**:
- Some brands have 0 mentions
- Competitive analysis incomplete

**Solutions**:

```python
# 1. Check if brand in taxonomy
with open('shared/config/brand_taxonomy.yaml') as f:
    taxonomy = yaml.safe_load(f)
# Verify brand listed

# 2. Check if brand detection working
text = "I love Coca-Cola"
mentioned = detect_brand_mentions(text, brands_list)
print(f"Detected: {mentioned}")

# 3. Add brand aliases
# In taxonomy:
brands:
  - name: "Coca-Cola"
    aliases: ["Coke", "Coca Cola", "CocaCola"]

# 4. Check API search results
# Reddit: Is brand term too specific?
# News: Adjust search query
```

### Issue: Duplicate Sentiment Events

**Symptoms**:
- Test failure: Multiple rows with same `sentiment_event_id`

**Solutions**:

```sql
-- 1. Identify duplicates
SELECT sentiment_event_id, COUNT(*) as cnt
FROM fct_sentiment_events
GROUP BY sentiment_event_id
HAVING COUNT(*) > 1;

-- 2. Enhance surrogate key uniqueness
{{ generate_surrogate_key([
    'content_id', 
    'published_at', 
    'row_num',  -- Add this
    'ingested_at'  -- And this if needed
]) }}

-- 3. Add deduplication CTE
WITH deduped AS (
    SELECT *,
        ROW_NUMBER() OVER (
            PARTITION BY sentiment_event_id
            ORDER BY ingested_at DESC
        ) as rn
    FROM base_data
)
SELECT * FROM deduped WHERE rn = 1
```

### Issue: Anomalies Not Detected

**Symptoms**:
- No anomalies flagged despite obvious sentiment spikes

**Solutions**:

```sql
-- 1. Check z-score calculation
SELECT 
    sentiment_date,
    brand,
    avg_sentiment,
    AVG(avg_sentiment) OVER (PARTITION BY brand) as brand_avg,
    STDDEV(avg_sentiment) OVER (PARTITION BY brand) as brand_stddev,
    z_score_sentiment,
    anomaly_flag
FROM mart_daily_sentiment
WHERE brand = 'Coca-Cola'
ORDER BY sentiment_date DESC;

-- 2. Adjust threshold
-- In mart_daily_sentiment.sql:
CASE 
    WHEN ABS(z_score) > 1.5  -- Less strict (was 2)
    THEN 'ANOMALY'
    ELSE 'NORMAL'
END

-- 3. Ensure enough historical data
-- Need 30+ days for meaningful stddev
```

---

## Getting More Help

If issues persist:

1. **Check Logs**:
   ```bash
   # Ingestion logs
   python pipelines/ingest_real_data.py 2>&1 | tee ingestion.log
   
   # dbt logs
   cat dbt/logs/dbt.log
   
   # Streamlit logs
   # Check terminal where streamlit is running
   ```

2. **Enable Debug Mode**:
   ```bash
   # dbt debug mode
   dbt run --select model_name --profiles-dir . --debug
   
   # Python debug logging
   import logging
   logging.basicConfig(level=logging.DEBUG)
   ```

3. **Contact Support**:
   - GitHub Issues: [repository]/issues
   - Email: narensham@example.com
   - Include: error message, logs, steps to reproduce

---

**Last Updated**: November 2025  
**Maintainer**: narensham