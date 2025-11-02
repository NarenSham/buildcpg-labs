{#
  Validate sentiment is in valid range
  Reusable across models
#}
{% macro validate_sentiment(column_name) %}
    ({{ column_name }} BETWEEN -1 AND 1 AND {{ column_name }} IS NOT NULL)
{% endmacro %}