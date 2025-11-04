{{ config(
  materialized='incremental',
  unique_key='sentiment_event_id',
  alias='fct_sentiment_events',
  tags=['mart', 'facts'],
  description='Fact table: One row per sentiment event',
  incremental_strategy='delete+insert'
) }}

-- Step 1: Pull raw unified data
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

        -- Quality tracking
        CASE 
            WHEN NOT {{ validate_sentiment('sentiment_score') }} THEN 'INVALID_SENTIMENT'
            WHEN headline IS NULL THEN 'NULL_HEADLINE'
            ELSE 'VALID'
        END AS quality_flag

    FROM {{ ref('int_sentiment_unified') }}
    
    {% if is_incremental() %}
        -- 👇 Include a 1-day overlap window to capture late-arriving or reprocessed data
        WHERE published_at >= (
            SELECT COALESCE(MAX(published_at), CAST('1900-01-01' AS DATE)) FROM {{ this }}
        ) - INTERVAL 1 DAY
    {% endif %}
),

-- Step 2: Deduplicate on event ID (keep most recent ingested record)
deduped AS (
    SELECT
        *,
        ROW_NUMBER() OVER (
            PARTITION BY sentiment_event_id
            ORDER BY ingested_at DESC
        ) AS rn
    FROM base_data
)

-- Step 3: Final output
SELECT
    CAST(sentiment_event_id AS VARCHAR) AS sentiment_event_id,
    brand_key,
    CAST(source_key AS INTEGER) AS source_key,
    content_id,
    creator,
    brand,
    headline,
    body_text,
    CAST(engagement_count AS BIGINT) AS engagement_count,
    sentiment_score,
    sentiment_category,
    published_at,
    source,
    ingested_at,

    -- Date components
    CAST(published_at AS DATE) AS published_date,
    CAST(EXTRACT(YEAR FROM published_at) AS BIGINT) AS published_year,
    CAST(EXTRACT(MONTH FROM published_at) AS BIGINT) AS published_month,
    CAST(EXTRACT(DAYOFWEEK FROM published_at) AS BIGINT) AS published_day_of_week,
    CAST(EXTRACT(HOUR FROM published_at) AS BIGINT) AS published_hour,

    quality_flag,

    -- Metadata
    get_current_timestamp() AS _dbt_updated_at,
    '{{ run_started_at }}' AS _dbt_run_timestamp

FROM deduped
WHERE rn = 1
  AND quality_flag = 'VALID'
