# on_demand_analyzer.py (Corrected Add/Remove Logic)
import os
import asyncio
import json
import random
import feedparser
from modules import ai_processor, telegram_sender, web_scraper, memory_manager
from modules.content_collector import fetch_sample_articles_from_feeds # Keep correct import

# Define topics globally for consistency
ALL_TOPICS = {
    "ai": "هوش مصنوعی", "fintech": "فناوری مالی", "pm": "مدیریت محصول",
    "funding": "جمع‌آوری کمک‌های مالی", "team": "تیم‌سازی", "growth": "رشد", "saas": "SaaS"
}

def filter_feeds_by_topics(all_feeds: list, selected_topics: list) -> list:
    """Filters a list of feeds based on selected topics."""
    if not selected_topics:
        return all_feeds # Return all if no topics are selected

    print(f"Filtering feeds based on selected topics: {selected_topics}")
    # Filter logic: include feed if it has NO tags OR includes 'custom' OR has ANY matching selected tag
    filtered_feeds = [
        feed for feed in all_feeds if isinstance(feed, dict) and (
            not feed.get('tags') or # Should feeds without tags always be shown? Maybe not. Let's reconsider.
            'custom' in feed.get('tags', []) or # Always show custom feeds
            any(tag in feed.get('tags', []) for tag in selected_topics)
        )
    ]
    print(f"Original list size: {len(all_feeds)}, Filtered list size: {len(filtered_feeds)}")
    return filtered_feeds


async def handle_display_feeds(user_data: dict, display_filtered: bool = True):
    """
    Displays the user's feed list and management options.
    If display_filtered is True, it filters based on selected_topics.
    """
    print(f"handle_display_feeds triggered. Display filtered: {display_filtered}")
    all_user_feeds = user_data.get('user_feeds', [])
    selected_topics = user_data.get('selected_topics', [])

    feeds_to_display = all_user_feeds
    if display_filtered:
        feeds_to_display = filter_feeds_by_topics(all_user_feeds, selected_topics)

    feed_list_text = "این لیست منابع شماست"
    if display_filtered and selected_topics:
        feed_list_text += " (بر اساس اولویت‌های انتخابی شما)"
    feed_list_text += ":\n\n"


    if not feeds_to_display:
        if display_filtered and selected_topics:
             feed_list_text += "هیچ منبعی مطابق با اولویت‌های انتخابی شما یافت نشد. می‌توانید فید اضافه کنید یا اولویت‌ها را تغییر دهید."
        else:
            feed_list_text += "لیست شما در حال حاضر خالی است."
    else:
        feed_list_text += "\n".join(
            f"{i}. {feed.get('name', feed.get('url', 'فید بدون نام'))}"
            for i, feed in enumerate(feeds_to_display, 1) if isinstance(feed, dict)
        )

    await telegram_sender.send_text_to_telegram(feed_list_text)

    action_buttons = [
        [("افزودن فید", "add_feed"), ("حذف فید", "remove_feed")],
        [("نه، عالی است", "feeds_done")]
    ]
    # Optionally add a button to view all feeds if currently filtered? Maybe later.
    await telegram_sender.send_text_with_buttons("آیا می‌خواهید فیدی اضافه یا حذف کنید؟", action_buttons)


