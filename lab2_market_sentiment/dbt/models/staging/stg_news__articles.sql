{{ config(
    materialized='ephemeral',
    tags=['staging', 'news'],
    description='Raw news articles'
) }}

SELECT
    article_id,
    publication,
    UPPER(nfc_normalize(brand)) AS brand,
    UPPER(nfc_normalize(parent_company)) AS parent_company, 
    UPPER(nfc_normalize(brand_category)) AS brand_category,
    headline,
    body,
    url,
    published_at,
    sentiment_score,
    source,
    ingested_at,
    get_current_timestamp() as _loaded_at
FROM read_csv_auto('../data/raw/news_brands.csv') --lab2_market_sentiment/data/raw/news_brands.csv
WHERE article_id IS NOT NULL