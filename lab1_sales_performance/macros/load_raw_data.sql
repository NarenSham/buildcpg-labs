{% macro load_raw_data() %}
    create schema if not exists raw;
    create or replace table raw.sales_data as
    select *
    from read_csv_auto('data/raw/sales_data.csv', header=true, encoding='LATIN1');
{% endmacro %}
