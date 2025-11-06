"""
Competitive Intelligence Page
Multi-page Streamlit app - Competitive analysis view
"""

import streamlit as st
import pandas as pd
import duckdb
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
from datetime import datetime

st.set_page_config(page_title="Competitive Intelligence", page_icon="🎯", layout="wide")

# Database
DB_PATH = Path(__file__).parent.parent.parent / "data" / "lab2_market_sentiment.duckdb"

@st.cache_resource
def get_db():
    return duckdb.connect(str(DB_PATH), read_only=True)

@st.cache_data(ttl=1800)
def load_competitive_data():
    conn = get_db()
    return conn.execute("SELECT * FROM mart_brand_competitive_analysis ORDER BY share_of_voice_pct DESC").df()

@st.cache_data(ttl=1800)
def load_trending_topics():
    conn = get_db()
    return conn.execute("SELECT * FROM mart_trending_topics WHERE trend_status IN ('HOT', 'TRENDING') ORDER BY trending_score DESC LIMIT 50").df()

# Load data
try:
    df_competitive = load_competitive_data()
    df_topics = load_trending_topics()
except Exception as e:
    st.error(f"Error loading data: {e}")
    st.stop()

# Header
st.title("🎯 Competitive Intelligence Dashboard")

# Filters
col1, col2 = st.columns(2)
with col1:
    companies = sorted(df_competitive['parent_company'].unique())
    selected_companies = st.multiselect("Parent Companies", companies, default=companies)
with col2:
    categories = sorted(df_competitive['brand_category'].unique())
    selected_categories = st.multiselect("Categories", categories, default=categories)

df_filtered = df_competitive[
    (df_competitive['parent_company'].isin(selected_companies)) &
    (df_competitive['brand_category'].isin(selected_categories))
]

# KPIs
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Brands Tracked", len(df_filtered))
with col2:
    st.metric("Total Mentions", f"{df_filtered['total_mentions'].sum():,}")
with col3:
    st.metric("Avg Sentiment", f"{df_filtered['avg_sentiment'].mean():.3f}")
with col4:
    market_leaders = (df_filtered['competitive_position'] == 'MARKET_LEADER').sum()
    st.metric("Market Leaders", market_leaders)

st.markdown("---")

# Share of Voice
st.markdown("## 📢 Share of Voice")

df_sov = df_filtered.nlargest(15, 'share_of_voice_pct')

fig_sov = go.Figure()
fig_sov.add_trace(go.Bar(
    y=df_sov['brand'],
    x=df_sov['share_of_voice_pct'],
    orientation='h',
    marker=dict(
        color=df_sov['avg_sentiment'],
        colorscale='RdYlGn',
        cmin=-1,
        cmax=1,
        colorbar=dict(title="Sentiment")
    ),
    text=df_sov['share_of_voice_pct'].apply(lambda x: f"{x}%"),
    textposition='outside'
))

fig_sov.update_layout(
    title="Top 15 Brands by Share of Voice",
    xaxis_title="Share of Voice (%)",
    height=500,
    yaxis=dict(autorange="reversed")
)

st.plotly_chart(fig_sov, use_container_width=True)

# Competitive Positioning Matrix
st.markdown("## 🎯 Competitive Positioning Matrix")

fig_matrix = px.scatter(
    df_filtered,
    x='volume_percentile',
    y='sentiment_percentile',
    size='total_mentions',
    color='competitive_position',
    hover_data=['brand', 'parent_company'],
    title='Brand Positioning: Sentiment vs Volume',
    color_discrete_map={
        'MARKET_LEADER': '#2ecc71',
        'NICHE_FAVORITE': '#3498db',
        'AT_RISK': '#e74c3c',
        'LOW_VISIBILITY': '#95a5a6',
        'MIDDLE_PACK': '#f39c12'
    }
)

fig_matrix.add_hline(y=0.5, line_dash="dash", line_color="gray", opacity=0.5)
fig_matrix.add_vline(x=0.5, line_dash="dash", line_color="gray", opacity=0.5)
fig_matrix.update_layout(height=600)

st.plotly_chart(fig_matrix, use_container_width=True)

# Trending Topics
st.markdown("## 🔥 Trending Topics")

if not df_topics.empty:
    df_topics_display = df_topics.nlargest(20, 'trending_score')[[
        'brand', 'topic', 'trending_score', 'mention_count', 
        'avg_sentiment', 'trend_status', 'sentiment_tone'
    ]].copy()
    
    df_topics_display['trending_score'] = df_topics_display['trending_score'].round(2)
    df_topics_display['avg_sentiment'] = df_topics_display['avg_sentiment'].round(3)
    
    st.dataframe(df_topics_display, use_container_width=True, hide_index=True)
else:
    st.info("No trending topics data available yet.")

st.markdown("---")
st.caption(f"Last updated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")