# on_demand_analyzer.py (Final Corrected Version)
import os
import asyncio
import json
import random
import feedparser
from modules import ai_processor, telegram_sender, web_scraper, memory_manager
from modules.content_collector import fetch_sample_articles_from_feeds

async def handle_display_feeds(user_data: dict):
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
    print(f"Handling URL as a potential feed submission: {submitted_url}")
    try:
        feed = feedparser.parse(submitted_url)
        if feed.feed and feed.feed.get('title') and feed.entries:
            feed_title = feed.feed.get('title', 'فید بدون عنوان')
            confirmation_text = f"فید '{feed_title}' را پیدا کردم. آیا می‌خواهید آن را به لیست اضافه کنید؟"
            confirmation_buttons = [
                [("بله، اضافه کن", f"confirm_add:{submitted_url}"), ("خیر، لغو", "cancel_add")]
            ]
            await telegram_sender.send_text_with_buttons(confirmation_text, confirmation_buttons)
            return True
        else:
            return False
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

    if input_type == 'message':
        user_text = user_data.get('text', '').strip()
        user_first_name = user_data.get('first_name', 'کاربر')

        if not user_text:
            return

        if user_text.lower() == '/start':
            welcome_message = f"{user_first_name} عزیز، سلام! به رادار استراتژیک خوش آمدید. من هر هفته جدیدترین مقالات مرتبط با اولویت‌های شما را تحلیل می‌کنم و خلاصه‌های صوتی/متنی تولید می‌کنم.\n\nبرای شروع، لطفاً یکی از گزینه‌های زیر را انتخاب کنید:"
            start_buttons = [
                [("راه‌اندازی سریع (استفاده از منابع پیش‌فرض)", "activate_quick")],
                [("راه‌اندازی سفارشی (انتخاب منابع دستی)", "activate_custom")]
            ]
            await telegram_sender.send_text_with_buttons(welcome_message, start_buttons)
            
            # Fetch and send sample analysis
            sample_feeds = [feed for feed in DEFAULT_FEEDS if 'ai' in feed['tags']][:3]
            sample_articles = await fetch_sample_articles_from_feeds(sample_feeds)
            if sample_articles:
                await telegram_sender.send_text_to_telegram("📚 در حال آماده‌سازی نمونه تحلیل...")
                analysis = await ai_processor.generate_analysis(sample_articles)
                await telegram_sender.send_text_to_telegram(f"نمونه تحلیل:\n\n{analysis}")

        elif user_text.startswith(('http://', 'https://')):
            is_feed = await handle_feed_submission(user_text, user_data)
            if not is_feed:
                print("URL not a feed, scraping as webpage.")
                try:
                    article_content = await web_scraper.scrape_webpage(user_text)
                    if article_content:
                        analysis = await ai_processor.generate_analysis([article_content])
                        await telegram_sender.send_text_to_telegram(f"تحلیل مقاله:\n\n{analysis}")
                    else:
                        await telegram_sender.send_text_to_telegram("متاسفانه نتوانستم محتوای این صفحه را استخراج کنم.")
                except Exception as e:
                    print(f"Web scraping error: {e}")
                    await telegram_sender.send_text_to_telegram("خطا در پردازش صفحه وب. لطفاً آدرس معتبری وارد کنید.")
        else:
            await telegram_sender.send_text_to_telegram("پیام شما دریافت شد، اما در حال حاضر فقط می‌توانم لینک‌ها را تحلیل کنم.")

    elif input_type == 'callback':
        callback_data = user_data.get('data')
        print(f"Received callback: {callback_data}")

        if callback_data == 'activate_quick':
            user_prefs = { 'selected_topics': [], 'user_feeds': user_data.get('user_feeds', []) }
            memory_manager.save_user_preferences(user_prefs)
            await telegram_sender.send_text_to_telegram("عالی! گزارش‌های شما هر جمعه ساعت ۹ صبح به وقت تهران ارسال خواهد شد.")
    
        elif callback_data == 'activate_custom' or callback_data == 'display_topics':
            intro_text = "اولویت‌های اصلی شما چیست؟ (می‌توانید تا سه مورد همزمان را انتخاب کنید)"
            all_topics = {
                "ai": "هوش مصنوعی", "fintech": "فناوری مالی", "pm": "مدیریت محصول",
                "funding": "جمع‌آوری کمک‌های مالی", "team": "تیم‌سازی", "growth": "رشد", "saas": "SaaS"
            }
            selected_topics = user_data.get('selected_topics', [])
            
            topic_buttons = []
            row = []
            for topic_id, topic_name in sorted(all_topics.items()):
                display_name = f"✅ {topic_name}" if topic_id in selected_topics else topic_name
                row.append((display_name, f"topic_{topic_id}"))
                if len(row) >= 2:
                    topic_buttons.append(row)
                    row = []
            if row:
                topic_buttons.append(row)
                
            topic_buttons.append([("تمام شد، بیایید به فیدها برویم", "topics_done")])
            
            await telegram_sender.send_text_with_buttons(intro_text, topic_buttons)

        elif callback_data == 'topics_done':
            await telegram_sender.send_text_to_telegram("اولویت‌های شما ثبت شد. حالا منابع خبری مرتبط با انتخاب شما را مدیریت کنید.")
            
            selected_topics = user_data.get('selected_topics', [])
            all_user_feeds = user_data.get('user_feeds', [])
            
            final_feeds_to_display = all_user_feeds
            if selected_topics:
                print(f"Filtering feeds based on: {selected_topics}")
                filtered_feeds = [
                    feed for feed in all_user_feeds 
                    if 'custom' in feed.get('tags', []) or any(tag in feed.get('tags', []) for tag in selected_topics)
                ]
                final_feeds_to_display = filtered_feeds
            
            display_data = user_data.copy()
            display_data['user_feeds'] = final_feeds_to_display
            await handle_display_feeds(display_data)

        elif callback_data == 'feeds_done':
            user_prefs = {
                'selected_topics': user_data.get('selected_topics', []),
                'user_feeds': user_data.get('user_feeds', [])
            }
            memory_manager.save_user_preferences(user_prefs)
            await telegram_sender.send_text_to_telegram("اطلاعات شما ذخیره شد. خلاصه‌ای تحلیل‌شده از آخرین مقالات هر آخر هفته در دسترس شما خواهد بود.")
        
        elif callback_data == 'add_feed':
            await telegram_sender.send_text_to_telegram("لطفاً لینک فید RSS مورد نظر خود را برای من ارسال کنید.")

        elif callback_data == 'remove_feed':
            user_feeds = user_data.get('user_feeds', [])
            if not user_feeds:
                await telegram_sender.send_text_to_telegram("لیست منابع شما خالی است.")
                return
                
            remove_buttons = [
                [(feed['name'], f"remove_execute:{feed['url']}")] 
                for feed in user_feeds
            ]
            remove_buttons.append([("لغو", "cancel_remove")])
            await telegram_sender.send_text_with_buttons("کدام منبع را می‌خواهید حذف کنید؟", remove_buttons)

        elif callback_data.startswith('remove_execute:'):
            url_to_remove = callback_data.split(':')[1]
            # Actual removal happens in Cloudflare Worker
            await telegram_sender.send_text_to_telegram(f"درخواست حذف منبع برای {url_to_remove} ثبت شد.")

        elif callback_data == 'cancel_add':
            await telegram_sender.send_text_to_telegram("عملیات اضافه کردن فید لغو شد.")

        elif callback_data == 'cancel_remove':
            await telegram_sender.send_text_to_telegram("عملیات حذف فید لغو شد.")


if __name__ == "__main__":
    asyncio.run(main())