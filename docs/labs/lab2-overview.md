# Lab 2: Market Sentiment Analysis

## Overview

Lab 2 implements an **automated, production-ready market sentiment analysis pipeline** for Consumer Packaged Goods (CPG) brands. It ingests real data from Reddit and News APIs, performs sentiment analysis, tracks competitive intelligence, and provides interactive dashboards for brand monitoring.

**Key Highlights:**
- ✅ Real API integration (Reddit PRAW + NewsAPI)
- ✅ GitHub Actions automation (weekly runs)
- ✅ Shared brand taxonomy across labs
- ✅ Advanced competitive analytics
- ✅ Trending topics detection
- ✅ Interactive Streamlit dashboards
- ✅ Production-grade data quality tests

## Purpose

Monitor and analyze public sentiment towards CPG brands to:

- 📊 **Track brand reputation** trends over time
- ⚠️ **Identify sentiment anomalies** requiring immediate attention
- 🏆 **Benchmark competitive positioning** across brands
- 🔥 **Detect trending topics** and emerging themes
- 📈 **Measure share of voice** and engagement metrics
- 🎯 **Inform brand strategy** with data-driven insights

## Architecture

### Data Flow

```
┌─────────────────────────────────────────────────────────┐
│              INGESTION LAYER                             │
│  Reddit API (PRAW) + News API → Python Scripts          │
│  ↓                                                       │
│  Raw CSV Files (data/raw/)                              │
│    - reddit_brands.csv                                  │
│    - news_brands.csv                                    │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│            TRANSFORMATION LAYER (dbt)                    │
│  ┌─────────────────────────────────────┐                │
│  │  STAGING                            │                │
│  │  - stg_reddit__posts                │                │
│  │  - stg_news__articles               │                │
│  └──────────────┬──────────────────────┘                │
│                 ↓                                        │
│  ┌─────────────────────────────────────┐                │
│  │  INTERMEDIATE                       │                │
│  │  - int_sentiment_unified            │                │
│  │    (surrogate keys, enrichment)     │                │
│  └──────────────┬──────────────────────┘                │
│                 ↓                                        │
│  ┌─────────────────────────────────────┐                │
│  │  DIMENSIONS                         │                │
│  │  - dim_brands                       │                │
│  │  - dim_sources                      │                │
│  └──────────────┬──────────────────────┘                │
│                 ↓                                        │
│  ┌─────────────────────────────────────┐                │
│  │  MARTS (Analytics Layer)            │                │
│  │  - fct_sentiment_events             │                │
│  │  - mart_daily_sentiment             │                │
│  │  - mart_brand_competitive_analysis  │                │
│  │  - mart_trending_topics             │                │
│  └──────────────┬──────────────────────┘                │
└─────────────────┼───────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────────────────────┐
│           ANALYTICS & VISUALIZATION                      │
│  - Streamlit Dashboard (Main)                           │
│  - Competitive Intelligence Page                        │
│  - DuckDB Database (OLAP queries)                       │
└─────────────────────────────────────────────────────────┘
```

### Automation

**GitHub Actions Workflow** (`weekly_pipeline.yml`):
- **Schedule**: Every Sunday at 2 AM UTC
- **Manual Trigger**: Available via GitHub Actions UI
- **Steps**:
  1. Data ingestion from APIs
  2. dbt transformations
  3. Data quality tests
  4. Artifact upload (DuckDB database)

## Technology Stack

| Component | Technology | Version |
|-----------|-----------|---------|
| **Database** | DuckDB | 0.9.1 |
| **Transformation** | dbt-core + dbt-duckdb | 1.7.0 |
| **Data Quality** | dbt tests + dbt_expectations | 0.10.4 |
| **Orchestration** | Prefect + GitHub Actions | 2.x |
| **Ingestion** | Python (PRAW + NewsAPI) | 3.11+ |
| **Sentiment Analysis** | VADER Sentiment | 3.3.2 |
| **Dashboards** | Streamlit + Plotly | 1.28.1 |
| **CI/CD** | GitHub Actions | N/A |

## Shared Brand Taxonomy

**New in v2:** Lab 2 now uses a **shared brand taxonomy** located in `buildcpg-labs/shared/config/brand_taxonomy.yaml`.

