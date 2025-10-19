-- Add calculated columns
select
    *,
    quantity * price as total_price
from "lab1"."main"."bronze_orders"