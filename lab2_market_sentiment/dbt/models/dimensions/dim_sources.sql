{{ config(
    materialized='table',
    tags=['dimension']
) }}

SELECT
    1 as source_key,
    'reddit' as source_name,
    'Social Media' as source_type,
    'https://reddit.com' as source_url,
    'User-generated content and discussions' as description,
    TRUE as is_active
UNION ALL
SELECT
    2 as source_key,
    'news' as source_name,
    'News Media' as source_type,
    'https://newsapi.org' as source_url,
    'Professional journalism and news articles' as description,
    TRUE as is_active