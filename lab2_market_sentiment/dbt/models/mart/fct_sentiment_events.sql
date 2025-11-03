{{ config(
  materialized='incremental',
  unique_key='sentiment_event_id',
  tags=['mart', 'facts'],
  description='Fact table: One row per sentiment event',
  incremental_strategy='delete+insert'
) }}

WITH base_data AS (
    SELECT
        sentiment_event_id,
        brand_key,
        source_key,
        content_id,
        creator,
        brand,
        headline,
        body_text,
        engagement_count,
        sentiment_score,
        sentiment_category,
        published_at,
        source,
        ingested_at,
        
        -- Quality tracking (calculate here so we can filter on it)
        CASE 
            WHEN NOT {{ validate_sentiment('sentiment_score') }} THEN 'INVALID_SENTIMENT'
            WHEN headline IS NULL THEN 'NULL_HEADLINE'
            ELSE 'VALID'
        END as quality_flag
        
    FROM {{ ref('int_sentiment_unified') }}
    
    {% if is_incremental() %}
    WHERE published_at > (SELECT MAX(published_at) FROM {{ this }})
    {% endif %}
)

SELECT
    CAST(sentiment_event_id AS VARCHAR) as sentiment_event_id,
    brand_key,
    CAST(source_key AS INTEGER) as source_key,
    content_id,
    creator,
    brand,
    headline,
    body_text,
    CAST(engagement_count AS BIGINT) as engagement_count,  -- Changed to BIGINT
    sentiment_score,
    sentiment_category,
    published_at,
    source,
    ingested_at,
    
    -- Date components for easy filtering
    CAST(published_at AS DATE) as published_date,
    CAST(EXTRACT(YEAR FROM published_at) AS BIGINT) as published_year,      -- Changed to BIGINT
    CAST(EXTRACT(MONTH FROM published_at) AS BIGINT) as published_month,    -- Changed to BIGINT
    CAST(EXTRACT(DAYOFWEEK FROM published_at) AS BIGINT) as published_day_of_week,  -- Changed to BIGINT
    CAST(EXTRACT(HOUR FROM published_at) AS BIGINT) as published_hour,      -- Changed to BIGINT
    
    quality_flag,
    
    -- Metadata
    get_current_timestamp() as _dbt_updated_at,
    '{{ run_started_at }}' as _dbt_run_timestamp

FROM base_data
WHERE quality_flag = 'VALID'