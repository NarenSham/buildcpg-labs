{{ config(
    materialized='table',
    tags=['mart', 'topics'],
    description='Trending topics and themes by brand'
) }}

WITH content_exploded AS (
    -- Extract key terms from headlines and body text
    SELECT
        brand,
        parent_company,
        headline,
        body_text,
        sentiment_score,
        sentiment_category,
        published_at,
        source,
        engagement_count,
        
        -- Combine text for analysis
        LOWER(headline || ' ' || COALESCE(body_text, '')) as full_text
        
    FROM {{ ref('fct_sentiment_events') }}
    WHERE published_at >= CURRENT_DATE - INTERVAL '30 days'
),

-- Extract common topic keywords (this is simplified - you'd use NLP in production)
topic_keywords AS (
    SELECT
        brand,
        parent_company,
        
        -- Detect product launches
        CASE WHEN full_text LIKE '%new%' OR full_text LIKE '%launch%' OR full_text LIKE '%debut%' 
             THEN 'Product Launch' END as topic_1,
             
        -- Detect pricing/value discussions
        CASE WHEN full_text LIKE '%price%' OR full_text LIKE '%expensive%' OR full_text LIKE '%cheap%' OR full_text LIKE '%value%'
             THEN 'Pricing' END as topic_2,
             
        -- Detect quality issues
        CASE WHEN full_text LIKE '%recall%' OR full_text LIKE '%defect%' OR full_text LIKE '%quality%' OR full_text LIKE '%problem%'
             THEN 'Quality Issues' END as topic_3,
             
        -- Detect sustainability
        CASE WHEN full_text LIKE '%sustain%' OR full_text LIKE '%green%' OR full_text LIKE '%eco%' OR full_text LIKE '%environment%' OR full_text LIKE '%plastic%'
             THEN 'Sustainability' END as topic_4,
             
        -- Detect health/nutrition
        CASE WHEN full_text LIKE '%health%' OR full_text LIKE '%sugar%' OR full_text LIKE '%calor%' OR full_text LIKE '%diet%' OR full_text LIKE '%nutrition%'
             THEN 'Health & Nutrition' END as topic_5,
             
        -- Detect marketing/ads
        CASE WHEN full_text LIKE '%ad%' OR full_text LIKE '%commercial%' OR full_text LIKE '%campaign%' OR full_text LIKE '%super bowl%'
             THEN 'Marketing & Advertising' END as topic_6,
             
        -- Detect comparisons
        CASE WHEN full_text LIKE '%vs%' OR full_text LIKE '%versus%' OR full_text LIKE '%better than%' OR full_text LIKE '%compared to%'
             THEN 'Brand Comparison' END as topic_7,
             
        -- Detect taste/flavor
        CASE WHEN full_text LIKE '%taste%' OR full_text LIKE '%flavor%' OR full_text LIKE '%delicious%' OR full_text LIKE '%yum%'
             THEN 'Taste & Flavor' END as topic_8,
             
        sentiment_score,
        sentiment_category,
        published_at,
        source,
        engagement_count
        
    FROM content_exploded
),

-- Unpivot topics
topics_unpivoted AS (
    SELECT brand, parent_company, topic_1 as topic, sentiment_score, sentiment_category, published_at, source, engagement_count
    FROM topic_keywords WHERE topic_1 IS NOT NULL
    UNION ALL
    SELECT brand, parent_company, topic_2, sentiment_score, sentiment_category, published_at, source, engagement_count
    FROM topic_keywords WHERE topic_2 IS NOT NULL
    UNION ALL
    SELECT brand, parent_company, topic_3, sentiment_score, sentiment_category, published_at, source, engagement_count
    FROM topic_keywords WHERE topic_3 IS NOT NULL
    UNION ALL
    SELECT brand, parent_company, topic_4, sentiment_score, sentiment_category, published_at, source, engagement_count
    FROM topic_keywords WHERE topic_4 IS NOT NULL
    UNION ALL
    SELECT brand, parent_company, topic_5, sentiment_score, sentiment_category, published_at, source, engagement_count
    FROM topic_keywords WHERE topic_5 IS NOT NULL
    UNION ALL
    SELECT brand, parent_company, topic_6, sentiment_score, sentiment_category, published_at, source, engagement_count
    FROM topic_keywords WHERE topic_6 IS NOT NULL
    UNION ALL
    SELECT brand, parent_company, topic_7, sentiment_score, sentiment_category, published_at, source, engagement_count
    FROM topic_keywords WHERE topic_7 IS NOT NULL
    UNION ALL
    SELECT brand, parent_company, topic_8, sentiment_score, sentiment_category, published_at, source, engagement_count
    FROM topic_keywords WHERE topic_8 IS NOT NULL
),

-- Aggregate by topic and brand
topic_aggregates AS (
    SELECT
        brand,
        parent_company,
        topic,
        
        -- Volume
        COUNT(*) as mention_count,
        COUNT(*) FILTER (WHERE source = 'reddit') as reddit_mentions,
        COUNT(*) FILTER (WHERE source = 'news') as news_mentions,
        
        -- Recency
        MAX(published_at) as latest_mention,
        COUNT(*) FILTER (WHERE published_at >= CURRENT_DATE - INTERVAL '7 days') as mentions_last_7d,
        COUNT(*) FILTER (WHERE published_at >= CURRENT_DATE - INTERVAL '14 days') as mentions_last_14d,
        
        -- Sentiment
        ROUND(AVG(sentiment_score), 3) as avg_sentiment,
        COUNT(*) FILTER (WHERE sentiment_category = 'positive') as positive_mentions,
        COUNT(*) FILTER (WHERE sentiment_category = 'negative') as negative_mentions,
        
        -- Engagement
        ROUND(AVG(engagement_count), 0) as avg_engagement,
        MAX(engagement_count) as max_engagement
        
    FROM topics_unpivoted
    GROUP BY brand, parent_company, topic
),

-- Calculate trending score
with_trending_score AS (
    SELECT
        *,
        
        -- Trending score: combines recency, volume growth, and engagement
        ROUND(
            COALESCE(
                (mentions_last_7d * 2.0 / NULLIF(mentions_last_14d, 0)) * 
                LOG(NULLIF(mention_count, 0) + 1) * 
                (1 + COALESCE(avg_engagement, 0) / 100.0),
                0.0  -- Default to 0 if any part is NULL
            ),
            2
        ) as trending_score,
        
        -- Rank topics within each brand
        DENSE_RANK() OVER (PARTITION BY brand ORDER BY mention_count DESC) as topic_rank_for_brand,
        
        -- Overall topic popularity
        SUM(mention_count) OVER (PARTITION BY topic) as topic_total_mentions
        
    FROM topic_aggregates
)

SELECT
    brand,
    parent_company,
    topic,
    
    -- Volume metrics
    mention_count,
    reddit_mentions,
    news_mentions,
    mentions_last_7d,
    mentions_last_14d,
    
    -- Trending metrics
    trending_score,
    topic_rank_for_brand,
    topic_total_mentions,
    
    -- Sentiment metrics
    avg_sentiment,
    positive_mentions,
    negative_mentions,
    ROUND(positive_mentions * 100.0 / NULLIF(mention_count, 0), 1) as positive_pct,
    
    -- Engagement
    avg_engagement,
    max_engagement,
    
    -- Temporal
    latest_mention,
    
    -- Classification
    CASE
        WHEN trending_score > 10 AND mentions_last_7d > mentions_last_14d / 2 THEN 'HOT'
        WHEN trending_score > 5 THEN 'TRENDING'
        WHEN mention_count > 10 THEN 'STABLE'
        ELSE 'EMERGING'
    END as trend_status,
    
    CASE
        WHEN avg_sentiment > 0.3 THEN 'POSITIVE_BUZZ'
        WHEN avg_sentiment < -0.3 THEN 'NEGATIVE_BUZZ'
        ELSE 'NEUTRAL_DISCUSSION'
    END as sentiment_tone,
    
    -- Metadata
    get_current_timestamp() as _created_at,
    '{{ run_started_at }}' as _dbt_run_timestamp
    
FROM with_trending_score
WHERE mention_count >= 3  -- Filter noise
ORDER BY trending_score DESC