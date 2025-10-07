{{ config(materialized='table') }}

with sales as (
    select *
    from {{ ref('stg_sales') }}
)

select
    date_trunc('month', sale_date) as month,
    product_id,
    sum(quantity) as total_quantity,
    sum(total_amount) as total_revenue
from sales
group by month, product_id
