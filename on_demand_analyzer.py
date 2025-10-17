# on_demand_analyzer.py
import os
import asyncio
import json
import random
import feedparser
from modules import ai_processor, telegram_sender, web_scraper, memory_manager
from modules.content_collector import fetch_sample_articles_from_feeds

async def handle_display_feeds(user_data: dict):
    """Displays the user's current feed list and management options."""
    print("handle_display_feeds triggered.")
    user_feeds = user_data.get('user_feeds', [])
    
    feed_list_text = "این لیست منابع شماست:\n\n"
    if not user_feeds:
        feed_list_text += "لیست شما در حال حاضر خالی است."
    else:
        feed_list_text += "\n".join(
            f"{i}. {feed.get('name', feed.get('url', 'فید بدون نام'))}"
            for i, feed in enumerate(user_feeds, 1)
        )
    
    await telegram_sender.send_text_to_telegram(feed_list_text)
    
    action_buttons = [
        [("افزودن فید", "add_feed"), ("حذف فید", "remove_feed")],
        [("نه، عالی است", "feeds_done")]
    ]
    await telegram_sender.send_text_with_buttons("آیا می‌خواهید فیدی اضافه یا حذف کنید؟", action_buttons)

async def handle_feed_submission(submitted_url: str, user_data: dict):
    """Handles the logic for validating and confirming a new feed URL."""
    print(f"Handling URL as a potential feed submission: {submitted_url}")
    try:
        feed = feedparser.parse(submitted_url)
        # A valid feed must have a title and at least one entry
        if feed.feed and feed.feed.get('title') and feed.entries:
            feed_title = feed.feed.get('title', 'فید بدون عنوان')
            confirmation_text = f"فید '{feed_title}' را پیدا کردم. آیا می‌خواهید آن را به لیست اضافه کنید؟"
            
            # The callback_data now contains ONLY the URL, which is much shorter.
            confirmation_buttons = [
                [("بله، اضافه کن", f"confirm_add:{submitted_url}"), ("خیر، لغو", "cancel_add")]
            ]
            await telegram_sender.send_text_with_buttons(confirmation_text, confirmation_buttons)
            return True # Indicates the URL was handled as a feed
        else:
            return False # Indicates this was not a valid feed
    except Exception as e:
        print(f"Error parsing feed URL during submission check: {e}")
        return False

