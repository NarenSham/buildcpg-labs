# Lab 2: Setup Guide

This guide will help you set up the Market Sentiment Analysis pipeline from scratch.

## Prerequisites

### System Requirements

- **Python**: 3.11 or higher
- **Git**: For cloning the repository
- **GitHub Account**: For Actions automation (optional but recommended)
- **4GB RAM minimum**: For DuckDB operations

### API Keys Required

You'll need to obtain API keys from the following services:

1. **Reddit API** (free)
2. **News API** (free tier available)

## Step 1: Clone the Repository

```bash
# Clone the main repository
git clone https://github.com/yourusername/buildcpg-labs.git
cd buildcpg-labs/lab2_market_sentiment
```

## Step 2: Set Up Python Environment

### Option A: Using venv (Recommended)

```bash
# Create virtual environment
python3.11 -m venv venv

# Activate it
# On macOS/Linux:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Option B: Using conda

```bash
# Create conda environment
conda create -n lab2 python=3.11
conda activate lab2

# Install dependencies
pip install -r requirements.txt
```

### Verify Installation

```bash
# Check installations
python -c "import duckdb; print(f'DuckDB: {duckdb.__version__}')"
python -c "import streamlit; print(f'Streamlit: {streamlit.__version__}')"
dbt --version
```

Expected output:
```
DuckDB: 0.9.1
Streamlit: 1.28.1
Core:
  - installed: 1.7.0
  - latest:    X.X.X
```

## Step 3: Obtain API Keys

### Reddit API Setup

1. **Go to**: [https://www.reddit.com/prefs/apps](https://www.reddit.com/prefs/apps)
2. **Click**: "Create App" or "Create Another App"
3. **Fill in**:
   - Name: `CPG Sentiment Tracker`
   - App type: Choose "script"
   - Description: `Market sentiment analysis for CPG brands`
   - About URL: (leave blank)
   - Redirect URI: `http://localhost:8080`
4. **Click**: "Create app"
5. **Save**:
   - **Client ID**: The string under "personal use script"
   - **Client Secret**: The "secret" value

### News API Setup

