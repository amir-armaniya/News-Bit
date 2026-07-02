import os
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import TelegramError
from modules.ai_processor import LANGUAGE_CONFIGS
from modules import settings_manager

def get_chat_id(chat_id=None):
    """Get chat_id from parameter or environment"""
    return chat_id or os.getenv('TELEGRAM_CHAT_ID')

def get_menu_text(key: str, language: str = 'en') -> str:
    """Get localized menu text."""
    lang_config = LANGUAGE_CONFIGS.get(language, LANGUAGE_CONFIGS['en'])
    return lang_config['menu'].get(key, key)

async def send_article_analysis(analysis_dict: dict, buttons: list = None, chat_id: str = None, language: str = 'en') -> bool:
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
    
    # Translate content if needed
    from modules.ai_processor import translate_to_language
    if language != 'en':
        title = translate_to_language(title, language)
        comprehensive_summary = translate_to_language(comprehensive_summary, language)
        contrarian_view = translate_to_language(contrarian_view, language)
        practical_application = translate_to_language(practical_application, language)
        glossary = translate_to_language(glossary, language)
    
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
    
    # Get translated section headers
    header_summary = get_menu_text('summary', language) if language != 'en' else 'Comprehensive Summary'
    header_contrarian = get_menu_text('contrarian', language) if language != 'en' else 'Contrarian View'
    header_practical = get_menu_text('practical', language) if language != 'en' else 'Practical Application for You'
    header_glossary = get_menu_text('glossary', language) if language != 'en' else 'Glossary'
    
    message = f"""*__{title_esc}__*

*{header_summary}:*
{comprehensive_summary_esc}

*{header_contrarian}:*
{contrarian_view_esc}

*{header_practical}:*
{practical_application_esc}

*{header_glossary}:*
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

async def send_settings_menu(chat_id: str = None) -> bool:
    """Sends the settings menu with language and auto mode options."""
    current_lang = settings_manager.get_language()
    auto_mode = settings_manager.is_auto_mode()
    
    # Get menu text in current language
    settings_text = settings_manager.get_menu_text('settings')
    language_text = settings_manager.get_menu_text('language')
    auto_mode_text = settings_manager.get_menu_text('auto_mode')
    
    # Auto mode status
    auto_status = "ON" if auto_mode else "OFF"
    if current_lang == 'fa':
        auto_status = "فعال" if auto_mode else "غیرفعال"
    elif current_lang == 'ar':
        auto_status = "مفعّل" if auto_mode else "معطّل"
    
    text = f"""*{settings_text}*

*{language_text}:* {LANGUAGE_CONFIGS[current_lang]['name']}
*{auto_mode_text}:* {auto_status}

Select language:"""
    
    # Language buttons
    buttons = [
        [
            InlineKeyboardButton("فارسی", callback_data="lang_fa"),
            InlineKeyboardButton("العربية", callback_data="lang_ar"),
            InlineKeyboardButton("English", callback_data="lang_en")
        ],
        [
            InlineKeyboardButton(f"{auto_mode_text}: {auto_status}", callback_data="toggle_auto")
        ]
    ]
    
    return await send_text_with_buttons(text, buttons, chat_id)