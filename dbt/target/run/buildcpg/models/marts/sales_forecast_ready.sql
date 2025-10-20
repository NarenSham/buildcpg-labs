
  
  create view "buildcpg"."main"."sales_forecast_ready__dbt_tmp" as (
    SELECT
  sku_id,
  region,
  DATE_TRUNC('week', order_date) AS week,
  SUM(sales) AS total_sales,
  AVG(discount) AS avg_discount,
  AVG(stock_on_hand) AS avg_stock
FROM "buildcpg"."main"."stg_sales"
GROUP BY 1,2,3
  );
