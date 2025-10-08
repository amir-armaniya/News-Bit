# on_demand_analyzer.py
import os
import asyncio
import json
import random
from modules import ai_processor, telegram_sender, web_scraper
from modules.content_collector import fetch_recent_articles

async def main():
    raw_input = os.getenv('ON_DEMAND_INPUT', '{}').strip()
    try:
        user_data = json.loads(raw_input)
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON input: {raw_input}")
        return

    input_type = user_data.get('type')

    # --- NEW: ROUTER FOR INPUT TYPE ---
    if input_type == 'callback':
        callback_data = user_data.get('data')
        print(f"Received callback query with data: {callback_data}")

        if callback_data == 'activate_quick':
            confirmation_message = "عالی! گزارش‌های شما هر جمعه ساعت ۹ صبح به وقت تهران ارسال خواهد شد."
            await telegram_sender.send_text_to_telegram(confirmation_message)
            print("Sent quick activation confirmation.")
        
        # --- NEW: HANDLER FOR CUSTOMIZATION PATH ---
        elif callback_data == 'activate_custom':
            intro_text = "بسیار خب. بیایید دستیار را برای شما شخصی‌سازی کنیم. اولویت‌های اصلی شما چیست؟ (می‌توانید تا سه مورد همزمان را انتخاب کنید)"
            
            topic_buttons = [
                [("هوش مصنوعی", "topic_ai"), ("فناوری مالی", "topic_fintech")],
                [("مدیریت محصول", "topic_pm"), ("جمع‌آوری کمک‌های مالی", "topic_funding")],
                [("تیم‌سازی", "topic_team")],
                [("تمام شد، بیایید به فیدها برویم", "topics_done")]
            ]

            await telegram_sender.send_text_with_buttons(intro_text, topic_buttons)
            print("Sent topic selection interface.")
        
        # Add other callback handlers here in the future...

    elif input_type == 'message':
        user_text = user_data.get('text', '').strip()
        user_first_name = user_data.get('first_name', 'کاربر')
        
        print(f"Received message with text: {user_text}")

        if not user_text:
            print("No text provided in the input. Exiting.")
            return

        # --- UPDATED LOGIC FOR /start COMMAND ---
        if user_text.lower() == '/start':
        # Step 1: Send initial value proposition
        initial_message = "رباتی که اخبار هفتگی مورد نیاز شما را تجزیه و تحلیل، ترجمه و ارائه می‌دهد."
        await telegram_sender.send_text_to_telegram(initial_message)
        
        # Step 2: Send personalized welcome
        welcome_message = f"{user_first_name} عزیز، سلام! این ربات اخبار هفتگی شما را تجزیه و تحلیل و ترجمه می‌کند. برای نشان دادن نحوه کار آن، یک مقاله جدید از یک وب‌سایت نمونه برای شما ارسال خواهیم کرد."
        await telegram_sender.send_text_to_telegram(welcome_message)

        print("Sent initial proposition and personalized welcome for /start command.")
        
        # --- NEW: VALUE DEMONSTRATION LOGIC ---
        print("Starting value demonstration...")
        try:
            # 1. Fetch recent articles
            recent_articles = fetch_recent_articles("config.json")

            if not recent_articles:
                await telegram_sender.send_text_to_telegram("متاسفانه در حال حاضر مقاله جدیدی برای نمایش نمونه پیدا نشد. لطفاً کمی بعد دوباره تلاش کنید.")
                return

            # 2. Select a random article
            sample_article = random.choice(recent_articles)
            print(f"Selected sample article: {sample_article['title']}")
            
            # 3. Process the article
            analysis_dict = ai_processor.process_article_in_persian(
                sample_article['title'],
                sample_article['summary'],
                sample_article['link']
            )

            # 4. Send analysis with decision buttons
            if analysis_dict:
                decision_buttons = [
                    [
                        ("عالی، هر هفته برای من ارسال کنید", "activate_quick"),
                        ("عالیه، بریم و منابع رو مشخص کنیم", "activate_custom")
                    ]
                ]
                await telegram_sender.send_article_analysis(analysis_dict, buttons=decision_buttons)
                print("Successfully sent sample analysis with decision buttons.")
            else:
                await telegram_sender.send_text_to_telegram("خطایی در تحلیل مقاله نمونه رخ داد. لطفاً بعداً تلاش کنید.")

        except Exception as e:
            print(f"An error occurred during value demonstration: {e}")
            await telegram_sender.send_text_to_telegram("یک خطای غیرمنتظره در آماده‌سازی نمونه رخ داد.")
        
            return # Stop execution after /start flow

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

    else:
        print(f"Unknown input type: {input_type}")

if __name__ == "__main__":
    asyncio.run(main())