### Benefits:
- ✅ **Single source of truth** for brand data across all labs
- ✅ **Consistent parent company mapping**
- ✅ **Standardized category classifications**
- ✅ **Easy to extend** with new brands

### Structure:

```yaml
beverages:
  coca_cola:
    parent: "The Coca-Cola Company"
    ticker: "KO"
    brands:
      - name: "Coca-Cola"
        aliases: ["Coke", "Coca Cola"]
        category: "Carbonated Soft Drinks"
      - name: "Sprite"
        category: "Lemon-Lime Soda"
```

### Usage:

Ingestion scripts automatically load the taxonomy:

```python
from pathlib import Path
import yaml

# Try shared config first, fall back to lab-specific
SHARED_CONFIG = Path("../shared/config/brand_taxonomy.yaml")
taxonomy = yaml.safe_load(open(SHARED_CONFIG))
```

## Data Models

### Staging Layer

#### `stg_reddit__posts`
- **Purpose**: Clean and normalize Reddit data
- **Materialization**: Ephemeral
- **Key Operations**:
  - Quality flagging (NULL_POST_ID, INVALID_SENTIMENT, etc.)
  - Deduplication by `(post_id, author, created_at)`
  - Sentiment score normalization (-1 to 1)
  - Brand name standardization (UPPER, TRIM)
- **Source**: `data/raw/reddit_brands.csv`

#### `stg_news__articles`
- **Purpose**: Clean and normalize news data
- **Materialization**: Ephemeral
- **Key Operations**:
  - URL-based deduplication
  - Headline text cleaning
  - Parent company mapping from taxonomy
- **Source**: `data/raw/news_brands.csv`

### Intermediate Layer

#### `int_sentiment_unified`
- **Purpose**: Unified view of all sentiment data with enrichment
- **Materialization**: Table
- **Key Features**:
  - Surrogate key generation (MD5 hash)
  - Brand key mapping to `dim_brands`
  - Sentiment categorization (positive/neutral/negative)
  - Engagement percentile calculation
  - 7-day moving average sentiment
  - Sentiment change tracking
  - Row-level deduplication

### Dimensions

#### `dim_brands`
- **Grain**: One row per brand
- **Purpose**: Brand master data
- **Columns**:
  - `brand_key` (surrogate key)
  - `brand` (name)
  - `parent_company` (from taxonomy)
  - `category` (product category)
  - `company_type` (Public/Private)

#### `dim_sources`
- **Grain**: One row per data source
- **Purpose**: Source metadata
- **Values**: Reddit, News

### Marts Layer

#### `fct_sentiment_events` (Fact Table)

**Grain**: One row per sentiment event (Reddit post or news article)

**Key Features**:
- **Materialization**: Incremental (delete+insert strategy)
- **Unique Key**: `sentiment_event_id`
- **Contract**: Enforced for data quality
- **1-day overlap window** for late-arriving data

**Columns** (25+):
- Event identifiers
- Brand and source foreign keys
- Sentiment metrics (score, category)
- Engagement metrics
- Temporal dimensions (date parts)
- Quality flags
- Metadata timestamps

**Use Cases**:
- Event-level analysis
- Drill-down into specific posts/articles
- Source of truth for all sentiment data

#### `mart_daily_sentiment` (Daily Aggregates)

**Grain**: One row per (date, brand)

**Key Features**:
- **Materialization**: Incremental
- **Unique Key**: `[sentiment_date, brand]`
- **Anomaly Detection**: Z-score based flagging

**Metrics**:
- **Volume**: Content count, source diversity
- **Sentiment**: Avg, min, max, stddev, category breakdown
- **Engagement**: Total, average
- **Quality**: Positive ratio, sentiment distribution
- **Anomalies**: Z-score, anomaly flag (NORMAL/ANOMALY)

**Use Cases**:
- Daily trend analysis
- Time-series visualization
- Anomaly alerting

#### `mart_brand_competitive_analysis` ⭐ NEW

**Grain**: One row per brand

**Key Features**:
- Share of voice calculation
- Competitive positioning classification
- Category benchmarking
- Momentum tracking (7d vs 30d)