async def main():
    raw_input = os.getenv('ON_DEMAND_INPUT', '{}').strip()
    try:
        user_data = json.loads(raw_input)
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON input: {raw_input}")
        return

    input_type = user_data.get('type')

    # --- Message Handler ---
    if input_type == 'message':
        user_text = user_data.get('text', '').strip()
        user_first_name = user_data.get('first_name', 'کاربر')

        if not user_text:
            return

        print(f"Received message: {user_text}")

        if user_text.lower() == '/start':
            welcome_message = f"{user_first_name} عزیز، سلام! این ربات اخبار هفتگی شما را تجزیه و تحلیل و ترجمه می‌کند. برای نشان دادن نحوه کار آن، یک مقاله جدید از یک وب‌سایت نمونه برای شما ارسال خواهیم کرد."
            await telegram_sender.send_text_to_telegram(welcome_message)
            
            try:
                feeds_for_sample = user_data.get('user_feeds', [])
                if not feeds_for_sample:
                    try:
                        with open('config.json', 'r', encoding='utf-8') as f:
                            config = json.load(f)
                        feeds_for_sample = config.get('rss_feeds', [])
                    except (FileNotFoundError, json.JSONDecodeError):
                        feeds_for_sample = []

                sample_articles = fetch_sample_articles_from_feeds(feeds_for_sample)

                if not sample_articles:
                    await telegram_sender.send_text_to_telegram("متاسفانه در حال حاضر مقاله جدیدی برای نمایش نمونه پیدا نشد.")
                    return

                sample_article = random.choice(sample_articles)
                analysis_dict = ai_processor.process_article_in_persian(
                    sample_article['title'], sample_article['summary'], sample_article['link']
                )

                if analysis_dict:
                    decision_buttons = [
                        [("عالی، هر هفته برای من ارسال کنید", "activate_quick"), ("عالیه، بریم و منابع رو مشخص کنیم", "activate_custom")]
                    ]
                    await telegram_sender.send_article_analysis(analysis_dict, buttons=decision_buttons)
                else:
                    await telegram_sender.send_text_to_telegram("خطایی در تحلیل مقاله نمونه رخ داد.")
            except Exception as e:
                print(f"Error during value demonstration: {e}")
                await telegram_sender.send_text_to_telegram("یک خطای غیرمنتظره در آماده‌سازی نمونه رخ داد.")
        
        elif user_text.startswith(('http://', 'https://')):
            # **NEW INTELLIGENT LOGIC**
            is_feed = await handle_feed_submission(user_text, user_data)
            
            if not is_feed:
                # If it was not a valid feed, fall back to scraping it as a webpage
                print("URL was not a valid feed. Falling back to web scraper.")
                scraped_content = web_scraper.scrape_url(user_text)
                if scraped_content:
                    analysis_dict = ai_processor.process_article_in_persian(
                        scraped_content['title'], scraped_content['text'], user_text
                    )
                    if analysis_dict:
                        memory_manager.save_analysis(analysis_dict)
                        await telegram_sender.send_article_analysis(analysis_dict)
                    else:
                        await telegram_sender.send_text_to_telegram("متاسفانه در تحلیل محتوای لینک خطایی رخ داد.")
                else:
                    await telegram_sender.send_text_to_telegram("متاسفانه نتوانستم محتوای این لینک را استخراج کنم. ممکن است یک لینک RSS نامعتبر یا یک صفحه وب خالی باشد.")
        else:
            await telegram_sender.send_text_to_telegram("پیام شما دریافت شد، اما در حال حاضر فقط می‌توانم لینک‌ها را تحلیل کنم.")

    # --- Callback Handler (No changes needed here) ---
    elif input_type == 'callback':
        callback_data = user_data.get('data')
        print(f"Received callback: {callback_data}")

        if callback_data == 'activate_quick':
            # Save user preferences before confirming
            user_prefs = {
                'selected_topics': user_data.get('selected_topics', []),
                'user_feeds': user_data.get('user_feeds', [])
            }
            memory_manager.save_user_preferences(user_prefs)
            await telegram_sender.send_text_to_telegram("عالی! گزارش‌های شما هر جمعه ساعت ۹ صبح به وقت تهران ارسال خواهد شد.")
        
        elif callback_data == 'display_topics' or callback_data == 'activate_custom':
            intro_text = "بسیار خب. بیایید دستیار را برای شما شخصی‌سازی کنیم. اولویت‌های اصلی شما چیست؟ (می‌توانید تا سه مورد همزمان را انتخاب کنید)"
            
            all_topics = {
                "ai": "هوش مصنوعی",
                "fintech": "فناوری مالی",
                "pm": "مدیریت محصول",
                "funding": "جمع‌آوری کمک‌های مالی",
                "team": "تیم‌سازی"
            }
            selected_topics = user_data.get('selected_topics', [])
            
            topic_buttons = []
            row = []
            for topic_id, topic_name in all_topics.items():
                display_name = f"✅ {topic_name}" if topic_id in selected_topics else topic_name
                row.append((display_name, f"topic_{topic_id}"))
                if len(row) == 2:
                    topic_buttons.append(row)
                    row = []
            if row:
                topic_buttons.append(row)
                
            topic_buttons.append([("تمام شد، بیایید به فیدها برویم", "topics_done")])
            
            await telegram_sender.send_text_with_buttons(intro_text, topic_buttons)

        elif callback_data in ['topics_done', 'display_feeds', 'cancel_add'] or callback_data.startswith('confirm_add:'):
            if callback_data == 'topics_done':
                 await telegram_sender.send_text_to_telegram("اولویت‌های شما ثبت شد. حالا منابع خبری را مدیریت کنید.")
            await handle_display_feeds(user_data)

        elif callback_data == 'add_feed':
            await telegram_sender.send_text_to_telegram("لطفاً لینک فید RSS مورد نظر خود را برای من ارسال کنید.")

        elif callback_data == 'remove_feed':
            user_feeds = user_data.get('user_feeds', [])
            if not user_feeds:
                await telegram_sender.send_text_to_telegram("شما هیچ منبع خبری برای حذف ندارید.")
                await handle_display_feeds(user_data)
            else:
                remove_buttons = [
                    [("❌ " + feed.get('name', feed.get('url')), f"remove_confirm:{feed.get('url')}")]
                    for feed in user_feeds
                ]
                remove_buttons.append([("لغو و بازگشت", "display_feeds")])
                await telegram_sender.send_text_with_buttons(
                    "کدام منبع را می‌خواهید حذف کنید؟",
                    remove_buttons
                )

        elif callback_data.startswith('remove_confirm:'):
            url = callback_data.split(':', 1)[1]
            feed_name = url 
            user_feeds = user_data.get('user_feeds', [])
            for feed in user_feeds:
                if feed.get('url') == url:
                    feed_name = feed.get('name', url)
                    break
            
            confirmation_text = f"آیا مطمئنید که می‌خواهید منبع '{feed_name}' را حذف کنید؟"
            confirmation_buttons = [
                [("بله، حذف کن", f"remove_execute:{url}"), ("خیر، بازگشت", "display_feeds")]
            ]
            await telegram_sender.send_text_with_buttons(confirmation_text, confirmation_buttons)

        elif callback_data == 'feeds_done':
            # Save user preferences before confirming
            user_prefs = {
                'selected_topics': user_data.get('selected_topics', []),
                'user_feeds': user_data.get('user_feeds', [])
            }
            memory_manager.save_user_preferences(user_prefs)
            await telegram_sender.send_text_to_telegram("اطلاعات شما ذخیره شد. خلاصه‌ای تحلیل‌شده از آخرین مقالات هر آخر هفته در دسترس شما خواهد بود.")

    # --- Feed Submission Handler ---
    elif input_type == 'feed_submission':
        submitted_url = user_data.get('url', '')
        print(f"Received feed submission for URL: {submitted_url}")

        if not submitted_url:
            await telegram_sender.send_text_to_telegram("هیچ لینکی دریافت نشد. لطفاً دوباره تلاش کنید.")
            await handle_display_feeds(user_data)
            return

        # Call the dedicated function to validate and send confirmation buttons
        # handle_feed_submission returns True if confirmation buttons were sent, False otherwise.
        was_successful = await handle_feed_submission(submitted_url, user_data)
        
        if not was_successful:
            # If handle_feed_submission returned False, it means validation failed.
            await telegram_sender.send_text_to_telegram("لینک RSS ارسالی معتبر به نظر نمی‌رسد یا عنوان ندارد. لطفاً لینک دیگری را امتحان کنید.")
            # Redisplay feed management options upon failure
            await handle_display_feeds(user_data)
        
        # If successful, handle_feed_submission has already sent the confirmation buttons,
        # and the script should exit successfully (silently).
            
    else:
        print(f"Unknown or unhandled input type: '{input_type}'")

if __name__ == "__main__":
    asyncio.run(main())