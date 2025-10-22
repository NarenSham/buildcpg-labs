import os
import gradio as gr
import duckdb
import pandas as pd
from query_helper import text_to_sql
#from summarize import summarize_df

DB_PATH = os.path.join(os.path.dirname(__file__), "../data/lab1_sales_performance.duckdb")
conn = duckdb.connect(DB_PATH, read_only=True)

# Connect to your local duckdb database
conn = duckdb.connect(DB_PATH, read_only=True)

def summarize_df(df):
    return f"Preview: {df.head(5).to_markdown()}"


def query_sales(question):
    """Takes a natural language question, generates SQL, runs it, and summarizes results."""
    sql = text_to_sql(question)
    try:
        df = conn.execute(sql).fetchdf()
        summary = summarize_df(df, question)
        return f"✅ **Query:** `{sql}`\n\n**Summary:** {summary}", df
    except Exception as e:
        return f"⚠️ Error running query: {e}\n\nSQL tried: `{sql}`", pd.DataFrame()

iface = gr.Interface(
    fn=query_sales,
    inputs=gr.Textbox(label="Ask about sales performance"),
    outputs=[
        gr.Markdown(label="Report Summary"),
        gr.Dataframe(label="Query Results")
    ],
    title="🧠 Lab 1 - Natural Language Reports",
    description="Ask things like 'show top 5 products by revenue' or 'total sales by country'"
)

if __name__ == "__main__":
    iface.launch()
