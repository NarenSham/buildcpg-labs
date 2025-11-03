"""
Simple sentiment data ingestion.
Generates synthetic Reddit and news data.
"""
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Paths
LAB_ROOT = Path(__file__).parent.parent
DATA_DIR = LAB_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"

def ensure_directories():
    """Create all required directories."""
    for d in [RAW_DIR, DATA_DIR / "bronze", DATA_DIR / "silver", DATA_DIR / "gold"]:
        d.mkdir(parents=True, exist_ok=True)
    logger.info(f"Directories created at {DATA_DIR}")

def generate_reddit_data(n_records=500):
    """Generate synthetic Reddit data."""
    brands = ["Coca-Cola", "PepsiCo", "Unilever", "Procter & Gamble", "Nestlé"]
    
    data = {
        "post_id": [f"reddit_{i:05d}" for i in range(n_records)],
        "author": [f"user_{np.random.randint(1000, 9999)}" for _ in range(n_records)],
        "brand": np.random.choice(brands, n_records),
        "title": [f"Post about brand {i}" for i in range(n_records)],
        "body": [f"This is a discussion about CPG products #{i}" for i in range(n_records)],
        "upvotes": np.random.randint(1, 5000, n_records),
        "comments_count": np.random.randint(0, 500, n_records),
        "created_at": [
            (datetime.utcnow() - timedelta(days=np.random.randint(1, 90))).isoformat()
            for _ in range(n_records)
        ],
        "sentiment_score": np.random.uniform(-1, 1, n_records).round(3),
        "source": "reddit",
        "ingested_at": datetime.utcnow().isoformat(),
    }
    
    return pd.DataFrame(data)

def generate_news_data(n_records=300):
    """Generate synthetic news data."""
    brands = ["Coca-Cola", "PepsiCo", "Unilever", "Procter & Gamble", "Nestlé"]
    publications = ["Forbes", "Reuters", "Bloomberg", "WSJ", "TechCrunch"]
    
    data = {
        "article_id": [f"news_{i:05d}" for i in range(n_records)],
        "publication": np.random.choice(publications, n_records),
        "brand": np.random.choice(brands, n_records),
        "headline": [f"News: {brand} announces new product {i}" for i, brand in enumerate(np.random.choice(brands, n_records))],
        "body": [f"Article content about CPG market #{i}" for i in range(n_records)],
        "url": [f"https://example.com/article-{i}" for i in range(n_records)],
        "published_at": [
            (datetime.utcnow() - timedelta(days=np.random.randint(1, 90))).isoformat()
            for _ in range(n_records)
        ],
        "sentiment_score": np.random.uniform(-1, 1, n_records).round(3),
        "source": "news",
        "ingested_at": datetime.utcnow().isoformat(),
    }
    
    return pd.DataFrame(data)

def ingest_reddit_data():
    """Ingest Reddit data."""
    try:
        logger.info("🔄 Fetching Reddit data...")
        df_reddit = generate_reddit_data(n_records=500)
        
        reddit_path = RAW_DIR / "reddit_real.csv"
        df_reddit.to_csv(reddit_path, index=False)
        
        logger.info(f"Reddit data ingested: {len(df_reddit)} records → {reddit_path}")
        return {"source": "reddit", "records": len(df_reddit), "status": "success"}
    except Exception as e:
        logger.error(f"Reddit ingestion failed: {str(e)}")
        return {"source": "reddit", "records": 0, "status": "failed"}

def ingest_news_data():
    """Ingest news data."""
    try:
        logger.info("🔄 Fetching news data...")
        df_news = generate_news_data(n_records=300)
        
        news_path = RAW_DIR / "news_real.csv"
        df_news.to_csv(news_path, index=False)
        
        logger.info(f"News data ingested: {len(df_news)} records → {news_path}")
        return {"source": "news", "records": len(df_news), "status": "success"}
    except Exception as e:
        logger.error(f"News ingestion failed: {str(e)}")
        return {"source": "news", "records": 0, "status": "failed"}

def main():
    """Main ingestion flow."""
    ensure_directories()
    results = []
    results.append(ingest_reddit_data())
    results.append(ingest_news_data())
    logger.info(f"Ingestion complete. Results: {results}")
    return results

if __name__ == "__main__":
    main()