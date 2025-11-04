"""
Real data ingestion from Reddit and News API with sentiment analysis.
"""
import praw
from newsapi import NewsApiClient
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
import logging
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Paths
LAB_ROOT = Path(__file__).parent.parent
DATA_DIR = LAB_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"

# Brands to track
BRANDS = ["Coca-Cola", "PepsiCo", "Unilever", "Procter & Gamble", "Nestlé"]

# Initialize sentiment analyzer
sentiment_analyzer = SentimentIntensityAnalyzer()


def analyze_sentiment(text: str) -> float:
    """
    Analyze sentiment using VADER.
    Returns compound score between -1 and 1.
    """
    if not text:
        return 0.0
    scores = sentiment_analyzer.polarity_scores(text)
    return scores['compound']


def ingest_reddit_data(limit_per_brand=20):
    """
    Fetch real Reddit posts mentioning CPG brands.
    """
    try:
        logger.info("🔄 Fetching Reddit data...")
        
        # Initialize Reddit API
        reddit = praw.Reddit(
            client_id=os.getenv('REDDIT_CLIENT_ID'),
            client_secret=os.getenv('REDDIT_CLIENT_SECRET'),
            user_agent=os.getenv('REDDIT_USER_AGENT')
        )
        
        all_posts = []
        
        for brand in BRANDS:
            logger.info(f"  Searching for: {brand}")
            
            # Search across multiple subreddits
            subreddits = reddit.subreddit('all')
            
            for post in subreddits.search(brand, limit=limit_per_brand, time_filter='month'):
                # Combine title and selftext for sentiment
                full_text = f"{post.title} {post.selftext}"
                
                post_data = {
                    'post_id': post.id,
                    'author': str(post.author) if post.author else 'deleted',
                    'brand': brand,
                    'title': post.title,
                    'body': post.selftext if post.selftext else post.title,
                    'upvotes': post.score,
                    'comments_count': post.num_comments,
                    'created_at': datetime.fromtimestamp(post.created_utc).isoformat(),
                    'sentiment_score': analyze_sentiment(full_text),
                    'source': 'reddit',
                    'ingested_at': datetime.utcnow().isoformat(),
                    'url': f"https://reddit.com{post.permalink}"
                }
                all_posts.append(post_data)
        
        df = pd.DataFrame(all_posts)
        
        # Save to CSV
        reddit_path = RAW_DIR / "reddit_real.csv"
        df.to_csv(reddit_path, index=False)
        
        logger.info(f"✅ Reddit data ingested: {len(df)} posts → {reddit_path}")
        return {"source": "reddit", "records": len(df), "status": "success"}
        
    except Exception as e:
        logger.error(f"❌ Reddit ingestion failed: {str(e)}")
        return {"source": "reddit", "records": 0, "status": "failed", "error": str(e)}


def ingest_news_data(days_back=7):
    """
    Fetch real news articles mentioning CPG brands.
    """
    try:
        logger.info("🔄 Fetching news data...")
        
        # Initialize News API
        newsapi = NewsApiClient(api_key=os.getenv('NEWS_API_KEY'))
        
        all_articles = []
        from_date = (datetime.utcnow() - timedelta(days=days_back)).strftime('%Y-%m-%d')
        
        for brand in BRANDS:
            logger.info(f"  Searching for: {brand}")
            
            # Search for articles
            response = newsapi.get_everything(
                q=brand,
                from_param=from_date,
                language='en',
                sort_by='relevancy',
                page_size=20  # Free tier limit
            )
            
            for article in response.get('articles', []):
                # Combine title and description for sentiment
                full_text = f"{article.get('title', '')} {article.get('description', '')}"
                
                article_data = {
                    'article_id': article.get('url', '').split('/')[-1][:50],  # Use URL slug as ID
                    'publication': article.get('source', {}).get('name', 'Unknown'),
                    'brand': brand,
                    'headline': article.get('title', ''),
                    'body': article.get('description', '') or article.get('content', ''),
                    'url': article.get('url', ''),
                    'published_at': article.get('publishedAt', datetime.utcnow().isoformat()),
                    'sentiment_score': analyze_sentiment(full_text),
                    'source': 'news',
                    'ingested_at': datetime.utcnow().isoformat()
                }
                all_articles.append(article_data)
        
        df = pd.DataFrame(all_articles)
        
        # Remove duplicates based on URL
        df = df.drop_duplicates(subset=['url'], keep='first')
        
        # Save to CSV
        news_path = RAW_DIR / "news_real.csv"
        df.to_csv(news_path, index=False)
        
        logger.info(f"✅ News data ingested: {len(df)} articles → {news_path}")
        return {"source": "news", "records": len(df), "status": "success"}
        
    except Exception as e:
        logger.error(f"❌ News ingestion failed: {str(e)}")
        return {"source": "news", "records": 0, "status": "failed", "error": str(e)}


def ensure_directories():
    """Create all required directories."""
    for d in [RAW_DIR, DATA_DIR / "bronze", DATA_DIR / "silver", DATA_DIR / "gold"]:
        d.mkdir(parents=True, exist_ok=True)
    logger.info(f"📁 Directories created at {DATA_DIR}")


def main():
    """Main ingestion flow."""
    ensure_directories()
    
    results = []
    results.append(ingest_reddit_data(limit_per_brand=20))
    results.append(ingest_news_data(days_back=7))
    
    logger.info(f"\n📊 Ingestion Summary:")
    for result in results:
        status_emoji = "✅" if result['status'] == 'success' else "❌"
        logger.info(f"  {status_emoji} {result['source']}: {result['records']} records")
    
    return results


if __name__ == "__main__":
    main()