

-- Aggregate sales by product line
SELECT
    product_line,
    COUNT(DISTINCT order_id) as total_orders,
    SUM(quantity_ordered) as total_quantity,
    SUM(total_price) as total_revenue,
    ROUND(AVG(total_price), 2) as avg_order_value
FROM "lab1_sales_performance"."raw_silver"."silver_orders"
GROUP BY product_line
ORDER BY total_revenue DESC