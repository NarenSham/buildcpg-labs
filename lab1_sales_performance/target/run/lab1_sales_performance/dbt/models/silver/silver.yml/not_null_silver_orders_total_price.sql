
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select total_price
from "lab1_sales_performance"."raw_silver"."silver_orders"
where total_price is null



  
  
      
    ) dbt_internal_test