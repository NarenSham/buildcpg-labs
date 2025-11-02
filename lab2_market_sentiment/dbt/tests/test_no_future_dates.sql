-- No records should have future dates
SELECT *
FROM {{ ref('fct_sentiment_events') }}
WHERE published_at > get_current_timestamp()