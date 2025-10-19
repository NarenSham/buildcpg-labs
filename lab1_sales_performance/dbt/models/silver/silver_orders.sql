-- Add calculated columns
select
    *,
    quantity * price as total_price
from {{ ref('bronze_orders') }}
