{{ config(
    materialized='table',
    tags=['dimension']
) }}

WITH brand_data AS (
    SELECT DISTINCT
        {{ generate_surrogate_key(['brand']) }} as brand_key,
        brand,
        parent_company,                                    -- ✅ Now comes from data
        brand_category as category,                        -- ✅ Now comes from data
        CASE 
            WHEN parent_company IN ('The Coca-Cola Company', 'PepsiCo Inc.', 'Unilever PLC', 
                                    'The Procter & Gamble Company', 'Nestlé S.A.') 
            THEN 'Public'
            ELSE 'Private'
        END as company_type,
        TRUE as is_active,
        get_current_timestamp() as _dbt_created_at,
        '{{ run_started_at }}' as _dbt_run_timestamp
    FROM {{ ref('int_sentiment_unified') }}
)

SELECT * FROM brand_data