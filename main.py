import os
import asyncio
from dotenv import load_dotenv
import socket

import modules.content_collector
import modules.ai_processor
import modules.podcast_generator
import modules.telegram_sender

load_dotenv()

socket.setdefaulttimeout(20)

async def main():
    CONFIG_PATH = "config.json"
    OUTPUT_AUDIO_PATH = "weekly_summary.mp3"
    
    # Step 1: Fetch Articles
    articles = modules.content_collector.fetch_recent_articles(CONFIG_PATH)
    if not articles:
        print("No new articles found. Exiting.")
        return
    
    # Step 2: Summarize Articles
    summaries = []
    for i, article in enumerate(articles):
        print(f"Summarizing article {i+1}/{len(articles)}: {article['title']}")
        summary = modules.ai_processor.summarize_article(article['title'], article['summary'])
        if summary:
            summaries.append(summary)
    
    # Step 3: Aggregate Summaries
    if not summaries:
        print("No summaries were generated. Exiting.")
        return
    
    aggregated_text = "Weekly AI & Startup Briefing\n\n" + "\n---\n".join(summaries)
    
    # Step 4: Generate Podcast
    podcast_path = modules.podcast_generator.create_podcast_from_text(aggregated_text, OUTPUT_AUDIO_PATH)
    if podcast_path is None:
        print("Critical error: Failed to generate podcast. Exiting.")
        return
    
    # Step 5: Send to Telegram
    success = await modules.telegram_sender.send_summary_to_telegram(aggregated_text, OUTPUT_AUDIO_PATH)
    if success:
        print("Podcast sent to Telegram successfully.")
    else:
        print("Failed to send to Telegram.")
    
    # Step 6: Cleanup
    if os.path.exists(OUTPUT_AUDIO_PATH):
        try:
            os.remove(OUTPUT_AUDIO_PATH)
            print("Temporary audio file cleaned up.")
        except Exception as e:
            print(f"Warning: Could not delete audio file: {e}")

if __name__ == "__main__":
    asyncio.run(main())