**Metrics**:
- **Volume**: Total mentions, Reddit vs News split
- **Share of Voice**: % of total mentions
- **Sentiment**: Avg sentiment, volatility, net score
- **Engagement**: Reddit engagement rate
- **Rankings**: Sentiment rank, volume rank (within category)
- **Positioning**: MARKET_LEADER, NICHE_FAVORITE, AT_RISK, LOW_VISIBILITY, MIDDLE_PACK

**Use Cases**:
- Competitive intelligence
- Market positioning analysis
- Executive dashboards

#### `mart_trending_topics` ⭐ NEW

**Grain**: One row per (brand, topic)

**Key Features**:
- Keyword-based topic extraction
- Trending score calculation
- Sentiment tone classification

**Topics Tracked**:
1. Product Launch
2. Pricing
3. Quality Issues
4. Sustainability
5. Health & Nutrition
6. Marketing & Advertising
7. Brand Comparison
8. Taste & Flavor

**Metrics**:
- **Volume**: Mention count by source, recency (7d, 14d)
- **Trending Score**: Combines recency, growth, engagement
- **Sentiment**: Avg sentiment, positive/negative breakdown
- **Classification**: HOT, TRENDING, STABLE, EMERGING

**Use Cases**:
- Topic monitoring
- Content strategy planning
- Early warning system

## Key Features

### 1. Surrogate Key Generation

Ensures unique event identification using MD5 hashing:

```sql
MD5(CONCAT(
    COALESCE(CAST(content_id AS VARCHAR), ''),
    '|',
    COALESCE(CAST(published_at AS VARCHAR), ''),
    '|',
    COALESCE(CAST(row_num AS VARCHAR), '')
))
```

### 2. Sentiment Categorization

Configurable thresholds via dbt variables:

```yaml
vars:
  sentiment_threshold_positive: 0.5
  sentiment_threshold_negative: -0.5
```

Categories:
- **Positive**: Score ≥ 0.5
- **Negative**: Score ≤ -0.5
- **Neutral**: -0.5 < Score < 0.5

### 3. Quality Flags

Multi-level quality tracking:

| Flag | Description | Action |
|------|-------------|--------|
| `VALID` | Clean, usable data | ✅ Include |
| `INVALID_SENTIMENT` | Score out of range | ❌ Exclude |
| `NULL_HEADLINE` | Missing headline | ❌ Exclude |
| `FUTURE_DATE` | Published date in future | ❌ Exclude |

### 4. Anomaly Detection

Statistical z-score based anomaly flagging:

```sql
z_score = (daily_avg - brand_avg) / brand_stddev

IF ABS(z_score) > 2 THEN 'ANOMALY' ELSE 'NORMAL'
```

**Use Case**: Alert on days with unusual sentiment patterns (e.g., PR crises, viral posts)

### 5. Incremental Processing

Efficient data processing:

```sql
{% if is_incremental() %}
    WHERE published_at >= (
        SELECT COALESCE(MAX(published_at), '1900-01-01') 
        FROM {{ this }}
    ) - INTERVAL 1 DAY
{% endif %}
```

**Benefits**:
- Only processes new data
- 1-day overlap window captures late-arriving records
- Faster pipeline runs (minutes vs hours)

### 6. Competitive Positioning

Automatic classification based on percentile rankings:

| Position | Criteria | Description |
|----------|----------|-------------|
| `MARKET_LEADER` | High sentiment + High volume | Top brands with strong positive buzz |
| `NICHE_FAVORITE` | High sentiment + Low volume | Well-loved but niche brands |
| `AT_RISK` | Low sentiment + High volume | Popular brands facing reputation issues |
| `LOW_VISIBILITY` | Low sentiment + Low volume | Struggling brands |
| `MIDDLE_PACK` | Moderate on both | Average performing brands |

### 7. Trending Score Algorithm

Combines multiple signals:

```sql
trending_score = 
    (mentions_last_7d * 2.0 / mentions_last_14d) 
    * LOG(mention_count + 1) 
    * (1 + avg_engagement / 100.0)
```

**Components**:
- **Recency**: 7d vs 14d growth
- **Volume**: Logarithmic mention count
- **Engagement**: Normalized engagement boost

## Data Quality

### dbt Tests Implemented

**✅ 20+ tests passing**

