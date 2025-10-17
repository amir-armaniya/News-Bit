# modules/content_collector.py
import json
import feedparser
from datetime import datetime, timedelta, timezone
import time
from modules import memory_manager

def fetch_recent_articles(config_path: str) -> list:
    """
    Fetches recent articles from all RSS feeds defined in the config file.
    Returns a list of article dictionaries.
    """
    # --- Load already processed links from memory ---
    processed_links = memory_manager.load_processed_links()
    print(f"Loaded {len(processed_links)} links from memory.")

    # Read and parse config
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
    except FileNotFoundError:
        print(f"Config file not found: {config_path}")
        return []
    except json.JSONDecodeError:
        print("Invalid JSON in config file.")
        return []

    # --- MODIFIED: Get feeds from the new structure ---
    feeds_config = config.get('rss_feeds', [])
    if not feeds_config:
        print("No RSS feeds configured.")
        return []

    articles = []
    print(f"Starting to fetch articles from {len(feeds_config)} feeds...")

    # Cutoff for articles: last 7 days
    cutoff = datetime.now(timezone.utc) - timedelta(days=7)

    # --- MODIFIED: Loop through the new feed structure ---
    for feed_info in feeds_config:
        # Get URL and name from the dictionary
        url = feed_info.get('url')
        name = feed_info.get('name', url) # Use URL as fallback name

        if not url:
            continue

        print(f"-> Checking feed: {name} ({url})")
        new_articles_count = 0
        try:
            # Add user agent to avoid being blocked
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            feed = feedparser.parse(url, request_headers=headers)

            if feed.bozo:
                print(f"   Warning parsing feed: {feed.bozo_exception}")
                # Continue processing even with warnings

            for entry in feed.entries:
                # --- Check if link has been processed before ---
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
                            'summary': entry.summary,
                            'source': name  # --- NEW: Add source name to article
                        }
                        articles.append(article)
                        new_articles_count += 1
                        # --- NEW: Add link to memory immediately to avoid duplicates
                        processed_links.add(entry.link)

            print(f"   Found {new_articles_count} new, unprocessed articles from this feed.")
        except Exception as e:
            print(f"   Error fetching feed: {e}")
            continue

        # Be a good citizen to the feed server
        time.sleep(1)

    # --- NEW: Save the updated list of processed links
    memory_manager.save_processed_links(processed_links)

    print(f"\nFinished fetching. Total new articles found: {len(articles)}")
    return articles
    return articles

def fetch_sample_articles_from_feeds(feeds_config: list) -> list:
    """
    Fetches a small number of random articles for sample demonstration ONLY.
    This function intentionally IGNORES the processed_links memory.
    """
    articles = []
    if not feeds_config:
        return []

    # Check up to 3 random feeds to find at least one article quickly
    for feed_info in random.sample(feeds_config, min(len(feeds_config), 3)):
        try:
            print(f"-> Fetching sample from: {feed_info.get('name')}")
            feed = feedparser.parse(feed_info['url'])
            if feed.entries:
                # Pick a random recent entry
                entry = random.choice(feed.entries)
                article = {
                    'title': entry.title,
                    'link': entry.link,
                    'summary': entry.summary,
                    'source': feed_info.get('name', feed_info['url'])
                }
                articles.append(article)
        except Exception as e:
            print(f"   Error fetching sample from feed: {e}")
            continue
    return articles

def fetch_sample_article(feeds: list) -> dict:
    """
    Fetches a single random article from randomly selected feeds without memory checks.
    Designed for onboarding sample articles that should always be fresh.
    """
    articles = fetch_sample_articles_from_feeds(feeds)
    return random.choice(articles) if articles else None