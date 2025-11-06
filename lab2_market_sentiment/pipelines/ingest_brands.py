"""
Enhanced brand-level data ingestion with taxonomy support.
Tracks actual consumer brands, not just parent companies.
"""
import praw
from newsapi import NewsApiClient
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import pandas as pd
import yaml
from pathlib import Path
from datetime import datetime, timedelta
import logging
import os
from dotenv import load_dotenv
from collections import defaultdict

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Paths
LAB_ROOT = Path(__file__).parent.parent
SHARED_ROOT = LAB_ROOT.parent / "shared"  # Go up to buildcpg-labs/shared/
DATA_DIR = LAB_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"

# Try shared config first, fall back to lab-specific
SHARED_CONFIG = SHARED_ROOT / "config" / "brand_taxonomy.yaml"
LOCAL_CONFIG = LAB_ROOT / "config" / "brand_taxonomy.yaml"
CONFIG_PATH = SHARED_CONFIG if SHARED_CONFIG.exists() else LOCAL_CONFIG

# Initialize sentiment analyzer
sentiment_analyzer = SentimentIntensityAnalyzer()


def load_brand_taxonomy():
    """
    Load brand taxonomy from YAML config.
    Checks shared config first, then lab-specific config.
    """
    if not CONFIG_PATH.exists():
        logger.error(f"❌ Brand taxonomy not found!")
        logger.info(f"Checked: {SHARED_CONFIG}")
        logger.info(f"Checked: {LOCAL_CONFIG}")
        logger.info("Please create shared/config/brand_taxonomy.yaml")
        raise FileNotFoundError("brand_taxonomy.yaml not found")
    
    logger.info(f"📋 Loading brand taxonomy from: {CONFIG_PATH}")
    
    with open(CONFIG_PATH, 'r') as f:
        taxonomy = yaml.safe_load(f)
    
    # Optionally merge with lab-specific overrides
    if SHARED_CONFIG.exists() and LOCAL_CONFIG.exists() and CONFIG_PATH == SHARED_CONFIG:
        logger.info(f"📋 Merging lab-specific overrides from: {LOCAL_CONFIG}")
        with open(LOCAL_CONFIG, 'r') as f:
            local_taxonomy = yaml.safe_load(f)
            # Merge logic here if needed (e.g., add lab-specific brands)
    
    return taxonomy


def get_all_brands(taxonomy):
    """Extract all brands with their parent company mapping."""
    brands_list = []
    
    for category, companies in taxonomy.items():
        if category == 'collection_config':
            continue
            
        for company_key, company_data in companies.items():
            parent_company = company_data['parent']
            ticker = company_data.get('ticker', '')
            
            for brand in company_data['brands']:
                brands_list.append({
                    'brand_name': brand['name'],
                    'brand_aliases': brand.get('aliases', []),
                    'parent_company': parent_company,
                    'ticker': ticker,
                    'category': brand['category'],
                    'segment': category
                })
    
    return brands_list


def analyze_sentiment(text: str) -> float:
    """Analyze sentiment using VADER."""
    if not text:
        return 0.0
    scores = sentiment_analyzer.polarity_scores(text)
    return scores['compound']


def detect_brand_mentions(text: str, brands_list: list) -> list:
    """
    Detect which brands are mentioned in text.
    Returns list of brand names found.
    """
    text_lower = text.lower()
    mentioned_brands = []
    
    for brand_info in brands_list:
        brand_name = brand_info['brand_name']
        aliases = brand_info['brand_aliases']
        
        # Check main brand name
        if brand_name.lower() in text_lower:
            mentioned_brands.append(brand_info)
            continue
            
        # Check aliases
        for alias in aliases:
            if alias.lower() in text_lower:
                mentioned_brands.append(brand_info)
                break
    
    return mentioned_brands


