
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select total_revenue
from "lab1_sales_performance"."raw_gold"."gold_orders_summary"
where total_revenue is null



  
  
      
    ) dbt_internal_test