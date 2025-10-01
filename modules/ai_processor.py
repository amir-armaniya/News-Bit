import os
from openai import OpenAI

# --- مدل‌های مورد تایید شما ---
# مدل سریع و کم‌هزینه برای فیلتر اولیه
FAST_MODEL = "qwen/qwen2-7b-instruct:free" 
# مدل قدرتمند برای تحلیل عمیق و استراتژیک
POWERFUL_MODEL = "qwen/qwen2-72b-instruct:free"

def is_article_relevant(article_title: str, article_summary: str) -> bool:
    """Uses a fast and cheap AI call to quickly determine if an article is relevant."""
    api_key = os.getenv('OPENROUTER_API_KEY')
    if not api_key:
        return False
    client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=api_key)
    user_context = ""
    try:
        with open('context.txt', 'r', encoding='utf-8') as f:
            user_context = f.read().strip()
    except FileNotFoundError:
        pass
    
    prompt = f"""
    User's professional interests: "{user_context}"
    Based on the user's interests, is the following article relevant?
    Title: "{article_title}"
    Summary: "{article_summary}"
    Respond with only the single word 'YES' or 'NO'.
    """
    try:
        response = client.chat.completions.create(
            model=FAST_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=5,
            temperature=0.1
        )
        answer = response.choices[0].message.content.strip().upper()
        return "YES" in answer
    except Exception as e:
        print(f"Relevance check failed: {e}")
        return False

def process_article_in_persian(article_title: str, article_summary: str, article_link: str) -> dict | None:
    """Processes a single article using the powerful model for in-depth analysis."""
    api_key = os.getenv('OPENROUTER_API_KEY')
    if not api_key:
        return None
    client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=api_key)
    
    # Implementation remains the same as our last correct version, just ensure POWERFUL_MODEL is used
    user_context = ""
    try:
        with open('context.txt', 'r', encoding='utf-8') as f:
            user_context = f.read().strip()
    except FileNotFoundError:
        pass

    # Step 1: Translation
    combined_text = f"Title: {article_title}\n\nSummary: {article_summary}"
    try:
        response_translation = client.chat.completions.create(
            model=POWERFUL_MODEL,
            messages=[
                {"role": "system", "content": "You are an expert translator. Translate the following English text to Persian. Output only the translated text."},
                {"role": "user", "content": combined_text}
            ]
        )
        translated_text = response_translation.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error during translation: {e}")
        return None

    # Step 2: Strategic Analysis
    system_prompt_analysis = """You are a world-class strategic analyst for a tech founder. Analyze the [NEWS ARTICLE] based on the [USER CONTEXT]. Structure your response in Persian using these exact delimiters:
[خلاصه جامع]
(A detailed paragraph covering the news.)
[دیدگاه مخالف]
(A short paragraph with the hidden risks or a critical contrarian viewpoint.)
[کاربرد عملی برای کاربر]
(Based on the user's context, provide actionable ideas for their FinTech/SaaS projects.)
[واژه‌نامه]
(Explain key terms in the format: '- Term: Explanation')"""
    
    user_message = f"[USER CONTEXT]\n{user_context}\n\n[NEWS ARTICLE]\n{translated_text}"
    
    try:
        response_analysis = client.chat.completions.create(
            model=POWERFUL_MODEL,
            messages=[
                {"role": "system", "content": system_prompt_analysis},
                {"role": "user", "content": user_message}
            ]
        )
        analysis_text = response_analysis.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error during analysis: {e}")
        return None

    # Parsing Logic
    try:
        comprehensive_summary = analysis_text.split('[خلاصه جامع]')[1].split('[دیدگاه مخالف]')[0].strip()
        contrarian_view = analysis_text.split('[دیدگاه مخالف]')[1].split('[کاربرد عملی برای کاربر]')[0].strip()
        practical_application = analysis_text.split('[کاربرد عملی برای کاربر]')[1].split('[واژه‌نامه]')[0].strip()
        glossary = analysis_text.split('[واژه‌نامه]')[1].strip()
    except IndexError:
        print(f"Error parsing analysis response. The model did not follow the format. Response was:\n{analysis_text}")
        return None

    return {
        'title': article_title, 'link': article_link,
        'comprehensive_summary': comprehensive_summary, 'contrarian_view': contrarian_view,
        'practical_application': practical_application, 'glossary': glossary
    }