#### Uniqueness Tests:
- `sentiment_event_id` must be unique
- `(sentiment_date, brand)` composite key must be unique
- `(brand, parent_company)` in competitive analysis
- `(brand, topic)` in trending topics

#### Not Null Tests:
- All primary and foreign keys
- Core metrics (sentiment_score, published_date)

#### Range Tests:
- Sentiment scores: -1 to 1
- Share of voice: 0 to 100%
- No future dates allowed

#### Accepted Values Tests:
- `quality_flag`: ['VALID', 'INVALID_SENTIMENT', 'NULL_HEADLINE']
- `anomaly_flag`: ['NORMAL', 'ANOMALY']
- `competitive_position`: ['MARKET_LEADER', 'NICHE_FAVORITE', ...]
- `trend_status`: ['HOT', 'TRENDING', 'STABLE', 'EMERGING']
- `sentiment_tone`: ['POSITIVE_BUZZ', 'NEGATIVE_BUZZ', 'NEUTRAL_DISCUSSION']

#### Custom Business Logic Tests:
- All brands from fact table appear in daily mart
- Sentiment validation macro reusability
- Fact table grain enforcement

### Test Results

```bash
$ dbt test --profiles-dir .

Completed with 20 total tests, 0 failures, 0 errors, 0 skipped
```

## Dashboards

### Main Dashboard (`streamlit_app.py`)

**Features**:
- 📊 KPI metrics with week-over-week deltas
- 📈 Sentiment trend with dual-axis (sentiment + volume)
- 📱 Source distribution (Reddit vs News)
- 🏢 Brand sentiment comparison (horizontal bar chart)
- 🎯 Sentiment category distribution
- 📰 Top content tables (most positive, negative, engaged)
- ⚠️ Anomaly detection and alerts

**Filters**:
- Date range picker
- Brand multi-select
- Source multi-select
- Sentiment category filter

### Competitive Intelligence Page ⭐ NEW

**Features**:
- 📢 Share of Voice analysis (top 15 brands)
- 🎯 Competitive Positioning Matrix (sentiment vs volume)
- 🔥 Trending Topics table
- Company and category filters

**Insights**:
- Identify market leaders vs at-risk brands
- Benchmark against category averages
- Track momentum (7d vs 30d growth)

## GitHub Actions Automation

### Workflow Configuration

**File**: `.github/workflows/weekly_pipeline.yml`

```yaml
name: Weekly Sentiment Pipeline

on:
  schedule:
    - cron: '0 2 * * 0'  # Every Sunday at 2 AM UTC
  workflow_dispatch:  # Manual trigger

jobs:
  run-pipeline:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run pipeline
        env:
          REDDIT_CLIENT_ID: ${{ secrets.REDDIT_CLIENT_ID }}
          REDDIT_CLIENT_SECRET: ${{ secrets.REDDIT_CLIENT_SECRET }}
          REDDIT_USER_AGENT: ${{ secrets.REDDIT_USER_AGENT }}
          NEWS_API_KEY: ${{ secrets.NEWS_API_KEY }}
        run: python orchestrate_weekly.py
      - name: Upload artifacts
        uses: actions/upload-artifact@v4
        with:
          name: duckdb-database
          path: data/lab2_market_sentiment.duckdb
```

### Orchestration (`orchestrate_weekly.py`)

**Prefect Flow Steps**:
1. ✅ Check prerequisites (.env, dbt project, scripts)
2. 🔄 Ingest data (Reddit + News APIs)
3. 🔄 Run dbt models (`dbt build`)
4. 📊 Generate data quality report

**Error Handling**:
- Task retries with exponential backoff
- Timeout protection (30min ingestion, 10min dbt)
- Comprehensive logging
- Quality report generation

**Outputs**:
- DuckDB database artifact
- Execution logs
- Data quality metrics

## Metrics Available

### Event-Level Metrics (`fct_sentiment_events`)

- Sentiment score (-1 to 1)
- Sentiment category (positive/neutral/negative)
- Engagement count (upvotes, comments, shares)
- Content quality flag
- Published date/time (with date parts)
- Brand, parent company, category
- Source (Reddit vs News)
- Headline and body text

### Daily Aggregate Metrics (`mart_daily_sentiment`)

- Average, min, max, stddev sentiment
- Content counts (total, by category)
- Positive ratio
- Total and average engagement
- Source diversity
- Z-score for anomaly detection
- Anomaly flag (NORMAL/ANOMALY)

