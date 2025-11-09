"""
Prune old data from DuckDB to keep database size manageable.
Keeps data from last 90 days.
"""
import duckdb
from pathlib import Path
import logging
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Correct path: lab2_market_sentiment/data/
DATA_DIR = Path(__file__).parent / "data"
DB_PATH = DATA_DIR / "lab2_market_sentiment.duckdb"

# Configuration
RETENTION_DAYS = 90  # Keep 90 days of raw data

def prune_old_data():
    """Remove data older than RETENTION_DAYS."""
    
    if not DB_PATH.exists():
        logger.warning(f"No database found at {DB_PATH}, skipping pruning")
        return
    
    cutoff_date = datetime.utcnow() - timedelta(days=RETENTION_DAYS)
    
    logger.info(f"🧹 Pruning data older than {cutoff_date.strftime('%Y-%m-%d')}")
    logger.info(f"   Database: {DB_PATH.absolute()}")
    
    conn = duckdb.connect(str(DB_PATH))
    
    # Check current size
    before_count = conn.execute("SELECT COUNT(*) FROM fct_sentiment_events").fetchone()[0]
    logger.info(f"   Before: {before_count:,} records")
    
    # Delete old raw events
    conn.execute(f"""
        DELETE FROM fct_sentiment_events 
        WHERE published_at < '{cutoff_date.isoformat()}'
    """)
    
    # Vacuum to reclaim space
    conn.execute("VACUUM")
    
    after_count = conn.execute("SELECT COUNT(*) FROM fct_sentiment_events").fetchone()[0]
    deleted_count = before_count - after_count
    
    logger.info(f"   After: {after_count:,} records")
    logger.info(f"   Deleted: {deleted_count:,} old records")
    
    # Get database size
    size_mb = DB_PATH.stat().st_size / (1024 * 1024)
    logger.info(f"   Database size: {size_mb:.2f} MB")
    
    if size_mb > 90:
        logger.warning(f"⚠️  Database is {size_mb:.2f} MB - approaching GitHub 100MB limit!")
        logger.info("   Consider reducing RETENTION_DAYS or moving to cloud storage")
    
    conn.close()
    logger.info("✅ Pruning complete")

if __name__ == "__main__":
    prune_old_data()