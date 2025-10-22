from transformers import pipeline
import torch
# A small, free model trained for text-to-SQL tasks
device = torch.device("cpu")  # force CPU
nl2sql = pipeline("text-generation", model="defog/sqlcoder-7b-2", device=device)


def text_to_sql(question):
    """Converts a natural language question into an approximate SQL query."""
    prompt = f"""
You are an expert SQL generator for a DuckDB database. 
You have access to these tables:
- gold_orders_summary (product_line, total_revenue, avg_order_value)
- silver_orders (order_id, total_price, product_line)
- bronze_orders (order_id, product_line, order_date, total_price)

Write a SQL query for: {question}
Output only valid SQL.
"""
    res = nl2sql(prompt, max_new_tokens=100)
    return res[0]['generated_text']
