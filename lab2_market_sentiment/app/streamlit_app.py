import streamlit as st
import pandas as pd
import duckdb
from pathlib import Path
from datetime import datetime, timedelta
import plotly.express as px

# Page config
st.set_page_config(
    page_title="Market Sentiment Dashboard",
    page_icon="📊",
    layout="wide"
)

# Database path
DB_PATH = Path(__file__).parent.parent / "data" / "lab2_market_sentiment.duckdb"

# DB connection
@st.cache_resource
def get_db_connection():
    return duckdb.connect(str(DB_PATH), read_only=True)

# Load sentiment events
@st.cache_data(ttl=300)
def load_sentiment_data():
    conn = get_db_connection()
    df = conn.execute("""
        SELECT *
        FROM fct_sentiment_events
        ORDER BY published_at DESC
    """).df()
    return df

# Load data
try:
    df = load_sentiment_data()
    
    if df.empty:
        st.warning("No sentiment data found. Run the pipeline first:")
        st.code("python pipelines/ingest_sentiment.py && cd dbt && dbt build --profiles-dir .")
        st.stop()
    
    # Sidebar filters
    st.sidebar.header("Filters")
    brands = st.sidebar.multiselect("Select Brands", options=df['brand'].unique(), default=df['brand'].unique())
    sources = st.sidebar.multiselect("Select Sources", options=df['source'].unique(), default=df['source'].unique())
    
    df_filtered = df[(df['brand'].isin(brands)) & (df['source'].isin(sources))]
    
    # KPIs
    st.title("📊 Market Sentiment Dashboard")
    
    # Compute current and last week sentiment
    today = df_filtered['published_at'].max().date()
    start_week = today - timedelta(days=7)
    start_prev_week = start_week - timedelta(days=7)
    
    df_current_week = df_filtered[df_filtered['published_at'].dt.date > start_week]
    df_prev_week = df_filtered[(df_filtered['published_at'].dt.date > start_prev_week) & (df_filtered['published_at'].dt.date <= start_week)]
    
    total_posts = len(df_current_week)
    avg_sentiment = df_current_week['sentiment_score'].mean() if total_posts > 0 else 0
    avg_prev = df_prev_week['sentiment_score'].mean() if len(df_prev_week) > 0 else 0
    sentiment_delta = avg_sentiment - avg_prev if len(df_prev_week) > 0 else None
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Posts (7d)", total_posts)
    with col2:
        st.metric("Avg Sentiment (7d)", f"{avg_sentiment:.2f}")
    with col3:
        if sentiment_delta is not None:
            st.metric("Sentiment Δ vs Last Week", f"{sentiment_delta:+.2f}")
        else:
            st.metric("Sentiment Δ vs Last Week", "N/A")
    with col4:
        st.metric("Total Brands", df_filtered['brand'].nunique())
    
    # Weekly sentiment trend
    st.subheader("📈 Sentiment Trend Over Time")
    df_trend = df_filtered.copy()
    df_trend['week_start'] = df_trend['published_at'].dt.to_period('W').apply(lambda r: r.start_time)
    df_weekly = df_trend.groupby('week_start').agg(avg_sentiment=('sentiment_score','mean')).reset_index()
    
    fig_trend = px.line(
        df_weekly,
        x='week_start',
        y='avg_sentiment',
        title="Average Sentiment (Weekly)",
        labels={'week_start':'Week Start','avg_sentiment':'Avg Sentiment'},
        markers=True
    )
    fig_trend.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)
    st.plotly_chart(fig_trend, use_container_width=True)
    
    # Source distribution (small visual)
    st.subheader("📱 Posts by Source")
    source_counts = df_filtered['source'].value_counts().reset_index()
    source_counts.columns = ['source','count']
    fig_source = px.pie(
        source_counts,
        names='source',
        values='count',
        title="Distribution of Posts by Source",
        color='source'
    )
    st.plotly_chart(fig_source, use_container_width=True)
    
    # Top posts driving sentiment
    st.subheader("📝 Top Posts Driving Sentiment")
    top_posts = df_filtered.sort_values('sentiment_score', ascending=False).head(20)
    
    # Display body_text / headline
    st.dataframe(
        top_posts[['published_at','brand','source','sentiment_score','body_text']],
        use_container_width=True,
        height=400
    )
    
    # Footer
    st.markdown("---")
    st.caption(f"Last updated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')} | Total posts in view: {len(df_filtered)}")
    
except Exception as e:
    st.error(f"❌ Error loading data: {str(e)}")
    st.info("Make sure to run the pipeline first:")
    st.code("python pipelines/ingest_sentiment.py && cd dbt && dbt build --profiles-dir .")
