{% test fact_table_grain(model, unique_id) %}
  
  SELECT
    {{ unique_id }},
    COUNT(*) as occurrence_count
  FROM {{ model }}
  GROUP BY {{ unique_id }}
  HAVING COUNT(*) > 1

{% endtest %}