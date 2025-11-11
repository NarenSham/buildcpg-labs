"""
Enhanced Market Sentiment Dashboard with Real Data Insights
"""
import streamlit as st
import pandas as pd
import duckdb
from pathlib import Path
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go

# Page config
st.set_page_config(
    page_title="CPG Market Sentiment",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': None,
        'Report a bug': None,
        'About': None
    }
)

# Force light theme
st.markdown("""
    <style>
        /* Force light theme colors */
        .stApp {
            background-color: white;
            color: black;
        }
        [data-testid="stSidebar"] {
            background-color: #f0f2f6;
        }
    </style>
""", unsafe_allow_html=True)


# Database path - POINTING TO DATA FOLDER
DB_PATH = Path(__file__).parent.parent / "data" / "lab2_market_sentiment.duckdb"

# Custom CSS
st.markdown("""
    <style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #1f77b4;
    }
    .positive { color: #28a745; }
    .negative { color: #dc3545; }
    .neutral { color: #6c757d; }
    </style>
""", unsafe_allow_html=True)

# DB connection
@st.cache_resource
def get_db_connection():
    if not DB_PATH.exists():
        st.error(f"Database not found at {DB_PATH}")
        st.info("Run: `cd dbt && dbt build --profiles-dir .`")
        st.stop()
    return duckdb.connect(str(DB_PATH), read_only=True)

# Load sentiment events
@st.cache_data(ttl=300)
def load_sentiment_data():
    conn = get_db_connection()
    df = conn.execute("""
        SELECT *
        FROM main.fct_sentiment_events
        ORDER BY published_at DESC
    """).df()
    return df

@st.cache_data(ttl=300)
def load_daily_aggregates():
    conn = get_db_connection()
    df = conn.execute("""
        SELECT *
        FROM main.mart_daily_sentiment
        ORDER BY sentiment_date DESC
    """).df()
    return df

