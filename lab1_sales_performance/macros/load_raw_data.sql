{% macro load_raw_data() %}
    
    {% if execute %}
        {% do log('🔄 Starting load_raw_data macro...', info=true) %}
        
        -- Create raw schema
        {% do run_query("CREATE SCHEMA IF NOT EXISTS raw") %}
        {% do log('✅ Created raw schema', info=true) %}
        
        -- Load CSV into raw schema
        {% do run_query("CREATE OR REPLACE TABLE raw.sales_data AS SELECT * FROM read_csv_auto('data/raw/sales_data.csv')") %}
        {% do log('✅ Loaded raw.sales_data', info=true) %}
        
        -- Verify load
        {% set result = run_query("SELECT COUNT(*) as cnt FROM raw.sales_data") %}
        {% set count = result.rows[0]['cnt'] %}
        {% do log('✅ raw.sales_data has ' ~ count ~ ' rows', info=true) %}
    {% endif %}
    
{% endmacro %}