1. **Go to**: [https://newsapi.org/register](https://newsapi.org/register)
2. **Register** for a free account
3. **Verify** your email
4. **Copy** your API key from the dashboard

**Free Tier Limits**:
- 100 requests per day
- Up to 100 results per request
- Historical data: Last 30 days

## Step 4: Configure Environment Variables

### Create `.env` File

```bash
# Create .env file in lab2_market_sentiment directory
cat > .env << 'EOF'
# Reddit API Credentials
REDDIT_CLIENT_ID=your_reddit_client_id_here
REDDIT_CLIENT_SECRET=your_reddit_client_secret_here
REDDIT_USER_AGENT="CPG Sentiment Tracker v1.0 by /u/yourusername"

# News API Credentials
NEWS_API_KEY=your_newsapi_key_here
EOF
```

### Verify Configuration

```bash
# Test that environment variables load correctly
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print('Reddit ID:', os.getenv('REDDIT_CLIENT_ID')[:8] + '...')"
```

## Step 5: Set Up Shared Brand Taxonomy

The brand taxonomy is shared across all labs in `buildcpg-labs/shared/config/`.

### Verify Shared Config Exists

```bash
# Check if shared config exists
ls -la ../shared/config/brand_taxonomy.yaml
```

### Optional: Create Lab-Specific Overrides

If you want to add lab-specific brands without modifying the shared config:

```bash
# Create lab-specific config directory
mkdir -p config

# Create override file
cat > config/brand_taxonomy.yaml << 'EOF'
# Lab 2 specific brand additions
beverages:
  local_brewery:
    parent: "Local Craft Brewery"
    brands:
      - name: "Local IPA"
        category: "Craft Beer"
EOF
```

The ingestion script will automatically:
1. Load shared config first
2. Merge with lab-specific overrides (if they exist)

## Step 6: Initialize DuckDB Database

### Create Data Directories

```bash
# Create all required directories
mkdir -p data/raw data/bronze data/silver data/gold
```

### Initialize dbt

```bash
# Navigate to dbt directory
cd dbt

# Install dbt packages (dbt_expectations)
dbt deps

# Run initial build (will create database and all tables)
dbt build --profiles-dir .
```

Expected output:
```
Completed successfully

Done. PASS=25 WARN=0 ERROR=0 SKIP=0 TOTAL=25
```

### Verify Database Creation

```bash
# Check if database was created
ls -lh ../data/lab2_market_sentiment.duckdb

# Should show file size (typically 100KB-1MB empty)
```

## Step 7: Run Initial Data Ingestion

### Test API Connections

```bash
# Return to lab root directory
cd ..

# Test Reddit API
python -c "
import praw, os
from dotenv import load_dotenv
load_dotenv()
reddit = praw.Reddit(
    client_id=os.getenv('REDDIT_CLIENT_ID'),
    client_secret=os.getenv('REDDIT_CLIENT_SECRET'),
    user_agent=os.getenv('REDDIT_USER_AGENT')
)
print('✅ Reddit API connected')
print(f'User: {reddit.read_only}')
"

# Test News API
python -c "
from newsapi import NewsApiClient
import os
from dotenv import load_dotenv
load_dotenv()
api = NewsApiClient(api_key=os.getenv('NEWS_API_KEY'))
response = api.get_top_headlines(language='en', page_size=1)
print('✅ News API connected')
print(f'Status: {response.get(\"status\")}')
"
```

### Run Full Ingestion

```bash
# Run the ingestion pipeline
python pipelines/ingest_real_data.py
```

Expected output:
```
INFO - 🔄 Fetching Reddit data...
INFO -   Searching for: Coca-Cola
INFO -   Searching for: PepsiCo
...
INFO - ✅ Reddit data ingested: 500 posts → data/raw/reddit_brands.csv
INFO - 🔄 Fetching news data...
INFO - ✅ News data ingested: 300 articles → data/raw/news_brands.csv
```

### Run dbt Transformations

```bash
# Navigate to dbt directory
cd dbt

# Run full build (incremental models will process new data)
dbt build --profiles-dir .

# Check results
dbt test --profiles-dir .
```

### Verify Data

```bash
# Quick data check using Python
cd ..
python << 'EOF'
import duckdb
conn = duckdb.connect('data/lab2_market_sentiment.duckdb')

# Check record counts
tables = {
    'fct_sentiment_events': 'SELECT COUNT(*) FROM fct_sentiment_events',
    'mart_daily_sentiment': 'SELECT COUNT(*) FROM mart_daily_sentiment',
    'mart_brand_competitive_analysis': 'SELECT COUNT(*) FROM mart_brand_competitive_analysis',
    'mart_trending_topics': 'SELECT COUNT(*) FROM mart_trending_topics'
}

print("\n📊 Data Summary:")
for table, query in tables.items():
    count = conn.execute(query).fetchone()[0]
    print(f"  {table}: {count:,} rows")

# Check brands
brands = conn.execute("SELECT COUNT(DISTINCT brand) FROM fct_sentiment_events").fetchone()[0]
print(f"\n  Unique brands: {brands}")

conn.close()
EOF
```

Expected output:
```
📊 Data Summary:
  fct_sentiment_events: 800 rows
  mart_daily_sentiment: 75 rows
  mart_brand_competitive_analysis: 5 rows
  mart_trending_topics: 40 rows

  Unique brands: 5
```

## Step 8: Launch Streamlit Dashboard

### Start the Dashboard

```bash
# From lab root directory
streamlit run app/streamlit_app.py
```

The dashboard will open in your browser at `http://localhost:8501`

### Test Dashboard Features

1. ✅ **Main Dashboard**: Check KPIs, charts load correctly
2. ✅ **Filters**: Try filtering by date, brand, source
3. ✅ **Competitive Intelligence Page**: Navigate via sidebar
4. ✅ **Data Refresh**: Modify filters and verify updates

## Step 9: Set Up GitHub Actions (Optional)

### Prerequisites

- GitHub repository for your project
- Repository secrets configured

### Add GitHub Secrets

1. Go to your repository on GitHub
2. Navigate to: **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret** for each:
   - `REDDIT_CLIENT_ID`
   - `REDDIT_CLIENT_SECRET`
   - `REDDIT_USER_AGENT`
   - `NEWS_API_KEY`

### Push Workflow File

```bash
# Ensure workflow file is in correct location
ls -la .github/workflows/weekly_pipeline.yml

# Commit and push
git add .github/workflows/weekly_pipeline.yml
git commit -m "Add weekly sentiment pipeline workflow"
git push origin main
```

### Test Manual Trigger

1. Go to your repository → **Actions** tab
2. Select **Weekly Sentiment Pipeline**
3. Click **Run workflow** dropdown
4. Click green **Run workflow** button

Monitor the run in real-time. If successful, you'll see:
- ✅ All steps completed
- Artifact available for download (DuckDB database)

### Schedule Verification

The workflow will now run automatically every Sunday at 2 AM UTC.

## Step 10: Optional Enhancements

### Set Up Prefect Cloud (For Better Observability)

```bash
# Install Prefect
pip install prefect

# Login to Prefect Cloud (free tier)
prefect cloud login

# Deploy flow
python orchestrate_weekly.py
```

### Configure Email Alerts

Add to `orchestrate_weekly.py`:

```python
from prefect.blocks.notifications.email import EmailServerBlock

# In your flow, add error handling:
try:
    sentiment_pipeline()
except Exception as e:
    email_block = EmailServerBlock.load("email-alerts")
    email_block.notify(
        subject="❌ Sentiment Pipeline Failed",
        body=f"Error: {str(e)}"
    )
    raise
```

### Add More Brands

Edit `shared/config/brand_taxonomy.yaml`:

```yaml
beverages:
  starbucks:
    parent: "Starbucks Corporation"
    ticker: "SBUX"
    brands:
      - name: "Starbucks"
        aliases: ["Starbucks Coffee", "SBUX"]
        category: "Coffee"
```

Then re-run ingestion.

## Troubleshooting

### Issue: API Rate Limits

**Error**: `429 Too Many Requests`

**Solution**:
```python
# Reduce posts_per_brand in ingest_real_data.py
limit_per_brand = 10  # Instead of 20
```

### Issue: DuckDB File Locked

**Error**: `IO Error: Could not set lock on file`

**Solution**:
```bash
# Close all connections, then:
rm data/lab2_market_sentiment.duckdb.wal
```

### Issue: dbt Models Fail

**Error**: `Compilation Error`

**Solution**:
```bash
# Clean and rebuild
cd dbt
dbt clean
dbt deps
dbt build --profiles-dir . --full-refresh
```

### Issue: Streamlit Port Already in Use

**Error**: `Address already in use`

**Solution**:
```bash
# Use different port
streamlit run app/streamlit_app.py --server.port 8502
```

### Issue: No Data in Dashboard

**Symptoms**: Empty charts, "No data" messages

**Solution**:
1. Check if ingestion ran: `ls -la data/raw/`
2. Check if dbt ran: `duckdb data/lab2_market_sentiment.duckdb "SELECT COUNT(*) FROM fct_sentiment_events"`
3. Check Streamlit logs for errors

## Verification Checklist

Before considering setup complete, verify:

- [ ] ✅ Python 3.11+ installed
- [ ] ✅ All dependencies installed (`pip list`)
- [ ] ✅ API keys configured in `.env`
- [ ] ✅ Reddit and News API connections tested
- [ ] ✅ dbt models built successfully
- [ ] ✅ All dbt tests passing (20/20)
- [ ] ✅ Data ingested (800+ sentiment events)
- [ ] ✅ Streamlit dashboard loads
- [ ] ✅ Both pages accessible (Main + Competitive Intelligence)
- [ ] ✅ Filters work correctly
- [ ] ✅ GitHub Actions workflow configured (optional)
- [ ] ✅ Manual workflow run successful (optional)

## Next Steps

Once setup is complete:

1. 📖 Read [Lab 2 Overview](../lab2-overview/) for architecture details
2. 🔍 Explore [dbt Model Documentation](../lab2-dbt-docs/)
3. 📊 Customize dashboards in `app/` directory
4. 🔧 Add more brands to taxonomy
5. 🚀 Deploy to production (e.g., Streamlit Cloud)

## Support

If you encounter issues not covered here:

1. Check [Lab 2 Troubleshooting Guide](../lab2-troubleshooting/)
2. Review GitHub Issues
3. Contact: narensham@example.com

---

**Setup Time**: ~30 minutes  
**Difficulty**: Intermediate  
**Last Updated**: November 2025