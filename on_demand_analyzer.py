# on_demand_analyzer.py
import os
import asyncio
from modules import ai_processor, telegram_sender, web_scraper

async def main():
    user_input = os.getenv('ON_DEMAND_INPUT', '').strip()

    if not user_input:
        print("No on-demand input provided. Exiting.")
        return

    print(f"Received on-demand input: {user_input}")

    # --- Simple Command Handling ---
    if user_input.lower().startswith('/add_source'):
        await telegram_sender.send_text_to_telegram("Functionality to add sources is not yet implemented.")
        return

    # --- URL Analysis ---
    if user_input.startswith(('http://', 'https://')):
        print(f"Input is a URL. Starting web scraping for: {user_input}")

        scraped_content = web_scraper.scrape_url(user_input)

        if not scraped_content:
            await telegram_sender.send_text_to_telegram(f"متاسفانه نتوانستم محتوای لینک را استخراج کنم: {user_input}")
            return

        print("Scraping successful. Analyzing content...")
        analysis_dict = ai_processor.process_article_in_persian(
            scraped_content['title'],
            scraped_content['text'],
            user_input
        )

        if analysis_dict:
            # Save the analysis to memory
            from modules import memory_manager
            memory_manager.save_analysis(analysis_dict)
            
            await telegram_sender.send_article_analysis(analysis_dict)
            print("Analysis sent successfully.")
        else:
            await telegram_sender.send_text_to_telegram("متاسفانه در تحلیل محتوای لینک خطایی رخ داد.")
    else:
        await telegram_sender.send_text_to_telegram("پیام شما دریافت شد، اما در حال حاضر فقط می‌توانم لینک‌ها را تحلیل کنم.")
        print("Non-URL input handled.")

if __name__ == "__main__":
    asyncio.run(main())