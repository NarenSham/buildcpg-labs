
  
  create view "lab1_sales_performance"."main"."bronze_orders__dbt_tmp" as (
    select *
from "lab1_sales_performance"."raw"."sales_data"
  );
