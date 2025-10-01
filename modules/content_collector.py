import json
import feedparser
from datetime import datetime, timedelta, timezone
import time
from modules import memory_manager # Import the new memory manager

def fetch_recent_articles(config_path: str) -> list:
    # --- NEW: Load already processed links from memory ---
    processed_links = memory_manager.load_processed_links()
    print(f"Loaded {len(processed_links)} links from memory.")
    
    # Read and parse config (rest of the function is similar)
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
    except FileNotFoundError:
        print(f"Config file not found: {config_path}")
        return []
    except json.JSONDecodeError:
        print("Invalid JSON in config file.")
        return []

    rss_feeds = config.get('rss_feeds', [])
    if not rss_feeds:
        print("No RSS feeds configured.")
        return []

    articles = []
    print(f"Starting to fetch articles from {len(rss_feeds)} feeds...")

    # Cutoff for articles: last 7 days
    cutoff = datetime.now(timezone.utc) - timedelta(days=7)

    for url in rss_feeds:
        print(f"-> Checking feed: {url}")
        new_articles_count = 0
        try:
            feed = feedparser.parse(url)
            if feed.bozo:
                print(f"   Error parsing feed: {feed.bozo_exception}")
                continue

            for entry in feed.entries:
                # --- NEW: Check if link has been processed before ---
                if entry.link in processed_links:
                    continue

                pub_date = entry.get('published_parsed')
                if pub_date:
                    # Convert struct_time to datetime with UTC timezone
                    pub_datetime = datetime(*pub_date[:6], tzinfo=timezone.utc)
                    if pub_datetime >= cutoff:
                        article = {
                            'title': entry.title,
                            'link': entry.link,
                            'summary': entry.summary
                        }
                        articles.append(article)
                        new_articles_count += 1

            print(f"   Found {new_articles_count} new, unprocessed articles from this feed.")
        except Exception as e:
            print(f"   Error fetching feed: {e}")
            continue

    print(f"\nFinished fetching. Total new articles found: {len(articles)}")
    return articles
