{{ config(
    materialized='table',
    tags=['intermediate', 'unified'],
    description='Unified sentiment with surrogate keys and enrichment'
) }}

WITH reddit_refined AS (
    SELECT
        post_id as content_id,
        author as creator,
        brand,
        parent_company,                   
        brand_category,                    
        title as headline,
        body as body_text,
        upvotes as engagement_count,
        sentiment_score,
        created_at as published_at,
        'reddit' as source,
        subreddit,
        ingested_at,
        {{ generate_surrogate_key(['post_id', 'created_at']) }} as content_hash
    FROM {{ ref('stg_reddit__posts') }}
),

news_refined AS (
    SELECT
        article_id as content_id,
        publication as creator,
        brand,
        parent_company,                   
        brand_category,                    
        headline,
        body as body_text,
        0 as engagement_count,
        sentiment_score,
        published_at,
        'news' as source,
        NULL as subreddit, 
        ingested_at,
        {{ generate_surrogate_key(['article_id', 'published_at']) }} as content_hash
    FROM {{ ref('stg_news__articles') }}
),
combined AS (
    SELECT * FROM reddit_refined
    UNION ALL
    SELECT * FROM news_refined
),
combined_with_dedup AS (
    SELECT 
        *,
        ROW_NUMBER() OVER (
            PARTITION BY content_id, published_at 
            ORDER BY ingested_at
        ) as row_num
    FROM combined
),

-- Add surrogate keys
with_surrogate_keys AS (
    SELECT
        {{ generate_surrogate_key(['content_id', 'published_at','row_num']) }} as sentiment_event_id,
        {{ generate_surrogate_key(['brand']) }} as brand_key,
        CASE 
            WHEN source = 'reddit' THEN 1
            WHEN source = 'news' THEN 2
            ELSE 0
        END as source_key,
        combined_with_dedup.*
    FROM combined_with_dedup
),

-- Add business logic
with_business_logic AS (
    SELECT
        *,
        
        -- Sentiment category
        CASE 
            WHEN sentiment_score >= {{ var('sentiment_threshold_positive') }} THEN 'positive'
            WHEN sentiment_score <= {{ var('sentiment_threshold_negative') }} THEN 'negative'
            ELSE 'neutral'
        END as sentiment_category,
        
        -- Engagement score
        ROUND(
            (engagement_count) / 
            NULLIF(MAX(engagement_count) OVER (), 0),
            3
        ) as engagement_percentile,
        
        -- Rank within brand
        ROW_NUMBER() OVER (
            PARTITION BY brand 
            ORDER BY engagement_count DESC
        ) as post_rank_by_brand,
        
        -- 7-day moving average
        AVG(sentiment_score) OVER (
            PARTITION BY brand 
            ORDER BY published_at 
            ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
        ) as moving_avg_sentiment_7d,
        
        -- Trend indicator
        sentiment_score - LAG(sentiment_score) OVER (
            PARTITION BY brand 
            ORDER BY published_at
        ) as sentiment_change
    
    FROM with_surrogate_keys
)

SELECT
    *,
    get_current_timestamp() as _dbt_load_date,
    '{{ run_started_at }}' as _dbt_run_timestamp
FROM with_business_logic
WHERE {{ validate_sentiment('sentiment_score') }}