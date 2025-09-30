import os
from telegram import Bot
from telegram.error import TelegramError

async def send_article_analysis(analysis_dict: dict) -> bool:
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    
    if not token:
        print("Critical error: TELEGRAM_BOT_TOKEN environment variable not found.")
        return False
    if not chat_id:
        print("Critical error: TELEGRAM_CHAT_ID environment variable not found.")
        return False
    
    # Get fields from analysis_dict
    title = analysis_dict.get('title', '')
    comprehensive_summary = analysis_dict.get('comprehensive_summary', '')
    contrarian_view = analysis_dict.get('contrarian_view', '')
    practical_application = analysis_dict.get('practical_application', '')
    glossary = analysis_dict.get('glossary', '')
    link = analysis_dict.get('link', '')
    
    def escape_markdown_v2(text: str) -> str:
        # Escape special characters for MarkdownV2: _ * [ ] ( ) ~ ` > # + - = | { } . !
        chars_to_escape = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
        for char in chars_to_escape:
            text = text.replace(char, f'\\{char}')
        return text
    
    title_esc = escape_markdown_v2(title)
    comprehensive_summary_esc = escape_markdown_v2(comprehensive_summary)
    contrarian_view_esc = escape_markdown_v2(contrarian_view)
    practical_application_esc = escape_markdown_v2(practical_application)
    glossary_esc = escape_markdown_v2(glossary)
    
    message = f"""*__{title_esc}__*

*خلاصه جامع:*
{comprehensive_summary_esc}

*دیدگاه مخالف:*
{contrarian_view_esc}

*کاربرد عملی برای شما:*
{practical_application_esc}

*واژه‌نامه:*
{glossary_esc}

[لینک منبع]({link})"""
    
    bot = Bot(token=token)
    
    async with bot:
        try:
            await bot.send_message(chat_id=chat_id, text=message, parse_mode='MarkdownV2')
            print("Article analysis sent to Telegram successfully.")
            return True
        except TelegramError as e:
            print(f"Error sending to Telegram: {e}")
            return False
