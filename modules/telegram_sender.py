import os
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import TelegramError

async def send_article_analysis(analysis_dict: dict, buttons: list = None) -> bool:
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
    
    # --- NEW LOGIC FOR BUTTONS ---
    reply_markup = None
    if buttons:
        keyboard = [
            [InlineKeyboardButton(text, callback_data=data) for text, data in row]
            for row in buttons
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
    
    bot = Bot(token=token)
    
    async with bot:
        try:
            await bot.send_message(
                chat_id=chat_id,
                text=message,
                parse_mode='MarkdownV2',
                reply_markup=reply_markup
            )
            print("Article analysis sent to Telegram successfully.")
            return True
        except TelegramError as e:
            print(f"Error sending to Telegram: {e}")
            return False
async def send_audio_file(filepath: str) -> bool:
    """Sends an audio file to the specified chat."""
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')

    if not token or not chat_id:
        print("Critical error: Telegram credentials not found for sending audio.")
        return False

    bot = Bot(token=token)
    async with bot:
        try:
            with open(filepath, 'rb') as audio_file:
                await bot.send_audio(chat_id=chat_id, audio=audio_file)
            print("Podcast sent to Telegram successfully.")
            return True
        except TelegramError as e:
            print(f"Error sending audio to Telegram: {e}")
            return False
        except FileNotFoundError:
            print(f"Error: Audio file not found at {filepath}")
            return False


async def send_text_to_telegram(text: str) -> bool:
    """Sends a simple text message to the specified chat."""
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    
    if not token:
        print("Critical error: TELEGRAM_BOT_TOKEN environment variable not found.")
        return False
    if not chat_id:
        print("Critical error: TELEGRAM_CHAT_ID environment variable not found.")
        return False
    
    def escape_markdown_v2(text: str) -> str:
        chars_to_escape = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
        for char in chars_to_escape:
            text = text.replace(char, f'\\{char}')
        return text
    
    escaped_text = escape_markdown_v2(text)
    
    bot = Bot(token=token)
    
    async with bot:
        try:
            await bot.send_message(chat_id=chat_id, text=escaped_text, parse_mode='MarkdownV2')
            print("Text message sent to Telegram successfully.")
            return True
        except TelegramError as e:
            print(f"Error sending text to Telegram: {e}")
            return False
