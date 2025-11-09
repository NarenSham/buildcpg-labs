# Lab 2: Setup & Deployment Guide

Complete guide for deploying the Market Sentiment Analysis pipeline to production with GitHub + Streamlit Cloud.

## Overview

Lab 2 uses a **serverless, git-based architecture** with:
- ✅ **GitHub** for code, database storage, and orchestration (via Actions)
- ✅ **Streamlit Cloud** for dashboard hosting (free tier)
- ✅ **DuckDB** for embedded analytics database
- ✅ **No traditional cloud infrastructure** required (AWS/GCP/Azure)

**Total Cost**: **$0/month** (using only free tiers)

---

## Prerequisites

Before deployment, ensure you have:

- [ ] GitHub account with repository access
- [ ] Streamlit Cloud account (sign up at [share.streamlit.io](https://share.streamlit.io))
- [ ] Reddit API credentials ([apply here](https://www.reddit.com/prefs/apps))
- [ ] News API key ([register here](https://newsapi.org/register))
- [ ] Local environment tested and working

---

## Step 1: Configure GitHub Repository

### 1.1 Update `.gitignore`

Ensure database is **allowed** but raw CSVs are **blocked**:
```gitignore
# Data - General exclusions
*.csv.bak
*.duckdb.wal
*.duckdb.tmp

# CRITICAL: Allow lab2 data directory FIRST
!lab2_market_sentiment/data/
!lab2_market_sentiment/data/**

# NOW block .duckdb files globally
*.duckdb

# EXCEPT allow the specific production database
!lab2_market_sentiment/data/lab2_market_sentiment.duckdb

# But still ignore raw data files in lab2
lab2_market_sentiment/data/raw/
lab2_market_sentiment/data/*.csv

# Ignore other lab data directories
/data/
lab1_*/data/
lab3_*/data/
```

### 1.2 Commit Database Structure
```bash
# Create directory with placeholder
mkdir -p lab2_market_sentiment/data
touch lab2_market_sentiment/data/.gitkeep

# Commit structure
git add lab2_market_sentiment/data/.gitkeep
git commit -m "Add lab2 data directory structure"
git push
```

### 1.3 Set GitHub Secrets

Go to: **Settings → Secrets and variables → Actions**

Click **"New repository secret"** for each:

| Secret Name | Value | Where to Get It |
|-------------|-------|-----------------|
| `REDDIT_CLIENT_ID` | Your Reddit app client ID | [reddit.com/prefs/apps](https://www.reddit.com/prefs/apps) |
| `REDDIT_CLIENT_SECRET` | Your Reddit app secret | Same as above |
| `REDDIT_USER_AGENT` | `"CPG Sentiment v1.0 by /u/yourname"` | Create your own string |
| `NEWS_API_KEY` | Your NewsAPI key | [newsapi.org](https://newsapi.org) |

**Important**: 
- No quotes around values when adding to GitHub
- No trailing spaces
- Double-check for typos

### 1.4 Enable GitHub Actions Write Permissions

Go to: **Settings → Actions → General**

Under **Workflow permissions**:
- ✅ Select **"Read and write permissions"**
- ✅ Check **"Allow GitHub Actions to create and approve pull requests"**
- Click **Save**

This allows the workflow to commit the updated database back to the repo.

---

## Step 2: Set Up GitHub Actions Workflow

### 2.1 Verify Workflow File

Ensure `.github/workflows/weekly_pipeline.yml` exists with the complete configuration including database commit and pruning steps.

### 2.2 Create Pruning Script

The `lab2_market_sentiment/prune_old_data.py` script should exist to manage database size.

### 2.3 Test Workflow Locally

Before pushing, test the workflow steps locally:
```bash
# Test database creation
python lab2_market_sentiment/orchestrate_weekly.py

# Test pruning
python lab2_market_sentiment/prune_old_data.py

# Verify database size
du -h lab2_market_sentiment/data/lab2_market_sentiment.duckdb
```

---

## Step 3: Test GitHub Actions

### 3.1 Trigger Manual Run

1. Go to your GitHub repository
2. Click **"Actions"** tab
3. Select **"Weekly Sentiment Pipeline"** from the left sidebar
4. Click **"Run workflow"** dropdown (top right)
5. Select branch: `main`
6. Click green **"Run workflow"** button

### 3.2 Monitor Execution

Watch the workflow run in real-time:

- ✅ **Set up Python** (~30s)
- ✅ **Install dependencies** (~2 min)
- ✅ **Run pipeline** (~10 min)
  - Data ingestion from APIs
  - dbt transformations
  - Data quality tests
- ✅ **Prune old data** (~30s)
- ✅ **Commit updated database** (~10s)
- ✅ **Upload artifacts** (~30s)

**Total time**: ~15 minutes

### 3.3 Verify Success

After workflow completes:

**1. Check commit history:**
```bash
git pull
git log --oneline -5 | grep "Weekly data update"
```

**2. Verify database exists:**
```bash
ls -lh lab2_market_sentiment/data/lab2_market_sentiment.duckdb
# Should show file with size (e.g., 15MB)
```

**3. Download artifact (backup):**
- Go to Actions → Completed run
- Scroll to **"Artifacts"** section
- Download `duckdb-database-backup`

---

## Step 4: Deploy to Streamlit Cloud

### 4.1 Sign Up for Streamlit Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Click **"Sign up"**
3. Choose **"Continue with GitHub"**
4. Authorize Streamlit Cloud to access your repositories

### 4.2 Create New App

1. Click **"New app"** button
2. **Repository**: Select `yourusername/buildcpg-labs`
3. **Branch**: `main`
4. **Main file path**: `lab2_market_sentiment/app/streamlit_app.py`
5. **App URL**: Choose a custom URL (e.g., `buildcpg-labs-sentiment`)
6. Click **"Deploy"**

### 4.3 Configure Advanced Settings

Click **"Advanced settings"** before deploying:

**Python version**: `3.11`

**Requirements file**: `lab2_market_sentiment/requirements.txt`

Click **"Deploy"**

### 4.4 Enable Auto-Redeploy

After deployment:

1. Go to app settings (⚙️ icon)
2. Under **"GitHub"** section
3. ✅ Enable **"Auto-deploy on commit"**
4. Click **"Save"**

Now, whenever GitHub Actions commits the updated database, Streamlit will automatically redeploy (~30 seconds).

### 4.5 Test Dashboard

Visit your app URL: `https://your-app-name.streamlit.app/`

**Expected behavior**:
- ✅ Dashboard loads successfully
- ✅ Shows data freshness badge
- ✅ All charts render
- ✅ Filters work correctly
- ✅ Competitive Intelligence page accessible

---

## Step 5: Verify End-to-End Flow

### 5.1 Complete Update Cycle

Test the full pipeline:
```
GitHub Actions Runs (Sunday 2 AM UTC or manual)
    ↓
Fetches data from Reddit + News APIs
    ↓
Runs dbt transformations
    ↓
Prunes old data (>90 days)
    ↓
Commits updated database to GitHub
    ↓
Streamlit Cloud detects commit
    ↓
Auto-redeploys app (~30s)
    ↓
Users see fresh data ✨
```

### 5.2 Verification Checklist

- [ ] GitHub Actions workflow runs successfully
- [ ] Database file committed to repo
- [ ] Database size < 90MB
- [ ] Streamlit app auto-redeploys
- [ ] Dashboard shows fresh data
- [ ] Data freshness badge updates
- [ ] All charts and filters work

---

## Step 6: Monitor & Maintain

### 6.1 Set Up Monitoring

**GitHub Actions Notifications:**
1. Go to Settings → Notifications
2. Enable email notifications for failed workflows

**Streamlit Health Check:**
- Bookmark: `https://your-app.streamlit.app/`
- Check weekly that data is updating

### 6.2 Database Size Management

Monitor database size in workflow logs:
```bash
# In GitHub Actions output, look for:
Database size: 45.2 MB  ✅ Good
Database size: 92.1 MB  ⚠️ Warning - approaching limit
```

**If approaching 100MB limit:**
```python
# Edit lab2_market_sentiment/prune_old_data.py
RETENTION_DAYS = 60  # Reduce from 90
```

### 6.3 Weekly Maintenance Tasks

**Every Sunday after pipeline runs:**
1. ✅ Check Actions tab for green checkmark
2. ✅ Verify dashboard shows updated data
3. ✅ Review any anomalies detected
4. ✅ Check database size in logs

**Monthly:**
1. Review brand taxonomy for new brands
2. Check API usage and costs
3. Update dependencies if needed

---

## Troubleshooting Deployment

### Issue: Workflow fails on database commit

**Error**: `permission denied` or `refusing to allow a GitHub App`

**Solution**:
1. Settings → Actions → General
2. Workflow permissions → "Read and write permissions"
3. Re-run workflow

### Issue: Database not tracked in git

**Error**: `.gitignore` blocking database

**Solution**:
```bash
# Force add database once
git add -f lab2_market_sentiment/data/lab2_market_sentiment.duckdb
git commit -m "Force add production database"
git push

# Future updates will work automatically
```

### Issue: Streamlit not redeploying

**Solution**:
1. Streamlit Cloud → App settings
2. Check "Auto-deploy" is enabled
3. Manually reboot app
4. Check deployment logs for errors

### Issue: Database too large (>100MB)

**Solution**:
```bash
# Reduce retention period
# Edit prune_old_data.py: RETENTION_DAYS = 30

# Run manually to test
python lab2_market_sentiment/prune_old_data.py

# Commit and push
git add lab2_market_sentiment/prune_old_data.py
git commit -m "Reduce data retention to 30 days"
git push

# Wait for next workflow run
```

---

## Production Best Practices

### Security

✅ **Never commit API keys** to repository
✅ **Use GitHub Secrets** for all credentials
✅ **Rotate API keys** every 90 days
✅ **Monitor workflow logs** for exposed secrets

### Performance

✅ **Keep database < 90MB** for GitHub
✅ **Prune old data** automatically
✅ **Cache Streamlit data** (TTL: 5-10 min)
✅ **Use aggregated marts** for dashboards

### Reliability

✅ **Enable workflow notifications**
✅ **Keep artifacts** as backup (90 days)
✅ **Monitor data freshness**
✅ **Test manual triggers** monthly

### Cost Management

✅ **Stay within free tiers**:
- GitHub Actions: 2,000 min/month
- Streamlit Cloud: 1 app free
- Reddit API: Free
- News API: 100 req/day free

---

## Scaling Beyond Free Tier

### When to Upgrade

**GitHub Actions** ($0.008/min):
- Running pipeline daily instead of weekly
- Processing more brands (>20)
- Longer ingestion times

**Streamlit Cloud** ($20/month):
- Multiple apps needed
- Need more resources
- Custom domain required

**News API** ($449/month):
- Need more than 100 requests/day
- Historical data beyond 30 days
- Real-time news required

### Migration to Cloud Storage

If database exceeds 100MB:

**Option 1: AWS S3 + DuckDB**
```python
# Install: pip install s3fs duckdb
import duckdb
conn = duckdb.connect()
conn.execute("INSTALL httpfs")
conn.execute("LOAD httpfs")
conn.execute("SET s3_region='us-east-1'")

# Read from S3
df = conn.execute("SELECT * FROM 's3://bucket/data.parquet'").df()
```

**Option 2: Google Cloud Storage**
```python
from google.cloud import storage
import duckdb

# Download from GCS
client = storage.Client()
bucket = client.bucket('your-bucket')
blob = bucket.blob('lab2_market_sentiment.duckdb')
blob.download_to_filename('local.duckdb')

conn = duckdb.connect('local.duckdb')
```

---

## Deployment Checklist

Before going live:

- [ ] `.gitignore` configured correctly
- [ ] GitHub Secrets added (all 4)
- [ ] Write permissions enabled
- [ ] Workflow file committed
- [ ] Pruning script created
- [ ] Manual workflow run successful
- [ ] Database committed to repo
- [ ] Streamlit Cloud app deployed
- [ ] Auto-redeploy enabled
- [ ] End-to-end test completed
- [ ] Monitoring configured
- [ ] Documentation updated

---

## Support

**Issues**: [GitHub Issues](https://github.com/yourusername/buildcpg-labs/issues)  
**Email**: narensham@example.com  
**Documentation**: [Lab 2 Overview](lab2-overview.md)

---

**Deployment Time**: ~2 hours  
**Last Updated**: November 2025  
**Maintainer**: narensham