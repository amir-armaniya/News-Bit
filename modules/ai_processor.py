import os
from openai import OpenAI

def summarize_article(article_title: str, article_summary: str) -> str:
    api_key = os.getenv('OPENROUTER_API_KEY')
    if not api_key:
        print("Error: OPENROUTER_API_KEY environment variable not found.")
        return ""

    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key
    )

    user_message = f"Title: {article_title}\n\nSummary: {article_summary}"

    system_prompt = "You are a world-class strategic analyst and product manager. Your goal is to extract the core insights from the following text for a tech founder and product leader. Summarize the key idea, the most important lesson, or the critical data point in 2-3 concise Persian sentences. Focus on the 'so what?' for a startup builder. Ignore pleasantries and get straight to the strategic point."

    try:
        response = client.chat.completions.create(
            model="google/gemma-3-27b-it:free",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            temperature=0.5,
            max_tokens=400
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error during API call: {e}")
        return ""
