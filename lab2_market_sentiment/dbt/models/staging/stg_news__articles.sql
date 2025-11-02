{{ config(
    materialized='ephemeral',
    tags=['staging', 'news'],
    description='Raw news articles'
) }}

SELECT
    article_id,
    publication,
    brand,
    headline,
    body,
    url,
    published_at,
    sentiment_score,
    source,
    ingested_at,
    get_current_timestamp() as _loaded_at
FROM read_csv_auto('../data/raw/news_real.csv')
WHERE article_id IS NOT NULL