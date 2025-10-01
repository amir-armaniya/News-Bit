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
    articles = modules.content_collector.fetch_recent_articles(CONFIG_PATH)

    if not articles:
        print("No new articles found. Exiting.")
        return

    print(f"Fetched {len(articles)} articles. Processing...")

    for i, article in enumerate(articles, 1):
        print(f"--- Processing article {i}/{len(articles)}: {article['title']} ---")

        analysis_dict = modules.ai_processor.process_article_in_persian(
            article['title'], article['summary'], article['link']
        )

        if analysis_dict:
            await modules.telegram_sender.send_article_analysis(analysis_dict)
        else:
            print(f"Warning: Failed to analyze article: {article['title']}. Skipping.")

    print("--- All articles processed. Mission complete. ---")

if __name__ == "__main__":
    asyncio.run(main())