# Load data
try:
    df_events = load_sentiment_data()
    df_daily = load_daily_aggregates()
    
    if df_events.empty:
        st.warning("⚠️ No data found. Run the pipeline:")
        st.code("python pipelines/ingest_real_data.py && cd dbt && dbt build --profiles-dir .")
        st.stop()
    
    # Convert datetime
    df_events['published_at'] = pd.to_datetime(df_events['published_at'])
    df_daily['sentiment_date'] = pd.to_datetime(df_daily['sentiment_date'])
    
    # ============= HEADER =============
    st.title("📊 CPG Market Sentiment Tracker")
    st.markdown("*Real-time sentiment analysis from Reddit and News sources*")
    
    # ============= SIDEBAR FILTERS =============
    st.sidebar.header("🔍 Filters")
    
    # Date range
    min_date = df_events['published_at'].min().date()
    max_date = df_events['published_at'].max().date()
    
    date_range = st.sidebar.date_input(
        "Date Range",
        value=(max_date - timedelta(days=30), max_date),
        min_value=min_date,
        max_value=max_date
    )
    
    if len(date_range) == 2:
        start_date, end_date = date_range
    else:
        start_date = end_date = date_range[0]
    
    # Brand filter
    brand_counts = df_events['brand'].value_counts()
    st.sidebar.write("**Debug: Top 5 brands by count:**")
    st.sidebar.dataframe(brand_counts.head(5))
    all_brands = brand_counts.index.tolist()  # Already sorted by count (descending)
    st.sidebar.write(f"**First brand in list:** {all_brands[0]}")
    selected_brands = st.sidebar.multiselect(
        "Select Brands",
        options=all_brands,
        default=all_brands
    )
    
    # Source filter
    all_sources = sorted(df_events['source'].unique())
    selected_sources = st.sidebar.multiselect(
        "Select Sources",
        options=all_sources,
        default=all_sources
    )
    
    # Sentiment filter
    sentiment_categories = ['positive', 'neutral', 'negative']
    selected_sentiments = st.sidebar.multiselect(
        "Sentiment Type",
        options=sentiment_categories,
        default=sentiment_categories
    )
    
    # Apply filters
    df_filtered = df_events[
        (df_events['published_at'].dt.date >= start_date) &
        (df_events['published_at'].dt.date <= end_date) &
        (df_events['brand'].isin(selected_brands)) &
        (df_events['source'].isin(selected_sources)) &
        (df_events['sentiment_category'].isin(selected_sentiments))
    ].copy()
    
    if df_filtered.empty:
        st.warning("No data matches your filters. Try adjusting the selections.")
        st.stop()
    
    # ============= KEY METRICS ROW =============
    st.markdown("### 📈 Key Performance Indicators")
    
    # Calculate week-over-week metrics
    today = df_filtered['published_at'].max().date()
    week_start = today - timedelta(days=7)
    prev_week_start = week_start - timedelta(days=7)
    
    df_current = df_filtered[df_filtered['published_at'].dt.date > week_start]
    df_previous = df_filtered[
        (df_filtered['published_at'].dt.date > prev_week_start) &
        (df_filtered['published_at'].dt.date <= week_start)
    ]
    
    # Metrics calculations
    current_count = len(df_current)
    previous_count = len(df_previous)
    count_delta = current_count - previous_count
    count_pct = (count_delta / previous_count * 100) if previous_count > 0 else 0
    
    current_sentiment = df_current['sentiment_score'].mean()
    previous_sentiment = df_previous['sentiment_score'].mean() if len(df_previous) > 0 else 0
    sentiment_delta = current_sentiment - previous_sentiment
    
    positive_pct = (df_current['sentiment_category'] == 'positive').sum() / len(df_current) * 100
    prev_positive_pct = (df_previous['sentiment_category'] == 'positive').sum() / len(df_previous) * 100 if len(df_previous) > 0 else 0
    positive_delta = positive_pct - prev_positive_pct
    
    # Display metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "📝 Total Posts (7d)",
            f"{current_count:,}",
            delta=f"{count_delta:+,} ({count_pct:+.1f}%)",
            help="Total content pieces in the last 7 days vs previous 7 days"
        )
    
    with col2:
        st.metric(
            "💭 Avg Sentiment (7d)",
            f"{current_sentiment:.3f}",
            delta=f"{sentiment_delta:+.3f}",
            delta_color="normal",
            help="Average sentiment score from -1 (negative) to +1 (positive)"
        )
    
    with col3:
        st.metric(
            "✅ Positive Ratio",
            f"{positive_pct:.1f}%",
            delta=f"{positive_delta:+.1f}%",
            help="Percentage of positive sentiment content"
        )
    
    with col4:
        anomaly_count = (df_daily[df_daily['sentiment_date'].dt.date >= start_date]['anomaly_flag'] == 'ANOMALY').sum()
        st.metric(
            "⚠️ Anomalies",
            f"{anomaly_count}",
            help="Days with unusual sentiment patterns (>2 std dev)"
        )
    
    # ============= CHARTS ROW 1 =============
    col_left, col_right = st.columns([2, 1])
    
    with col_left:
        st.markdown("### 📈 Sentiment Trend Over Time")
        
        # Daily aggregation - Fixed to use .size() for counting
        df_trend = df_filtered.groupby(df_filtered['published_at'].dt.date).agg({
            'sentiment_score': 'mean'
        }).reset_index()
        df_count = df_filtered.groupby(df_filtered['published_at'].dt.date).size().reset_index(name='count')
        df_trend = df_trend.merge(df_count, left_on='published_at', right_on='published_at')
        df_trend.columns = ['date', 'avg_sentiment', 'count']
        
        # Create figure with secondary y-axis
        fig_trend = go.Figure()
        
        # Add sentiment line
        fig_trend.add_trace(go.Scatter(
            x=df_trend['date'],
            y=df_trend['avg_sentiment'],
            name='Avg Sentiment',
            line=dict(color='#1f77b4', width=3),
            yaxis='y'
        ))
        
        # Add volume bars
        fig_trend.add_trace(go.Bar(
            x=df_trend['date'],
            y=df_trend['count'],
            name='Volume',
            marker_color='rgba(31, 119, 180, 0.3)',
            yaxis='y2'
        ))
        
        # Add zero line
        fig_trend.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)
        
        fig_trend.update_layout(
            yaxis=dict(title='Average Sentiment', side='left'),
            yaxis2=dict(title='Post Count', side='right', overlaying='y'),
            hovermode='x unified',
            legend=dict(orientation='h', yanchor='bottom', y=1.02),
            height=400
        )
        
        st.plotly_chart(fig_trend, use_container_width=True)
    
    with col_right:
        st.markdown("### 📱 Source Distribution")
        
        source_counts = df_filtered['source'].value_counts().reset_index()
        source_counts.columns = ['source', 'count']
        
        fig_source = px.pie(
            source_counts,
            names='source',
            values='count',
            color='source',
            color_discrete_map={'reddit': '#FF4500', 'news': '#4A90E2'},
            hole=0.4
        )
        fig_source.update_traces(textposition='inside', textinfo='percent+label')
        fig_source.update_layout(height=400, showlegend=False)
        
        st.plotly_chart(fig_source, use_container_width=True)
    
    # ============= CHARTS ROW 2 =============
    col_left2, col_right2 = st.columns(2)
    
    with col_left2:
        st.markdown("### 🏢 Brand Sentiment Comparison")
        
        df_brand = df_filtered.groupby('brand').agg({
            'sentiment_score': 'mean'
        }).reset_index()
        df_brand_count = df_filtered.groupby('brand').size().reset_index(name='count')
        df_brand = df_brand.merge(df_brand_count, on='brand')
        df_brand.columns = ['brand', 'avg_sentiment', 'count']
        df_brand = df_brand.sort_values('avg_sentiment')
        
        fig_brands = px.bar(
            df_brand,
            x='avg_sentiment',
            y='brand',
            orientation='h',
            color='avg_sentiment',
            color_continuous_scale='RdYlGn',
            color_continuous_midpoint=0,
            text='avg_sentiment'
        )
        fig_brands.update_traces(texttemplate='%{text:.3f}', textposition='outside')
        fig_brands.update_layout(height=400, showlegend=False)
        fig_brands.add_vline(x=0, line_dash="dash", line_color="gray")
        
        st.plotly_chart(fig_brands, use_container_width=True)
    
    with col_right2:
        st.markdown("### 🎯 Sentiment Distribution")
        
        sentiment_counts = df_filtered['sentiment_category'].value_counts().reset_index()
        sentiment_counts.columns = ['category', 'count']
        
        fig_dist = px.bar(
            sentiment_counts,
            x='category',
            y='count',
            color='category',
            color_discrete_map={
                'positive': '#28a745',
                'neutral': '#6c757d',
                'negative': '#dc3545'
            },
            text='count'
        )
        fig_dist.update_traces(textposition='outside')
        fig_dist.update_layout(height=400, showlegend=False)
        
        st.plotly_chart(fig_dist, use_container_width=True)
    
    # ============= TOP CONTENT TABLE =============
    st.markdown("### 📰 Most Impactful Content")
    
    tab1, tab2, tab3 = st.tabs(["🔝 Most Positive", "🔻 Most Negative", "🔥 Most Engaged"])
    
    with tab1:
        top_positive = df_filtered.nlargest(15, 'sentiment_score')[
            ['published_at', 'brand', 'source', 'headline', 'sentiment_score', 'engagement_count']
        ].copy()
        top_positive['published_at'] = top_positive['published_at'].dt.strftime('%Y-%m-%d %H:%M')
        top_positive['sentiment_score'] = top_positive['sentiment_score'].round(3)
        st.dataframe(top_positive, use_container_width=True, hide_index=True)
    
    with tab2:
        top_negative = df_filtered.nsmallest(15, 'sentiment_score')[
            ['published_at', 'brand', 'source', 'headline', 'sentiment_score', 'engagement_count']
        ].copy()
        top_negative['published_at'] = top_negative['published_at'].dt.strftime('%Y-%m-%d %H:%M')
        top_negative['sentiment_score'] = top_negative['sentiment_score'].round(3)
        st.dataframe(top_negative, use_container_width=True, hide_index=True)
    
    with tab3:
        top_engaged = df_filtered.nlargest(15, 'engagement_count')[
            ['published_at', 'brand', 'source', 'headline', 'sentiment_score', 'engagement_count']
        ].copy()
        top_engaged['published_at'] = top_engaged['published_at'].dt.strftime('%Y-%m-%d %H:%M')
        top_engaged['sentiment_score'] = top_engaged['sentiment_score'].round(3)
        st.dataframe(top_engaged, use_container_width=True, hide_index=True)
    
    # ============= ANOMALIES SECTION =============
    if anomaly_count > 0:
        st.markdown("### ⚠️ Detected Anomalies")
        df_anomalies = df_daily[
            (df_daily['sentiment_date'].dt.date >= start_date) &
            (df_daily['anomaly_flag'] == 'ANOMALY')
        ][['sentiment_date', 'brand', 'avg_sentiment', 'z_score_sentiment', 'content_count']].sort_values(
            'sentiment_date', ascending=False
        )
        st.dataframe(df_anomalies, use_container_width=True, hide_index=True)
        st.info(f"Found {anomaly_count} day(s) with unusual sentiment. These may indicate significant events affecting brand perception.")
    
    # ============= FOOTER =============
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.caption(f"📅 Last updated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")
    with col2:
        st.caption(f"📊 Showing {len(df_filtered):,} posts from {len(selected_brands)} brands")
    with col3:
        st.caption(f"🗓️ Date range: {start_date} to {end_date}")

except Exception as e:
    st.error(f"❌ Error loading data: {str(e)}")
    st.info("Make sure the pipeline has run:")
    st.code("python pipelines/ingest_real_data.py && cd dbt && dbt build --profiles-dir .")
    
    with st.expander("🔧 Debug Information"):
        st.write(f"Database path: {DB_PATH}")
        st.write(f"Database exists: {DB_PATH.exists()}")
        st.exception(e)