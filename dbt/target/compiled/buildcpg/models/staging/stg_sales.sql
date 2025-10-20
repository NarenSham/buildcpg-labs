SELECT
  order_id::TEXT AS order_id,
  sku_id,
  CAST(order_date AS DATE) AS order_date,
  region,
  COALESCE(sales, 0) AS sales,
  CASE WHEN promo_flag IN (1, '1', true) THEN 1 ELSE 0 END AS promo_flag,
  discount,
  stock_on_hand
FROM "buildcpg"."main"."bronze_sales"
WHERE order_date IS NOT NULL