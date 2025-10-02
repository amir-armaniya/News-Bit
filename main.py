import os
import asyncio
from dotenv import load_dotenv
import socket
import time # Import the time library
import modules.content_collector
import modules.ai_processor
import modules.telegram_sender
from modules import memory_manager # Import the new memory manager

load_dotenv()
socket.setdefaulttimeout(20)

async def main():
    CONFIG_PATH = "config.json"
    all_articles = modules.content_collector.fetch_recent_articles(CONFIG_PATH)

    if not all_articles:
        print("No new articles found. Exiting.")
        return

    print(f"Fetched {len(all_articles)} total articles. Starting relevance filtering...")

    # --- Intelligent Filtering Step ---
    relevant_articles = []
    for i, article in enumerate(all_articles, 1):
        print(f"Filtering article {i}/{len(all_articles)}: {article['title'][:70]}...")
        if modules.ai_processor.is_article_relevant(article['title'], article['summary']):
            relevant_articles.append(article)
            print("   -> RELEVANT")
        else:
            print("   -> SKIPPED (Not Relevant)")
        
        # --- NEW: Add a delay to respect API rate limits ---
        time.sleep(8) # Wait for 8 seconds before the next request
    
    if not relevant_articles:
        print("No relevant articles found after filtering. Exiting.")
        return
        
    print(f"\nFound {len(relevant_articles)} relevant articles. Processing...")

    for i, article in enumerate(relevant_articles, 1):
        print(f"--- Processing article {i}/{len(relevant_articles)}: {article['title']} ---")
        
        analysis_dict = modules.ai_processor.process_article_in_persian(
            article['title'], article['summary'], article['link']
        )

        if analysis_dict:
            memory_manager.save_analysis(analysis_dict)
            await modules.telegram_sender.send_article_analysis(analysis_dict)
        else:
            print(f"Warning: Failed to analyze article: {article['title']}. Skipping.")

    print("--- All articles processed. Mission complete. ---")

if __name__ == "__main__":
    asyncio.run(main())
