# Lab 2: API Integration Guide

Detailed guide for integrating with Reddit and News APIs for sentiment analysis.

## Table of Contents

1. [Reddit API (PRAW)](#reddit-api-praw)
2. [News API](#news-api)
3. [Brand Detection](#brand-detection)
4. [Sentiment Analysis](#sentiment-analysis)
5. [Data Schema](#data-schema)
6. [Best Practices](#best-practices)

---

## Reddit API (PRAW)

### Overview

We use **PRAW (Python Reddit API Wrapper)** to access Reddit's API.

**Why Reddit?**
- ✅ User-generated discussions about brands
- ✅ Authentic sentiment (not corporate messaging)
- ✅ High engagement signals (upvotes, comments)
- ✅ Free API access
- ✅ Real-time data

### Authentication

```python
import praw
import os
from dotenv import load_dotenv

load_dotenv()

reddit = praw.Reddit(
    client_id=os.getenv('REDDIT_CLIENT_ID'),
    client_secret=os.getenv('REDDIT_CLIENT_SECRET'),
    user_agent=os.getenv('REDDIT_USER_AGENT')
)
```

### Rate Limits

- **60 requests per minute**
- PRAW handles rate limiting automatically
- Implements exponential backoff on errors

### Search Strategy

#### Basic Search

```python
# Search across all subreddits
subreddit = reddit.subreddit('all')

# Search for brand mentions
for post in subreddit.search("Coca-Cola", limit=20, time_filter='month'):
    print(post.title)
```

#### Advanced Search with Filters

```python
# Multiple search terms
query = 'Coca-Cola OR Coke OR "Coca Cola"'

# Time filters: 'hour', 'day', 'week', 'month', 'year', 'all'
posts = subreddit.search(query, limit=50, time_filter='month', sort='relevance')

# Iterate through results
for post in posts:
    # Access post attributes
    post_id = post.id
    title = post.title
    body = post.selftext
    upvotes = post.score
    comments = post.num_comments
    created = post.created_utc
    subreddit_name = post.subreddit.display_name
    author = str(post.author) if post.author else 'deleted'
    permalink = f"https://reddit.com{post.permalink}"
```

#### Subreddit-Specific Search

```python
# Target specific subreddits
target_subreddits = ['food', 'snacks', 'cooking', 'AskReddit', 'unpopularopinion']

all_posts = []
for sub_name in target_subreddits:
    subreddit = reddit.subreddit(sub_name)
    posts = subreddit.search("Coca-Cola", limit=10, time_filter='month')
    all_posts.extend(posts)
```

### Handling Deleted Content

```python
def safe_author(post):
    """Handle deleted authors gracefully."""
    try:
        return str(post.author) if post.author else 'deleted'
    except AttributeError:
        return 'deleted'

def safe_text(post):
    """Handle deleted text gracefully."""
    return post.selftext if post.selftext and post.selftext != '[removed]' else post.title
```

### Error Handling

```python
from prawcore.exceptions import (
    ResponseException,
    RequestException,
    TooManyRequests,
    Forbidden
)
import time

def fetch_posts_with_retry(query, limit=20, max_retries=3):
    """Fetch posts with automatic retry on errors."""
    for attempt in range(max_retries):
        try:
            posts = reddit.subreddit('all').search(query, limit=limit)
            return list(posts)
        except TooManyRequests:
            wait_time = 60 * (attempt + 1)  # Exponential backoff
            logger.warning(f"Rate limited. Waiting {wait_time}s...")
            time.sleep(wait_time)
        except (ResponseException, RequestException) as e:
            logger.error(f"Reddit API error: {e}")
            if attempt == max_retries - 1:
                raise
            time.sleep(5)
    return []
```

### Full Example

```python
def ingest_reddit_data(brands_list: list, limit_per_brand=20):
    """
    Fetch Reddit posts mentioning CPG brands.
    
    Args:
        brands_list: List of brand dictionaries with name, aliases, etc.
        limit_per_brand: Max posts to fetch per brand
    
    Returns:
        pandas.DataFrame with Reddit posts
    """
    reddit = praw.Reddit(
        client_id=os.getenv('REDDIT_CLIENT_ID'),
        client_secret=os.getenv('REDDIT_CLIENT_SECRET'),
        user_agent=os.getenv('REDDIT_USER_AGENT')
    )
    
    all_posts = []
    
    for brand_info in brands_list:
        brand_name = brand_info['brand_name']
        logger.info(f"Searching for: {brand_name}")
        
        try:
            subreddit = reddit.subreddit('all')
            
            for post in subreddit.search(brand_name, limit=limit_per_brand, time_filter='month'):
                # Combine title and body for sentiment
                full_text = f"{post.title} {post.selftext}"
                
                # Detect all brands mentioned
                mentioned_brands = detect_brand_mentions(full_text, brands_list)
                
                # Create record for each mentioned brand
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
    df = df.drop_duplicates(subset=['post_id', 'brand'], keep='first')
    
    return df
```

---

## News API

### Overview

We use **NewsAPI** to access news articles from 80,000+ sources.

**Why News API?**
- ✅ Professional journalism
- ✅ 80,000+ sources worldwide
- ✅ Historical data (30 days on free tier)
- ✅ Simple REST API
- ✅ Good search capabilities

### Authentication

```python
from newsapi import NewsApiClient

newsapi = NewsApiClient(api_key=os.getenv('NEWS_API_KEY'))
```

### Rate Limits & Tiers

**Free Tier**:
- 100 requests per day
- 100 results per request (max)
- Historical: Last 30 days only
- Delayed: 15-minute delay on breaking news

**Paid Tiers**:
- 250 to 100,000 requests per day
- Historical: Full archive access
- Real-time: No delay

### Search Endpoints

#### Everything Endpoint

```python
from datetime import datetime, timedelta

# Define date range
from_date = (datetime.utcnow() - timedelta(days=7)).strftime('%Y-%m-%d')
to_date = datetime.utcnow().strftime('%Y-%m-%d')

# Search for articles
response = newsapi.get_everything(
    q='Coca-Cola',                    # Search query
    from_param=from_date,             # Start date
    to=to_date,                       # End date
    language='en',                    # Language filter
    sort_by='relevancy',              # Sort by: relevancy, popularity, publishedAt
    page_size=100,                    # Max results (max 100)
    page=1                            # Pagination
)

# Response structure
{
    'status': 'ok',
    'totalResults': 453,
    'articles': [
        {
            'source': {'id': None, 'name': 'Forbes'},
            'author': 'John Doe',
            'title': 'Coca-Cola Announces New Product',
            'description': 'Brief description...',
            'url': 'https://...',
            'urlToImage': 'https://...',
            'publishedAt': '2025-11-01T10:30:00Z',
            'content': 'Full content (truncated)...'
        },
        # ... more articles
    ]
}
```

#### Top Headlines Endpoint

```python
# Get top headlines (breaking news)
response = newsapi.get_top_headlines(
    q='Coca-Cola',
    category='business',              # business, entertainment, general, health, science, sports, technology
    language='en',
    country='us',                     # ISO country code
    page_size=100
)
```

### Query Syntax

NewsAPI supports advanced query syntax:

```python
# OR operator
q = 'Coca-Cola OR Coke OR "Coca Cola"'

# AND operator
q = 'Coca-Cola AND (earnings OR revenue)'

# NOT operator
q = 'Coca-Cola NOT Trump'

# Phrase matching
q = '"Coca-Cola Company"'

# Combination
q = '(Coca-Cola OR Pepsi) AND (earnings OR revenue) NOT cryptocurrency'
```

### Pagination

```python
def fetch_all_articles(query, from_date, max_articles=500):
    """Fetch all articles with pagination."""
    all_articles = []
    page = 1
    page_size = 100
    
    while len(all_articles) < max_articles:
        response = newsapi.get_everything(
            q=query,
            from_param=from_date,
            language='en',
            sort_by='relevancy',
            page_size=page_size,
            page=page
        )
        
        articles = response.get('articles', [])
        if not articles:
            break  # No more articles
        
        all_articles.extend(articles)
        page += 1
    
    return all_articles[:max_articles]
```

### Error Handling

```python
from newsapi.newsapi_exception import NewsAPIException

def fetch_news_with_retry(query, from_date, max_retries=3):
    """Fetch news with retry logic."""
    for attempt in range(max_retries):
        try:
            response = newsapi.get_everything(
                q=query,
                from_param=from_date,
                language='en',
                sort_by='relevancy',
                page_size=100
            )
            return response.get('articles', [])
            
        except NewsAPIException as e:
            if e.get_code() == 426:  # Rate limit exceeded
                logger.error("Rate limit exceeded. Upgrade to paid plan or reduce frequency.")
                return []
            elif e.get_code() == 429:  # Too many requests
                wait_time = 60 * (attempt + 1)
                logger.warning(f"Too many requests. Waiting {wait_time}s...")
                time.sleep(wait_time)
            else:
                logger.error(f"NewsAPI error: {e}")
                if attempt == max_retries - 1:
                    raise
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            if attempt == max_retries - 1:
                raise
    
    return []
```

### Full Example

```python
def ingest_news_data(brands_list: list, days_back=7, articles_per_brand=20):
    """
    Fetch news articles mentioning CPG brands.
    
    Args:
        brands_list: List of brand dictionaries
        days_back: How many days of history to fetch
        articles_per_brand: Max articles per brand
    
    Returns:
        pandas.DataFrame with news articles
    """
    newsapi = NewsApiClient(api_key=os.getenv('NEWS_API_KEY'))
    
    all_articles = []
    from_date = (datetime.utcnow() - timedelta(days=days_back)).strftime('%Y-%m-%d')
    
    for brand_info in brands_list:
        brand_name = brand_info['brand_name']
        logger.info(f"Searching for: {brand_name}")
        
        try:
            response = newsapi.get_everything(
                q=brand_name,
                from_param=from_date,
                language='en',
                sort_by='relevancy',
                page_size=articles_per_brand
            )
            
            for article in response.get('articles', []):
                # Combine title and description for sentiment
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
    df = df.drop_duplicates(subset=['url', 'brand'], keep='first')
    
    return df
```

---

## Brand Detection

### Strategy

We detect brand mentions using:
1. **Exact brand name** matching
2. **Brand aliases** (e.g., "Coke" for "Coca-Cola")
3. **Case-insensitive** comparison

### Implementation

```python
def detect_brand_mentions(text: str, brands_list: list) -> list:
    """
    Detect which brands are mentioned in text.
    
    Args:
        text: Content to search
        brands_list: List of brand dictionaries with names and aliases
    
    Returns:
        List of brand_info dicts for mentioned brands
    """
    text_lower = text.lower()
    mentioned_brands = []
    
    for brand_info in brands_list:
        brand_name = brand_info['brand_name']
        aliases = brand_info.get('brand_aliases', [])
        
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
```

### Advanced: NLP-Based Detection

For production, consider using NLP for better accuracy:

```python
import spacy

nlp = spacy.load("en_core_web_sm")

def detect_brands_nlp(text: str, brands_list: list) -> list:
    """Use NLP for more accurate brand detection."""
    doc = nlp(text)
    
    # Extract organization entities
    org_entities = [ent.text.lower() for ent in doc.ents if ent.label_ == "ORG"]
    
    mentioned_brands = []
    for brand_info in brands_list:
        brand_name = brand_info['brand_name'].lower()
        
        # Check if brand name or alias is in entities
        if any(brand_name in entity or entity in brand_name for entity in org_entities):
            mentioned_brands.append(brand_info)
    
    return mentioned_brands
```

---

## Sentiment Analysis

### VADER Sentiment

We use **VADER (Valence Aware Dictionary and sEntiment Reasoner)**, optimized for social media text.

#### Why VADER?
- ✅ Designed for social media text
- ✅ Handles emojis, slang, capitalization
- ✅ Fast (no ML model loading)
- ✅ Compound score from -1 to 1
- ✅ Pre-trained, no tuning needed

#### Implementation

```python
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

sentiment_analyzer = SentimentIntensityAnalyzer()

def analyze_sentiment(text: str) -> float:
    """
    Analyze sentiment using VADER.
    
    Args:
        text: Content to analyze
    
    Returns:
        Compound score from -1 (very negative) to 1 (very positive)
    """
    if not text:
        return 0.0
    
    scores = sentiment_analyzer.polarity_scores(text)
    
    # VADER returns: {'neg': 0.1, 'neu': 0.6, 'pos': 0.3, 'compound': 0.5}
    return scores['compound']
```

#### Example Scores

```python
texts = [
    "I absolutely love Coca-Cola! Best drink ever! 😍",
    "Coca-Cola is okay, nothing special.",
    "I hate the new Coke formula. It's disgusting! 🤮"
]

for text in texts:
    score = analyze_sentiment(text)
    print(f"Text: {text}")
    print(f"Score: {score:.3f}\n")

# Output:
# Text: I absolutely love Coca-Cola! Best drink ever! 😍
# Score: 0.861

# Text: Coca-Cola is okay, nothing special.
# Score: 0.296

# Text: I hate the new Coke formula. It's disgusting! 🤮
# Score: -0.836
```

### Advanced: Transformer-Based Sentiment

For higher accuracy, use Hugging Face transformers:

```python
from transformers import pipeline

# Load pre-trained sentiment model
classifier = pipeline("sentiment-analysis", 
                     model="distilbert-base-uncased-finetuned-sst-2-english")

def analyze_sentiment_transformer(text: str) -> float:
    """Use transformer for sentiment analysis."""
    if not text:
        return 0.0
    
    # Truncate to 512 tokens (BERT limit)
    result = classifier(text[:512])[0]
    
    # Convert to -1 to 1 scale
    label = result['label']  # 'POSITIVE' or 'NEGATIVE'
    score = result['score']  # 0.0 to 1.0 confidence
    
    return score if label == 'POSITIVE' else -score
```

---

## Data Schema

### Reddit Data Schema

```python
{
    'post_id': str,              # Unique Reddit post ID
    'author': str,               # Username (or 'deleted')
    'brand': str,                # Brand name
    'parent_company': str,       # Parent company from taxonomy
    'brand_category': str,       # Product category
    'title': str,                # Post title
    'body': str,                 # Post body text
    'upvotes': int,              # Score (upvotes - downvotes)
    'comments_count': int,       # Number of comments
    'created_at': str,           # ISO timestamp
    'sentiment_score': float,    # -1 to 1
    'source': 'reddit',
    'subreddit': str,            # Subreddit name
    'ingested_at': str,          # ISO timestamp
    'url': str                   # Permalink
}
```

### News Data Schema

```python
{
    'article_id': str,           # URL slug or hash
    'publication': str,          # Source name (e.g., "Forbes")
    'brand': str,                # Brand name
    'parent_company': str,       # Parent company from taxonomy
    'brand_category': str,       # Product category
    'headline': str,             # Article title
    'body': str,                 # Article description/content
    'url': str,                  # Full article URL
    'published_at': str,         # ISO timestamp
    'sentiment_score': float,    # -1 to 1
    'source': 'news',
    'ingested_at': str          # ISO timestamp
}
```

---

## Best Practices

### 1. Respect Rate Limits

```python
# Track API calls
api_calls = {
    'reddit': 0,
    'news': 0,
    'last_reset': datetime.utcnow()
}

def check_rate_limit(api_name):
    """Check if we're within rate limits."""
    now = datetime.utcnow()
    
    # Reset counters every hour
    if (now - api_calls['last_reset']).seconds > 3600:
        api_calls['reddit'] = 0
        api_calls['news'] = 0
        api_calls['last_reset'] = now
    
    # Check limits
    if api_name == 'reddit' and api_calls['reddit'] >= 3600:  # 60 per min * 60 min
        raise Exception("Reddit rate limit reached")
    elif api_name == 'news' and api_calls['news'] >= 100:  # Daily limit
        raise Exception("News API rate limit reached")
    
    api_calls[api_name] += 1
```

### 2. Implement Exponential Backoff

```python
import time
import random

def exponential_backoff(attempt, base_wait=1, max_wait=60):
    """Calculate wait time with exponential backoff."""
    wait_time = min(base_wait * (2 ** attempt) + random.uniform(0, 1), max_wait)
    return wait_time

# Usage
for attempt in range(5):
    try:
        # API call
        break
    except Exception as e:
        if attempt == 4:
            raise
        wait = exponential_backoff(attempt)
        logger.info(f"Retry in {wait:.1f}s...")
        time.sleep(wait)
```

### 3. Cache API Responses

```python
import hashlib
import json
from pathlib import Path

CACHE_DIR = Path("data/cache")
CACHE_DIR.mkdir(exist_ok=True)

def cache_key(func_name, **kwargs):
    """Generate cache key from function name and arguments."""
    key_str = f"{func_name}:{json.dumps(kwargs, sort_keys=True)}"
    return hashlib.md5(key_str.encode()).hexdigest()

def fetch_with_cache(func, cache_ttl=3600, **kwargs):
    """Fetch data with caching."""
    key = cache_key(func.__name__, **kwargs)
    cache_file = CACHE_DIR / f"{key}.json"
    
    # Check cache
    if cache_file.exists():
        age = time.time() - cache_file.stat().st_mtime
        if age < cache_ttl:
            logger.info(f"Using cached result (age: {age:.0f}s)")
            with open(cache_file) as f:
                return json.load(f)
    
    # Fetch fresh data
    result = func(**kwargs)
    
    # Save to cache
    with open(cache_file, 'w') as f:
        json.dump(result, f)
    
    return result
```

### 4. Log All API Interactions

```python
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ingestion.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Log API calls
def fetch_reddit_posts(brand):
    logger.info(f"Fetching Reddit posts for: {brand}")
    try:
        posts = # ... API call ...
        logger.info(f"✅ Found {len(posts)} posts for {brand}")
        return posts
    except Exception as e:
        logger.error(f"❌ Error fetching {brand}: {e}")
        raise
```

### 5. Validate Data Before Saving

```python
def validate_post_data(post_data):
    """Validate required fields are present."""
    required_fields = ['post_id', 'brand', 'sentiment_score', 'created_at']
    
    for field in required_fields:
        if field not in post_data:
            raise ValueError(f"Missing required field: {field}")
    
    # Validate sentiment score
    score = post_data['sentiment_score']
    if not -1 <= score <= 1:
        raise ValueError(f"Invalid sentiment score: {score}")
    
    return True
```

---

## Testing API Integration

### Unit Tests

```python
import unittest
from unittest.mock import Mock, patch

class TestAPIIntegration(unittest.TestCase):
    
    @patch('praw.Reddit')
    def test_reddit_fetch(self, mock_reddit):
        """Test Reddit data fetching."""
        # Mock Reddit API
        mock_post = Mock()
        mock_post.id = 'test123'
        mock_post.title = 'Test post about Coca-Cola'
        mock_post.selftext = 'Great product!'
        mock_post.score = 100
        
        mock_reddit.return_value.subreddit.return_value.search.return_value = [mock_post]
        
        # Test function
        result = ingest_reddit_data(['Coca-Cola'])
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['post_id'], 'test123')
    
    def test_brand_detection(self):
        """Test brand mention detection."""
        text = "I love Coke and Sprite!"
        brands = [
            {'brand_name': 'Coca-Cola', 'brand_aliases': ['Coke']},
            {'brand_name': 'Sprite', 'brand_aliases': []}
        ]
        
        mentioned = detect_brand_mentions(text, brands)
        
        self.assertEqual(len(mentioned), 2)
        self.assertEqual(mentioned[0]['brand_name'], 'Coca-Cola')
        self.assertEqual(mentioned[1]['brand_name'], 'Sprite')
    
    def test_sentiment_analysis(self):
        """Test sentiment scoring."""
        positive = "I absolutely love this product!"
        negative = "Terrible quality, waste of money"
        neutral = "It's okay, nothing special"
        
        self.assertGreater(analyze_sentiment(positive), 0.5)
        self.assertLess(analyze_sentiment(negative), -0.5)
        self.assertAlmostEqual(analyze_sentiment(neutral), 0.0, delta=0.3)

if __name__ == '__main__':
    unittest.main()
```

---

## Monitoring & Alerting

### Track API Health

```python
import json
from datetime import datetime

def log_api_health():
    """Track API health metrics."""
    health = {
        'timestamp': datetime.utcnow().isoformat(),
        'reddit': {
            'status': 'ok',
            'calls_today': api_calls['reddit'],
            'errors': 0
        },
        'news': {
            'status': 'ok',
            'calls_today': api_calls['news'],
            'errors': 0
        }
    }
    
    with open('data/api_health.json', 'w') as f:
        json.dump(health, f)
```

---

**Last Updated**: November 2025  
**Maintainer**: narensham