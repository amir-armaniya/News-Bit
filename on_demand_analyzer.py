# on_demand_analyzer.py (Final Version with Syntax Fix & Preference Saving)
import os
import asyncio
import json
import random
import feedparser
from modules import ai_processor, telegram_sender, web_scraper, memory_manager
from modules.content_collector import fetch_sample_articles_from_feeds # Correct import

# Define topics globally for consistency
ALL_TOPICS = {
    "ai": "هوش مصنوعی", "fintech": "فناوری مالی", "pm": "مدیریت محصول",
    "funding": "جمع‌آوری کمک‌های مالی", "team": "تیم‌سازی", "growth": "رشد", "saas": "SaaS"
    # Add other relevant tags used in DEFAULT_FEEDS if necessary
}

async def handle_display_feeds(user_data: dict):
    """Displays the user's current feed list and management options."""
    print("handle_display_feeds triggered.")
    user_feeds = user_data.get('user_feeds', []) # This list might already be filtered

    feed_list_text = "این لیست منابع شماست:\n\n"
    if not user_feeds:
        feed_list_text += "لیست شما (بر اساس اولویت‌ها) در حال حاضر خالی است."
    else:
        feed_list_text += "\n".join(
            # Ensure feed is a dict before accessing keys
            f"{i}. {feed.get('name', feed.get('url', 'فید بدون نام'))}"
            for i, feed in enumerate(user_feeds, 1) if isinstance(feed, dict)
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
                    # Do NOT save sample analysis
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
            # Intelligent URL Handling
            is_feed_submission_attempt = await handle_feed_submission(user_text, user_data)

            if not is_feed_submission_attempt:
                print("URL not a valid feed or submission failed. Falling back to web scraper.")
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
                    await telegram_sender.send_text_to_telegram("متاسفانه نتوانستم محتوای این لینک را استخراج کنم. ممکن است لینک RSS نامعتبر یا صفحه وب خالی باشد.")
        else:
            await telegram_sender.send_text_to_telegram("پیام شما دریافت شد، اما در حال حاضر فقط می‌توانم لینک‌ها را تحلیل کنم.")

    # --- Callback Handler ---
    elif input_type == 'callback':
        callback_data = user_data.get('data')
        print(f"Received callback: {callback_data}")

        if callback_data == 'activate_quick':
            # Finalize and save preferences (no topics selected, use default/all feeds from worker)
            user_prefs = {
                'selected_topics': [],
                'user_feeds': user_data.get('user_feeds', []) # Worker sends current list
            }
            memory_manager.save_user_preferences(user_prefs)
            await telegram_sender.send_text_to_telegram("عالی! گزارش‌های شما هر جمعه ساعت ۹ صبح به وقت تهران ارسال خواهد شد.")

        elif callback_data == 'activate_custom' or callback_data == 'display_topics':
            intro_text = "اولویت‌های اصلی شما چیست؟ (می‌توانید تا سه مورد را انتخاب کنید)"
            selected_topics = user_data.get('selected_topics', [])

            topic_buttons = []
            row = []
            # Use globally defined ALL_TOPICS
            for topic_id, topic_name in sorted(ALL_TOPICS.items()):
                display_name = f"✅ {topic_name}" if topic_id in selected_topics else topic_name
                row.append((display_name, f"topic_{topic_id}"))
                # Adjust button layout (e.g., 2 per row)
                if len(row) >= 2:
                    topic_buttons.append(row)
                    row = []
            if row: # Add remaining buttons if any
                topic_buttons.append(row)

            topic_buttons.append([("تمام شد، بیایید به فیدها برویم", "topics_done")])

            await telegram_sender.send_text_with_buttons(intro_text, topic_buttons)

        elif callback_data == 'topics_done':
            await telegram_sender.send_text_to_telegram("اولویت‌های شما ثبت شد. حالا منابع خبری مرتبط با انتخاب شما را مدیریت کنید.")

            selected_topics = user_data.get('selected_topics', [])
            all_user_feeds = user_data.get('user_feeds', [])

            final_feeds_to_display = all_user_feeds # Default to all if no topics selected

            if selected_topics:
                print(f"Filtering feeds based on selected topics: {selected_topics}")
                # Filter logic: include feed if it has NO tags OR includes 'custom' OR has ANY matching selected tag
                filtered_feeds = [
                    feed for feed in all_user_feeds if isinstance(feed, dict) and (
                        not feed.get('tags') or
                        'custom' in feed.get('tags', []) or
                        any(tag in feed.get('tags', []) for tag in selected_topics)
                    )
                ]
                final_feeds_to_display = filtered_feeds
                print(f"Filtered list size: {len(final_feeds_to_display)}")


            # Create a new dictionary to pass only the relevant feeds for display
            display_data = user_data.copy()
            display_data['user_feeds'] = final_feeds_to_display
            await handle_display_feeds(display_data)

        elif callback_data == 'add_feed':
            await telegram_sender.send_text_to_telegram("لطفاً لینک فید RSS مورد نظر خود را برای من ارسال کنید.")

        elif callback_data == 'remove_feed':
            # IMPORTANT: The list shown for removal should be the UNFILTERED list from the worker state
            user_feeds_unfiltered = user_data.get('user_feeds', [])
            if not user_feeds_unfiltered:
                await telegram_sender.send_text_to_telegram("شما هیچ منبع خبری برای حذف ندارید.")
                # Show management options again, passing unfiltered list
                await handle_display_feeds({'user_feeds': user_feeds_unfiltered})
            else:
                remove_buttons = [
                    # Ensure feed is a dict before accessing keys
                    [("❌ " + feed.get('name', feed.get('url')), f"remove_confirm:{feed.get('url')}")]
                    for feed in user_feeds_unfiltered if isinstance(feed, dict) and feed.get('url')
                ]
                remove_buttons.append([("لغو و بازگشت", "display_feeds")])
                await telegram_sender.send_text_with_buttons("کدام منبع را می‌خواهید حذف کنید؟", remove_buttons)


        elif callback_data.startswith('remove_confirm:'):
            url = callback_data.split(':', 1)[1]
            feed_name = url
            user_feeds = user_data.get('user_feeds', [])
            # Find name from the potentially unfiltered list passed by worker
            for feed in user_feeds:
                 if isinstance(feed, dict) and feed.get('url') == url:
                    feed_name = feed.get('name', url)
                    break

            confirmation_text = f"آیا مطمئنید که می‌خواهید منبع '{feed_name}' را حذف کنید؟"
            confirmation_buttons = [
                [("بله، حذف کن", f"remove_execute:{url}"), ("خیر، بازگشت", "display_feeds")]
            ]
            await telegram_sender.send_text_with_buttons(confirmation_text, confirmation_buttons)

        # Handling display_feeds and cancel_add together after other specific actions
        elif callback_data in ['display_feeds', 'cancel_add'] or callback_data.startswith('confirm_add:'):
             # When redisplaying, show the potentially filtered list based on current topics
            selected_topics = user_data.get('selected_topics', [])
            all_user_feeds = user_data.get('user_feeds', [])
            final_feeds_to_display = all_user_feeds
            if selected_topics:
                 filtered_feeds = [
                    feed for feed in all_user_feeds if isinstance(feed, dict) and (
                        not feed.get('tags') or
                        'custom' in feed.get('tags', []) or
                        any(tag in feed.get('tags', []) for tag in selected_topics)
                    )
                ]
                 final_feeds_to_display = filtered_feeds

            display_data = user_data.copy()
            display_data['user_feeds'] = final_feeds_to_display
            await handle_display_feeds(display_data)


        elif callback_data == 'feeds_done':
            # Finalize and save preferences (selected topics and final unfiltered feed list from worker)
            user_prefs = {
                'selected_topics': user_data.get('selected_topics', []),
                'user_feeds': user_data.get('user_feeds', []) # Save the full list managed by worker
            }
            memory_manager.save_user_preferences(user_prefs)
            await telegram_sender.send_text_to_telegram("اطلاعات شما ذخیره شد. خلاصه‌ای تحلیل‌شده از آخرین مقالات هر آخر هفته در دسترس شما خواهد بود.")

        else:
             print(f"Unhandled callback data: {callback_data}")


    # Feed submission type is now handled within the 'message' handler logic
    elif input_type == 'feed_submission':
        print("Note: 'feed_submission' type is handled by 'message' type now.")
        pass

    else:
        print(f"Unknown or unhandled input type: '{input_type}'")


if __name__ == "__main__":
    asyncio.run(main())