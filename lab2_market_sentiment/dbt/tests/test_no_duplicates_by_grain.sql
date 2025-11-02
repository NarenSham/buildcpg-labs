{% test no_duplicates_by_grain(model, column_name) %}
  
  SELECT
    {{ column_name }},
    COUNT(*) as occurrence_count
  FROM {{ model }}
  GROUP BY {{ column_name }}
  HAVING COUNT(*) > 1

{% endtest %}