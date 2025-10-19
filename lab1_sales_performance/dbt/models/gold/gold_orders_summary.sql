-- Aggregate sales by product
select
    product_id,
    sum(quantity) as total_quantity,
    sum(total_price) as total_revenue
from {{ ref('silver_orders') }}
group by product_id
