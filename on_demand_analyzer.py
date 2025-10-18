# on_demand_analyzer.py
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
        print("No topics selected, returning all feeds.")
        return [feed for feed in all_feeds if isinstance(feed, dict)] # Return all valid dicts

    print(f"Filtering feeds based on selected topics: {selected_topics}")
    # Filter logic: include feed if it's custom OR has ANY matching selected tag
    filtered_feeds = [
        feed for feed in all_feeds if isinstance(feed, dict) and (
            'custom' in feed.get('tags', []) or # Always show custom feeds
            any(tag in feed.get('tags', []) for tag in selected_topics) # Show feeds matching selected topics
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
    all_user_feeds = user_data.get('user_feeds', []) # This is the full, unfiltered list from Worker
    selected_topics = user_data.get('selected_topics', [])

    feeds_to_display = all_user_feeds
    if display_filtered:
        feeds_to_display = filter_feeds_by_topics(all_user_feeds, selected_topics)

    feed_list_text = "این لیست منابع شماست"
    if display_filtered and selected_topics:
        feed_list_text += " (بر اساس اولویت‌های انتخابی شما)"
    elif not selected_topics:
         feed_list_text += " (تمام منابع)" # Clarify when showing all feeds
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
    await telegram_sender.send_text_with_buttons("آیا می‌خواهید فیدی اضافه یا حذف کنید؟", action_buttons)


async def handle_feed_submission(submitted_url: str, user_data: dict):
    """Handles the logic for validating and confirming a new feed URL, tolerating minor errors."""
    print(f"Handling URL as a potential feed submission: {submitted_url}")
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        feed = feedparser.parse(submitted_url, request_headers=headers)

        # **MORE TOLERANT VALIDATION:** Check primarily for the existence of entries.
        # Proceed even if feed.bozo is true, as long as we have entries.
        if feed and feed.entries:
            # Try to get title, fallback to URL if missing or empty
            feed_title = feed.feed.get('title', '').strip() or submitted_url
            
            confirmation_text = f"فید '{feed_title}' شناسایی شد"
            if feed.bozo:
                confirmation_text += " (هشدار: ممکن است فید خطای ساختاری جزئی داشته باشد)"
            confirmation_text += ". آیا می‌خواهید آن را اضافه کنید؟"

            confirmation_buttons = [
                [("بله، اضافه کن", f"confirm_add:{submitted_url}"), ("خیر، لغو", "cancel_add")]
            ]
            # Log success even with bozo
            print(f"Feed validation successful (bozo={feed.bozo}) for {submitted_url}. Sending confirmation.")
            await telegram_sender.send_text_with_buttons(confirmation_text, confirmation_buttons)
            return True # Indicates URL was handled and confirmation sent

        else:
            # Provide more detailed failure reason in logs
            if feed.bozo:
                 bozo_reason = feed.get('bozo_exception', 'Unknown reason')
                 # Check if the reason itself indicates a critical failure
                 if isinstance(bozo_reason, Exception) and "not well-formed" in str(bozo_reason):
                     print(f"Validation Critical Failure: Feedparser reported fatal bozo error '{bozo_reason}' for {submitted_url}")
                 else:
                      print(f"Validation Failed: Feedparser reported bozo error '{bozo_reason}' but found NO entries for {submitted_url}")
            elif not feed.entries:
                 print(f"Validation Failed: No entries found in feed {submitted_url}")
            else:
                 # This case should ideally not happen if feed object exists but has no entries
                 print(f"Validation Failed: Unknown feedparser issue (feed object exists but no entries?) for {submitted_url}")
            return False # Indicates this was not a valid feed

    except Exception as e:
        # Catch errors during the parsing itself (e.g., network issues)
        print(f"Exception during feedparser.parse for {submitted_url}: {e}")
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
            # --- /start logic (Remains Correct) ---
            # ... (omitted for brevity) ...
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
            # --- URL Handling (Remains Correct - No feed check here) ---
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
            # --- activate_quick logic (Correct) ---
            user_prefs = { 'selected_topics': [], 'user_feeds': user_data.get('user_feeds', []) }
            memory_manager.save_user_preferences(user_prefs)
            await telegram_sender.send_text_to_telegram("عالی! گزارش‌های شما هر جمعه ساعت ۹ صبح به وقت تهران ارسال خواهد شد.")

        elif callback_data == 'activate_custom' or callback_data == 'display_topics':
             # --- Topic Display Logic (Correct) ---
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
            # --- topics_done logic (Correct) ---
            await telegram_sender.send_text_to_telegram("اولویت‌های شما ثبت شد. حالا منابع خبری مرتبط با انتخاب شما را مدیریت کنید.")
            await handle_display_feeds(user_data, display_filtered=True) # Display filtered list

        elif callback_data == 'add_feed':
            # --- add_feed logic (Correct) ---
            await telegram_sender.send_text_to_telegram("لطفاً لینک فید RSS مورد نظر خود را برای من ارسال کنید.")

        elif callback_data == 'remove_feed':
            # **CORRECTED LOGIC: FILTER BEFORE DISPLAYING REMOVAL OPTIONS**
            all_user_feeds = user_data.get('user_feeds', [])
            selected_topics = user_data.get('selected_topics', [])

            # Filter the list *before* presenting options for removal
            feeds_to_display_for_removal = filter_feeds_by_topics(all_user_feeds, selected_topics)

            if not feeds_to_display_for_removal:
                await telegram_sender.send_text_to_telegram("شما هیچ منبع خبری (مطابق با اولویت‌ها) برای حذف ندارید.")
                await handle_display_feeds(user_data, display_filtered=True) # Show filtered management options
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
            user_feeds = user_data.get('user_feeds', []) # Get full list for name lookup
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
            # --- feeds_done logic (Correct) ---
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
            await handle_display_feeds(user_data, display_filtered=True)
            return

        # Call the validation function (sends confirmation buttons on success)
        was_successful_validation = await handle_feed_submission(submitted_url, user_data)

        if not was_successful_validation:
            # If validation failed, inform user and redisplay options
            # More specific error message based on relaxed validation
            await telegram_sender.send_text_to_telegram("لینک RSS ارسالی معتبر به نظر نمی‌رسد یا هیچ ورودی‌ای در آن یافت نشد. لطفاً لینک دیگری را امتحان کنید.")
            await handle_display_feeds(user_data, display_filtered=True)
        # If successful, handle_feed_submission sent buttons, script exits.

    else:
        print(f"Unknown or unhandled input type: '{input_type}'")


if __name__ == "__main__":
    asyncio.run(main())
