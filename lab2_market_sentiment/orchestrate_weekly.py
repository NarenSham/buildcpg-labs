"""
Weekly orchestration pipeline for brand sentiment analysis.
Runs every Sunday at 2 AM to refresh dashboard data.
"""

from prefect import flow, task
from prefect.task_runners import SequentialTaskRunner
from pathlib import Path
import subprocess
import logging
from datetime import datetime
import sys

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Paths
LAB_ROOT = Path(__file__).parent
DBT_DIR = LAB_ROOT / "dbt"
DATA_DIR = LAB_ROOT / "data"


@task(name="Check Prerequisites", retries=0)
def check_prerequisites():
    """Verify all required files exist."""
    logger.info("Checking prerequisites...")
    
    checks = {
        ".env file": LAB_ROOT / ".env",
        "dbt project": DBT_DIR / "dbt_project.yml",
        "Ingestion script": LAB_ROOT / "pipelines" / "ingest_real_data.py"
    }
    
    failed_checks = []
    for check_name, path in checks.items():
        if not path.exists():
            failed_checks.append(f"{check_name} missing at {path}")
            logger.error(f"❌ {check_name} missing")
        else:
            logger.info(f"✅ {check_name} found")
    
    if failed_checks:
        raise FileNotFoundError(f"Prerequisites failed: {', '.join(failed_checks)}")
    
    return True


@task(name="Ingest Data", retries=2, retry_delay_seconds=300)
def ingest_data():
    """Run data ingestion from Reddit and News APIs."""
    logger.info("Starting data ingestion...")
    
    try:
        result = subprocess.run(
            [sys.executable, "pipelines/ingest_real_data.py"],
            cwd=LAB_ROOT,
            capture_output=True,
            text=True,
            timeout=1800  # 30 minute timeout
        )
        
        if result.returncode != 0:
            logger.error(f"Ingestion failed: {result.stderr}")
            raise RuntimeError(f"Ingestion failed with code {result.returncode}")
        
        logger.info("✅ Data ingestion completed")
        logger.info(result.stdout)
        
        return {"status": "success", "output": result.stdout}
        
    except subprocess.TimeoutExpired:
        logger.error("Ingestion timed out after 30 minutes")
        raise
    except Exception as e:
        logger.error(f"Ingestion error: {e}")
        raise


@task(name="Run dbt Models", retries=1)
def run_dbt_models():
    """Execute dbt transformation pipeline."""
    logger.info("Running dbt models...")
    
    try:
        result = subprocess.run(
            ["dbt", "build", "--profiles-dir", "."],
            cwd=DBT_DIR,
            capture_output=True,
            text=True,
            timeout=600  # 10 minute timeout
        )
        
        if result.returncode != 0:
            logger.error(f"dbt build failed: {result.stderr}")
            raise RuntimeError(f"dbt failed with code {result.returncode}")
        
        logger.info("✅ dbt models completed")
        logger.info(result.stdout)
        
        return {"status": "success", "output": result.stdout}
        
    except subprocess.TimeoutExpired:
        logger.error("dbt timed out after 10 minutes")
        raise
    except Exception as e:
        logger.error(f"dbt error: {e}")
        raise


@task(name="Generate Report", retries=0)
def generate_data_quality_report():
    """Generate summary report of data quality."""
    logger.info("Generating data quality report...")
    
    try:
        import duckdb
        import pandas as pd
        
        db_path = DATA_DIR / "lab2_market_sentiment.duckdb"
        conn = duckdb.connect(str(db_path), read_only=True)
        
        # Get summary stats
        stats = {}
        
        stats['fct_sentiment_events'] = conn.execute("SELECT COUNT(*) FROM fct_sentiment_events").fetchone()[0]
        stats['mart_daily_sentiment'] = conn.execute("SELECT COUNT(*) FROM mart_daily_sentiment").fetchone()[0]
        stats['mart_brand_competitive'] = conn.execute("SELECT COUNT(*) FROM mart_brand_competitive_analysis").fetchone()[0]
        stats['mart_trending_topics'] = conn.execute("SELECT COUNT(*) FROM mart_trending_topics").fetchone()[0]
        
        stats['unique_brands'] = conn.execute("SELECT COUNT(DISTINCT brand) FROM fct_sentiment_events").fetchone()[0]
        
        latest = conn.execute("SELECT MAX(published_at) FROM fct_sentiment_events").fetchone()[0]
        stats['latest_data'] = latest
        
        sent = conn.execute("""
            SELECT 
                ROUND(AVG(sentiment_score), 3) as avg_sentiment,
                COUNT(*) FILTER (WHERE sentiment_category = 'positive') as positive_count,
                COUNT(*) FILTER (WHERE sentiment_category = 'negative') as negative_count
            FROM fct_sentiment_events
        """).fetchone()
        stats['avg_sentiment'] = sent[0]
        stats['positive_count'] = sent[1]
        stats['negative_count'] = sent[2]
        
        logger.info("\n" + "="*60)
        logger.info("📊 DATA QUALITY REPORT")
        logger.info("="*60)
        logger.info(f"Timestamp: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
        logger.info(f"\nRecord Counts:")
        logger.info(f"  Sentiment Events: {stats['fct_sentiment_events']:,}")
        logger.info(f"  Daily Aggregates: {stats['mart_daily_sentiment']:,}")
        logger.info(f"  Competitive Analysis: {stats['mart_brand_competitive']:,}")
        logger.info(f"  Trending Topics: {stats['mart_trending_topics']:,}")
        logger.info(f"\nCoverage:")
        logger.info(f"  Unique Brands: {stats['unique_brands']}")
        logger.info(f"  Latest Data: {stats['latest_data']}")
        logger.info(f"\nSentiment:")
        logger.info(f"  Average Score: {stats['avg_sentiment']}")
        logger.info(f"  Positive: {stats['positive_count']:,}")
        logger.info(f"  Negative: {stats['negative_count']:,}")
        logger.info("="*60)
        
        return stats
        
    except Exception as e:
        logger.error(f"Report generation error: {e}")
        return {"status": "error", "error": str(e)}


@flow(
    name="Brand Sentiment Pipeline",
    description="Weekly brand sentiment analysis pipeline",
    task_runner=SequentialTaskRunner()
)
def sentiment_pipeline():
    """Main orchestration flow."""
    start_time = datetime.utcnow()
    logger.info(f"🚀 Starting Brand Sentiment Pipeline at {start_time}")
    
    try:
        # Step 1: Prerequisites
        check_prerequisites()
        
        # Step 2: Ingest data
        ingest_result = ingest_data()
        
        # Step 3: Transform with dbt
        dbt_result = run_dbt_models()
        
        # Step 4: Report
        report = generate_data_quality_report()
        
        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()
        
        logger.info(f"\n✅ Pipeline completed successfully in {duration:.0f} seconds")
        logger.info(f"Dashboard ready at: streamlit run app/streamlit_app.py")
        
        return {
            "status": "success",
            "duration_seconds": duration,
            "timestamp": end_time.isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Pipeline failed: {e}")
        raise


if __name__ == "__main__":
    sentiment_pipeline()