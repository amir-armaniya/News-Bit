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

def save_analysis(analysis_dict: dict):
    """Appends a new successful analysis to the memory file."""
    try:
        with open(MEMORY_FILE, 'a', encoding='utf-8') as f:
            f.write(json.dumps(analysis_dict, ensure_ascii=False) + '\n')
    except Exception as e:
        print(f"Error saving analysis to memory file: {e}")
