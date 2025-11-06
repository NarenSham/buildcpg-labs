{{ config(
    materialized='table',
    tags=['mart', 'competitive'],
    description='Brand competitive intelligence and benchmarking'
) }}

WITH brand_metrics AS (
    SELECT
        brand,
        parent_company,
        brand_category,
        
        -- Volume metrics
        COUNT(*) as total_mentions,
        COUNT(DISTINCT CASE WHEN source = 'reddit' THEN content_id END) as reddit_mentions,
        COUNT(DISTINCT CASE WHEN source = 'news' THEN content_id END) as news_mentions,
        
        -- Sentiment metrics
        ROUND(AVG(sentiment_score), 3) as avg_sentiment,
        ROUND(STDDEV(sentiment_score), 3) as sentiment_volatility,
        
        -- Sentiment distribution
        COUNT(*) FILTER (WHERE sentiment_category = 'positive') as positive_mentions,
        COUNT(*) FILTER (WHERE sentiment_category = 'negative') as negative_mentions,
        COUNT(*) FILTER (WHERE sentiment_category = 'neutral') as neutral_mentions,
        
        -- Engagement (Reddit only)
        ROUND(AVG(CASE WHEN source = 'reddit' THEN engagement_count END), 0) as avg_reddit_engagement,
        MAX(CASE WHEN source = 'reddit' THEN engagement_count END) as max_reddit_engagement,
        
        -- Recency
        MAX(published_at) as most_recent_mention,
        MIN(published_at) as first_mention,
        
        -- Time-based
        COUNT(*) FILTER (WHERE published_at >= CURRENT_DATE - INTERVAL '7 days') as mentions_last_7d,
        COUNT(*) FILTER (WHERE published_at >= CURRENT_DATE - INTERVAL '30 days') as mentions_last_30d
        
    FROM {{ ref('fct_sentiment_events') }}
    GROUP BY brand, parent_company, brand_category
),

-- Calculate share of voice
share_of_voice AS (
    SELECT
        *,
        ROUND(total_mentions * 100.0 / SUM(total_mentions) OVER (), 2) as share_of_voice_pct,
        ROUND(total_mentions * 100.0 / SUM(total_mentions) OVER (PARTITION BY parent_company), 2) as share_within_parent
    FROM brand_metrics
),

-- Calculate competitive positioning
competitive_metrics AS (
    SELECT
        *,
        
        -- Sentiment percentile rank
        PERCENT_RANK() OVER (ORDER BY avg_sentiment) as sentiment_percentile,
        
        -- Volume percentile rank
        PERCENT_RANK() OVER (ORDER BY total_mentions) as volume_percentile,
        
        -- Engagement percentile rank (for Reddit)
        PERCENT_RANK() OVER (ORDER BY avg_reddit_engagement) as engagement_percentile,
        
        -- Category rankings
        DENSE_RANK() OVER (PARTITION BY brand_category ORDER BY avg_sentiment DESC) as sentiment_rank_in_category,
        DENSE_RANK() OVER (PARTITION BY brand_category ORDER BY total_mentions DESC) as volume_rank_in_category,
        
        -- Calculate Net Sentiment Score (positive % - negative %)
        ROUND(
            (positive_mentions * 100.0 / NULLIF(total_mentions, 0)) - 
            (negative_mentions * 100.0 / NULLIF(total_mentions, 0)),
            2
        ) as net_sentiment_score,
        
        -- Engagement rate (for brands with Reddit presence)
        ROUND(
            avg_reddit_engagement / NULLIF(reddit_mentions, 0),
            2
        ) as engagement_rate,
        
        -- Momentum (7d vs 30d growth)
        ROUND(
            (mentions_last_7d * 4.0 - mentions_last_30d) * 100.0 / NULLIF(mentions_last_30d, 0),
            2
        ) as momentum_pct
        
    FROM share_of_voice
),

-- Add competitive context
with_context AS (
    SELECT
        competitive_metrics.*,
        
        -- Category averages for benchmarking
        ROUND(AVG(competitive_metrics.avg_sentiment) OVER (PARTITION BY competitive_metrics.brand_category), 3) as category_avg_sentiment,
        ROUND(AVG(competitive_metrics.total_mentions) OVER (PARTITION BY competitive_metrics.brand_category), 0) as category_avg_mentions,
        ROUND(AVG(competitive_metrics.share_of_voice_pct) OVER (PARTITION BY competitive_metrics.brand_category), 2) as category_avg_sov,
         
        -- Parent company totals
        SUM(competitive_metrics.total_mentions) OVER (PARTITION BY competitive_metrics.parent_company) as parent_total_mentions,
        ROUND(AVG(competitive_metrics.avg_sentiment) OVER (PARTITION BY competitive_metrics.parent_company), 3) as parent_avg_sentiment,
        
        -- Competitive positioning flag
        CASE
            WHEN competitive_metrics.sentiment_percentile >= 0.75 AND competitive_metrics.volume_percentile >= 0.75 THEN 'MARKET_LEADER'
            WHEN competitive_metrics.sentiment_percentile >= 0.75 AND competitive_metrics.volume_percentile < 0.25 THEN 'NICHE_FAVORITE'
            WHEN competitive_metrics.sentiment_percentile < 0.25 AND competitive_metrics.volume_percentile >= 0.75 THEN 'AT_RISK'
            WHEN competitive_metrics.sentiment_percentile < 0.25 AND competitive_metrics.volume_percentile < 0.25 THEN 'LOW_VISIBILITY'
            ELSE 'MIDDLE_PACK'
        END as competitive_position,
        
        -- Sentiment vs category
        CASE
            WHEN competitive_metrics.avg_sentiment > AVG(competitive_metrics.avg_sentiment) OVER (PARTITION BY competitive_metrics.brand_category) + 0.1 THEN 'OUTPERFORMING'
            WHEN competitive_metrics.avg_sentiment < AVG(competitive_metrics.avg_sentiment) OVER (PARTITION BY competitive_metrics.brand_category) - 0.1 THEN 'UNDERPERFORMING'
            ELSE 'AT_PAR'
        END as sentiment_vs_category
        
    FROM competitive_metrics
)

SELECT
    brand,
    parent_company,
    brand_category,
    
    -- Volume metrics
    total_mentions,
    reddit_mentions,
    news_mentions,
    mentions_last_7d,
    mentions_last_30d,
    share_of_voice_pct,
    share_within_parent,
    
    -- Sentiment metrics
    avg_sentiment,
    sentiment_volatility,
    net_sentiment_score,
    positive_mentions,
    negative_mentions,
    neutral_mentions,
    
    -- Engagement metrics
    avg_reddit_engagement,
    max_reddit_engagement,
    engagement_rate,
    
    -- Competitive intelligence
    sentiment_rank_in_category,
    volume_rank_in_category,
    sentiment_percentile,
    volume_percentile,
    engagement_percentile,
    competitive_position,
    sentiment_vs_category,
    momentum_pct,
    
    -- Benchmarks
    category_avg_sentiment,
    category_avg_mentions,
    category_avg_sov,
    parent_avg_sentiment,
    parent_total_mentions,
    
    -- Temporal
    most_recent_mention,
    first_mention,
    
    -- Metadata
    get_current_timestamp() as _created_at,
    '{{ run_started_at }}' as _dbt_run_timestamp
    
FROM with_context
ORDER BY share_of_voice_pct DESC