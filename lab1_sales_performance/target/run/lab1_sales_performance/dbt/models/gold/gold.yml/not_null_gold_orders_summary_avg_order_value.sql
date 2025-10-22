
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select avg_order_value
from "lab1_sales_performance"."raw_gold"."gold_orders_summary"
where avg_order_value is null



  
  
      
    ) dbt_internal_test