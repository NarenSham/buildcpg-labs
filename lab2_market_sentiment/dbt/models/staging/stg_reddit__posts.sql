{{ config(
    materialized='ephemeral',
    tags=['staging', 'reddit'],
    description='Raw Reddit posts with quality flags and deduplication'
) }}

WITH source AS (
    SELECT
        post_id,
        author,
        UPPER(nfc_normalize(brand)) AS brand,
        parent_company,
        brand_category, 
        title,
        body,
        upvotes,
        comments_count,
        created_at,
        sentiment_score,
        source,
        subreddit,                         
        ingested_at,
        get_current_timestamp() as _loaded_at
    FROM read_csv_auto('../data/raw/reddit_brands.csv')
),

-- Quality checks
with_quality_flags AS (
    SELECT
        source.*,
        CASE 
            WHEN post_id IS NULL THEN 'NULL_POST_ID'
            WHEN brand IS NULL THEN 'NULL_BRAND'
            WHEN sentiment_score IS NULL THEN 'NULL_SENTIMENT'
            WHEN sentiment_score < -1 OR sentiment_score > 1 THEN 'INVALID_SENTIMENT_RANGE'
            WHEN created_at > get_current_timestamp() THEN 'FUTURE_DATE'
            ELSE 'VALID'
        END as _data_quality_flag,
        
        -- Duplicate detection
        ROW_NUMBER() OVER (
            PARTITION BY post_id, author, created_at 
            ORDER BY _loaded_at DESC
        ) as _duplicate_rank
    FROM source
),

-- Remove duplicates and invalid records
deduplicated AS (
    SELECT *
    FROM with_quality_flags
    WHERE _duplicate_rank = 1 AND _data_quality_flag = 'VALID'
),

-- Clean and normalize
cleaned AS (
    SELECT
        post_id,
        author,
        UPPER(TRIM(brand)) as brand,
        UPPER(TRIM(parent_company)) as parent_company,     -- ✅ NEW
        UPPER(TRIM(brand_category)) as brand_category,     -- ✅ NEW
        REGEXP_REPLACE(TRIM(title), '\s+', ' ') as title,
        body,
        upvotes,
        comments_count,
        CAST(created_at as TIMESTAMP) as created_at,
        
        -- Sentiment normalization
        ROUND(
            CASE 
                WHEN sentiment_score > 1 THEN 1.0
                WHEN sentiment_score < -1 THEN -1.0
                WHEN sentiment_score IS NULL THEN 0.0
                ELSE sentiment_score
            END,
            3
        ) as sentiment_score,
        
        'reddit' as source,
        subreddit,
        ingested_at,
        _loaded_at
    FROM deduplicated
)

SELECT
    cleaned.*,
    -- Generate lineage hash
    {{ generate_surrogate_key(['post_id', 'author', 'created_at']) }} as _source_hash
FROM cleaned