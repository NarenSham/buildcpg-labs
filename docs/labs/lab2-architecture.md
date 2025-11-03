# Lab 2: Market Sentiment Architecture

## Overview

The **Market Sentiment Analysis Architecture** enables near-real-time ingestion, transformation, and aggregation of public sentiment toward Consumer Packaged Goods (CPG) brands.

It’s designed around the **Medallion Architecture** — Raw → Bronze → Silver → Gold — and optimized for **local-first analytics** using DuckDB and dbt.

---

## High-Level Data Flow

```mermaid
    flowchart LR
    %% Layer titles
    subgraph INGESTION["🔹 Ingestion Layer"]
        A1[Reddit API]:::source --> B[Python Ingestion<br>(pipelines/ingest_sentiment.py)]:::process
        A2[News API]:::source --> B
    end

    subgraph RAW["🗂️ Raw Data"]
        B --> C[Raw CSV Files<br>(data/raw/)]:::storage
    end

    subgraph BRONZE["🥉 Bronze Layer"]
        C --> D[dbt Staging Models<br>(stg_reddit__*, stg_news__*)]:::bronze
    end

    subgraph SILVER["🥈 Silver Layer"]
        D --> E[dbt Intermediate Models<br>(int_sentiment_unified)]:::silver
    end

    subgraph GOLD["🥇 Gold Layer"]
        E --> F[dbt Marts Models<br>(mart_daily_sentiment, fct_sentiment_events)]:::gold
    end

    subgraph ANALYTICS["📊 Analytics Layer"]
        F --> G[Streamlit / DuckDB Dashboards]:::viz
    end

    %% Styling for classes
    classDef source fill:#e3f2fd,stroke:#1565c0,stroke-width:2px,color:#0d47a1,font-weight:bold;
    classDef process fill:#fff3e0,stroke:#ef6c00,stroke-width:2px,color:#4e342e,font-weight:bold;
    classDef storage fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px,color:#1b5e20,font-weight:bold;
    classDef bronze fill:#fbe9e7,stroke:#bf360c,stroke-width:2px,color:#3e2723,font-weight:bold;
    classDef silver fill:#eceff1,stroke:#607d8b,stroke-width:2px,color:#263238,font-weight:bold;
    classDef gold fill:#fff8e1,stroke:#f9a825,stroke-width:2px,color:#5f370e,font-weight:bold;
    classDef viz fill:#fce4ec,stroke:#ad1457,stroke-width:2px,color:#4a148c,font-weight:bold;


---

## Architecture Summary

| Layer | Description | Example Models |
|--------|--------------|----------------|
| **Raw** | External Reddit & News data sources | `reddit_real.csv`, `news_real.csv` |
| **Bronze (Staging)** | Cleans & standardizes raw data | `stg_reddit__posts`, `stg_news__articles` |
| **Silver (Intermediate)** | Combines and enriches sources | `int_sentiment_unified` |
| **Gold (Marts)** | Business-ready analytics tables | `fct_sentiment_events`, `mart_daily_sentiment` |

---

## Technology Stack

| Component | Tool | Purpose |
|------------|------|----------|
| Database | DuckDB | Lightweight analytical engine |
| Transformation | dbt | ELT orchestration and testing |
| Ingestion | Python 3.11+ | Reddit + News API collection |
| Sentiment Analysis | VADER / TextBlob | Text polarity scoring |
| Orchestration | Manual (Airflow planned) | Future automation |
| Visualization | Streamlit | Interactive dashboard layer |

---

## Key Features

- **Unified Sentiment Model:** Combines Reddit and News sentiment in one schema.
- **Surrogate Keys:** Ensures event-level uniqueness.
- **Categorized Sentiment:** Groups scores into positive, neutral, or negative.
- **Incremental Loads:** Processes only new data after each run.
- **Data Contracts:** Enforces consistent schema and data types.
- **Comprehensive Testing:** Uniqueness, nulls, ranges, and accepted values validated.

---

## Data Quality Tests

| Type | Target Columns | Description |
|-------|----------------|-------------|
| **Unique** | `sentiment_event_id`, `(sentiment_date, brand)` | Ensures grain-level uniqueness |
| **Not Null** | `brand_key`, `sentiment_score`, `published_date` | Core attributes must exist |
| **Range** | `sentiment_score` | Must be between -1 and 1 |
| **Accepted Values** | `quality_flag`, `anomaly_flag` | Restricts allowed values |

All core tests are **passing** as of the latest dbt run ✅

---

## Example Model Flow

1. **Ingestion:**  
   `ingest_sentiment.py` pulls new posts/articles and stores them under `/data/raw/`

2. **Transformation:**  
   dbt staging → intermediate → marts flow using DuckDB

3. **Analytics:**  
   Aggregate daily sentiment and engagement data for dashboards

---

## Current Status

| Area | Progress | Notes |
|------|-----------|-------|
| Data Ingestion | ✅ Completed | Synthetic Reddit + News data |
| dbt Models | ✅ Stable | Full medallion flow implemented |
| Data Quality | ✅ All tests passing | Custom tests working |
| Dashboard | 🔄 Planned | Streamlit interface next |
| Airflow Integration | 🔄 Planned | Orchestration phase |

---

## Related Documentation

- [Lab 2 Setup Guide](lab2-setup.md)
- [Lab 2 Data Models](lab2-data-models.md)
- [Lab 2 Troubleshooting](lab2-troubleshooting.md)
- [Architecture Overview](../architecture/overview.md)

---

**Author:** narensham  
**Last Updated:** November 2025  
**Status:** Active Development
