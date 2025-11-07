# Lab 2: Quick Reference

Quick reference for common tasks and commands in the Market Sentiment Analysis pipeline.

## Quick Start

```bash
# 1. Setup environment
python3.11 -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt

# 2. Configure API keys
cp .env.example .env
# Edit .env with your API keys

# 3. Run initial ingestion
python pipelines/ingest_real_data.py

# 4. Build dbt models
cd dbt && dbt build --profiles-dir .

# 5. Launch dashboard
streamlit run app/streamlit_app.py
```

## Common Commands

### Data Ingestion

```bash
# Full ingestion (Reddit + News)
python pipelines/ingest_real_data.py

# Test APIs only (no save)
python -c "from pipelines.ingest_real_data import *; test_apis()"

# Check raw data
ls -lh data/raw/
head -n 5 data/raw/reddit_brands.csv
```

### dbt Operations

```bash
cd dbt

# Build everything
dbt build --profiles-dir .

# Run only changed models
dbt build --select state:modified+ --profiles-dir .

# Run specific model and downstream
dbt run --select fct_sentiment_events+ --profiles-dir .

# Test everything
dbt test --profiles-dir .

# Test specific model
dbt test --select fct_sentiment_events --profiles-dir .

# Full refresh (rebuild from scratch)
dbt build --profiles-dir . --full-refresh

# Debug model
dbt compile --select model_name --profiles-dir .
cat target/compiled/lab2_market_sentiment/models/.../model_name.sql
```

### Dashboard

```bash
# Start dashboard
streamlit run app/streamlit_app.py

# Use custom port
streamlit run app/streamlit_app.py --server.port 8502

# Clear cache
# In browser: Press 'C' key
```

### Database Queries

```bash
# Connect to DuckDB
duckdb data/lab2_market_sentiment.duckdb

# Or use Python
python << 'EOF'
import duckdb
conn = duckdb.connect('data/lab2_market_sentiment.duckdb')

# Check tables
tables = conn.execute("SHOW TABLES").fetchall()
print(tables)

# Query data
df = conn.execute("SELECT * FROM fct_sentiment_events LIMIT 10").df()
print(df)

conn.close()
EOF
```

### GitHub Actions

```bash
# Trigger manual run
# Go to: Actions tab → Weekly Sentiment Pipeline → Run workflow

# Check workflow status
gh workflow view "Weekly Sentiment Pipeline"
gh run list --workflow="Weekly Sentiment Pipeline"

# Download artifact
gh run download <run-id> --name duckdb-database
```

## File Structure Reference

```
lab2_market_sentiment/
├── .env                          # API keys (gitignored)
├── requirements.txt              # Python dependencies
├── orchestrate_weekly.py         # Prefect orchestration
│
├── .github/
│   └── workflows/
│       └── weekly_pipeline.yml   # GitHub Actions
│
├── pipelines/
│   ├── ingest_real_data.py      # Main ingestion
│   └── ingest_brands.py          # Brand-aware ingestion
│
├── dbt/
│   ├── dbt_project.yml           # dbt config
│   ├── profiles.yml              # Database connection
│   ├── models/
│   │   ├── staging/              # Raw data cleaning
│   │   ├── intermediate/         # Business logic
│   │   ├── dimensions/           # Dimension tables
│   │   └── mart/                 # Analytics marts
│   └── schema.yml                # Tests & documentation
│
├── app/
│   ├── streamlit_app.py          # Main dashboard
│   └── pages/
│       └── Competitive_Intelligence.py
│
└── data/
    ├── raw/                      # CSV files from APIs
    ├── lab2_market_sentiment.duckdb  # Database
    └── cache/                    # API cache (optional)
```

## Environment Variables

```bash
# Reddit API
REDDIT_CLIENT_ID=your_client_id
REDDIT_CLIENT_SECRET=your_secret
REDDIT_USER_AGENT="CPG Sentiment Tracker v1.0"

# News API
NEWS_API_KEY=your_api_key
```

## dbt Model Relationships

```
Raw Data (CSV)
    ↓
stg_reddit__posts ─┐
stg_news__articles ┘
    ↓
int_sentiment_unified
    ↓
    ├─→ dim_brands
    ├─→ dim_sources
    ├─→ fct_sentiment_events
    ├─→ mart_daily_sentiment
    ├─→ mart_brand_competitive_analysis
    └─→ mart_trending_topics
```

## Key Metrics

### Event-Level (`fct_sentiment_events`)
- `sentiment_score`: -1 to 1
- `sentiment_category`: positive/neutral/negative
- `engagement_count`: upvotes/shares
- `published_at`: timestamp

### Daily Aggregates (`mart_daily_sentiment`)
- `avg_sentiment`: daily average
- `content_count`: posts per day
- `positive_ratio`: % positive
- `z_score_sentiment`: anomaly detection
- `anomaly_flag`: NORMAL/ANOMALY

### Competitive (`mart_brand_competitive_analysis`)
- `share_of_voice_pct`: % of total mentions
- `net_sentiment_score`: positive % - negative %
- `competitive_position`: MARKET_LEADER, NICHE_FAVORITE, etc.
- `momentum_pct`: 7d vs 30d growth

### Topics (`mart_trending_topics`)
- `trending_score`: combined metric
- `mention_count`: total mentions
- `trend_status`: HOT/TRENDING/STABLE/EMERGING
- `sentiment_tone`: POSITIVE_BUZZ/NEGATIVE_BUZZ/NEUTRAL

