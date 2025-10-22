
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select product_line
from "lab1_sales_performance"."raw_gold"."gold_orders_summary"
where product_line is null



  
  
      
    ) dbt_internal_test