### Competitive Metrics (`mart_brand_competitive_analysis`)

- Share of voice (%)
- Net sentiment score (positive % - negative %)
- Sentiment and volume percentile ranks
- Engagement rate
- Momentum (7d vs 30d growth %)
- Competitive position classification
- Sentiment vs category benchmark
- Category and parent company averages

### Topic Metrics (`mart_trending_topics`)

- Trending score
- Mention count (total, 7d, 14d)
- Sentiment breakdown
- Engagement metrics
- Trend status (HOT, TRENDING, etc.)
- Sentiment tone (POSITIVE_BUZZ, etc.)
- Topic rank within brand

## Common Issues & Solutions

### Issue: Duplicate sentiment_event_id (Historical)

**Root Cause**: Wrong dbt config parameter and double WHERE clause

**Solution Applied**:
1. ✅ Changed `unique_id` → `unique_key` in model config
2. ✅ Fixed double WHERE clause with proper CTE structure
3. ✅ Enhanced surrogate key to include `row_num` for true uniqueness
4. ✅ Fixed data type mismatches (INTEGER → BIGINT)

**Result**: All duplicates resolved, 0 failures in uniqueness tests

### Issue: API Rate Limits

**Symptoms**: Ingestion fails with 429 errors

**Solution**:
- Reddit: Use PRAW's built-in rate limiting
- NewsAPI: Implement exponential backoff with retries
- Free tier limits: 100 requests/day (NewsAPI), respect Reddit's 60 req/min

### Issue: Memory Issues with DuckDB

**Symptoms**: Out of memory errors on large datasets

**Solution**:
```python
# Set memory limits in duckdb connection
conn = duckdb.connect(str(DB_PATH))
conn.execute("SET memory_limit='2GB';")
conn.execute("SET max_memory='2GB';")
```

### Issue: Streamlit Caching

**Symptoms**: Dashboard shows stale data

**Solution**:
```python
@st.cache_data(ttl=300)  # 5-minute TTL
def load_data():
    # ...
```

## Current Status

### ✅ Completed

- ✅ Real API integration (Reddit PRAW, NewsAPI)
- ✅ Shared brand taxonomy architecture
- ✅ GitHub Actions automation
- ✅ Prefect orchestration
- ✅ VADER sentiment analysis
- ✅ All 4 mart tables (events, daily, competitive, topics)
- ✅ 20+ data quality tests
- ✅ Main Streamlit dashboard
- ✅ Competitive Intelligence page
- ✅ Full documentation

### 🔄 In Progress

- 🔄 Advanced NLP topic extraction (vs keyword matching)
- 🔄 Hugging Face transformer sentiment (vs VADER)
- 🔄 Email alerting for anomalies

### 📋 Planned

- 📋 Historical backfill (6+ months of data)
- 📋 ML-based sentiment prediction
- 📋 Correlation analysis (sentiment vs stock prices)
- 📋 Slack/Teams integration for alerts
- 📋 Export to BigQuery for larger-scale analysis

## Getting Started

See [Lab 2 Setup Guide](../lab2-setup/) for:
- Prerequisites and installation
- API key configuration
- First pipeline run
- Dashboard deployment

## Performance Metrics

**Pipeline Runtime** (typical):
- Ingestion: 5-10 minutes (100 posts per brand)
- dbt build: 2-3 minutes (incremental)
- Total: **~10 minutes** end-to-end

**Data Volumes** (typical weekly run):
- Reddit posts: 500-1,000
- News articles: 300-500
- Total sentiment events: 800-1,500
- Daily aggregates: 50-100 rows

**Dashboard Performance**:
- Initial load: 2-3 seconds
- Filter updates: <1 second (cached)
- Data refresh: 5 minutes (TTL)

## Related Documentation

- [Lab 2 Setup Guide](../lab2-setup/)
- [Lab 2 Troubleshooting](../lab2-troubleshooting/)
- [dbt Model Documentation](../lab2-dbt-docs/)
- [API Integration Guide](../lab2-api-integration/)

---

**Lab Owner**: narensham  
**Created**: November 2025  
**Last Updated**: November 2025  
**Status**: ✅ Production-Ready