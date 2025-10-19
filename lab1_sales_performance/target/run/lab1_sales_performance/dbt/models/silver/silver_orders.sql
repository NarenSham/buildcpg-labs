
  
  create view "lab1_sales_performance"."raw_silver"."silver_orders__dbt_tmp" as (
    

-- Add calculated columns and transformations
SELECT
    order_id,
    quantity_ordered,
    price_each,
    order_line_number,
    sales,
    order_date,
    status,
    qtr_id,
    month_id,
    year_id,
    product_line,
    msrp,
    product_code,
    customer_name,
    phone,
    address_line1,
    address_line2,
    city,
    state,
    postal_code,
    country,
    territory,
    contact_last_name,
    contact_first_name,
    deal_size,
    -- Calculated column
    quantity_ordered * price_each as total_price
FROM "lab1_sales_performance"."raw_bronze"."bronze_orders"
WHERE status IS NOT NULL
  );
