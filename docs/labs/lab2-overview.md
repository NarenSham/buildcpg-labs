# Lab 2: Market Sentiment Analysis

## Overview

Lab 2 implements a **real-time market sentiment analysis pipeline** for Consumer Packaged Goods (CPG) brands. It ingests data from Reddit and news sources, analyzes sentiment, and provides daily aggregated metrics for brand reputation monitoring.

## Purpose

Monitor and analyze public sentiment towards CPG brands to:
- Track brand reputation trends over time
- Identify sentiment anomalies requiring attention
- Compare sentiment across multiple brands
- Understand engagement patterns and content performance

## Architecture

### Data Flow

```
Raw Data Sources
    ↓
Reddit API + News API
    ↓
Python Ingestion (pipelines/ingest_sentiment.py)
    ↓
CSV Files (data/raw/)
    ↓
dbt Staging Layer (stg_reddit__posts, stg_news__articles)
    ↓
dbt Intermediate Layer (int_sentiment_unified)
    ↓
dbt Marts Layer (fct_sentiment_events, mart_daily_sentiment)
    ↓
Analytics & Dashboards
```

### Technology Stack

| Component | Technology |
|-----------|------------|
| **Database** | DuckDB 0.9.1 |
| **Transformation** | dbt 1.7.0 |
| **Data Quality** | dbt tests + dbt_expectations |
| **Ingestion** | Python 3.11+ |
| **Sentiment Analysis** | VADER / TextBlob (planned) |
| **Orchestration** | Manual (Airflow planned) |

## Data Models

### Staging Layer

**`stg_reddit__posts`**
- Raw Reddit post data
- Cleaned column names
- Basic type casting
- Source: `data/raw/reddit_real.csv`

**`stg_news__articles`**
- Raw news article data  
- Cleaned column names
- Basic type casting
- Source: `data/raw/news_real.csv`

### Intermediate Layer

**`int_sentiment_unified`**
- Unified Reddit + News data
- Surrogate keys generated
- Sentiment categorization (positive/negative/neutral)
- Engagement metrics
- 7-day moving averages
- Quality flags

### Marts Layer

**`fct_sentiment_events`** (Fact Table)
- Grain: One row per sentiment event
- Unique key: `sentiment_event_id`
- Incremental materialization
- Contract enforcement for data quality
- Columns: 20+ including sentiment scores, engagement, temporal fields

**`mart_daily_sentiment`** (Aggregate Table)
- Grain: One row per (date, brand)
- Daily sentiment aggregates
- Anomaly detection (z-score based)
- Content counts by sentiment category
- Engagement metrics
- Incremental materialization

## Key Features

### 1. Surrogate Key Generation
Ensures unique event identification:
```sql
generate_surrogate_key(['content_id', 'published_at', 'source'])
```

### 2. Sentiment Categorization
Classifies sentiment into actionable categories:
- **Positive:** Score ≥ 0.3
- **Negative:** Score ≤ -0.3  
- **Neutral:** -0.3 < Score < 0.3

### 3. Quality Flags
Tracks data quality issues:
- `VALID` - Clean, usable data
- `INVALID_SENTIMENT` - Sentiment score out of range
- `NULL_HEADLINE` - Missing headline text

### 4. Anomaly Detection
Statistical anomaly flagging using z-scores:
- `NORMAL` - Within expected range
- `ANOMALY` - 2+ standard deviations from mean

### 5. Incremental Processing
Only processes new data on subsequent runs:
```sql
WHERE published_at > (SELECT MAX(published_at) FROM {{ this }})
```

## Data Quality

### dbt Tests Implemented

**Uniqueness Tests:**
- `sentiment_event_id` must be unique
- `(sentiment_date, brand)` composite key must be unique

**Not Null Tests:**
- `sentiment_event_id`
- `brand_key`
- `sentiment_score`
- `published_date`
- `sentiment_date`

**Range Tests:**
- Sentiment scores between -1 and 1
- No future dates allowed

**Accepted Values Tests:**
- `quality_flag` in ['VALID', 'INVALID_SENTIMENT', 'NULL_HEADLINE']
- `anomaly_flag` in ['NORMAL', 'ANOMALY']

**Custom Tests:**
- All brands present in daily aggregates
- Sentiment score validation

### Test Results
✅ **14/14 tests passing** (as of latest run)

## Metrics Available

### Event-Level Metrics
- Sentiment score (-1 to 1)
- Engagement count (upvotes, shares)
- Content quality flag
- Temporal dimensions (year, month, day, hour)

### Daily Aggregate Metrics
- Average sentiment
- Min/Max sentiment
- Standard deviation
- Content counts (total, positive, negative, neutral)
- Positive ratio
- Total/Average engagement
- Source diversity
- Z-score for anomaly detection

## Common Issues & Solutions

### Issue: 800 Duplicate sentiment_event_id

**Root Cause:**
- Wrong config parameter (`unique_id` vs `unique_key`)
- Double WHERE clause in SQL
- Insufficient uniqueness in surrogate key

**Solution Applied:**
1. Changed `unique_id` → `unique_key` in model config
2. Fixed double WHERE clause with proper CTE structure
3. Enhanced surrogate key to include `source` field
4. Fixed data type mismatches (INTEGER → BIGINT)

**Result:** ✅ All duplicates resolved, uniqueness test passing

### Issue: Contract Enforcement Errors

**Root Cause:**
- Schema mismatches between contract and actual SQL output
- Incremental model schema changes
- Missing columns in contract definition

**Solution Applied:**
1. Updated data types in SQL to match contract (BIGINT vs INTEGER)
2. Added missing columns to contract in schema.yml
3. Removed contracts where not needed (marts without strict requirements)

## Current Status

### ✅ Completed
- Synthetic data generation
- Staging models (Reddit + News)
- Intermediate unified model
- Fact table (fct_sentiment_events)
- Daily aggregate mart
- 14 data quality tests
- Full documentation

### 🔄 In Progress
- Real API integration (Reddit PRAW, NewsAPI)
- Advanced sentiment analysis (Hugging Face transformers)
- Streamlit dashboard

### 📋 Planned
- Airflow orchestration
- Brand comparison analytics
- Temporal pattern analysis
- ML-based sentiment prediction
- Email alerting for anomalies

## Getting Started

See [Lab 2 Setup Guide](lab2-setup.md) for installation and configuration instructions.

## Related Documentation

- [Lab 2 Setup Guide](lab2-setup.md)
- [Lab 2 Data Models](lab2-data-models.md)
- [Lab 2 Troubleshooting](lab2-troubleshooting.md)
- [dbt Best Practices](https://docs.getdbt.com/guides/best-practices)
- [Architecture Overview](../architecture/overview.md)

---

**Lab Owner:** narensham  
**Created:** November 2025  
**Last Updated:** November 2025  
**Status:** ✅ Active Development