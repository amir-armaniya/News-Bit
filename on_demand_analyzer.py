# on_demand_analyzer.py
import os
import asyncio
import json
import random
import feedparser
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
        
        # --- NEW: DEDICATED HANDLER FOR REMOVE FEED UI ---
        elif callback_data == 'remove_feed':
            print("Displaying remove feed interface.")
            custom_feeds = user_data.get('custom_feeds', [])

            if not custom_feeds:
                await telegram_sender.send_text_to_telegram("شما هیچ منبع شخصی برای حذف ندارید.")
            else:
                remove_buttons = []
                for url in custom_feeds:
                    # Each feed gets its own row for clarity
                    remove_buttons.append([(url, f"remove_url:{url}")])
                
                # Add a final cancel button
                remove_buttons.append([("لغو و بازگشت", "display_feeds")])

                await telegram_sender.send_text_with_buttons(
                    "کدام منبع شخصی را می‌خواهید حذف کنید؟",
                    remove_buttons
                )

        # --- RENAMED AND MODIFIED: HANDLER FOR DISPLAYING FEEDS ---
        elif callback_data == 'display_feeds' or callback_data.startswith('confirm_add:') or callback_data in ['cancel_add', 'topics_done', 'feeds_done']:
            print("Displaying dynamic feed management screen.")
            
            # 1. Get custom feeds from payload
            custom_feed_urls = user_data.get('custom_feeds', [])
            
            # 2. Read default feeds from config
            all_feeds = []
            try:
                with open('config.json', 'r', encoding='utf-8') as f:
                    config = json.load(f)
                # Add default feeds as dictionaries
                all_feeds.extend(config.get('rss_feeds', []))
            except (FileNotFoundError, json.JSONDecodeError) as e:
                print(f"Could not read or parse config.json: {e}")
                # Continue with custom feeds even if default fails

            # 3. Merge and De-duplicate
            # Create a set of existing URLs to prevent duplicates
            existing_urls = {feed.get('url') for feed in all_feeds if 'url' in feed}
            for url in custom_feed_urls:
                if url not in existing_urls:
                    all_feeds.append({'name': url, 'url': url}) # Add custom feed as a dictionary
                    existing_urls.add(url)

            # 4. Format and Send the list
            if not all_feeds:
                await telegram_sender.send_text_to_telegram("هیچ منبع خبری برای نمایش وجود ندارد. یکی اضافه کنید!")
            else:
                feed_list_text = "این لیست منابع شماست:\n\n"
                for i, feed in enumerate(all_feeds, 1):
                    feed_list_text += f"{i}. {feed.get('name', 'Unnamed Feed')}\n"
                await telegram_sender.send_text_to_telegram(feed_list_text)

            # 5. Send action buttons
            action_text = "آیا می‌خواهید فیدی اضافه یا حذف کنید؟"
            action_buttons = [
                [("افزودن فید", "add_feed"), ("حذف فید", "remove_feed")],
                [("نه، عالی است", "feeds_done")]
            ]
            await telegram_sender.send_text_with_buttons(action_text, action_buttons)

        # --- NEW: HANDLER FOR ADD FEED CALLBACK ---
        elif callback_data == 'add_feed':
            prompt_message = "لطفاً لینک فید مورد نظر خود را برای من ارسال کنید."
            await telegram_sender.send_text_to_telegram(prompt_message)
            print("Prompted user to send a feed URL.")

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

    # --- NEW: HANDLER FOR FEED SUBMISSION ---
    elif input_type == 'feed_submission':
        submitted_url = user_data.get('url', '')
        print(f"Received feed submission for URL: {submitted_url}")

        if not submitted_url:
            await telegram_sender.send_text_to_telegram("هیچ لینکی دریافت نشد.")
            return

        try:
            feed = feedparser.parse(submitted_url)
            # A valid feed should not be a "bozo" and should have entries.
            if not feed.bozo and feed.entries:
                feed_title = feed.feed.get('title', 'بدون عنوان')
                confirmation_text = f"فید '{feed_title}' را پیدا کردم. آیا می‌خواهید آن را به لیست اضافه کنید؟"
                confirmation_buttons = [
                    [
                        ("بله، اضافه کن", f"confirm_add:{submitted_url}"),
                        ("خیر، لغو", "cancel_add")
                    ]
                ]
                await telegram_sender.send_text_with_buttons(confirmation_text, confirmation_buttons)
            else:
                error_message = "لینک RSS ارسالی معتبر به نظر نمی‌رسد. لطفاً دوباره تلاش کنید."
                await telegram_sender.send_text_to_telegram(error_message)
        except Exception as e:
            print(f"Error parsing feed: {e}")
            await telegram_sender.send_text_to_telegram("خطایی در پردازش لینک فید رخ داد.")

    else:
        print(f"Unknown input type: {input_type}")

if __name__ == "__main__":
    asyncio.run(main())