## SQL Queries Cheat Sheet

```sql
-- Check data freshness
SELECT MAX(published_at) as latest_data
FROM fct_sentiment_events;

-- Brand sentiment summary
SELECT 
    brand,
    COUNT(*) as mentions,
    ROUND(AVG(sentiment_score), 3) as avg_sentiment,
    COUNT(*) FILTER (WHERE sentiment_category = 'positive') as positive
FROM fct_sentiment_events
WHERE published_at >= CURRENT_DATE - INTERVAL '7 days'
GROUP BY brand
ORDER BY mentions DESC;

-- Anomaly detection
SELECT 
    sentiment_date,
    brand,
    avg_sentiment,
    z_score_sentiment
FROM mart_daily_sentiment
WHERE anomaly_flag = 'ANOMALY'
ORDER BY sentiment_date DESC;

-- Top trending topics
SELECT 
    brand,
    topic,
    trending_score,
    mention_count,
    sentiment_tone
FROM mart_trending_topics
WHERE trend_status IN ('HOT', 'TRENDING')
ORDER BY trending_score DESC
LIMIT 20;

-- Competitive positioning
SELECT 
    brand,
    parent_company,
    share_of_voice_pct,
    competitive_position,
    sentiment_vs_category
FROM mart_brand_competitive_analysis
ORDER BY share_of_voice_pct DESC;
```

## Troubleshooting Quick Fixes

```bash
# API rate limit errors
# → Reduce limit_per_brand in ingest_real_data.py

# DuckDB locked
rm data/lab2_market_sentiment.duckdb.wal

# dbt compilation errors
cd dbt && dbt clean && dbt deps && dbt build --profiles-dir .

# Streamlit port in use
streamlit run app/streamlit_app.py --server.port 8502

# Clear Streamlit cache
# Browser: Press 'C' key

# No data in dashboard
python pipelines/ingest_real_data.py
cd dbt && dbt build --profiles-dir . --full-refresh

# GitHub Actions secrets not working
# Settings → Secrets → Verify names match exactly

# Out of memory
# Edit dbt/profiles.yml:
# Add: threads: 2
# Reduce memory usage
```

## Testing Commands

```bash
# Test API connections
python -c "
import praw, os
from dotenv import load_dotenv
load_dotenv()
reddit = praw.Reddit(
    client_id=os.getenv('REDDIT_CLIENT_ID'),
    client_secret=os.getenv('REDDIT_CLIENT_SECRET'),
    user_agent=os.getenv('REDDIT_USER_AGENT')
)
print('✅ Reddit connected')
"

# Test dbt models
cd dbt
dbt run --select model_name --profiles-dir . --debug

# Run unit tests
python -m pytest tests/  # if tests exist

# Validate data
python << 'EOF'
import duckdb
conn = duckdb.connect('data/lab2_market_sentiment.duckdb')

# Check for nulls
nulls = conn.execute("""
    SELECT 
        COUNT(*) FILTER (WHERE sentiment_score IS NULL) as null_sentiment,
        COUNT(*) FILTER (WHERE brand IS NULL) as null_brand
    FROM fct_sentiment_events
""").fetchone()
print(f"Null sentiment: {nulls[0]}, Null brand: {nulls[1]}")
EOF
```

## Performance Optimization

```bash
# Reduce ingestion time
# → Lower limit_per_brand in scripts

# Speed up dbt
cd dbt
dbt run --profiles-dir . --threads 4

# Optimize dashboard queries
# → Use mart tables instead of fact table
# → Add date filters to limit data
# → Increase cache TTL

# Reduce memory usage
# → Set memory_limit in DuckDB connection
# → Process data in chunks
# → Use columnar selection in queries
```

## Maintenance Tasks

```bash
# Weekly
python pipelines/ingest_real_data.py
cd dbt && dbt build --profiles-dir .

# Monthly
# 1. Review brand taxonomy for new brands
# 2. Check API usage and costs
# 3. Analyze anomalies and trends
# 4. Update documentation

# Quarterly
# 1. Full data refresh
cd dbt && dbt build --profiles-dir . --full-refresh

# 2. Review and optimize slow queries
# 3. Update Python dependencies
pip install -r requirements.txt --upgrade

# 4. Clean up old cache files
rm -rf data/cache/*
```

## Useful Links

- **Documentation Home**: [Lab 2 Overview](../lab2-overview/)
- **Setup Guide**: [Lab 2 Setup](../lab2-setup/)
- **Troubleshooting**: [Lab 2 Troubleshooting](../lab2-troubleshooting/)
- **API Guide**: [API Integration](../lab2-api-integration/)
- **dbt Docs**: Run `dbt docs generate && dbt docs serve` in dbt/
- **Reddit API**: https://www.reddit.com/dev/api
- **News API**: https://newsapi.org/docs
- **PRAW Docs**: https://praw.readthedocs.io/
- **DuckDB Docs**: https://duckdb.org/docs/

## Getting Help

```bash
# Check logs
tail -f ingestion.log
cat dbt/logs/dbt.log

# Enable debug mode
export DBT_DEBUG=1
dbt run --select model_name --profiles-dir .

# Get model SQL
dbt compile --select model_name --profiles-dir .
cat target/compiled/.../model_name.sql

# Check dbt version
dbt --version

# Check Python packages
pip list
```

---

**Last Updated**: November 2025  
**Version**: 2.0  
**Maintainer**: narensham