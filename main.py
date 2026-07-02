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

# Default language setting (English for all users by default)
DEFAULT_LANGUAGE = 'en'

async def main():
    """Manual run mode - for on-demand analysis."""
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
        await modules.telegram_sender.send_text_to_telegram("No new articles found for analysis.")
        return

    print(f"Fetched {len(all_articles)} total articles. Starting relevance filtering...")

    # --- Intelligent Filtering Step ---
    relevant_articles = []
    for i, article in enumerate(all_articles, 1):
        print(f"Filtering article {i}/{len(all_articles)}: {article['title'][:70]}...")
        
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
        
        await asyncio.sleep(3)
    
    if not relevant_articles:
        print("No relevant articles found after filtering.")
        await modules.telegram_sender.send_text_to_telegram("New articles were found, but none were relevant to your work area.")
        return
        
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

        await asyncio.sleep(8)
        
    await modules.telegram_sender.send_text_to_telegram(f"Successfully processed {len(relevant_articles)} relevant articles.")
    print("--- All articles processed. Mission complete. ---")

if __name__ == "__main__":
    asyncio.run(main())
