import os
from openai import OpenAI

def process_article_in_persian(article_title: str, article_summary: str, article_link: str) -> dict | None:
    # Use the more reliable model designed for instruction following
    RELIABLE_MODEL = "qwen/qwen3-235b-a22b:free"
    
    api_key = os.getenv('OPENROUTER_API_KEY')
    if not api_key:
        print("Error: OPENROUTER_API_KEY environment variable not found.")
        return None

    client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=api_key)

    # Step 1: Read user context
    user_context = ""
    try:
        with open('context.txt', 'r', encoding='utf-8') as f:
            user_context = f.read().strip()
    except FileNotFoundError:
        print("Warning: context.txt not found. Proceeding without user context.")
        user_context = ""

    # Step 2: Translation
    combined_text = f"Title: {article_title}\n\nSummary: {article_summary}"
    try:
        response_translation = client.chat.completions.create(
            model=RELIABLE_MODEL,
            messages=[
                {"role": "system", "content": "You are an expert translator. Translate the following English text to Persian. Output only the translated text."},
                {"role": "user", "content": combined_text}
            ],
            temperature=0.3,
            max_tokens=1500
        )
        translated_text = response_translation.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error during translation API call: {e}")
        return None

    # Step 3: Strategic Analysis
    system_prompt_analysis = """You are a world-class strategic analyst. Analyze the [NEWS ARTICLE] based on the [USER CONTEXT]. Structure your entire response in Persian using these exact delimiters:
[خلاصه جامع]
(A detailed paragraph covering all aspects of the news.)
[دیدگاه مخالف]
(A short paragraph with the hidden risks or a critical contrarian viewpoint.)
[کاربرد عملی برای کاربر]
(Based on the user's context, provide 2-3 actionable ideas for their FinTech/SaaS projects.)
[واژه‌نامه]
(Explain up to 3 key terms from the article in the format: '- Term: Explanation')"""
    
    user_message = f"[USER CONTEXT]\n{user_context}\n\n[NEWS ARTICLE]\n{translated_text}"
    
    try:
        response_analysis = client.chat.completions.create(
            model=RELIABLE_MODEL,
            messages=[
                {"role": "system", "content": system_prompt_analysis},
                {"role": "user", "content": user_message}
            ],
            temperature=0.5,
            max_tokens=2000
        )
        analysis_text = response_analysis.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error during analysis API call: {e}")
        return None

    # Robust Parsing Logic
    try:
        comprehensive_summary = analysis_text.split('[خلاصه جامع]')[1].split('[دیدگاه مخالف]')[0].strip()
        contrarian_view = analysis_text.split('[دیدگاه مخالف]')[1].split('[کاربرد عملی برای کاربر]')[0].strip()
        practical_application = analysis_text.split('[کاربرد عملی برای کاربر]')[1].split('[واژه‌نامه]')[0].strip()
        glossary = analysis_text.split('[واژه‌نامه]')[1].strip()

        if not all([comprehensive_summary, contrarian_view, practical_application, glossary]):
            raise ValueError("One or more sections are missing after parsing.")

    except (IndexError, ValueError) as e:
        print(f"Error parsing analysis response: {e}. Full response was:\n{analysis_text}")
        return None

    return {
        'title': article_title, 'link': article_link,
        'comprehensive_summary': comprehensive_summary, 'contrarian_view': contrarian_view,
        'practical_application': practical_application, 'glossary': glossary
    }