def ingest_reddit_data(brands_list: list, config: dict):
    """Fetch Reddit posts mentioning consumer brands."""
    try:
        logger.info("🔄 Fetching Reddit data...")
        
        reddit = praw.Reddit(
            client_id=os.getenv('REDDIT_CLIENT_ID'),
            client_secret=os.getenv('REDDIT_CLIENT_SECRET'),
            user_agent=os.getenv('REDDIT_USER_AGENT')
        )
        
        all_posts = []
        limit_per_brand = config['collection_config']['reddit']['posts_per_brand']
        time_filter = config['collection_config']['reddit']['time_filter']
        
        # Search by brand name
        for brand_info in brands_list:
            brand_name = brand_info['brand_name']
            logger.info(f"  Searching for: {brand_name}")
            
            try:
                subreddit = reddit.subreddit('all')
                
                for post in subreddit.search(brand_name, limit=limit_per_brand, time_filter=time_filter):
                    full_text = f"{post.title} {post.selftext}"
                    
                    # Detect all brands mentioned (might mention multiple)
                    mentioned_brands = detect_brand_mentions(full_text, brands_list)
                    
                    # Create a record for each mentioned brand
                    for mentioned_brand in mentioned_brands:
                        post_data = {
                            'post_id': post.id,
                            'author': str(post.author) if post.author else 'deleted',
                            'brand': mentioned_brand['brand_name'],
                            'parent_company': mentioned_brand['parent_company'],
                            'brand_category': mentioned_brand['category'],
                            'title': post.title,
                            'body': post.selftext if post.selftext else post.title,
                            'upvotes': post.score,
                            'comments_count': post.num_comments,
                            'created_at': datetime.fromtimestamp(post.created_utc).isoformat(),
                            'sentiment_score': analyze_sentiment(full_text),
                            'source': 'reddit',
                            'subreddit': post.subreddit.display_name,
                            'ingested_at': datetime.utcnow().isoformat(),
                            'url': f"https://reddit.com{post.permalink}"
                        }
                        all_posts.append(post_data)
                        
            except Exception as e:
                logger.warning(f"Error fetching {brand_name}: {e}")
                continue
        
        df = pd.DataFrame(all_posts)
        
        # Remove duplicates (same post might mention multiple brands)
        df = df.drop_duplicates(subset=['post_id', 'brand'], keep='first')
        
        reddit_path = RAW_DIR / "reddit_brands.csv"
        df.to_csv(reddit_path, index=False)
        
        logger.info(f"✅ Reddit: {len(df)} posts across {df['brand'].nunique()} brands → {reddit_path}")
        return {"source": "reddit", "records": len(df), "brands": df['brand'].nunique(), "status": "success"}
        
    except Exception as e:
        logger.error(f"❌ Reddit ingestion failed: {str(e)}")
        return {"source": "reddit", "records": 0, "status": "failed", "error": str(e)}


def ingest_news_data(brands_list: list, config: dict):
    """Fetch news articles mentioning consumer brands."""
    try:
        logger.info("🔄 Fetching news data...")
        
        newsapi = NewsApiClient(api_key=os.getenv('NEWS_API_KEY'))
        
        all_articles = []
        days_back = config['collection_config']['news']['days_back']
        articles_per_brand = config['collection_config']['news']['articles_per_brand']
        from_date = (datetime.utcnow() - timedelta(days=days_back)).strftime('%Y-%m-%d')
        
        for brand_info in brands_list:
            brand_name = brand_info['brand_name']
            logger.info(f"  Searching for: {brand_name}")
            
            try:
                response = newsapi.get_everything(
                    q=brand_name,
                    from_param=from_date,
                    language='en',
                    sort_by='relevancy',
                    page_size=articles_per_brand
                )
                
                for article in response.get('articles', []):
                    full_text = f"{article.get('title', '')} {article.get('description', '')}"
                    
                    # Detect all brands mentioned
                    mentioned_brands = detect_brand_mentions(full_text, brands_list)
                    
                    for mentioned_brand in mentioned_brands:
                        article_data = {
                            'article_id': article.get('url', '').split('/')[-1][:50],
                            'publication': article.get('source', {}).get('name', 'Unknown'),
                            'brand': mentioned_brand['brand_name'],
                            'parent_company': mentioned_brand['parent_company'],
                            'brand_category': mentioned_brand['category'],
                            'headline': article.get('title', ''),
                            'body': article.get('description', '') or article.get('content', ''),
                            'url': article.get('url', ''),
                            'published_at': article.get('publishedAt', datetime.utcnow().isoformat()),
                            'sentiment_score': analyze_sentiment(full_text),
                            'source': 'news',
                            'ingested_at': datetime.utcnow().isoformat()
                        }
                        all_articles.append(article_data)
                        
            except Exception as e:
                logger.warning(f"Error fetching {brand_name}: {e}")
                continue
        
        df = pd.DataFrame(all_articles)
        
        # Remove duplicates
        df = df.drop_duplicates(subset=['url', 'brand'], keep='first')
        
        news_path = RAW_DIR / "news_brands.csv"
        df.to_csv(news_path, index=False)
        
        logger.info(f"✅ News: {len(df)} articles across {df['brand'].nunique()} brands → {news_path}")
        return {"source": "news", "records": len(df), "brands": df['brand'].nunique(), "status": "success"}
        
    except Exception as e:
        logger.error(f"❌ News ingestion failed: {str(e)}")
        return {"source": "news", "records": 0, "status": "failed", "error": str(e)}


