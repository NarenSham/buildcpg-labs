{{ config(
    materialized='table',
    tags=['dimension']
) }}

WITH brand_data AS (
    SELECT DISTINCT
        {{ generate_surrogate_key(['brand']) }} as brand_key,
        brand,
        CASE 
            WHEN brand = 'Coca-Cola' THEN 'Beverages'
            WHEN brand = 'PepsiCo' THEN 'Beverages'
            WHEN brand = 'Unilever' THEN 'Personal Care'
            WHEN brand = 'Procter & Gamble' THEN 'Personal Care'
            WHEN brand = 'Nestlé' THEN 'Food & Beverage'
            ELSE 'Other'
        END as category,
        CASE 
            WHEN brand IN ('Coca-Cola', 'PepsiCo') THEN 'Public'
            WHEN brand = 'Unilever' THEN 'Public'
            WHEN brand = 'Procter & Gamble' THEN 'Public'
            WHEN brand = 'Nestlé' THEN 'Public'
            ELSE 'Private'
        END as company_type,
        CASE 
            WHEN brand = 'Coca-Cola' THEN 'The Coca-Cola Company'
            WHEN brand = 'PepsiCo' THEN 'PepsiCo Inc.'
            WHEN brand = 'Unilever' THEN 'Unilever PLC'
            WHEN brand = 'Procter & Gamble' THEN 'The Procter & Gamble Company'
            WHEN brand = 'Nestlé' THEN 'Nestlé S.A.'
            ELSE brand
        END as parent_company,
        TRUE as is_active,
        get_current_timestamp() as _dbt_created_at,
        '{{ run_started_at }}' as _dbt_run_timestamp
    FROM {{ ref('int_sentiment_unified') }}
)

SELECT * FROM brand_data