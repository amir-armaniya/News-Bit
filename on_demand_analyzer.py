import os
import asyncio
import json
import random
import feedparser
from modules import ai_processor, telegram_sender, web_scraper

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
                sample_articles = fetch_sample_articles(user_data.get('user_feeds', []))
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
                await handle_display_feeds(user_data) # Show management options again
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
                
                # We must pass the data as a JSON string within the callback data
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