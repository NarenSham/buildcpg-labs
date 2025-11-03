"""
Market Sentiment Dashboard - Lab 02
📊 Focused on storytelling: brand sentiment trend, top posts, source breakdown
"""

import streamlit as st
import pandas as pd
import duckdb
import plotly.express as px
from pathlib import Path
from datetime import datetime, timedelta

# ===========================
# Page configuration
# ===========================
st.set_page_config(
    page_title="Market Sentiment | Lab 02",
    page_icon="📊",
    layout="wide"
)

# ===========================
# Database path and connection
# ===========================
DB_PATH = Path(__file__).parent.parent / "data" / "lab2_market_sentiment.duckdb"

@st.cache_resource
def get_db_connection():
    return duckdb.connect(str(DB_PATH), read_only=True)

@st.cache_data(ttl=300)
def load_data():
    conn = get_db_connection()
    
    # Load daily sentiment (weekly aggregated for smoother trend)
    df_daily = conn.execute("""
        SELECT 
            brand,
            DATE_TRUNC('week', published_at) AS week_start,
            ROUND(AVG(sentiment_score), 3) AS avg_sentiment,
            SUM(engagement_count) AS total_engagement
        FROM main.mart_daily_sentiment
        GROUP BY brand, DATE_TRUNC('week', published_at)
        ORDER BY week_start ASC
    """).df()
    
    # Load raw sentiment events
    df_events = conn.execute("""
        SELECT
            brand,
            headline,
            body_text,
            sentiment_score,
            source,
            published_at,
            url
        FROM main.fct_sentiment_events
        ORDER BY published_at DESC
        LIMIT 2000
    """).df()
    
    return df_daily, df_events

# ===========================
# Load data
# ===========================
try:
    df_daily, df_events = load_data()
    
    if df_events.empty:
        st.warning("No data available. Run the ingestion pipeline first.")
        st.stop()
    
except Exception as e:
    st.error(f"❌ Error loading data: {e}")
    st.info("Run the ingestion and dbt build first:")
    st.code("python pipelines/ingest_sentiment.py && cd dbt && dbt build --profiles-dir .")
    st.stop()

# ===========================
# Header
# ===========================
st.title("Market Sentiment Dashboard")
st.markdown(
    "*Tracking real-time sentiment trends for CPG brands across Reddit and news sources*"
)

# ===========================
# Top KPIs
# ===========================
st.subheader("📌 Key Metrics")
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total Posts/Articles", len(df_events))

with col2:
    st.metric("Total Brands", df_events['brand'].nunique())

with col3:
    avg_sentiment = df_events['sentiment_score'].mean()
    st.metric("Avg Sentiment Score", f"{avg_sentiment:.2f}")

with col4:
    st.metric("Total Sources", df_events['source'].nunique())

# ===========================
# Filters
# ===========================
st.subheader("🔍 Filter Data")
col1, col2 = st.columns(2)
with col1:
    brands_filter = st.multiselect(
        "Select Brands",
        options=df_events['brand'].unique(),
        default=df_events['brand'].unique()
    )
with col2:
    sources_filter = st.multiselect(
        "Select Sources",
        options=df_events['source'].unique(),
        default=df_events['source'].unique()
    )

df_filtered = df_events[
    (df_events['brand'].isin(brands_filter)) &
    (df_events['source'].isin(sources_filter))
]

df_trend_filtered = df_daily[df_daily['brand'].isin(brands_filter)]

# ===========================
# Sentiment Trend Over Time
# ===========================
st.subheader("📈 Weekly Sentiment Trend")
fig_trend = px.line(
    df_trend_filtered,
    x='week_start',
    y='avg_sentiment',
    color='brand',
    markers=True,
    title='Weekly Average Sentiment by Brand',
    labels={'week_start': 'Week Start', 'avg_sentiment': 'Avg Sentiment'}
)
fig_trend.update_layout(height=400, legend_title_text='Brand', yaxis_range=[-1, 1])
st.plotly_chart(fig_trend, use_container_width=True)

# ===========================
# Source Distribution
# ===========================
st.subheader("📊 Source Distribution")
source_counts = df_filtered['source'].value_counts()
fig_source = px.bar(
    x=source_counts.index,
    y=source_counts.values,
    labels={'x': 'Source', 'y': 'Count'},
    title='Posts/Articles by Source',
    text=source_counts.values
)
fig_source.update_layout(height=300)
st.plotly_chart(fig_source, use_container_width=True)

# ===========================
# Top Posts Driving Sentiment
# ===========================
st.subheader("📝 Top Posts Driving Sentiment")

# Sort by sentiment score
top_positive = df_filtered.sort_values('sentiment_score', ascending=False).head(5)
top_negative = df_filtered.sort_values('sentiment_score', ascending=True).head(5)

def render_posts(df_posts, title_emoji=""):
    for _, row in df_posts.iterrows():
        st.markdown(f"**{title_emoji} Brand:** {row['brand']} | **Score:** {row['sentiment_score']:.2f} | **Source:** {row['source']}")
        st.markdown(f"**Headline:** {row['headline']}")
        st.markdown(f"**Content:** {row['body_text'][:300]}{'...' if len(row['body_text']) > 300 else ''}")
        st.markdown(f"[🔗 Link]({row['url']})")
        st.markdown("---")

st.markdown("#### Top Positive Posts")
render_posts(top_positive, "👍")

st.markdown("#### Top Negative Posts")
render_posts(top_negative, "👎")

# ===========================
# Raw Data Explorer
# ===========================
st.subheader("🔍 Raw Data Table")
st.dataframe(
    df_filtered[['brand', 'headline', 'body_text', 'sentiment_score', 'source', 'published_at', 'url']],
    use_container_width=True,
    height=400
)

# ===========================
# Footer
# ===========================
st.markdown("---")
st.caption(f"Last updated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')} | Records displayed: {len(df_filtered)}")
