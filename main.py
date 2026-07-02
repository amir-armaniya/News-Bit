import os
import json
import asyncio
from dotenv import load_dotenv
import socket
import modules.content_collector
import modules.ai_processor
import modules.telegram_sender
from modules import memory_manager

load_dotenv()
socket.setdefaulttimeout(20)

# Default language setting
DEFAULT_LANGUAGE = 'en'

async def process_news_once():
    """Process news once - used by both manual and auto modes."""
    CONFIG_PATH = "config.json"
    
    # Load user preferences
    user_prefs = {}
    try:
        with open('user_prefs.json', 'r', encoding='utf-8') as f:
            user_prefs = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        pass
    
    # Get language setting
    language = user_prefs.get('language', DEFAULT_LANGUAGE)
        
    all_articles = modules.content_collector.fetch_recent_articles(CONFIG_PATH)

    if not all_articles:
        print("No new articles found.")
        return False

    print(f"Fetched {len(all_articles)} total articles. Starting relevance filtering...")

    # --- Intelligent Filtering Step ---
    relevant_articles = []
    for i, article in enumerate(all_articles, 1):
        print(f"Filtering article {i}/{len(all_articles)}: {article['title'][:70]}...")
        
        # Try to check article relevance with error handling
        max_retries = 3
        for retry in range(max_retries):
            try:
                if modules.ai_processor.is_article_relevant(
                    article['title'],
                    article['summary'],
                    selected_topics=user_prefs.get('selected_topics')
                ):
                    relevant_articles.append(article)
                    print("   -> RELEVANT")
                else:
                    print("   -> SKIPPED (Not Relevant)")
                break
            except Exception as e:
                if "429" in str(e) and retry < max_retries - 1:
                    print(f"   -> Rate limit hit. Waiting 60 seconds...")
                    await asyncio.sleep(60)
                else:
                    print(f"   -> Error: {e}")
                    break
        
        # 3-second delay for rate limiting (20 requests per minute)
        await asyncio.sleep(3)
    
    if not relevant_articles:
        print("No relevant articles found after filtering.")
        return False
        
    print(f"\nFound {len(relevant_articles)} relevant articles. Processing...")

    for i, article in enumerate(relevant_articles, 1):
        print(f"--- Processing article {i}/{len(relevant_articles)}: {article['title']} ---")
        
        analysis_dict = modules.ai_processor.process_article_in_english(
            article['title'], article['summary'], article['link']
        )

        if analysis_dict:
            memory_manager.save_analysis(analysis_dict)
            await modules.telegram_sender.send_article_analysis(analysis_dict, language=language)
        else:
            print(f"Warning: Failed to analyze article: {article['title']}. Skipping.")

        # Longer delay for article analysis (using more powerful model)
        await asyncio.sleep(8)
        
    await modules.telegram_sender.send_text_to_telegram(f"Successfully processed {len(relevant_articles)} relevant articles.")
    print("--- All articles processed. Mission complete. ---")
    return True

async def main():
    """Main entry point - supports both single run and auto mode."""
    # Load user preferences to check mode
    user_prefs = {}
    try:
        with open('user_prefs.json', 'r', encoding='utf-8') as f:
            user_prefs = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        pass
    
    # Check if auto mode is enabled
    auto_mode = user_prefs.get('auto_mode', False)
    language = user_prefs.get('language', DEFAULT_LANGUAGE)
    
    if auto_mode:
        print("=== AUTO MODE ENABLED ===")
        print(f"Language: {language}")
        print("Will process news every 30 minutes...")
        
        while True:
            try:
                await process_news_once()
                print(f"\nWaiting 30 minutes before next check...")
                await asyncio.sleep(1800)  # 30 minutes
            except KeyboardInterrupt:
                print("\nAuto mode stopped by user.")
                break
            except Exception as e:
                print(f"Error in auto mode: {e}")
                print("Waiting 5 minutes before retry...")
                await asyncio.sleep(300)  # 5 minutes on error
    else:
        print("=== SINGLE RUN MODE ===")
        await process_news_once()

if __name__ == "__main__":
    asyncio.run(main())