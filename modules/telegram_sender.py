import os
import asyncio
import telegram
from telegram.error import TelegramError

async def send_summary_to_telegram(text_message: str, audio_filepath: str) -> bool:
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    
    if not token:
        print("Critical error: TELEGRAM_BOT_TOKEN environment variable not found.")
        return False
    if not chat_id:
        print("Critical error: TELEGRAM_CHAT_ID environment variable not found.")
        return False
    
    bot = telegram.Bot(token=token)
    
    async with bot:
        try:
            await bot.send_message(chat_id=chat_id, text=text_message)
            await bot.send_audio(chat_id=chat_id, audio=open(audio_filepath, 'rb'))
            print("Summary sent to Telegram successfully.")
            return True
        except TelegramError as e:
            print(f"Error sending to Telegram: {e}")
            return False
