"""
Weekly orchestration pipeline for brand sentiment analysis.
Runs every Sunday at 2 AM to refresh dashboard data.

This script is designed to work with GitHub Actions orchestration.
No additional orchestration framework (like Prefect) is needed.
"""

from pathlib import Path
import subprocess
import logging
from datetime import datetime
import sys

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Paths
LAB_ROOT = Path(__file__).parent
DBT_DIR = LAB_ROOT / "dbt"
DATA_DIR = LAB_ROOT / "data"


def check_prerequisites():
    """Verify all required files exist."""
    logger.info("Checking prerequisites...")

    # Create necessary directories
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    (DBT_DIR / "target").mkdir(parents=True, exist_ok=True)
    (DBT_DIR / "logs").mkdir(parents=True, exist_ok=True)

    
    checks = {
        "dbt project": DBT_DIR / "dbt_project.yml",
        "Ingestion script": LAB_ROOT / "pipelines" / "ingest_brands.py"
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
    
    logger.info("✅ Prerequisites check passed")
    return True


def ingest_data():
    """Run data ingestion from Reddit and News APIs."""
    logger.info("=" * 60)
    logger.info("STEP 1: DATA INGESTION")
    logger.info("=" * 60)
    
    try:
        result = subprocess.run(
            [sys.executable, "pipelines/ingest_real_data.py"],
            cwd=LAB_ROOT,
            capture_output=True,
            text=True,
            timeout=1800  # 30 minute timeout
        )
        
        if result.returncode != 0:
            logger.error(f"❌ Ingestion failed with return code {result.returncode}")
            logger.error(f"STDERR: {result.stderr}")
            raise RuntimeError(f"Ingestion failed with code {result.returncode}")
        
        logger.info("✅ Data ingestion completed successfully")
        logger.info(f"STDOUT:\n{result.stdout}")
        
        return {"status": "success", "output": result.stdout}
        
    except subprocess.TimeoutExpired:
        logger.error("❌ Ingestion timed out after 30 minutes")
        raise
    except Exception as e:
        logger.error(f"❌ Ingestion error: {e}")
        raise


def run_dbt_models():
    """Execute dbt transformation pipeline."""
    logger.info("=" * 60)
    logger.info("STEP 2: DBT TRANSFORMATIONS")
    logger.info("=" * 60)
    
    try:
        result = subprocess.run(
            ["dbt", "build", "--profiles-dir", ".","--target", "prod"],
            cwd=DBT_DIR,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,  # Merge stderr into stdout
            text=True,
            timeout=600  # 10 minute timeout
        )

        logger.info(f"dbt output:\n{result.stdout}")
        
        if result.returncode != 0:
            logger.error(f"❌ dbt build failed with return code {result.returncode}")
            logger.error(f"STDERR: {result.stderr}")
            raise RuntimeError(f"dbt failed with code {result.returncode}")
        
        logger.info("✅ dbt models completed successfully")
        logger.info(f"STDOUT:\n{result.stdout}")
        
        return {"status": "success", "output": result.stdout}
        
    except subprocess.TimeoutExpired:
        logger.error("❌ dbt timed out after 10 minutes")
        raise
    except Exception as e:
        logger.error(f"❌ dbt error: {e}")
        raise


def generate_data_quality_report():
    """Generate summary report of data quality."""
    logger.info("=" * 60)
    logger.info("STEP 3: DATA QUALITY REPORT")
    logger.info("=" * 60)
    
    try:
        import duckdb
        
        db_path = DATA_DIR / "lab2_market_sentiment.duckdb"
        
        if not db_path.exists():
            logger.warning(f"⚠️ Database not found at {db_path}")
            return {"status": "warning", "message": "Database not found"}
        
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
        
        conn.close()
        
        # Print formatted report
        logger.info("📊 DATA QUALITY REPORT")
        logger.info("=" * 60)
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
        logger.info("=" * 60)
        
        return stats
        
    except Exception as e:
        logger.error(f"❌ Report generation error: {e}")
        return {"status": "error", "error": str(e)}


def main():
    """Main orchestration function."""
    start_time = datetime.utcnow()
    
    logger.info("\n" + "=" * 60)
    logger.info("🚀 BRAND SENTIMENT PIPELINE")
    logger.info("=" * 60)
    logger.info(f"Started at: {start_time.strftime('%Y-%m-%d %H:%M:%S UTC')}")
    logger.info("=" * 60 + "\n")
    
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
        
        logger.info("\n" + "=" * 60)
        logger.info("✅ PIPELINE COMPLETED SUCCESSFULLY")
        logger.info("=" * 60)
        logger.info(f"Duration: {duration:.0f} seconds ({duration/60:.1f} minutes)")
        logger.info(f"Completed at: {end_time.strftime('%Y-%m-%d %H:%M:%S UTC')}")
        logger.info("=" * 60)
        
        return 0  # Success exit code
        
    except Exception as e:
        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()
        
        logger.error("\n" + "=" * 60)
        logger.error("❌ PIPELINE FAILED")
        logger.error("=" * 60)
        logger.error(f"Error: {str(e)}")
        logger.error(f"Duration before failure: {duration:.0f} seconds")
        logger.error(f"Failed at: {end_time.strftime('%Y-%m-%d %H:%M:%S UTC')}")
        logger.error("=" * 60)
        
        return 1  # Error exit code


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)