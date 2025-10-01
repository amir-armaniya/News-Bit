import requests
from bs4 import BeautifulSoup
import re

def scrape_url(url: str) -> dict | None:
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract title: prefer <title> or first <h1>
        title_tag = soup.find('title')
        if not title_tag:
            title_tag = soup.find('h1')
        title = title_tag.get_text().strip() if title_tag else re.search(r'<title[^>]*>([^<]+)</title>', response.text, re.IGNORECASE | re.DOTALL).group(1).strip() if re.search(r'<title[^>]*>([^<]+)</title>', response.text, re.IGNORECASE | re.DOTALL) else 'No Title Found'
        
        # Extract main text: collect <p> under <article> or <main>, or all <p>, remove scripts/styles
        for tag in soup(["script", "style", "nav", "header", "footer"]):
            tag.decompose()
        
        article_tag = soup.find('article') or soup.find('main') or soup
        paragraphs = article_tag.find_all('p')
        main_text = '\n'.join([p.get_text().strip() for p in paragraphs if p.get_text().strip()])
        
        if len(main_text) < 100:
            # Fallback to all <p>
            paragraphs = soup.find_all('p')
            main_text = '\n'.join([p.get_text().strip() for p in paragraphs if p.get_text().strip()])
        
        if not main_text:
            return None
            
        # Limit text to reasonable length for AI
        main_text = main_text[:4000]  # Approx 1000 words
        
        return {'title': title, 'text': main_text}
        
    except Exception as e:
        print(f"Error scraping URL {url}: {e}")
        return None
