# on_demand_analyzer.py
import os
import asyncio
import json
import random
import feedparser
from modules import ai_processor, telegram_sender, web_scraper, memory_manager
from modules.content_collector import fetch_sample_articles_from_feeds

# Define topics globally for consistency
ALL_TOPICS = {
    "ai": "Artificial Intelligence", "fintech": "FinTech", "pm": "Product Management",
    "funding": "Funding", "team": "Team Building", "growth": "Growth", "saas": "SaaS"
}

def filter_feeds_by_topics(all_feeds: list, selected_topics: list) -> list:
    """Filters a list of feeds based on selected topics."""
    if not selected_topics:
        print("No topics selected, returning all feeds.")
        return [feed for feed in all_feeds if isinstance(feed, dict)]

    print(f"Filtering feeds based on selected topics: {selected_topics}")
    filtered_feeds = [
        feed for feed in all_feeds if isinstance(feed, dict) and (
            'custom' in feed.get('tags', []) or
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

    feed_list_text = "This is your feed list"
    if display_filtered and selected_topics:
        feed_list_text += " (based on your selected preferences)"
    elif not selected_topics:
         feed_list_text += " (all feeds)"
    feed_list_text += ":\n\n"

    if not feeds_to_display:
        if display_filtered and selected_topics:
             feed_list_text += "No feeds found matching your selected preferences. You can add a feed or change your preferences."
        else:
            feed_list_text += "Your list is currently empty."
    else:
        feed_list_text += "\n".join(
            f"{i}. {feed.get('name', feed.get('url', 'Unnamed Feed'))}"
            for i, feed in enumerate(feeds_to_display, 1) if isinstance(feed, dict)
        )

    await telegram_sender.send_text_to_telegram(feed_list_text)

    action_buttons = [
        [("Add Feed", "add_feed"), ("Remove Feed", "remove_feed")],
        [("No, that's great", "feeds_done")]
    ]
    await telegram_sender.send_text_with_buttons("Would you like to add or remove any feeds?", action_buttons)


async def handle_feed_submission(submitted_url: str, user_data: dict):
    """Handles the logic for validating and confirming a new feed URL, tolerating minor errors."""
    print(f"Handling URL as a potential feed submission: {submitted_url}")
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        feed = feedparser.parse(submitted_url, request_headers=headers)

        if feed and feed.entries:
            feed_title = feed.feed.get('title', '').strip() or submitted_url
            
            confirmation_text = f"Feed '{feed_title}' was identified"
            if feed.bozo:
                confirmation_text += " (warning: the feed may have minor structural errors)"
            confirmation_text += ". Would you like to add it?"

            confirmation_buttons = [
                [("Yes, add it", f"confirm_add:{submitted_url}"), ("No, cancel", "cancel_add")]
            ]
            print(f"Feed validation successful (bozo={feed.bozo}) for {submitted_url}. Sending confirmation.")
            await telegram_sender.send_text_with_buttons(confirmation_text, confirmation_buttons)
            return True

        else:
            if feed.bozo:
                 bozo_reason = feed.get('bozo_exception', 'Unknown reason')
                 if isinstance(bozo_reason, Exception) and "not well-formed" in str(bozo_reason):
                     print(f"Validation Critical Failure: Feedparser reported fatal bozo error '{bozo_reason}' for {submitted_url}")
                 else:
                      print(f"Validation Failed: Feedparser reported bozo error '{bozo_reason}' but found NO entries for {submitted_url}")
            elif not feed.entries:
                 print(f"Validation Failed: No entries found in feed {submitted_url}")
            else:
                 print(f"Validation Failed: Unknown feedparser issue (feed object exists but no entries?) for {submitted_url}")
            return False

    except Exception as e:
        print(f"Exception during feedparser.parse for {submitted_url}: {e}")
        return False

async def main():
    raw_input = os.getenv('ON_DEMAND_INPUT', '{}').strip()
    
    # Extract chatId for multi-user support
    chat_id = None
    try:
        user_data = json.loads(raw_input)
        chat_id = user_data.get('chatId')
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON input: {raw_input}")
        return

    input_type = user_data.get('type')
    print(f"Processing request for chatId: {chat_id}")

    # --- Message Handler ---
    if input_type == 'message':
        user_text = user_data.get('text', '').strip()
        user_first_name = user_data.get('first_name', 'User')

        if not user_text:
            return

        print(f"Received message: {user_text}")

        if user_text.lower() == '/start':
            welcome_message = f"Dear {user_first_name}, welcome! ..."
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
                    await telegram_sender.send_text_to_telegram("Unfortunately, no new articles were found to show a sample at this time.")
                    return
                sample_article = random.choice(sample_articles)
                analysis_dict = ai_processor.process_article_in_english(
                    sample_article['title'], sample_article['summary'], sample_article['link']
                )
                if analysis_dict:
                    decision_buttons = [
                         [("Great, send me weekly", "activate_quick"), ("Great, let's specify sources", "activate_custom")]
                     ]
                    await telegram_sender.send_article_analysis(analysis_dict, buttons=decision_buttons)
                else:
                     await telegram_sender.send_text_to_telegram("An error occurred while analyzing the sample article.")
            except Exception as e:
                 print(f"Error during value demonstration: {e}")
                 await telegram_sender.send_text_to_telegram("An unexpected error occurred while preparing the sample.")


        elif user_text.startswith(('http://', 'https://')):
            print("Treating URL as article for scraping.")
            scraped_content = web_scraper.scrape_url(user_text)
            if scraped_content:
                analysis_dict = ai_processor.process_article_in_english(
                    scraped_content['title'], scraped_content['text'], user_text
                )
                if analysis_dict:
                    memory_manager.save_analysis(analysis_dict)
                    await telegram_sender.send_article_analysis(analysis_dict)
                else:
                    await telegram_sender.send_text_to_telegram("Unfortunately, an error occurred while analyzing the link content.")
            else:
                await telegram_sender.send_text_to_telegram("Unfortunately, I couldn't extract the content from this link.")
        else:
            await telegram_sender.send_text_to_telegram("Your message was received, but I can only analyze links at the moment.")

    # --- Callback Handler ---
    elif input_type == 'callback':
        callback_data = user_data.get('data')
        print(f"Received callback: {callback_data}")

        if callback_data == 'activate_quick':
            user_prefs = { 'selected_topics': [], 'user_feeds': user_data.get('user_feeds', []) }
            memory_manager.save_user_preferences(user_prefs)
            await telegram_sender.send_text_to_telegram("Excellent! Your reports will be sent every Friday at 9 AM (Tehran time).")

        elif callback_data == 'activate_custom' or callback_data == 'display_topics':
             intro_text = "What are your main priorities? (You can select up to three)"
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
             topic_buttons.append([("Done, let's go to feeds", "topics_done")])
             await telegram_sender.send_text_with_buttons(intro_text, topic_buttons)


        elif callback_data == 'topics_done':
            await telegram_sender.send_text_to_telegram("Your preferences have been recorded. Now manage news sources related to your selections.")
            await handle_display_feeds(user_data, display_filtered=True)

        elif callback_data == 'add_feed':
            await telegram_sender.send_text_to_telegram("Please send me the RSS feed URL you'd like to add.")

        elif callback_data == 'remove_feed':
            all_user_feeds = user_data.get('user_feeds', [])
            selected_topics = user_data.get('selected_topics', [])

            feeds_to_display_for_removal = filter_feeds_by_topics(all_user_feeds, selected_topics)

            if not feeds_to_display_for_removal:
                await telegram_sender.send_text_to_telegram("You have no news sources (matching your preferences) to remove.")
                await handle_display_feeds(user_data, display_filtered=True)
            else:
                remove_buttons = [
                    [("❌ " + feed.get('name', feed.get('url')), f"remove_confirm:{feed.get('url')}")]
                    for feed in feeds_to_display_for_removal if isinstance(feed, dict) and feed.get('url')
                ]
                remove_buttons.append([("Cancel and go back", "display_feeds")])
                await telegram_sender.send_text_with_buttons("Which source from the filtered list would you like to remove?", remove_buttons)


        elif callback_data.startswith('remove_confirm:'):
            url = callback_data.split(':', 1)[1]
            feed_name = url
            user_feeds = user_data.get('user_feeds', [])
            for feed in user_feeds:
                 if isinstance(feed, dict) and feed.get('url') == url:
                    feed_name = feed.get('name', url)
                    break
            confirmation_text = f"Are you sure you want to remove the source '{feed_name}'?"
            confirmation_buttons = [
                [("Yes, remove it", f"remove_execute:{url}"), ("No, go back", "display_feeds")]
            ]
            await telegram_sender.send_text_with_buttons(confirmation_text, confirmation_buttons)

        elif callback_data in ['display_feeds', 'cancel_add'] or callback_data.startswith('confirm_add:'):
             await handle_display_feeds(user_data, display_filtered=True)


        elif callback_data == 'feeds_done':
            user_prefs = {
                'selected_topics': user_data.get('selected_topics', []),
                'user_feeds': user_data.get('user_feeds', [])
            }
            memory_manager.save_user_preferences(user_prefs)
            await telegram_sender.send_text_to_telegram("Your information has been saved. An analyzed summary of the latest articles will be available to you every weekend.")

        else:
             print(f"Unhandled callback data: {callback_data}")


    # --- Feed Submission Handler ---
    elif input_type == 'feed_submission':
        submitted_url = user_data.get('url', '')
        print(f"Received feed submission for URL: {submitted_url}")

        if not submitted_url:
            await telegram_sender.send_text_to_telegram("No link was received. Please try again.")
            await handle_display_feeds(user_data, display_filtered=True)
            return

        was_successful_validation = await handle_feed_submission(submitted_url, user_data)

        if not was_successful_validation:
            await telegram_sender.send_text_to_telegram("The RSS link you sent doesn't appear to be valid or no entries were found in it. Please try a different link.")
            await handle_display_feeds(user_data, display_filtered=True)

    else:
        print(f"Unknown or unhandled input type: '{input_type}'")


if __name__ == "__main__":
    asyncio.run(main())