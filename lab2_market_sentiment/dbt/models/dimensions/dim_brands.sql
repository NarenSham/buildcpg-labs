{{ config(
    materialized='table',
    tags=['dimension']
) }}

WITH brand_data AS (
    SELECT DISTINCT
        brand,
        parent_company,
        brand_category as category,
        CASE 
            WHEN parent_company IN ('The Coca-Cola Company', 'PepsiCo Inc.', 'Unilever PLC', 
                                    'The Procter & Gamble Company', 'Nestlé S.A.') 
            THEN 'Public'
            ELSE 'Private'
        END as company_type
    FROM {{ ref('int_sentiment_unified') }}
)

SELECT
    {{ generate_surrogate_key(['brand']) }} as brand_key,
    brand,
    parent_company,
    category,
    company_type,
    TRUE as is_active,
    get_current_timestamp() as _dbt_created_at,
    '{{ run_started_at }}' as _dbt_run_timestamp
FROM brand_data