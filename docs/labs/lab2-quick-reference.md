# Lab 2: Quick Reference Card

Essential commands and information for Market Sentiment Analysis lab.

## Common Commands

```bash
# Setup
cd lab2_market_sentiment
source lab2_env/bin/activate
dbt deps

# Generate Data
python pipelines/ingest_sentiment.py

# Run Pipeline
cd dbt
dbt run                    # Incremental
dbt run --full-refresh     # Full rebuild
dbt run --select fct_sentiment_events  # Single model

# Test
dbt test                   # All tests
dbt test --select fct_sentiment_events  # Model tests

# Documentation
dbt docs generate
dbt docs serve

# Cleanup
dbt clean
```

## Key Metrics

| Metric | Location | Description |
|--------|----------|-------------|
| Event Count | fct_sentiment_events | Total sentiment events |
| Avg Sentiment | mart_daily_sentiment | Daily average by brand |
| Anomaly Flag | mart_daily_sentiment | Statistical outliers |
| Engagement | Both tables | Upvotes/shares metric |
| Quality Flag | fct_sentiment_events | Data quality status |

## Model Materialization

| Model | Type | Refresh |
|-------|------|---------|
| stg_reddit__posts | View | Always |
| stg_news__articles | View | Always |
| int_sentiment_unified | Table | Full |
| fct_sentiment_events | Incremental | New data only |
| mart_daily_sentiment | Incremental | New dates only |

## Data Quality Checks

- ✅ 14 tests total
- Uniqueness: sentiment_event_id, (date, brand)
- Ranges: sentiment [-1, 1]
- Not null: 4 critical fields
- Accepted values: 2 categorical fields

## Key Thresholds

```python
sentiment_threshold_positive = 0.3
sentiment_threshold_negative = -0.3
anomaly_z_score_threshold = 2.0
```

## Common Queries

### Brand Sentiment Overview
```sql
SELECT 
    brand,
    AVG(avg_sentiment) as sentiment,
    SUM(content_count) as mentions
FROM mart_daily_sentiment
GROUP BY brand
ORDER BY sentiment DESC;
```

### Recent Anomalies
```sql
SELECT * 
FROM mart_daily_sentiment
WHERE anomaly_flag = 'ANOMALY'
AND sentiment_date >= CURRENT_DATE - INTERVAL '7 days'
ORDER BY sentiment_date DESC;
```

### Top Performing Content
```sql
SELECT 
    headline,
    brand,
    sentiment_score,
    engagement_count
FROM fct_sentiment_events
ORDER BY engagement_count DESC
LIMIT 10;
```

## File Locations

```
lab2_market_sentiment/
├── data/
│   ├── raw/*.csv           # Source data
│   └── *.duckdb            # Database
├── dbt/
│   ├── models/             # SQL transformations
│   ├── macros/             # Reusable SQL
│   ├── tests/              # Custom tests
│   └── schema.yml          # Model contracts
└── pipelines/
    └── ingest_sentiment.py # Data generator
```

## Troubleshooting Quick Fixes

| Issue | Quick Fix |
|-------|-----------|
| Duplicates | `dbt run --full-refresh` |
| Contract error | Check data types match schema.yml |
| Test fails | `dbt test --select [test_name]` |
| Slow run | Use `--select` for specific models |
| Database locked | Close all connections, retry |

## Important dbt Config

```yaml
# dbt_project.yml
vars:
  sentiment_threshold_positive: 0.3
  sentiment_threshold_negative: -0.3

# fct_sentiment_events
materialized: incremental
unique_key: sentiment_event_id
incremental_strategy: delete+insert

# mart_daily_sentiment
materialized: incremental
unique_key: ['sentiment_date', 'brand']
```

## Database Connection

```yaml
# dbt/profiles.yml
lab2_market_sentiment:
  outputs:
    dev:
      type: duckdb
      path: ../data/lab2_market_sentiment.duckdb
      threads: 4
  target: dev
```

## Python Dependencies

```txt
dbt-duckdb==1.7.0
duckdb==0.9.1
pandas>=2.0.0
numpy>=1.24.0
pyyaml>=6.0
```

## Useful SQL Snippets

### Check Row Counts
```sql
SELECT 
    'reddit' as source,
    COUNT(*) as count 
FROM stg_reddit__posts
UNION ALL
SELECT 
    'news' as source,
    COUNT(*) as count 
FROM stg_news__articles;
```

### Find Data Quality Issues
```sql
SELECT 
    quality_flag,
    COUNT(*) as count
FROM fct_sentiment_events
GROUP BY quality_flag;
```

### Check Incremental Status
```sql
SELECT 
    MAX(published_at) as latest_event,
    MAX(_dbt_updated_at) as latest_refresh
FROM fct_sentiment_events;
```

## dbt Packages

```yaml
# packages.yml
packages:
  - package: calogica/dbt_expectations
    version: 0.10.4
  - package: calogica/dbt_date
    version: 0.10.1
```

## Metrics Dashboard (Future)

Planned visualizations:
- Sentiment trend by brand (line chart)
- Daily mention volume (bar chart)
- Anomaly alerts (table)
- Engagement distribution (histogram)
- Brand comparison (radar chart)

## Next Steps After Setup

1. Review [Data Models](lab2-data-models.md)
2. Understand [Troubleshooting](lab2-troubleshooting.md)
3. Explore dbt docs: `dbt docs serve`
4. Plan real API integration
5. Design Streamlit dashboard

---

**Quick Help:** See [Lab 2 Overview](lab2-overview.md) for full details

**Last Updated:** November 2025