def generate_brand_metrics_report(brands_list: list):
    """
    Generate a summary report of brand coverage.
    This helps track share of voice and engagement.
    """
    try:
        reddit_df = pd.read_csv(RAW_DIR / "reddit_brands.csv")
        news_df = pd.read_csv(RAW_DIR / "news_brands.csv")
        
        # Combine data
        reddit_df['mentions'] = 1
        news_df['mentions'] = 1
        
        reddit_summary = reddit_df.groupby(['brand', 'parent_company']).agg({
            'mentions': 'sum',
            'upvotes': 'sum',
            'sentiment_score': 'mean'
        }).reset_index()
        reddit_summary['source'] = 'reddit'
        
        news_summary = news_df.groupby(['brand', 'parent_company']).agg({
            'mentions': 'sum',
            'sentiment_score': 'mean'
        }).reset_index()
        news_summary['source'] = 'news'
        
        combined = pd.concat([reddit_summary, news_summary])
        
        # Calculate share of voice
        total_mentions = combined['mentions'].sum()
        combined['share_of_voice'] = (combined['mentions'] / total_mentions * 100).round(2)
        
        # Save report
        report_path = RAW_DIR / "brand_metrics_snapshot.csv"
        combined.to_csv(report_path, index=False)
        
        logger.info(f"📊 Brand metrics report generated → {report_path}")
        
    except Exception as e:
        logger.warning(f"Could not generate metrics report: {e}")


def ensure_directories():
    """Create all required directories."""
    for d in [RAW_DIR, DATA_DIR / "bronze", DATA_DIR / "silver", DATA_DIR / "gold", LAB_ROOT / "config"]:
        d.mkdir(parents=True, exist_ok=True)


def main():
    """Main ingestion flow."""
    ensure_directories()
    
    # Load taxonomy
    if not CONFIG_PATH.exists():
        logger.error(f"❌ Brand taxonomy not found at {CONFIG_PATH}")
        logger.info("Please create config/brand_taxonomy.yaml")
        return
    
    taxonomy = load_brand_taxonomy()
    brands_list = get_all_brands(taxonomy)
    
    logger.info(f"📋 Loaded {len(brands_list)} brands from taxonomy")
    
    # Ingest data
    results = []
    results.append(ingest_reddit_data(brands_list, taxonomy))
    results.append(ingest_news_data(brands_list, taxonomy))
    
    # Generate metrics
    generate_brand_metrics_report(brands_list)
    
    # Summary
    logger.info("\n" + "="*50)
    logger.info("📊 Ingestion Summary:")
    for result in results:
        status_emoji = "✅" if result['status'] == 'success' else "❌"
        brands_count = result.get('brands', 0)
        logger.info(f"  {status_emoji} {result['source']}: {result['records']} records, {brands_count} brands")
    logger.info("="*50)
    
    return results


if __name__ == "__main__":
    main()