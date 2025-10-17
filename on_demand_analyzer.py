# on_demand_analyzer.py
import os
import asyncio
import json
import random
import feedparser
from modules import ai_processor, telegram_sender, web_scraper
from modules.content_collector import fetch_recent_articles

async def handle_display_feeds(user_data: dict):
    """Display user's feeds with management options"""
    user_feeds = user_data.get('user_feeds', [])
    
    # Validate feed objects
    valid_feeds = []
    for feed in user_feeds:
        if isinstance(feed, dict) and feed.get('url'):
            valid_feeds.append(feed)
    
    if not valid_feeds:
        await telegram_sender.send_text_to_telegram("هنوز هیچ فیدی اضافه نکرده‌اید.")
        return
    
    # Format feed list
    feed_list = "\n".join(
        f"{i}. {feed.get('name', feed['url'])}"
        for i, feed in enumerate(valid_feeds, 1)
    )
    await telegram_sender.send_text_to_telegram(f"فیدهای فعلی:\n{feed_list}")
    
    # Create action buttons
    markup = [
        [("افزودن فید", "add_feed"), ("حذف فید", "remove_feed")],
        [("نه، عالی است", "feeds_done")]
    ]
    await telegram_sender.send_text_with_buttons(
        "آیا می‌خواهید فیدی اضافه یا حذف کنید؟",
        markup
    )

