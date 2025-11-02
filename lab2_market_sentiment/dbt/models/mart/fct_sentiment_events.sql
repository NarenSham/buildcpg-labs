{{ config(
    materialized='incremental',
    unique_id='sentiment_event_id',
    incremental_strategy='merge',
    tags=['mart', 'facts'],
    description='Fact table: One row per sentiment event',
    contract={
        'enforced': True,
        'columns': [
            {'name': 'sentiment_event_id', 'data_type': 'string', 'constraints': ['not_null', 'unique']},
            {'name': 'brand_key', 'data_type': 'string', 'constraints': ['not_null']},
            {'name': 'source_key', 'data_type': 'int64'},
            {'name': 'sentiment_score', 'data_type': 'double', 'constraints': ['not_null']},
        ]
    }
) }}

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
    
    -- Date components for easy filtering
    CAST(published_at AS DATE) as published_date,
    EXTRACT(YEAR FROM published_at) as published_year,
    EXTRACT(MONTH FROM published_at) as published_month,
    EXTRACT(DAYOFWEEK FROM published_at) as published_day_of_week,
    EXTRACT(HOUR FROM published_at) as published_hour,
    
    -- Quality tracking
    CASE 
        WHEN NOT {{ validate_sentiment('sentiment_score') }} THEN 'INVALID_SENTIMENT'
        WHEN headline IS NULL THEN 'NULL_HEADLINE'
        ELSE 'VALID'
    END as quality_flag,
    
    -- Metadata
    get_current_timestamp() as _dbt_updated_at,
    '{{ run_started_at }}' as _dbt_run_timestamp

FROM {{ ref('int_sentiment_unified') }}

{% if execute %}
    {% if this.exists %}
        WHERE published_at > (SELECT MAX(published_at) FROM {{ this }})
    {% endif %}
{% endif %}

WHERE quality_flag = 'VALID'