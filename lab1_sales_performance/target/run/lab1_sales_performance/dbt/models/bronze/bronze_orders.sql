
  
    
    

    create  table
      "lab1_sales_performance"."raw_bronze"."bronze_orders__dbt_tmp"
  
    as (
      

-- Rename columns from uppercase to lowercase snake_case
SELECT
    ORDERNUMBER as order_id,
    QUANTITYORDERED as quantity_ordered,
    PRICEEACH as price_each,
    ORDERLINENUMBER as order_line_number,
    SALES as sales,
    ORDERDATE as order_date,
    STATUS as status,
    QTR_ID as qtr_id,
    MONTH_ID as month_id,
    YEAR_ID as year_id,
    PRODUCTLINE as product_line,
    MSRP as msrp,
    PRODUCTCODE as product_code,
    CUSTOMERNAME as customer_name,
    PHONE as phone,
    ADDRESSLINE1 as address_line1,
    ADDRESSLINE2 as address_line2,
    CITY as city,
    STATE as state,
    POSTALCODE as postal_code,
    COUNTRY as country,
    TERRITORY as territory,
    CONTACTLASTNAME as contact_last_name,
    CONTACTFIRSTNAME as contact_first_name,
    DEALSIZE as deal_size
FROM "lab1_sales_performance"."raw"."sales_data"
    );
  
  