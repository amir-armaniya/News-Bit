# on_demand_analyzer.py
import os
import asyncio
import json
from modules import ai_processor, telegram_sender, web_scraper

async def main():
    raw_input = os.getenv('ON_DEMAND_INPUT', '{}').strip()

    try:
        user_data = json.loads(raw_input)
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON input: {raw_input}")
        return

    user_text = user_data.get('text', '').strip()
    user_first_name = user_data.get('first_name', 'کاربر') # Default to 'کاربر'

    if not user_text:
        print("No text provided in the input. Exiting.")
        return

    print(f"Received on-demand text: {user_text}")

    # --- UPDATED LOGIC FOR /start COMMAND ---
    if user_text.lower() == '/start':
        # Step 1: Send initial value proposition
        initial_message = "رباتی که اخبار هفتگی مورد نیاز شما را تجزیه و تحلیل، ترجمه و ارائه می‌دهد."
        await telegram_sender.send_text_to_telegram(initial_message)
        
        # Step 2: Send personalized welcome
        welcome_message = f"{user_first_name} عزیز، سلام! این ربات اخبار هفتگی شما را تجزیه و تحلیل و ترجمه می‌کند. برای نشان دادن نحوه کار آن، یک مقاله جدید از یک وب‌سایت نمونه برای شما ارسال خواهیم کرد."
        await telegram_sender.send_text_to_telegram(welcome_message)

        print("Sent initial proposition and personalized welcome for /start command.")
        return # Important: Stop further execution

    # --- Existing Command Handling (ensure it uses user_text) ---
    if user_text.lower().startswith('/add_source'):
        await telegram_sender.send_text_to_telegram("Functionality to add sources is not yet implemented.")
        return

    # --- Existing URL Analysis (ensure it uses user_text) ---
    if user_text.startswith(('http://', 'https://')):
        print(f"Input is a URL. Starting web scraping for: {user_text}")

        scraped_content = web_scraper.scrape_url(user_text)

        if not scraped_content:
            await telegram_sender.send_text_to_telegram(f"متاسفانه نتوانستم محتوای لینک را استخراج کنم: {user_text}")
            return

        print("Scraping successful. Analyzing content...")
        analysis_dict = ai_processor.process_article_in_persian(
            scraped_content['title'],
            scraped_content['text'],
            user_text
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