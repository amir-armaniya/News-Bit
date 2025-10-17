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
        
        elif callback_data == 'remove_feed':
            print("Displaying remove feed interface.")
            custom_feeds = user_data.get('custom_feeds', [])
            if not custom_feeds:
                await telegram_sender.send_text_to_telegram("شما هیچ منبع شخصی برای حذف ندارید.")
            else:
                remove_buttons = [[(url, f"remove_url:{url}")] for url in custom_feeds]
                remove_buttons.append([("لغو و بازگشت", "display_feeds")])
                await telegram_sender.send_text_with_buttons("کدام منبع شخصی را می‌خواهید حذف کنید؟", remove_buttons)

        elif callback_data == 'feeds_done':
            confirmation_message = "اطلاعات شما دریافت شد، خلاصه‌ای تحلیل‌شده از آخرین مقالات هر آخر هفته در دسترس شما خواهد بود."
            await telegram_sender.send_text_to_telegram(confirmation_message)
            print("Sent final customization confirmation message.")

        elif callback_data == 'display_feeds' or callback_data.startswith('confirm_add:') or callback_data in ['cancel_add', 'topics_done']:
            print("Displaying dynamic feed management screen.")
            custom_feed_urls = user_data.get('custom_feeds', [])
            all_feeds = []
            try:
                with open('config.json', 'r', encoding='utf-8') as f:
                    config = json.load(f)
                all_feeds.extend(config.get('rss_feeds', []))
            except (FileNotFoundError, json.JSONDecodeError) as e:
                print(f"Could not read or parse config.json: {e}")

            existing_urls = {feed.get('url') for feed in all_feeds if 'url' in feed}
            for url in custom_feed_urls:
                if url not in existing_urls:
                    all_feeds.append({'name': url, 'url': url})
                    existing_urls.add(url)

            if not all_feeds:
                await telegram_sender.send_text_to_telegram("هیچ منبع خبری برای نمایش وجود ندارد. یکی اضافه کنید!")
            else:
                feed_list_text = "این لیست منابع شماست:\n\n" + "\n".join(f"{i}. {feed.get('name', 'Unnamed Feed')}" for i, feed in enumerate(all_feeds, 1))
                await telegram_sender.send_text_to_telegram(feed_list_text)

            action_text = "آیا می‌خواهید فیدی اضافه یا حذف کنید؟"
            action_buttons = [
                [("افزودن فید", "add_feed"), ("حذف فید", "remove_feed")],
                [("نه، عالی است", "feeds_done")]
            ]
            await telegram_sender.send_text_with_buttons(action_text, action_buttons)

        elif callback_data == 'add_feed':
            prompt_message = "لطفاً لینک فید مورد نظر خود را برای من ارسال کنید."
            await telegram_sender.send_text_to_telegram(prompt_message)
            print("Prompted user to send a feed URL.")

    elif input_type == 'feed_deletion_request':
        print("Processing feed deletion request")
        custom_feeds = user_data.get('custom_feeds', [])
        if not custom_feeds:
            await telegram_sender.send_text_to_telegram("هیچ منبع شخصی برای حذف وجود ندارد.")
            return
        
        try:
            indices_input = user_data.get('text', '').strip()
            if not indices_input:
                await telegram_sender.send_text_to_telegram("هیچ شماره‌ای وارد نشده است.")
                return
                
            selected_indices = [int(idx.strip()) for idx in indices_input.split(',') if idx.strip().isdigit()]
            if not selected_indices:
                await telegram_sender.send_text_to_telegram("فرمت ورودی نامعتبر است. لطفاً اعداد را با کاما جدا کنید.")
                return
            
            # Get combined feed list to validate indices
            try:
                with open('config.json', 'r', encoding='utf-8') as f:
                    config = json.load(f)
                default_feeds = config.get('rss_feeds', [])
            except (FileNotFoundError, json.JSONDecodeError) as e:
                print(f"Could not read or parse config.json: {e}")
                default_feeds = []
            
            all_feeds = default_feeds + [{'name': url, 'url': url} for url in custom_feeds]
            max_valid_index = len(all_feeds)
            
            # Validate indices are within range
            if any(idx < 1 or idx > max_valid_index for idx in selected_indices):
                await telegram_sender.send_text_to_telegram(f"شماره‌های انتخاب شده باید بین ۱ تا {max_valid_index} باشند.")
                return
            
            # Identify custom feed indices (offset by default feed count)
            default_count = len(default_feeds)
            custom_indices_to_delete = set()
            for idx in selected_indices:
                if idx > default_count:  # Only custom feeds can be deleted
                    custom_indices_to_delete.add(idx - default_count - 1)
            
            # Remove selected custom feeds
            new_custom_feeds = [
                url for i, url in enumerate(custom_feeds)
                if i not in custom_indices_to_delete
            ]
            
            if len(new_custom_feeds) == len(custom_feeds):
                await telegram_sender.send_text_to_telegram("هیچ منبع شخصی انتخاب نشده یا منابع انتخاب شده پیش‌فرض هستند.")
                return
            
            # Update state with remaining custom feeds
            user_data['custom_feeds'] = new_custom_feeds
            removed_count = len(custom_feeds) - len(new_custom_feeds)
            
            # Show confirmation
            confirmation_text = f"✅ {removed_count} منبع با موفقیت حذف شدند.\n\nلیست منابع به‌روزرسانی شده:"
            await telegram_sender.send_text_to_telegram(confirmation_text)
            
            # Display updated list
            updated_all_feeds = default_feeds + [{'name': url, 'url': url} for url in new_custom_feeds]
            feed_list_text = "\n".join(
                f"{i}. {feed.get('name', feed.get('url', 'Unnamed Feed'))} "
                f"{'(پیش‌فرض)' if feed in default_feeds else '(شخصی)'}"
                for i, feed in enumerate(updated_all_feeds, 1)
            )
            await telegram_sender.send_text_to_telegram(feed_list_text)
            
            # Show management buttons
            action_buttons = [
                [("افزودن فید", "add_feed"), ("حذف فید", "remove_feed")],
                [("نه، عالی است", "feeds_done")]
            ]
            await telegram_sender.send_text_with_buttons("چه کاری انجام دهیم؟", action_buttons)
            
        except Exception as e:
            print(f"Error processing deletion request: {e}")
            await telegram_sender.send_text_to_telegram("خطایی در پردازش درخواست حذف رخ داد.")

    elif input_type == 'message':
        user_text = user_data.get('text', '').strip()
        user_first_name = user_data.get('first_name', 'کاربر')
        
        if not user_text:
            return

        print(f"Received message with text: {user_text}")

        # Route feed deletion requests
        if user_data.get('context') == 'awaiting_feed_deletion':
            user_data['type'] = 'feed_deletion_request'
            return await main()  # Reprocess with new type

        # Set context for next input if we're in feed removal flow
        if user_data.get('last_callback') == 'remove_feed':
            user_data['context'] = 'awaiting_feed_deletion'

        # --- /start handler ---
        if user_text.lower() == '/start':
            # Send personalized welcome
            welcome_message = f"{user_first_name} عزیز، سلام! این ربات اخبار هفتگی شما را تجزیه و تحلیل و ترجمه می‌کند. برای نشان دادن نحوه کار آن، یک مقاله جدید از یک وب‌سایت نمونه برای شما ارسال خواهیم کرد."
            await telegram_sender.send_text_to_telegram(welcome_message)
            print("Sent personalized welcome.")
            
            # Value Demonstration
            print("Starting value demonstration...")
            try:
                recent_articles = fetch_recent_articles("config.json")
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
                confirmation_text = f"فید '{feed_title}' را پیدا کردم. آیا می‌خواهید آن را به لیست اضافه کنید؟"
                confirmation_buttons = [
                    [("بله، اضافه کن", f"confirm_add:{submitted_url}"), ("خیر، لغو", "cancel_add")]
                ]
                await telegram_sender.send_text_with_buttons(confirmation_text, confirmation_buttons)
            else:
                await telegram_sender.send_text_to_telegram("لینک RSS ارسالی معتبر به نظر نمی‌رسد.")
        except Exception as e:
            print(f"Error parsing feed: {e}")
            await telegram_sender.send_text_to_telegram("خطایی در پردازش لینک فید رخ داد.")

    else:
        print(f"Unknown or empty input type received: '{input_type}'")

if __name__ == "__main__":
    asyncio.run(main())