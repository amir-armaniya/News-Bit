# modules/settings_manager.py
import json
import os
from modules.ai_processor import LANGUAGE_CONFIGS

SETTINGS_FILE = 'user_prefs.json'

def load_settings() -> dict:
    """Load user settings from file."""
    try:
        with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {'language': 'en', 'auto_mode': False, 'selected_topics': []}

def save_settings(settings: dict):
    """Save user settings to file."""
    try:
        with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(settings, f, ensure_ascii=False, indent=2)
        print(f"Settings saved: {settings}")
    except Exception as e:
        print(f"Error saving settings: {e}")

def get_language() -> str:
    """Get current language setting."""
    settings = load_settings()
    return settings.get('language', 'en')

def set_language(lang_code: str) -> bool:
    """Set language setting."""
    if lang_code not in LANGUAGE_CONFIGS:
        print(f"Invalid language code: {lang_code}")
        return False
    
    settings = load_settings()
    settings['language'] = lang_code
    save_settings(settings)
    return True

def get_menu_text(key: str) -> str:
    """Get menu text in current language."""
    lang = get_language()
    lang_config = LANGUAGE_CONFIGS.get(lang, LANGUAGE_CONFIGS['en'])
    return lang_config['menu'].get(key, key)

def toggle_auto_mode() -> bool:
    """Toggle auto mode on/off."""
    settings = load_settings()
    settings['auto_mode'] = not settings.get('auto_mode', False)
    save_settings(settings)
    return settings['auto_mode']

def is_auto_mode() -> bool:
    """Check if auto mode is enabled."""
    settings = load_settings()
    return settings.get('auto_mode', False)