async def main():
    raw_input = os.getenv('ON_DEMAND_INPUT', '{}').strip()
    try:
        user_data = json.loads(raw_input)
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON input: {raw_input}")
        return

    input_type = user_data.get('type')

    if input_type == 'callback':
        callback_data = user_data.get('data')
        print(f"Received callback query with data: {callback_data}")

        if callback_data == 'activate_quick':
            confirmation_message = "عالی! گزارش‌های شما هر جمعه ساعت ۹ صبح به وقت تهران ارسال خواهد شد."
            await telegram_sender.send_text_to_telegram(confirmation_message)
            print("Sent quick activation confirmation.")
        
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
        
        elif callback_data == 'topics_done':
            user_feeds = user_data.get('user_feeds', [])
            
            payload = {
                'type': 'callback',
                'data': 'topics_done',
                'user_feeds': user_feeds
            }
            # In a real implementation, we would send this payload to the next processing stage
            print(f"Prepared topics_done payload with user feeds: {payload}")
            await telegram_sender.send_text_to_telegram("اولویت‌های شما ثبت شد. حالا منابع خبری پیش‌فرض را بررسی می‌کنیم.")
            await handle_display_feeds(user_data)
        
        elif callback_data == 'remove_feed':
            print("Displaying remove feed interface.")
            user_feeds = user_data.get('user_feeds', [])
            if not user_feeds:
                await telegram_sender.send_text_to_telegram("شما هیچ منبع شخصی برای حذف ندارید.")
            else:
                # Create remove buttons for each user feed
                remove_buttons = [
                    [("❌ " + feed.get('name', feed['url']), f"remove_confirm:{feed['url']}")]
                    for feed in user_feeds
                ]
                remove_buttons.append([("لغو و بازگشت", "display_feeds")])
                await telegram_sender.send_text_with_buttons(
                    "کدام منبع شخصی را می‌خواهید حذف کنید؟ روی منبع کلیک کنید تا انتخاب شود.",
                    remove_buttons
                )

        elif callback_data.startswith('remove_confirm:'):
            url = callback_data.split(':', 1)[1]
            print(f"Received removal confirmation request for URL: {url}")
            
            feed_name = url  # Use URL directly since we don't have config names
            
            confirmation_text = f"آیا مطمئنید که می‌خواهید منبع '{feed_name}' را حذف کنید؟"
            confirmation_buttons = [
                [("بله، حذف کن", f"remove_execute:{url}"), ("خیر، بازگشت", "display_feeds")]
            ]
            await telegram_sender.send_text_with_buttons(confirmation_text, confirmation_buttons)

        elif callback_data == 'feeds_done':
            confirmation_message = "اطلاعات شما دریافت شد، خلاصه‌ای تحلیل‌شده از آخرین مقالات هر آخر هفته در دسترس شما خواهد بود."
            await telegram_sender.send_text_to_telegram(confirmation_message)
            print("Sent final customization confirmation message.")

        if callback_data in ['topics_done', 'display_feeds', 'cancel_add', 'feeds_done'] \
           or callback_data.startswith(('remove_execute:', 'confirm_add:')):
            await handle_display_feeds(user_data)

        elif callback_data == 'remove_feed':
            print("Displaying remove feed interface.")
            user_feeds = user_data.get('user_feeds', [])
            if not user_feeds:
                await telegram_sender.send_text_to_telegram("شما هیچ منبع شخصی برای حذف ندارید.")
            else:
                # Create remove buttons for each user feed
                remove_buttons = [
                    [("❌ " + feed.get('name', feed['url']), f"remove_confirm:{feed['url']}")]
                    for feed in user_feeds
                ]
                remove_buttons.append([("لغو و بازگشت", "display_feeds")])
                await telegram_sender.send_text_with_buttons(
                    "کدام منبع شخصی را می‌خواهید حذف کنید؟ روی منبع کلیک کنید تا انتخاب شود.",
                    remove_buttons
                )

        elif callback_data.startswith('remove_confirm:'):
            url = callback_data.split(':', 1)[1]
            print(f"Received removal confirmation request for URL: {url}")
            
            feed_name = url  # Use URL directly since we don't have config names
            
            confirmation_text = f"آیا مطمئنید که می‌خواهید منبع '{feed_name}' را حذف کنید؟"
            confirmation_buttons = [
                [("بله، حذف کن", f"remove_execute:{url}"), ("خیر، بازگشت", "display_feeds")]
            ]
            await telegram_sender.send_text_with_buttons(confirmation_text, confirmation_buttons)

        elif callback_data == 'add_feed':
            prompt_message = "لطفاً لینک فید مورد نظر خود را برای من ارسال کنید."
            await telegram_sender.send_text_to_telegram(prompt_message)
            print("Prompted user to send a feed URL.")

    elif input_type == 'message':
        user_text = user_data.get('text', '').strip()
        user_first_name = user_data.get('first_name', 'کاربر')
        
        if not user_text:
            return

        print(f"Received message with text: {user_text}")

        # --- CORRECTED INDENTATION BLOCK FOR /start ---
        if user_text.lower() == '/start':
            # Send personalized welcome
            welcome_message = f"{user_first_name} عزیز، سلام! این ربات اخبار هفتگی شما را تجزیه و تحلیل و ترجمه می‌کند. برای نشان دادن نحوه کار آن، یک مقاله جدید از یک وب‌سایت نمونه برای شما ارسال خواهیم کرد."
            await telegram_sender.send_text_to_telegram(welcome_message)
            print("Sent personalized welcome.")
            
            # Value Demonstration
            print("Starting value demonstration...")
            try:
                recent_articles = fetch_recent_articles(user_data.get('user_feeds', []))
                if not recent_articles:
                    await telegram_sender.send_text_to_telegram("متاسفانه در حال حاضر مقاله جدیدی برای نمایش نمونه پیدا نشد.")
                    return

                sample_article = random.choice(recent_articles)
                print(f"Selected sample article: {sample_article['title']}")
                
                analysis_dict = ai_processor.process_article_in_persian(
                    sample_article['title'], sample_article['summary'], sample_article['link']
                )

                if analysis_dict:
                    decision_buttons = [
                        [("عالی، هر هفته برای من ارسال کنید", "activate_quick"), ("عالیه، بریم و منابع رو مشخص کنیم", "activate_custom")]
                    ]
                    await telegram_sender.send_article_analysis(analysis_dict, buttons=decision_buttons)
                    print("Successfully sent sample analysis with decision buttons.")
                else:
                    await telegram_sender.send_text_to_telegram("خطایی در تحلیل مقاله نمونه رخ داد.")
            except Exception as e:
                print(f"An error occurred during value demonstration: {e}")
                await telegram_sender.send_text_to_telegram("یک خطای غیرمنتظره در آماده‌سازی نمونه رخ داد.")
            return # IMPORTANT: Stop execution after the /start flow is complete.
        
        # --- Other message handling ---
        elif user_text.startswith(('http://', 'https://')):
            print(f"Input is a URL. Scraping: {user_text}")
            scraped_content = web_scraper.scrape_url(user_text)
            if scraped_content:
                analysis_dict = ai_processor.process_article_in_persian(
                    scraped_content['title'], scraped_content['text'], user_text
                )
                if analysis_dict:
                    await telegram_sender.send_article_analysis(analysis_dict)
                else:
                    await telegram_sender.send_text_to_telegram("متاسفانه در تحلیل محتوای لینک خطایی رخ داد.")
            else:
                await telegram_sender.send_text_to_telegram(f"متاسفانه نتوانستم محتوای لینک را استخراج کنم.")
        else:
            await telegram_sender.send_text_to_telegram("پیام شما دریافت شد، اما در حال حاضر فقط می‌توانم لینک‌ها را تحلیل کنم.")
            print("Non-URL, non-command input handled.")

    elif input_type == 'feed_submission':
        submitted_url = user_data.get('url', '')
        print(f"Received feed submission for URL: {submitted_url}")
        if not submitted_url:
            await telegram_sender.send_text_to_telegram("هیچ لینکی دریافت نشد.")
            return
        try:
            feed = feedparser.parse(submitted_url)
            if not feed.bozo and feed.entries:
                feed_title = feed.feed.get('title', 'بدون عنوان')
                
                # Validate feed structure
                if not feed_title or not submitted_url:
                    await telegram_sender.send_text_to_telegram("ساختار فید نامعتبر است. لطفاً یک فید معتبر ارسال کنید.")
                    return
                    
                confirmation_text = f"فید '{feed_title}' را پیدا کردم. آیا می‌خواهید آن را به لیست اضافه کنید؟"
                feed_data = json.dumps({"name": feed_title, "url": submitted_url})
                callback_data = f"confirm_add:{feed_data}"
                confirmation_buttons = [
                    [("بله، اضافه کن", callback_data), ("خیر، لغو", "display_feeds")]
                ]
                await telegram_sender.send_text_with_buttons(confirmation_text, confirmation_buttons)
            else:
                await telegram_sender.send_text_to_telegram("لینک RSS ارسالی معتبر به نظر نمی‌رسد.")
        except Exception as e:
            print(f"Error parsing feed: {e}")
            await telegram_sender.send_text_to_telegram("خطایی در پردازش لینک فید رخ داد.")

    elif input_type == 'remove_execute':
        url_to_remove = user_data.get('url')
        if url_to_remove:
            user_feeds = user_data.get('user_feeds', [])
            # Validate feed structure before processing
            if not isinstance(user_feeds, list):
                await telegram_sender.send_text_to_telegram("خطا در ساختار داده‌های منابع کاربر.")
                return

            # Find feed by URL
            feed_to_remove = next((feed for feed in user_feeds if isinstance(feed, dict) and feed.get('url') == url_to_remove), None)
            if feed_to_remove:
                user_feeds.remove(feed_to_remove)
                await telegram_sender.send_text_to_telegram(f"منبع '{feed_to_remove.get('name', url_to_remove)}' با موفقیت حذف شد.")
                # Refresh feed display
                await handle_display_feeds(user_data)
                
    elif input_type == 'display_feeds':
        await handle_display_feeds(user_data)
            else:
                await telegram_sender.send_text_to_telegram("این منبع در لیست شما وجود ندارد.")
        else:
            await telegram_sender.send_text_to_telegram("هیچ لینکی برای حذف مشخص نشده است.")
    
    else:
        print(f"Unknown or empty input type received: '{input_type}'")

if __name__ == "__main__":
    asyncio.run(main())