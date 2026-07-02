# modules/settings_manager.py
import json
import os
from modules.ai_processor import LANGUAGE_CONFIGS

SETTINGS_FILE = 'user_prefs.json'

def load_all_settings() -> dict:
    """Load all users settings from file."""
    try:
        with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_all_settings(settings: dict):
    """Save all users settings to file."""
    try:
        with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(settings, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error saving settings: {e}")

def get_user_settings(chat_id: str) -> dict:
    """Get settings for a specific user by chat_id."""
    all_settings = load_all_settings()
    user_key = str(chat_id)
    if user_key not in all_settings:
        # Return default settings for new users
        return {'language': 'en', 'auto_mode': False, 'selected_topics': []}
    return all_settings[user_key]

def save_user_settings(chat_id: str, settings: dict):
    """Save settings for a specific user by chat_id."""
    all_settings = load_all_settings()
    all_settings[str(chat_id)] = settings
    save_all_settings(all_settings)
    print(f"Settings saved for user {chat_id}: {settings}")

def get_language(chat_id: str) -> str:
    """Get current language setting for a user."""
    settings = get_user_settings(chat_id)
    return settings.get('language', 'en')

def set_language(chat_id: str, lang_code: str) -> bool:
    """Set language setting for a user."""
    if lang_code not in LANGUAGE_CONFIGS:
        print(f"Invalid language code: {lang_code}")
        return False
    
    settings = get_user_settings(chat_id)
    settings['language'] = lang_code
    save_user_settings(chat_id, settings)
    return True

def get_menu_text(key: str, chat_id: str = None) -> str:
    """Get menu text in user's language."""
    if chat_id:
        lang = get_language(chat_id)
    else:
        lang = 'en'  # Default to English if no chat_id
    lang_config = LANGUAGE_CONFIGS.get(lang, LANGUAGE_CONFIGS['en'])
    return lang_config['menu'].get(key, key)

def toggle_auto_mode(chat_id: str) -> bool:
    """Toggle auto mode on/off for a user."""
    settings = get_user_settings(chat_id)
    settings['auto_mode'] = not settings.get('auto_mode', False)
    save_user_settings(chat_id, settings)
    return settings['auto_mode']

def is_auto_mode(chat_id: str) -> bool:
    """Check if auto mode is enabled for a user."""
    settings = get_user_settings(chat_id)
    return settings.get('auto_mode', False)
