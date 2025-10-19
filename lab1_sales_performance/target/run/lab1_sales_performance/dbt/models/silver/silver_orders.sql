
  
  create view "lab1"."main"."silver_orders__dbt_tmp" as (
    -- Add calculated columns
select
    *,
    quantity * price as total_price
from "lab1"."main"."bronze_orders"
  );
