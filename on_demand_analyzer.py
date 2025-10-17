# on_demand_analyzer.py (Final Corrected Version)
import os
import asyncio
import json
import random
import feedparser
from modules import ai_processor, telegram_sender, web_scraper, memory_manager
from modules.content_collector import fetch_sample_articles_from_feeds

# Helper functions (handle_display_feeds, handle_feed_submission) are correct and omitted for brevity...

async def main():
    raw_input = os.getenv('ON_DEMAND_INPUT', '{}').strip()
    try:
        user_data = json.loads(raw_input)
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON input: {raw_input}")
        return

    input_type = user_data.get('type')

    # Message handler is correct and omitted for brevity...

    elif input_type == 'callback':
        callback_data = user_data.get('data')
        print(f"Received callback: {callback_data}")

        if callback_data == 'activate_quick':
            # Finalize and save preferences
            user_prefs = { 'selected_topics': [], 'user_feeds': user_data.get('user_feeds', []) }
            memory_manager.save_user_preferences(user_prefs)
            await telegram_sender.send_text_to_telegram("عالی! گزارش‌های شما هر جمعه ساعت ۹ صبح به وقت تهران ارسال خواهد شد.")
    
        elif callback_data == 'activate_custom' or callback_data == 'display_topics':
            intro_text = "اولویت‌های اصلی شما چیست؟ (می‌توانید تا سه مورد را انتخاب کنید)"
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
            
            final_feeds_to_display = all_user_feeds # Default to all
            if selected_topics:
                print(f"Filtering feeds based on: {selected_topics}")
                # A custom feed with no tags should still be shown, or filter them out? Let's show them.
                filtered_feeds = [
                    feed for feed in all_user_feeds 
                    if not feed.get('tags') or 'custom' in feed.get('tags', []) or any(tag in feed.get('tags', []) for tag in selected_topics)
                ]
                final_feeds_to_display = filtered_feeds
            
            display_data = user_data.copy() # Avoid modifying the original dict
            display_data['user_feeds'] = final_feeds_to_display
            await handle_display_feeds(display_data)

        elif callback_data == 'feeds_done':
            # Finalize and save preferences
            user_prefs = {
                'selected_topics': user_data.get('selected_topics', []),
                'user_feeds': user_data.get('user_feeds', [])
            }
            memory_manager.save_user_preferences(user_prefs)
            await telegram_sender.send_text_to_telegram("اطلاعات شما ذخیره شد. خلاصه‌ای تحلیل‌شده از آخرین مقالات هر آخر هفته در دسترس شما خواهد بود.")
        
        # Other handlers (add_feed, remove_feed etc.) are correct and omitted for brevity

# Main execution guard
if __name__ == "__main__":
    asyncio.run(main())