import os
from dotenv import load_dotenv
import praw

load_dotenv()

print("=" * 50)
print("REDDIT CREDENTIALS CHECK")
print("=" * 50)

client_id = os.getenv('REDDIT_CLIENT_ID')
client_secret = os.getenv('REDDIT_CLIENT_SECRET')
user_agent = os.getenv('REDDIT_USER_AGENT')

print(f"CLIENT_ID: {client_id[:5]}...{client_id[-3:] if client_id else 'MISSING'}")
print(f"CLIENT_SECRET: {client_secret[:5]}...{client_secret[-3:] if client_secret else 'MISSING'}")
print(f"USER_AGENT: {user_agent}")
print("=" * 50)

if not all([client_id, client_secret, user_agent]):
    print("❌ ERROR: One or more credentials are missing!")
    exit(1)

print("\nAttempting connection...")
try:
    reddit = praw.Reddit(
        client_id=client_id,
        client_secret=client_secret,
        user_agent=user_agent
    )
    
    # Test with a simple read-only operation
    print("Testing read-only access...")
    subreddit = reddit.subreddit('python')
    post = next(subreddit.hot(limit=1))
    print(f"✅ SUCCESS! Retrieved post: {post.title[:60]}...")
    
except praw.exceptions.ResponseException as e:
    print(f"❌ Authentication Error: {e}")
    print("\nPossible issues:")
    print("1. CLIENT_ID is incorrect (should be ~14 chars)")
    print("2. CLIENT_SECRET is incorrect (should be ~27 chars)")
    print("3. App type is not 'script' on Reddit")
    print("\nDouble-check at: https://www.reddit.com/prefs/apps")
    
except Exception as e:
    print(f"❌ Unexpected Error: {e}")