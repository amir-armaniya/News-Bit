import os
import asyncio
import json # CRITICAL FIX: Added json import to resolve UnboundLocalError
import random
import feedparser
from modules import ai_processor, telegram_sender, web_scraper

<<<<<<< HEAD
<<<<<<< HEAD
# NEW LOGIC: Isolated function for fetching a sample article for onboarding.
# This function DOES NOT and SHOULD NOT check or interact with processed_articles.jsonl.
def fetch_sample_article() -> dict | None:
    """
    Fetches a single, random recent article for the initial user demonstration.
    This function is completely independent of the memory manager.
    """
    print("Fetching a sample article for value demonstration...")
    try:
        with open('config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
        feeds = config.get('rss_feeds', [])
        if not feeds:
            print("config.json is empty or has no feeds.")
            return None

        # Try a few random feeds to increase chances of finding a recent article
        for feed_info in random.sample(feeds, min(len(feeds), 5)):
            try:
                print(f"  -> Checking sample feed: {feed_info.get('name')}")
                feed = feedparser.parse(feed_info['url'])
                if feed.entries:
                    # To ensure freshness, let's pick from the 5 most recent entries
                    recent_entry = random.choice(feed.entries[:5])
                    article = {
                        'title': recent_entry.title,
                        'link': recent_entry.link,
                        'summary': recent_entry.summary
                    }
                    print(f"  -> Found sample: {article['title']}")
                    return article
            except Exception as e:
                print(f"  -> Could not parse sample feed {feed_info.get('name')}: {e}")
                continue # Try next feed
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error reading config.json for sample article: {e}")
        return None
    
    print("Could not find any sample articles after checking feeds.")
    return None

=======
=======
>>>>>>> parent of d72799d (Add fetch_sample_article for onboarding samples)
# This function is now defined in modules.content_collector, but we need a local version for the sample
def fetch_sample_articles(feeds: list) -> list:
    """A simplified local version to fetch articles for the initial sample."""
    articles = []
    if not feeds:
        # Fallback to config.json ONLY if no user_feeds are provided for the sample
        try:
            with open('config.json', 'r', encoding='utf-8') as f:
                config = json.load(f)
            feeds = config.get('rss_feeds', [])
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    for feed_info in random.sample(feeds, min(len(feeds), 3)): # Check 3 random feeds
        try:
            feed = feedparser.parse(feed_info['url'])
            if feed.entries:
                entry = random.choice(feed.entries)
                articles.append({
                    'title': entry.title,
                    'link': entry.link,
                    'summary': entry.summary,
                    'source': feed_info.get('name', feed_info['url'])
                })
        except Exception:
            continue
    return articles
<<<<<<< HEAD
>>>>>>> parent of d72799d (Add fetch_sample_article for onboarding samples)
=======
>>>>>>> parent of d72799d (Add fetch_sample_article for onboarding samples)

async def handle_display_feeds(user_data: dict):
    """Displays the user's current feed list and management options."""
    # This function remains unchanged, but is included for completeness.
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

async def main():
    raw_input = os.getenv('ON_DEMAND_INPUT', '{}').strip()
    try:
        user_data = json.loads(raw_input)
    except json.JSONDecodeError: # Now works because json is imported
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
<<<<<<< HEAD
<<<<<<< HEAD
                # NEW LOGIC: Call the new, isolated function
                sample_article = fetch_sample_article()
                if not sample_article:
                    await telegram_sender.send_text_to_telegram("متاسفانه در حال حاضر مقاله جدیدی برای نمایش نمونه پیدا نشد.")
                    return

=======
                sample_articles = fetch_sample_articles(user_data.get('user_feeds', []))
                if not sample_articles:
                    await telegram_sender.send_text_to_telegram("متاسفانه در حال حاضر مقاله جدیدی برای نمایش نمونه پیدا نشد.")
                    return

                sample_article = random.choice(sample_articles)
>>>>>>> parent of d72799d (Add fetch_sample_article for onboarding samples)
=======
                sample_articles = fetch_sample_articles(user_data.get('user_feeds', []))
                if not sample_articles:
                    await telegram_sender.send_text_to_telegram("متاسفانه در حال حاضر مقاله جدیدی برای نمایش نمونه پیدا نشد.")
                    return

                sample_article = random.choice(sample_articles)
>>>>>>> parent of d72799d (Add fetch_sample_article for onboarding samples)
                analysis_dict = ai_processor.process_article_in_persian(
                    sample_article['title'], sample_article['summary'], sample_article['link']
                )

                if analysis_dict:
                    decision_buttons = [
                        [("عالی، هر هفته برای من ارسال کنید", "activate_quick"), ("عالیه، بریم و منابع رو مشخص کنیم", "activate_custom")]
                    ]
                    # The sample analysis is sent but NOT saved to memory_manager
                    await telegram_sender.send_article_analysis(analysis_dict, buttons=decision_buttons)
                else:
                    await telegram_sender.send_text_to_telegram("خطایی در تحلیل مقاله نمونه رخ داد.")
            except Exception as e:
                print(f"Error during value demonstration: {e}")
                await telegram_sender.send_text_to_telegram("یک خطای غیرمنتظره در آماده‌سازی نمونه رخ داد.")
        
        elif user_text.startswith(('http://', 'https://')):
            # This logic remains the same
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
                await telegram_sender.send_text_to_telegram("متاسفانه نتوانستم محتوای لینک را استخراج کنم.")
        else:
            await telegram_sender.send_text_to_telegram("پیام شما دریافت شد، اما در حال حاضر فقط می‌توانم لینک‌ها را تحلیل کنم.")

    # --- Callback Handler ---
    elif input_type == 'callback':
        # This entire section can remain as it was in the previous correct version,
        # as it correctly handles the UI flow.
        callback_data = user_data.get('data')
        print(f"Received callback: {callback_data}")

        if callback_data == 'activate_quick':
            await telegram_sender.send_text_to_telegram("عالی! گزارش‌های شما هر جمعه ساعت ۹ صبح به وقت تهران ارسال خواهد شد.")
        
        elif callback_data == 'activate_custom':
            intro_text = "بسیار خب. بیایید دستیار را برای شما شخصی‌سازی کنیم. اولویت‌های اصلی شما چیست؟ (می‌توانید تا سه مورد همزمان را انتخاب کنید)"
            topic_buttons = [
                [("هوش مصنوعی", "topic_ai"), ("فناوری مالی", "topic_fintech")],
                [("مدیریت محصول", "topic_pm"), ("جمع‌آوری کمک‌های مالی", "topic_funding")],
                [("تیم‌سازی", "topic_team")],
                [("تمام شد، بیایید به فیدها برویم", "topics_done")]
            ]
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
            await telegram_sender.send_text_to_telegram("اطلاعات شما ذخیره شد. خلاصه‌ای تحلیل‌شده از آخرین مقالات هر آخر هفته در دسترس شما خواهد بود.")

    # --- Feed Submission Handler ---
    elif input_type == 'feed_submission':
        # This section can also remain as it was.
        submitted_url = user_data.get('url', '')
        if not submitted_url:
            await telegram_sender.send_text_to_telegram("هیچ لینکی دریافت نشد. لطفاً دوباره تلاش کنید.")
            await handle_display_feeds(user_data)
            return
        
        try:
            feed = feedparser.parse(submitted_url)
            if feed.feed and feed.feed.get('title'):
                feed_title = feed.feed.get('title', 'فید بدون عنوان')
                confirmation_text = f"فید '{feed_title}' را پیدا کردم. آیا می‌خواهید آن را به لیست اضافه کنید؟"
                
                feed_data = json.dumps({"name": feed_title, "url": submitted_url}, ensure_ascii=False)
                
                confirmation_buttons = [
                    [("بله، اضافه کن", f"confirm_add:{feed_data}"), ("خیر، لغو", "cancel_add")]
                ]
                await telegram_sender.send_text_with_buttons(confirmation_text, confirmation_buttons)
            else:
                await telegram_sender.send_text_to_telegram("لینک RSS ارسالی معتبر به نظر نمی‌رسد یا عنوان ندارد. لطفاً لینک دیگری را امتحان کنید.")
                await handle_display_feeds(user_data)
        except Exception as e:
            print(f"Error parsing feed URL: {e}")
            await telegram_sender.send_text_to_telegram("خطایی در پردازش لینک فید شما رخ داد.")
            await handle_display_feeds(user_data)
            
    else:
        print(f"Unknown or unhandled input type: '{input_type}'")

if __name__ == "__main__":
    asyncio.run(main())