async def handle_feed_submission(submitted_url: str, user_data: dict):
    """Handles the logic for validating and confirming a new feed URL."""
    print(f"Handling URL as a potential feed submission: {submitted_url}")
    try:
        feed = feedparser.parse(submitted_url)
        # Check for both feed title and entries
        if feed.feed and feed.feed.get('title') and feed.entries:
            feed_title = feed.feed.get('title', 'فید بدون عنوان')
            confirmation_text = f"فید '{feed_title}' را پیدا کردم. آیا می‌خواهید آن را به لیست اضافه کنید؟"

            # Short callback data: Only the URL
            confirmation_buttons = [
                [("بله، اضافه کن", f"confirm_add:{submitted_url}"), ("خیر، لغو", "cancel_add")]
            ]
            await telegram_sender.send_text_with_buttons(confirmation_text, confirmation_buttons)
            return True # Indicates URL was handled as a feed and confirmation sent
        else:
            print("Validation failed: Feed has no title or no entries.")
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
            # --- /start logic (Correct, no changes needed) ---
            welcome_message = f"{user_first_name} عزیز، سلام! ..." # Omitted for brevity
            await telegram_sender.send_text_to_telegram(welcome_message)
            try:
                # Fetch sample correctly
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
            # --- URL Handling (Correct, no changes needed) ---
            # It should NOT try feed submission here anymore. Worker handles state.
            print("Treating URL as article for scraping.")
            scraped_content = web_scraper.scrape_url(user_text)
            if scraped_content:
                analysis_dict = ai_processor.process_article_in_persian(
                    scraped_content['title'], scraped_content['text'], user_text
                )
                if analysis_dict:
                    memory_manager.save_analysis(analysis_dict) # Save on-demand analysis
                    await telegram_sender.send_article_analysis(analysis_dict)
                else:
                    await telegram_sender.send_text_to_telegram("متاسفانه در تحلیل محتوای لینک خطایی رخ داد.")
            else:
                await telegram_sender.send_text_to_telegram("متاسفانه نتوانستم محتوای این لینک را استخراج کنم.")
        else:
            await telegram_sender.send_text_to_telegram("پیام شما دریافت شد، اما در حال حاضر فقط می‌توانم لینک‌ها را تحلیل کنم.")

    # --- Callback Handler ---
    elif input_type == 'callback':
        callback_data = user_data.get('data')
        print(f"Received callback: {callback_data}")

        if callback_data == 'activate_quick':
            # --- activate_quick logic (Correct, save prefs) ---
            user_prefs = { 'selected_topics': [], 'user_feeds': user_data.get('user_feeds', []) }
            memory_manager.save_user_preferences(user_prefs)
            await telegram_sender.send_text_to_telegram("عالی! گزارش‌های شما هر جمعه ساعت ۹ صبح به وقت تهران ارسال خواهد شد.")

        elif callback_data == 'activate_custom' or callback_data == 'display_topics':
             # --- Topic Display Logic (Correct, no changes needed) ---
             intro_text = "اولویت‌های اصلی شما چیست؟ (می‌توانید تا سه مورد را انتخاب کنید)"
             selected_topics = user_data.get('selected_topics', [])
             topic_buttons = []
             row = []
             for topic_id, topic_name in sorted(ALL_TOPICS.items()):
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
            # --- topics_done logic (Correct, filter before display) ---
            await telegram_sender.send_text_to_telegram("اولویت‌های شما ثبت شد. حالا منابع خبری مرتبط با انتخاب شما را مدیریت کنید.")
            # Display feeds, filtered by topics selected
            await handle_display_feeds(user_data, display_filtered=True)

        elif callback_data == 'add_feed':
            # --- add_feed logic (Correct) ---
            await telegram_sender.send_text_to_telegram("لطفاً لینک فید RSS مورد نظر خود را برای من ارسال کنید.")

        elif callback_data == 'remove_feed':
            # **CORRECTED LOGIC FOR REMOVE FEED**
            all_user_feeds = user_data.get('user_feeds', [])
            selected_topics = user_data.get('selected_topics', [])

            # Filter the list *before* presenting options for removal
            feeds_to_display_for_removal = filter_feeds_by_topics(all_user_feeds, selected_topics)

            if not feeds_to_display_for_removal:
                await telegram_sender.send_text_to_telegram("شما هیچ منبع خبری (مطابق با اولویت‌ها) برای حذف ندارید.")
                # Show management options again, displaying potentially filtered list
                await handle_display_feeds(user_data, display_filtered=True)
            else:
                remove_buttons = [
                    [("❌ " + feed.get('name', feed.get('url')), f"remove_confirm:{feed.get('url')}")]
                    for feed in feeds_to_display_for_removal if isinstance(feed, dict) and feed.get('url')
                ]
                remove_buttons.append([("لغو و بازگشت", "display_feeds")])
                await telegram_sender.send_text_with_buttons("کدام منبع را از لیست فیلتر شده می‌خواهید حذف کنید؟", remove_buttons)


        elif callback_data.startswith('remove_confirm:'):
            # --- remove_confirm logic (Correct) ---
            url = callback_data.split(':', 1)[1]
            feed_name = url
            user_feeds = user_data.get('user_feeds', [])
            for feed in user_feeds:
                 if isinstance(feed, dict) and feed.get('url') == url:
                    feed_name = feed.get('name', url)
                    break
            confirmation_text = f"آیا مطمئنید که می‌خواهید منبع '{feed_name}' را حذف کنید؟"
            confirmation_buttons = [
                [("بله، حذف کن", f"remove_execute:{url}"), ("خیر، بازگشت", "display_feeds")]
            ]
            await telegram_sender.send_text_with_buttons(confirmation_text, confirmation_buttons)

        # Handle redisplay after confirmation or cancellation
        elif callback_data in ['display_feeds', 'cancel_add'] or callback_data.startswith('confirm_add:'):
             # When redisplaying, show the list filtered by current topics
            await handle_display_feeds(user_data, display_filtered=True)


        elif callback_data == 'feeds_done':
            # --- feeds_done logic (Correct, save prefs) ---
            user_prefs = {
                'selected_topics': user_data.get('selected_topics', []),
                'user_feeds': user_data.get('user_feeds', []) # Save the full, unfiltered list
            }
            memory_manager.save_user_preferences(user_prefs)
            await telegram_sender.send_text_to_telegram("اطلاعات شما ذخیره شد. خلاصه‌ای تحلیل‌شده از آخرین مقالات هر آخر هفته در دسترس شما خواهد بود.")

        else:
             print(f"Unhandled callback data: {callback_data}")


    # --- Feed Submission Handler (CORRECTED) ---
    elif input_type == 'feed_submission':
        submitted_url = user_data.get('url', '')
        print(f"Received feed submission for URL: {submitted_url}")

        if not submitted_url:
            await telegram_sender.send_text_to_telegram("هیچ لینکی دریافت نشد. لطفاً دوباره تلاش کنید.")
            # Redisplay feed management options, filtered
            await handle_display_feeds(user_data, display_filtered=True)
            return

        # Call the validation function (which sends confirmation buttons on success)
        was_successful = await handle_feed_submission(submitted_url, user_data)

        if not was_successful:
            # If validation failed, inform user and redisplay options
            await telegram_sender.send_text_to_telegram("لینک RSS ارسالی معتبر به نظر نمی‌رسد یا عنوان ندارد. لطفاً لینک دیگری را امتحان کنید.")
            await handle_display_feeds(user_data, display_filtered=True)
        # If successful, handle_feed_submission sent buttons, so script exits here.

    else:
        print(f"Unknown or unhandled input type: '{input_type}'")


if __name__ == "__main__":
    asyncio.run(main())
