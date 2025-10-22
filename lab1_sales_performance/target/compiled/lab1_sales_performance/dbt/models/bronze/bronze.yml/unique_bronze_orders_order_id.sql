
    
    

select
    order_id as unique_field,
    count(*) as n_records

from "lab1_sales_performance"."raw_bronze"."bronze_orders"
where order_id is not null
group by order_id
having count(*) > 1


