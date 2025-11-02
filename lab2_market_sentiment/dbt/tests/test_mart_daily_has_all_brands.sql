-- Every brand from fact table should appear in daily mart
WITH brands_in_fact AS (
    SELECT DISTINCT brand FROM {{ ref('fct_sentiment_events') }}
),
brands_in_mart AS (
    SELECT DISTINCT brand FROM {{ ref('mart_daily_sentiment') }}
),
missing_brands AS (
    SELECT f.brand
    FROM brands_in_fact f
    LEFT JOIN brands_in_mart m ON f.brand = m.brand
    WHERE m.brand IS NULL
)
SELECT * FROM missing_brands