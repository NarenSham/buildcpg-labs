
    
    

select
    product_line as unique_field,
    count(*) as n_records

from "lab1_sales_performance"."raw_gold"."gold_orders_summary"
where product_line is not null
group by product_line
having count(*) > 1


