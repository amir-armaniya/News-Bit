import os
from openai import OpenAI

# مدل سریع و کم‌هزینه برای فیلتر اولیه
FAST_MODEL = "qwen/qwen3-14b:free" 
# مدل قدرتمند برای تحلیل عمیق و استراتژیک
POWERFUL_MODEL = "qwen/qwen3-235b-a22b:free"

def is_article_relevant(article_title: str, article_summary: str) -> bool:
    # This function remains the same as our last correct version.
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
    api_key = os.getenv('OPENROUTER_API_KEY')
    if not api_key:
        return None
    client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=api_key)
    
    user_context = ""
    try:
        with open('context.txt', 'r', encoding='utf-8') as f:
            user_context = f.read().strip()
    except FileNotFoundError:
        pass

    # Step 1: Translation (no change)
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

    # --- CRITICAL UPGRADE: Chain of Thought Prompt ---
    system_prompt_analysis = """You are a world-class strategic analyst, acting as a personal advisor to a tech founder. Your task is to perform a multi-step analysis of the provided [NEWS ARTICLE] based on the [USER CONTEXT].

Your thought process must be as follows:
1.  **Summarize:** First, identify the core message and key data points of the article.
2.  **Critique:** Second, think about the hidden risks, challenges, or contrarian viewpoints.
3.  **Apply:** Third, connect the article's insights directly to the user's goals (SaaS, FinTech, product management, funding).
4.  **Define:** Fourth, identify any important technical or business jargon that needs explanation.
5.  **Synthesize:** Finally, combine all of your thoughts into a structured, well-written report in Persian using the specified delimiters.

Your entire final output MUST be structured using these exact delimiters:
[خلاصه جامع]
(A detailed paragraph based on your summary.)
[دیدگاه مخالف]
(A short paragraph based on your critique.)
[کاربرد عملی برای کاربر]
(2-3 actionable ideas based on your application step.)
[واژه‌نامه]
(Explain up to 5 key terms based on your definition step, in the format: '- Term: Explanation')"""
    
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

    # Parsing Logic (no change)
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
