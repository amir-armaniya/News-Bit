# modules/memory_manager.py
import json

MEMORY_FILE = 'processed_articles.jsonl'

def load_processed_links() -> set:
    """Reads the memory file and returns a set of all processed article links."""
    processed_links = set()
    try:
        with open(MEMORY_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    data = json.loads(line)
                    if 'link' in data:
                        processed_links.add(data['link'])
                except json.JSONDecodeError:
                    continue # Ignore corrupted lines
    except FileNotFoundError:
        pass # The file doesn't exist yet, which is fine
    return processed_links

def save_processed_links(processed_links: set):
    """Saves the set of processed links to the memory file."""
    try:
        # Read existing data
        existing_data = []
        try:
            with open(MEMORY_FILE, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        data = json.loads(line)
                        if 'link' in data:
                            existing_data.append(data)
                    except json.JSONDecodeError:
                        continue
        except FileNotFoundError:
            pass
        
        # Write back only the links that are in the processed_links set
        with open(MEMORY_FILE, 'w', encoding='utf-8') as f:
            for data in existing_data:
                if data['link'] in processed_links:
                    f.write(json.dumps(data, ensure_ascii=False) + '\n')
    except Exception as e:
        print(f"Error saving processed links to memory file: {e}")

def save_analysis(analysis_dict: dict):
    """Appends a new successful analysis to the memory file."""
    try:
        with open(MEMORY_FILE, 'a', encoding='utf-8') as f:
            f.write(json.dumps(analysis_dict, ensure_ascii=False) + '\n')
    except Exception as e:
        print(f"Error saving analysis to memory file: {e}")

def save_user_preferences(prefs: dict):
    """Saves the user's selected topics and final feed list to a JSON file."""
    try:
        # Basic validation
        if not isinstance(prefs.get('selected_topics'), list):
            prefs['selected_topics'] = []
        if not isinstance(prefs.get('user_feeds'), list):
            prefs['user_feeds'] = []
            
        with open('user_prefs.json', 'w', encoding='utf-8') as f:
            json.dump(prefs, f, ensure_ascii=False, indent=2)
        print(f"Successfully saved user preferences: {prefs}")
    except Exception as e:
        print(f"CRITICAL ERROR saving user preferences: {e}")