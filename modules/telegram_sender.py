import os
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import TelegramError

def get_chat_id(chat_id=None):
    """Get chat_id from parameter or environment"""
    return chat_id or os.getenv('TELEGRAM_CHAT_ID')

async def send_article_analysis(analysis_dict: dict, buttons: list = None, chat_id: str = None) -> bool:
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    target_chat_id = get_chat_id(chat_id)
    
    if not token:
        print("Critical error: TELEGRAM_BOT_TOKEN environment variable not found.")
        return False
    if not target_chat_id:
        print("Critical error: No chat_id provided for sending message.")
        return False
    
    # Get fields from analysis_dict
    title = analysis_dict.get('title', '')
    comprehensive_summary = analysis_dict.get('comprehensive_summary', '')
    contrarian_view = analysis_dict.get('contrarian_view', '')
    practical_application = analysis_dict.get('practical_application', '')
    glossary = analysis_dict.get('glossary', '')
    link = analysis_dict.get('link', '')
    
    def escape_markdown_v2(text: str) -> str:
        # Escape special characters for MarkdownV2
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

*Comprehensive Summary:*
{comprehensive_summary_esc}

*Contrarian View:*
{contrarian_view_esc}

*Practical Application for You:*
{practical_application_esc}

*Glossary:*
{glossary_esc}

[Source Link]({link})"""
    
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
                chat_id=target_chat_id,
                text=message,
                parse_mode='MarkdownV2',
                reply_markup=reply_markup
            )
            print(f"Article analysis sent to chat_id {target_chat_id} successfully.")
            return True
        except TelegramError as e:
            print(f"Error sending to Telegram: {e}")
            return False

async def send_text_to_telegram(text: str, chat_id: str = None) -> bool:
    """Sends a simple text message to the specified chat."""
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    target_chat_id = get_chat_id(chat_id)
    
    if not token:
        print("Critical error: TELEGRAM_BOT_TOKEN environment variable not found.")
        return False
    if not target_chat_id:
        print("Critical error: No chat_id provided for sending message.")
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
            await bot.send_message(chat_id=target_chat_id, text=escaped_text, parse_mode='MarkdownV2')
            print(f"Text message sent to chat_id {target_chat_id} successfully.")
            return True
        except TelegramError as e:
            print(f"Error sending text to Telegram: {e}")
            return False

async def send_text_with_buttons(text: str, buttons: list, chat_id: str = None) -> bool:
    """Sends a simple text message with an inline keyboard."""
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    target_chat_id = get_chat_id(chat_id)
    
    if not token or not target_chat_id:
        print("Critical error: Telegram credentials not found.")
        return False

    def escape_markdown_v2(text: str) -> str:
        chars_to_escape = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
        for char in chars_to_escape:
            text = text.replace(char, f'\\{char}')
        return text

    escaped_text = escape_markdown_v2(text)

    keyboard = [
        [InlineKeyboardButton(btn_text, callback_data=data) for btn_text, data in row]
        for row in buttons
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    bot = Bot(token=token)
    async with bot:
        try:
            await bot.send_message(chat_id=target_chat_id, text=escaped_text, reply_markup=reply_markup, parse_mode='MarkdownV2')
            print(f"Message with buttons sent to chat_id {target_chat_id} successfully.")
            return True
        except TelegramError as e:
            print(f"Error sending message with buttons: {e}")
            return False