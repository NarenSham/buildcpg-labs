"""
Brand Sentiment Intelligence Dashboard
A professional analytics tool for CPG brand monitoring
"""
import streamlit as st
import pandas as pd
import duckdb
from pathlib import Path
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os

# Page config
st.set_page_config(
    page_title="Brand Sentiment Intelligence",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Database path
DB_PATH = Path(__file__).parent.parent.parent / "data" / "lab2_market_sentiment.duckdb"

@st.cache_resource
def get_db(_db_path):
    """Connect to database."""
    if not _db_path.exists():
        st.error(f"Database not found at {_db_path}")
        st.stop()
    return duckdb.connect(str(_db_path), read_only=True)

def get_db_mtime():
    """Get database modification time for cache busting."""
    if DB_PATH.exists():
        return os.path.getmtime(DB_PATH)
    return 0

# Current DB modification time
db_mtime = get_db_mtime()

@st.cache_data(ttl=3600)
def load_competitive_data(_mtime):
    """Load competitive analysis data."""
    conn = get_db(DB_PATH)
    return conn.execute("SELECT * FROM mart_brand_competitive_analysis ORDER BY share_of_voice_pct DESC").df()

@st.cache_data(ttl=3600)
def load_trending_topics(_mtime):
    """Load trending topics data."""
    conn = get_db(DB_PATH)
    return conn.execute("SELECT * FROM mart_trending_topics WHERE trend_status IN ('HOT', 'TRENDING') ORDER BY trending_score DESC LIMIT 50").df()

# Load data
try:
    df_competitive = load_competitive_data(db_mtime)
    df_topics = load_trending_topics(db_mtime)
except Exception as e:
    st.error(f"Error loading data: {e}")
    st.stop()

# Professional styling with light mode enforcement
st.markdown("""
    <style>
    /* Force light mode */
    [data-testid="stAppViewContainer"] {
        background-color: #ffffff;
    }
    [data-testid="stSidebar"] {
        background-color: #f8f9fa;
    }
    [data-testid="stHeader"] {
        background-color: #ffffff;
    }
    
    /* Text colors for light mode */
    .main h1, .main h2, .main h3, .main h4, .main h5, .main h6, .main p, .main label {
        color: #1a1a1a !important;
    }
    
    /* Headers */
    .main-header {
        font-size: 2.5rem;
        font-weight: 600;
        color: #1a1a1a;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #666;
        margin-bottom: 1rem;
    }
    
    /* Data freshness badge */
    .freshness-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 12px;
        font-size: 0.875rem;
        font-weight: 500;
        margin-bottom: 1rem;
    }
    .freshness-fresh {
        background-color: #d4edda;
        color: #155724;
        border: 1px solid #c3e6cb;
    }
    .freshness-recent {
        background-color: #fff3cd;
        color: #856404;
        border: 1px solid #ffeaa7;
    }
    .freshness-stale {
        background-color: #f8d7da;
        color: #721c24;
        border: 1px solid #f5c6cb;
    }
    
    /* Insight box */
    .insight-box {
        background-color: #f0f4ff;
        border-left: 4px solid #667eea;
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 4px;
        color: #1a1a1a;
    }
    
    /* Metrics */
    div[data-testid="stMetricValue"] {
        font-size: 2rem;
        color: #1a1a1a !important;
    }
    div[data-testid="stMetricLabel"] {
        color: #666 !important;
    }
    
    /* Selectbox and input styling */
    div[data-baseweb="select"] > div {
        background-color: #ffffff;
        border-color: #d1d5db;
    }
    
    /* Expander styling */
    div[data-testid="stExpander"] {
        background-color: #ffffff;
        border: 1px solid #e5e7eb;
        border-radius: 4px;
    }
    div[data-testid="stExpander"] summary {
        color: #1a1a1a !important;
    }
    
    /* Dataframe styling */
    .dataframe {
        color: #1a1a1a !important;
    }
    
    /* Tab styling */
    button[data-baseweb="tab"] {
        color: #1a1a1a !important;
    }
    button[data-baseweb="tab"][aria-selected="true"] {
        color: #667eea !important;
        border-bottom-color: #667eea !important;
    }
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

@st.cache_data(ttl=3600)
def load_sentiment_data(_mtime):
    conn = get_db_connection()
    df = conn.execute("""
        SELECT *
        FROM main.fct_sentiment_events
        ORDER BY published_at DESC
    """).df()
    return df

@st.cache_data(ttl=3600)
def load_daily_aggregates(_mtime):
    conn = get_db_connection()
    df = conn.execute("""
        SELECT *
        FROM main.mart_daily_sentiment
        ORDER BY sentiment_date DESC
    """).df()
    return df

# Load data
try:
    df_events = load_sentiment_data(db_mtime)
    df_daily = load_daily_aggregates(db_mtime)
    
    if df_events.empty:
        st.warning("No data found. Run the pipeline:")
        st.code("python pipelines/ingest_real_data.py && cd dbt && dbt build --profiles-dir .")
        st.stop()
    
    # Convert datetime - ensure timezone-naive
    df_events['published_at'] = pd.to_datetime(df_events['published_at']).dt.tz_localize(None)
    df_daily['sentiment_date'] = pd.to_datetime(df_daily['sentiment_date']).dt.tz_localize(None)
    
    # ============= HEADER =============
    st.markdown('<div class="main-header">Brand Sentiment Intelligence</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Real-time consumer perception monitoring from social media and news sources</div>', unsafe_allow_html=True)

    # Data Freshness Badge
    if DB_PATH.exists():
        db_updated = datetime.fromtimestamp(os.path.getmtime(DB_PATH))
        age = datetime.now() - db_updated
        
        if age.days == 0:
            hours_ago = age.seconds // 3600
            if hours_ago == 0:
                freshness_text = f"✨ Updated less than an hour ago"
            else:
                freshness_text = f"✨ Updated {hours_ago}h ago"
            freshness_class = "freshness-fresh"
        elif age.days < 7:
            freshness_text = f"📅 Updated {age.days} day{'s' if age.days > 1 else ''} ago"
            freshness_class = "freshness-recent"
        else:
            freshness_text = f"⏰ Updated {age.days} days ago"
            freshness_class = "freshness-stale"
        
        st.markdown(
            f'<div class="freshness-badge {freshness_class}">{freshness_text} • Last refresh: {db_updated.strftime("%b %d, %Y at %I:%M %p UTC")}</div>',
            unsafe_allow_html=True
        )
        
        # Add manual refresh button
        if st.button("🔄 Refresh Data Cache"):
            st.cache_data.clear()
            st.rerun()
    else:
        st.error("Database not found")
    
    # ============= BRAND SELECTION (CHANGED: Parent Company → Brand) =============
    st.markdown("---")
    st.markdown("### Select Brand to Analyze")
    
    col1, col2, col3 = st.columns([2, 2, 1])
    
    with col1:
        # Get unique parent companies
        parent_companies = sorted(df_events['parent_company'].dropna().unique())
        selected_parent = st.selectbox(
            "Parent CPG Company",
            options=['All Companies'] + parent_companies,
            index=0,
            help="Select the parent company (e.g., PepsiCo, Unilever)"
        )
    
    with col2:
        # Filter brands by selected parent company
        if selected_parent == 'All Companies':
            brand_info = df_events[['brand', 'parent_company', 'brand_category']].drop_duplicates().sort_values(['parent_company', 'brand'])
        else:
            brand_info = df_events[df_events['parent_company'] == selected_parent][['brand', 'parent_company', 'brand_category']].drop_duplicates().sort_values('brand')
        
        brand_options = [f"{row['brand']} ({row['brand_category']})" for _, row in brand_info.iterrows()]
        brand_map = {f"{row['brand']} ({row['brand_category']})": row['brand'] for _, row in brand_info.iterrows()}
        
        selected_brand_display = st.selectbox(
            "Brand",
            options=brand_options,
            index=0,
            help="Select the specific brand to analyze"
        )
        selected_brand = brand_map[selected_brand_display]
    
    with col3:
        analysis_period = st.selectbox(
            "Time Period",
            options=[7, 14, 30, 60, 90],
            format_func=lambda x: f"Last {x} days",
            index=0
        )
    
    # Filter data for selected brand
    df_brand = df_events[df_events['brand'] == selected_brand].copy()
    
    if df_brand.empty:
        st.warning(f"No data available for {selected_brand}")
        st.stop()
    
    # Date filtering
    end_date = df_brand['published_at'].max()
    start_date = end_date - pd.Timedelta(days=analysis_period)
    df_period = df_brand[df_brand['published_at'] >= start_date].copy()
    
    # Get comparison period
    comparison_start = start_date - pd.Timedelta(days=analysis_period)
    df_comparison = df_brand[
        (df_brand['published_at'] >= comparison_start) & 
        (df_brand['published_at'] < start_date)
    ].copy()
    
    # ============= EXECUTIVE SUMMARY =============
    st.markdown("---")
    st.markdown("### Executive Summary")
    
    # Calculate key metrics
    current_mentions = len(df_period)
    previous_mentions = len(df_comparison)
    mention_change = ((current_mentions - previous_mentions) / previous_mentions * 100) if previous_mentions > 0 else 0
    
    current_sentiment = df_period['sentiment_score'].mean()
    previous_sentiment = df_comparison['sentiment_score'].mean() if len(df_comparison) > 0 else 0
    sentiment_change = current_sentiment - previous_sentiment
    
    positive_count = (df_period['sentiment_category'] == 'positive').sum()
    negative_count = (df_period['sentiment_category'] == 'negative').sum()
    neutral_count = (df_period['sentiment_category'] == 'neutral').sum()
    
    positive_pct = (positive_count / current_mentions * 100) if current_mentions > 0 else 0
    negative_pct = (negative_count / current_mentions * 100) if current_mentions > 0 else 0
    
    prev_positive_pct = ((df_comparison['sentiment_category'] == 'positive').sum() / previous_mentions * 100) if previous_mentions > 0 else 0
    positive_pct_change = positive_pct - prev_positive_pct
    
    # Display metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Total Mentions",
            f"{current_mentions:,}",
            delta=f"{mention_change:+.1f}%",
            help=f"Mentions in the last {analysis_period} days vs previous {analysis_period} days"
        )
    
    with col2:
        st.metric(
            "Average Sentiment",
            f"{current_sentiment:.3f}",
            delta=f"{sentiment_change:+.3f}",
            delta_color="normal",
            help="Scale: -1 (very negative) to +1 (very positive)"
        )
    
    with col3:
        st.metric(
            "Positive Share",
            f"{positive_pct:.1f}%",
            delta=f"{positive_pct_change:+.1f}pp",
            help="Percentage of mentions with positive sentiment"
        )
    
    with col4:
        net_sentiment = positive_pct - negative_pct
        prev_net = prev_positive_pct - ((df_comparison['sentiment_category'] == 'negative').sum() / previous_mentions * 100) if previous_mentions > 0 else 0
        net_change = net_sentiment - prev_net
        st.metric(
            "Net Sentiment",
            f"{net_sentiment:+.1f}%",
            delta=f"{net_change:+.1f}pp",
            help="Positive % minus Negative %"
        )
    
    # Key insight box
    if sentiment_change > 0.05:
        sentiment_direction = "improving"
        trend_color = "#155724"
    elif sentiment_change < -0.05:
        sentiment_direction = "declining"
        trend_color = "#721c24"
    else:
        sentiment_direction = "stable"
        trend_color = "#383d41"
    
    st.markdown(f"""
    <div class="insight-box">
        <strong>Key Insight:</strong> {selected_brand} sentiment is <span style="color: {trend_color}; font-weight: 600;">{sentiment_direction}</span> 
        with {current_mentions:,} mentions over the past {analysis_period} days. 
        The brand maintains a {positive_pct:.1f}% positive sentiment rate with a net sentiment of {net_sentiment:+.1f}%.
    </div>
    """, unsafe_allow_html=True) 
   
   
    # ============= SENTIMENT TREND =============
    st.markdown("---")
    st.markdown("### Sentiment Trajectory")
    
    # Daily trend
    df_daily_brand = df_daily[
        (df_daily['brand'] == selected_brand) &
        (df_daily['sentiment_date'] >= start_date)
    ].sort_values('sentiment_date')
    
    # Create dual-axis chart
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    # Add sentiment line
    fig.add_trace(
        go.Scatter(
            x=df_daily_brand['sentiment_date'],
            y=df_daily_brand['avg_sentiment'],
            name='Average Sentiment',
            line=dict(color='#667eea', width=3),
            mode='lines+markers'
        ),
        secondary_y=False
    )
    
    # Add volume bars
    fig.add_trace(
        go.Bar(
            x=df_daily_brand['sentiment_date'],
            y=df_daily_brand['content_count'],
            name='Daily Mentions',
            marker_color='rgba(102, 126, 234, 0.2)',
            showlegend=True
        ),
        secondary_y=True
    )
    
    # Add reference line at 0
    fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5, secondary_y=False)
    
    # Update layout
    fig.update_xaxes(title_text="Date")
    fig.update_yaxes(title_text="Average Sentiment Score", secondary_y=False)
    fig.update_yaxes(title_text="Number of Mentions", secondary_y=True)
    
    fig.update_layout(
        height=400,
        hovermode='x unified',
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1)
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # ============= SENTIMENT DISTRIBUTION =============
    st.markdown("---")
    st.markdown("### Sentiment Distribution")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        # Sentiment breakdown
        sentiment_data = pd.DataFrame({
            'Sentiment': ['Positive', 'Neutral', 'Negative'],
            'Count': [positive_count, neutral_count, negative_count],
            'Percentage': [positive_pct, (neutral_count/current_mentions*100), negative_pct]
        })
        
        fig_pie = px.pie(
            sentiment_data,
            values='Count',
            names='Sentiment',
            color='Sentiment',
            color_discrete_map={
                'Positive': '#28a745',
                'Neutral': '#6c757d',
                'Negative': '#dc3545'
            },
            hole=0.4
        )
        fig_pie.update_traces(textposition='inside', textinfo='percent+label')
        fig_pie.update_layout(height=350, showlegend=False)
        st.plotly_chart(fig_pie, use_container_width=True)
    
    with col2:
        # Sentiment score distribution
        fig_hist = px.histogram(
            df_period,
            x='sentiment_score',
            nbins=30,
            color_discrete_sequence=['#667eea'],
            labels={'sentiment_score': 'Sentiment Score', 'count': 'Frequency'}
        )
        fig_hist.add_vline(x=0, line_dash="dash", line_color="gray")
        fig_hist.add_vline(x=current_sentiment, line_dash="dash", line_color="red", 
                          annotation_text=f"Avg: {current_sentiment:.3f}")
        fig_hist.update_layout(height=350, showlegend=False)
        st.plotly_chart(fig_hist, use_container_width=True)
    
    # ============= SOURCE & CHANNEL BREAKDOWN =============
    st.markdown("---")
    st.markdown("### Channel Performance")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Source split
        source_sentiment = df_period.groupby('source').agg({
            'sentiment_score': 'mean',
            'content_id': 'count'
        }).reset_index()
        source_sentiment.columns = ['source', 'avg_sentiment', 'mentions']
        
        fig_source = go.Figure()
        fig_source.add_trace(go.Bar(
            x=source_sentiment['source'],
            y=source_sentiment['mentions'],
            name='Mentions',
            marker_color='#667eea',
            text=source_sentiment['mentions'],
            textposition='outside'
        ))
        fig_source.update_layout(
            title='Mentions by Source',
            height=300,
            showlegend=False
        )
        st.plotly_chart(fig_source, use_container_width=True)
    
    with col2:
        # Sentiment by source
        fig_sent_source = go.Figure()
        fig_sent_source.add_trace(go.Bar(
            x=source_sentiment['source'],
            y=source_sentiment['avg_sentiment'],
            marker_color=source_sentiment['avg_sentiment'].apply(
                lambda x: '#28a745' if x > 0.1 else '#dc3545' if x < -0.1 else '#6c757d'
            ),
            text=source_sentiment['avg_sentiment'].round(3),
            textposition='outside'
        ))
        fig_sent_source.add_hline(y=0, line_dash="dash", line_color="gray")
        fig_sent_source.update_layout(
            title='Average Sentiment by Source',
            height=300,
            showlegend=False
        )
        st.plotly_chart(fig_sent_source, use_container_width=True)
    
    # ============= WHAT PEOPLE ARE SAYING =============
    st.markdown("---")
    st.markdown("### What People Are Saying")
    
    # Create tabs for sentiment categories
    tab1, tab2, tab3, tab4 = st.tabs(["Positive Comments", "Negative Comments", "Neutral Comments", "Top Highlights"])
    
    with tab1:
        st.markdown(f"**{positive_count} positive mentions** — See what customers appreciate")
        positive_data = df_period[df_period['sentiment_category'] == 'positive'].sort_values('sentiment_score', ascending=False)
        
        if len(positive_data) > 0:
            for idx, row in positive_data.head(15).iterrows():
                with st.expander(f"[{row['source'].upper()}] {row['headline'][:100]}... | Score: {row['sentiment_score']:.3f} | {row['published_at'].strftime('%Y-%m-%d')}"):
                    st.markdown(f"**Published:** {row['published_at'].strftime('%Y-%m-%d %H:%M')}")
                    st.markdown(f"**Source:** {row['source'].title()}" + (f" — r/{row['subreddit']}" if pd.notna(row.get('subreddit')) else ""))
                    st.markdown(f"**Sentiment Score:** {row['sentiment_score']:.3f}")
                    st.markdown(f"**Engagement:** {row['engagement_count']:,}")
                    st.markdown("---")
                    st.markdown(f"**Headline:** {row['headline']}")
                    if pd.notna(row.get('body_text')) and row['body_text']:
                        st.markdown(f"**Full Text:**\n\n{row['body_text'][:1000]}{'...' if len(str(row['body_text'])) > 1000 else ''}")
        else:
            st.info("No positive mentions in this period")
    
    with tab2:
        st.markdown(f"**{negative_count} negative mentions** — Understand pain points and complaints")
        negative_data = df_period[df_period['sentiment_category'] == 'negative'].sort_values('sentiment_score')
        
        if len(negative_data) > 0:
            for idx, row in negative_data.head(15).iterrows():
                with st.expander(f"[{row['source'].upper()}] {row['headline'][:100]}... | Score: {row['sentiment_score']:.3f} | {row['published_at'].strftime('%Y-%m-%d')}"):
                    st.markdown(f"**Published:** {row['published_at'].strftime('%Y-%m-%d %H:%M')}")
                    st.markdown(f"**Source:** {row['source'].title()}" + (f" — r/{row['subreddit']}" if pd.notna(row.get('subreddit')) else ""))
                    st.markdown(f"**Sentiment Score:** {row['sentiment_score']:.3f}")
                    st.markdown(f"**Engagement:** {row['engagement_count']:,}")
                    st.markdown("---")
                    st.markdown(f"**Headline:** {row['headline']}")
                    if pd.notna(row.get('body_text')) and row['body_text']:
                        st.markdown(f"**Full Text:**\n\n{row['body_text'][:1000]}{'...' if len(str(row['body_text'])) > 1000 else ''}")
        else:
            st.info("No negative mentions in this period")
    
    with tab3:
        st.markdown(f"**{neutral_count} neutral mentions** — General discussions and observations")
        neutral_data = df_period[df_period['sentiment_category'] == 'neutral'].sort_values('published_at', ascending=False)
        
        if len(neutral_data) > 0:
            for idx, row in neutral_data.head(15).iterrows():
                with st.expander(f"[{row['source'].upper()}] {row['headline'][:100]}... | Score: {row['sentiment_score']:.3f} | {row['published_at'].strftime('%Y-%m-%d')}"):
                    st.markdown(f"**Published:** {row['published_at'].strftime('%Y-%m-%d %H:%M')}")
                    st.markdown(f"**Source:** {row['source'].title()}" + (f" — r/{row['subreddit']}" if pd.notna(row.get('subreddit')) else ""))
                    st.markdown(f"**Sentiment Score:** {row['sentiment_score']:.3f}")
                    st.markdown(f"**Engagement:** {row['engagement_count']:,}")
                    st.markdown("---")
                    st.markdown(f"**Headline:** {row['headline']}")
                    if pd.notna(row.get('body_text')) and row['body_text']:
                        st.markdown(f"**Full Text:**\n\n{row['body_text'][:1000]}{'...' if len(str(row['body_text'])) > 1000 else ''}")
        else:
            st.info("No neutral mentions in this period")
    
    with tab4:
        st.markdown("**Key highlights across all sentiment categories**")
        
        col_a, col_b = st.columns(2)
        
        with col_a:
            st.markdown("**Most Positive**")
            top_positive = df_period.nlargest(5, 'sentiment_score')[
                ['published_at', 'source', 'headline', 'sentiment_score', 'engagement_count']
            ].copy()
            if len(top_positive) > 0:
                top_positive['published_at'] = top_positive['published_at'].dt.strftime('%Y-%m-%d')
                top_positive['sentiment_score'] = top_positive['sentiment_score'].round(3)
                top_positive.columns = ['Date', 'Source', 'Content', 'Sentiment', 'Engagement']
                st.dataframe(top_positive, use_container_width=True, hide_index=True)
        
        with col_b:
            st.markdown("**Most Negative**")
            top_negative = df_period.nsmallest(5, 'sentiment_score')[
                ['published_at', 'source', 'headline', 'sentiment_score', 'engagement_count']
            ].copy()
            if len(top_negative) > 0:
                top_negative['published_at'] = top_negative['published_at'].dt.strftime('%Y-%m-%d')
                top_negative['sentiment_score'] = top_negative['sentiment_score'].round(3)
                top_negative.columns = ['Date', 'Source', 'Content', 'Sentiment', 'Engagement']
                st.dataframe(top_negative, use_container_width=True, hide_index=True)
        
        st.markdown("**Most Engaged (Reddit only)**")
        top_engaged = df_period[df_period['source'] == 'reddit'].nlargest(10, 'engagement_count')[
            ['published_at', 'subreddit', 'headline', 'sentiment_score', 'engagement_count']
        ].copy()
        if not top_engaged.empty:
            top_engaged['published_at'] = top_engaged['published_at'].dt.strftime('%Y-%m-%d')
            top_engaged['sentiment_score'] = top_engaged['sentiment_score'].round(3)
            top_engaged.columns = ['Date', 'Subreddit', 'Content', 'Sentiment', 'Engagement']
            st.dataframe(top_engaged, use_container_width=True, hide_index=True)
        else:
            st.info("No Reddit data available for this period")
    
    # ============= ANOMALIES & ALERTS =============
    if not df_daily_brand.empty:
        anomalies = df_daily_brand[df_daily_brand['anomaly_flag'] == 'ANOMALY']
        
        if len(anomalies) > 0:
            st.markdown("---")
            st.markdown("### Anomaly Detection")
            st.warning(f"Detected {len(anomalies)} day(s) with statistically unusual sentiment patterns (>2 standard deviations)")
            
            anomaly_display = anomalies[[
                'sentiment_date', 'avg_sentiment', 'z_score_sentiment', 'content_count'
            ]].copy()
            anomaly_display.columns = ['Date', 'Avg Sentiment', 'Z-Score', 'Mentions']
            anomaly_display['Avg Sentiment'] = anomaly_display['Avg Sentiment'].round(3)
            anomaly_display['Z-Score'] = anomaly_display['Z-Score'].round(2)
            st.dataframe(anomaly_display, use_container_width=True, hide_index=True)
    
    # ============= FOOTER =============
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.caption(f"Last updated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")
    with col2:
        st.caption(f"Analyzing {current_mentions:,} mentions across {analysis_period} days")
    with col3:
        st.caption(f"Data range: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")

except Exception as e:
    st.error(f"Error loading data: {str(e)}")
    st.info("Make sure the pipeline has run:")
    st.code("python pipelines/ingest_real_data.py && cd dbt && dbt build --profiles-dir .")
    
    with st.expander("Debug Information"):
        st.write(f"Database path: {DB_PATH}")
        st.write(f"Database exists: {DB_PATH.exists()}")
        st.exception(e)