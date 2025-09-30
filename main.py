import os
import asyncio
from dotenv import load_dotenv
import socket

import modules.content_collector
import modules.ai_processor
import modules.telegram_sender

load_dotenv()

socket.setdefaulttimeout(20)

async def main():
    CONFIG_PATH = "config.json"
    
    # Step 1: Fetch Articles
    articles = modules.content_collector.fetch_recent_articles(CONFIG_PATH)
    if not articles:
        print("No new articles found. Exiting.")
        return
    
    total_articles = len(articles)
    
    # Step 2: Process and Send in a Loop
    for i, article in enumerate(articles):
        print(f"--- Processing article {i+1}/{total_articles}: {article['title']} ---")
        
        analysis_dict = modules.ai_processor.process_article_in_persian(
            article['title'],
            article['summary'],
            article['link']
        )
        
        if analysis_dict is not None:
            success = await modules.telegram_sender.send_article_analysis(analysis_dict)
            if not success:
                print(f"Warning: Failed to send analysis for article: {article['title']}")
        else:
            print(f"Skipping article due to processing error: {article['title']}")
    
    print("--- All articles processed. Mission complete. ---")

if __name__ == "__main__":
    asyncio.run(main())
