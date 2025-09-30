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
    
    # Escape special characters for MarkdownV2
    short_summary = analysis_dict.get('short_summary', '')
    title = analysis_dict.get('title', '')
    long_summary = analysis_dict.get('long_summary', '')
    link = analysis_dict.get('link', '')
    
    def escape_markdown(text: str) -> str:
        return text.replace('-', '\\-').replace('.', '\\.').replace('!', '\\!').replace('(', '\\(').replace(')', '\\)')
    
    short_esc = escape_markdown(short_summary)
    title_esc = escape_markdown(title)
    long_esc = escape_markdown(long_summary)
    
    message = f"*_{short_esc}_*\n\n__{title_esc}__\n\n{long_esc}\n\n[Source Link]({link})"
    
    bot = Bot(token=token)
    
    async with bot:
        try:
            await bot.send_message(chat_id=chat_id, text=message, parse_mode='MarkdownV2')
            print("Article analysis sent to Telegram successfully.")
            return True
        except TelegramError as e:
            print(f"Error sending to Telegram: {e}")
            return False
