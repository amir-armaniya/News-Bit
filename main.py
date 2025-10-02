import os
import asyncio
from dotenv import load_dotenv
import socket
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
        # بازخورد به کاربر: هیچ مقاله جدیدی پیدا نشد
        await modules.telegram_sender.send_message("هیچ مقاله جدیدی برای تحلیل پیدا نشد.")
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
    
    if not relevant_articles:
        print("No relevant articles found after filtering. Exiting.")
        # بازخورد به کاربر: مقالات پیدا شدند اما هیچ‌کدام مرتبط نبودند
        await modules.telegram_sender.send_message("مقالات جدید پیدا شدند، اما هیچ‌کدام با حوزه کاری شما مرتبط نبودند.")
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

        await asyncio.sleep(8) # جایگزین time.sleep(8) در توابع async
        
    # بازخورد به کاربر: پردازش مقالات مرتبط با موفقیت انجام شد
    await modules.telegram_sender.send_message(f"پردازش {len(relevant_articles)} مقاله مرتبط با موفقیت انجام شد.")
    print("--- All articles processed. Mission complete. ---")

if __name__ == "__main__":
    asyncio.run(main())