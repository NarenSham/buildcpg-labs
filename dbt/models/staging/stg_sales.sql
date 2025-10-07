{{ config(
    materialized='incremental',
    unique_key='sale_id'
) }}

with bronze as (
    select * from {{ ref('bronze_sales') }}
)

select
    sale_id,
    customer_id,
    product_id,
    cast(sale_date as date) as sale_date,
    cast(quantity as integer) as quantity,
    cast(price as double) as price,
    quantity * price as total_amount
from bronze

{% if is_incremental() %}
where sale_date > (select max(sale_date) from {{ this }})
{% endif %}
