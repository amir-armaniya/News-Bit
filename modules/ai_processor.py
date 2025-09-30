import os
from openai import OpenAI

def process_article_in_persian(article_title: str, article_summary: str, article_link: str) -> dict | None:
    api_key = os.getenv('OPENROUTER_API_KEY')
    if not api_key:
        print("Error: OPENROUTER_API_KEY environment variable not found.")
        return None

    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key
    )

    # Step 1: Read user context
    user_context = ""
    try:
        with open('context.txt', 'r', encoding='utf-8') as f:
            user_context = f.read().strip()
    except FileNotFoundError:
        user_context = ""
    except Exception as e:
        print(f"Error reading context.txt: {e}")
        return None

    # Step 2: Translation to Persian
    combined_text = f"{article_title}\n\n{article_summary}"
    system_prompt_translation = "You are an expert translator. Translate the following English text to Persian. Your translation must be accurate, professional, and natural-sounding. Preserve the original meaning and tone. Output only the translated text."

    try:
        response_translation = client.chat.completions.create(
            model="google/gemma-3-27b-it:free",
            messages=[
                {"role": "system", "content": system_prompt_translation},
                {"role": "user", "content": combined_text}
            ],
            temperature=0.5,
            max_tokens=1000
        )
        translated_text = response_translation.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error during translation API call: {e}")
        return None

    # Step 3: Strategic Analysis
    system_prompt_analysis = """You are a world-class strategic analyst and a personal advisor to a tech founder. First, carefully read the user's background and goals provided in the [USER CONTEXT]. Then, analyze the [NEWS ARTICLE] text. Your entire response MUST be structured in Persian using these exact delimiters:
[خلاصه جامع]
(A detailed paragraph that covers all aspects of the news.)
[دیدگاه مخالف]
(A short paragraph expressing the hidden risks, challenges, or a critical contrarian viewpoint of the news.)
[کاربرد عملی برای کاربر]
(Based on the user's specific context, provide 2-3 actionable ideas on how they can use the insights from this news in their own FinTech and SaaS projects.)
[واژه‌نامه]
(Identify up to 3 key technical or business terms/acronyms from the article and provide a brief, simple explanation for each in the format: '- Term: Explanation')"""

    user_message = f"[USER CONTEXT]\n{user_context}\n\n[NEWS ARTICLE]\n{translated_text}"

    try:
        response_analysis = client.chat.completions.create(
            model="google/gemma-3-27b-it:free",
            messages=[
                {"role": "system", "content": system_prompt_analysis},
                {"role": "user", "content": user_message}
            ],
            temperature=0.5,
            max_tokens=1500
        )
        analysis_text = response_analysis.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error during analysis API call: {e}")
        return None

    # Parsing Logic
    try:
        # Split for [خلاصه جامع]
        parts1 = analysis_text.split('[خلاصه جامع]')
        if len(parts1) < 2:
            print("Error: Failed to parse [خلاصه جامع] section from analysis response.")
            return None
        remaining1 = parts1[1]

        # Split for [دیدگاه مخالف]
        parts2 = remaining1.split('[دیدگاه مخالف]')
        if len(parts2) < 2:
            print("Error: Failed to parse [دیدگاه مخالف] section from analysis response.")
            return None
        comprehensive_summary = parts2[0].strip()
        remaining2 = parts2[1]

        # Split for [کاربرد عملی برای کاربر]
        parts3 = remaining2.split('[کاربرد عملی برای کاربر]')
        if len(parts3) < 2:
            print("Error: Failed to parse [کاربرد عملی برای کاربر] section from analysis response.")
            return None
        contrarian_view = parts3[0].strip()
        remaining3 = parts3[1]

        # Split for [واژه‌نامه]
        parts4 = remaining3.split('[واژه‌نامه]')
        if len(parts4) < 2:
            print("Error: Failed to parse [واژه‌نامه] section from analysis response.")
            return None
        practical_application = parts4[0].strip()
        glossary = parts4[1].strip()

        # Validation: Check if all sections were extracted
        if not all([comprehensive_summary, contrarian_view, practical_application, glossary]):
            print("Error: One or more sections are missing or empty after parsing.")
            return None

    except Exception as e:
        print(f"Error during parsing analysis response: {e}")
        return None

    # Final output dictionary
    final_dict = {
        'title': article_title,
        'link': article_link,
        'comprehensive_summary': comprehensive_summary,
        'contrarian_view': contrarian_view,
        'practical_application': practical_application,
        'glossary': glossary
    }
    return final_dict
