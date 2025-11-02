-- Sentiment must be between -1 and 1
SELECT *
FROM {{ ref('fct_sentiment_events') }}
WHERE sentiment_score < -1 OR sentiment_score > 1