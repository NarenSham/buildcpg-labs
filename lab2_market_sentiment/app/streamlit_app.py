"""
Simple Streamlit dashboard for sentiment analysis.
"""
import streamlit as st
import pandas as pd
import duckdb
import plotly.express as px
from pathlib import Path
from datetime import datetime

# Page config
st.set_page_config(
    page_title="Market Sentiment | Lab 02",
    page_icon="📊",
    layout="wide"
)

DB_PATH = Path(__file__).parent.parent / "data" / "lab2_market_sentiment.duckdb"

@st.cache_resource
def get_db_connection():
    """Get DuckDB connection."""
    return duckdb.connect(str(DB_PATH))

@st.cache_data(ttl=300)
def load_daily_sentiment():
    """Load daily sentiment data."""
    conn = get_db_connection()
    return conn.execute("""
        SELECT * FROM mart_daily_sentiment
        ORDER BY sentiment_date DESC
        LIMIT 1000
    """).df()

@st.cache_data(ttl=300)
def load_sentiment_events():
    """Load all sentiment events."""
    conn = get_db_connection()
    return conn.execute("""
        SELECT * FROM fct_sentiment_events
        ORDER BY published_at DESC
        LIMIT 2000
    """).df()

# Header
st.title("Market Sentiment Pipeline")
st.markdown("*Real-time CPG brand sentiment monitoring from Reddit & news sources*")

# Metrics
try:
    df_daily = load_daily_sentiment()
    df_events = load_sentiment_events()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Records", len(df_events))
    
    with col2:
        st.metric("Total Brands", df_events['brand'].nunique())
    
    with col3:
        st.metric("Avg Sentiment", f"{df_events['sentiment_score'].mean():.2f}")
    
    with col4:
        positive_pct = (df_events['sentiment_category'] == 'positive').sum() / len(df_events) * 100
        st.metric("Positive %", f"{positive_pct:.1f}%")
    
    # Sentiment trend
    st.subheader("Sentiment Trend")
    df_trend = df_daily.groupby('sentiment_date')[['avg_sentiment']].mean().reset_index()
    
    fig_trend = px.line(
        df_trend,
        x='sentiment_date',
        y='avg_sentiment',
        title='Average Sentiment Over Time',
        labels={'sentiment_date': 'Date', 'avg_sentiment': 'Avg Sentiment'}
    )
    st.plotly_chart(fig_trend, use_container_width=True)
    
    # Brand comparison
    st.subheader("Brand Sentiment Comparison")
    df_brand_summary = df_daily.groupby('brand').agg({
        'avg_sentiment': 'mean',
        'content_count': 'sum'
    }).reset_index().sort_values('avg_sentiment', ascending=True)
    
    fig_brands = px.bar(
        df_brand_summary,
        x='avg_sentiment',
        y='brand',
        orientation='h',
        title='Average Sentiment by Brand',
        labels={'avg_sentiment': 'Avg Sentiment', 'brand': 'Brand'}
    )
    st.plotly_chart(fig_brands, use_container_width=True)
    
    # Distribution
    st.subheader("Sentiment Category Distribution")
    category_dist = df_events['sentiment_category'].value_counts()
    
    fig_dist = px.pie(
        values=category_dist.values,
        names=category_dist.index,
        title='Sentiment Distribution'
    )
    st.plotly_chart(fig_dist, use_container_width=True)
    
    # Raw data explorer
    st.subheader("Raw Data Explorer")
    st.dataframe(
        df_events[['brand', 'headline', 'sentiment_score', 'sentiment_category', 'source', 'published_at']],
        use_container_width=True,
        height=400
    )
    
    # Footer
    st.markdown("---")
    st.caption(f"Last updated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")
    
except Exception as e:
    st.error(f"Error loading data: {str(e)}")
    st.info("Make sure to run the pipeline first: `python pipelines/ingest_sentiment.py && cd dbt && dbt build`")