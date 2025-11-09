{{ config(
    materialized='table',
    tags=['dimension']
) }}

WITH brand_data AS (
    SELECT 
        brand,
        -- Use MAX to pick one value if there are slight variations
        MAX(parent_company) as parent_company,
        MAX(brand_category) as category
    FROM {{ ref('int_sentiment_unified') }}
    WHERE row_num = 1  -- Only use deduplicated records
    GROUP BY brand
)

SELECT
    {{ generate_surrogate_key(['brand']) }} as brand_key,
    brand,
    parent_company,
    category,
    CASE 
        WHEN parent_company IN ('The Coca-Cola Company', 'PepsiCo Inc.', 'Unilever PLC', 
                                'The Procter & Gamble Company', 'Nestlé S.A.') 
        THEN 'Public'
        ELSE 'Private'
    END as company_type,
    TRUE as is_active,
    get_current_timestamp() as _dbt_created_at,
    '{{ run_started_at }}' as _dbt_run_timestamp
FROM brand_data