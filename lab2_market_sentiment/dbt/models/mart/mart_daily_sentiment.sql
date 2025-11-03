{{ config(
    materialized='incremental',
    unique_key=['sentiment_date', 'brand'],
    on_schema_change='append_new_columns',
    incremental_strategy='delete+insert',
    tags=['mart', 'daily'],
    description='Daily sentiment aggregates by brand'
) }}

WITH daily_metrics AS (
    SELECT
        CAST(published_at AS DATE) as sentiment_date,
        brand,
        
        -- Volume
        COUNT(*) as content_count,
        COUNT(DISTINCT source) as source_count,
        
        -- Sentiment metrics
        ROUND(AVG(sentiment_score), 3) as avg_sentiment,
        ROUND(MIN(sentiment_score), 3) as min_sentiment,
        ROUND(MAX(sentiment_score), 3) as max_sentiment,
        ROUND(STDDEV(sentiment_score), 3) as stddev_sentiment,
        
        -- Category breakdown
        COUNT(*) FILTER (WHERE sentiment_category = 'positive') as positive_count,
        COUNT(*) FILTER (WHERE sentiment_category = 'negative') as negative_count,
        COUNT(*) FILTER (WHERE sentiment_category = 'neutral') as neutral_count,
        
        -- Ratios
        ROUND(
            COUNT(*) FILTER (WHERE sentiment_category = 'positive') / COUNT(*),
            3
        ) as positive_ratio,
        
        -- Engagement
        SUM(engagement_count) as total_engagement,
        ROUND(AVG(engagement_count), 2) as avg_engagement
    
    FROM {{ ref('fct_sentiment_events') }}
    
    {% if execute %}
        {% if this.exists %}
            WHERE CAST(published_at AS DATE) >= (SELECT MAX(sentiment_date) FROM {{ this }}) - INTERVAL '1 day'
        {% endif %}
    {% endif %}
    
    GROUP BY CAST(published_at AS DATE), brand
),

-- Anomaly detection
with_anomalies AS (
    SELECT
        *,
        -- Z-score for sentiment
        ROUND(
            (avg_sentiment - AVG(avg_sentiment) OVER (PARTITION BY brand)) 
            / NULLIF(STDDEV(avg_sentiment) OVER (PARTITION BY brand), 0),
            3
        ) as z_score_sentiment,
        
        -- Flag anomalies
        CASE 
            WHEN ABS((avg_sentiment - AVG(avg_sentiment) OVER (PARTITION BY brand)) 
                / NULLIF(STDDEV(avg_sentiment) OVER (PARTITION BY brand), 0)) > 2 
            THEN 'ANOMALY'
            ELSE 'NORMAL'
        END as anomaly_flag
    FROM daily_metrics
)

SELECT
    *,
    get_current_timestamp() as mart_load_date
FROM with_anomalies
ORDER BY sentiment_date DESC, brand