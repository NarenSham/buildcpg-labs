# Gold Layer Schema

## gold_orders_summary

**Purpose:** Aggregated sales metrics per product line

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| product_line | VARCHAR | Product category | "Classic Cars" |
| total_orders | INTEGER | Number of orders | 1,234 |
| total_quantity | INTEGER | Total units sold | 5,678 |
| total_revenue | DECIMAL | Total sales amount | $123,456.78 |
| avg_order_value | DECIMAL | Average order value | $99.99 |

**Sample Queries:**
- "What are total sales by product line?"
- "Which product line has the highest revenue?"
- "Show me average order value per category"