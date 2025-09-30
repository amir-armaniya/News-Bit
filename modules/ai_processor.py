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

    # Step 1: Translation to Persian
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
        persian_text = response_translation.choices[0].message.content
    except Exception as e:
        print(f"Error during translation API call: {e}")
        return None

    # Step 2: Unstructured Summarization
    system_prompt_summarization = "You are a world-class strategic analyst. Summarize the following text in detail for a tech founder. Explain the core ideas, the consequences, and the strategic value. Write in natural, flowing Persian."

    try:
        response_summarization = client.chat.completions.create(
            model="google/gemma-3-27b-it:free",
            messages=[
                {"role": "system", "content": system_prompt_summarization},
                {"role": "user", "content": persian_text}
            ],
            temperature=0.5,
            max_tokens=1000
        )
        full_summary_text = response_summarization.choices[0].message.content
    except Exception as e:
        print(f"Error during unstructured summarization API call: {e}")
        return None

    # Step 3: Intelligent Extraction
    system_prompt_extraction = """You are an expert text extractor. From the user's text, extract two specific pieces of information. Structure your response using these exact delimiters:
[SHORT_SUMMARY]
(The single best sentence from the text that can serve as a powerful headline)
[LONG_SUMMARY]
(The single most important paragraph from the text that best explains the key takeaway for a startup builder)"""

    try:
        response_extraction = client.chat.completions.create(
            model="google/gemma-3-27b-it:free",
            messages=[
                {"role": "system", "content": system_prompt_extraction},
                {"role": "user", "content": full_summary_text}
            ],
            temperature=0.5,
            max_tokens=500
        )
        response_text = response_extraction.choices[0].message.content

        # Parse the structured response using string manipulation
        short_parts = response_text.split('[SHORT_SUMMARY]')
        if len(short_parts) < 2:
            print("Error: Failed to parse SHORT_SUMMARY section from extraction response.")
            return None

        long_parts = short_parts[1].split('[LONG_SUMMARY]')
        if len(long_parts) < 2:
            print("Error: Failed to parse LONG_SUMMARY section from extraction response.")
            return None

        short_summary = long_parts[0].strip()
        long_summary = long_parts[1].strip()

        # Validation: Check if both summaries were extracted
        if not short_summary or not long_summary:
            print("Error: One or both summaries are missing or empty after parsing.")
            return None

    except Exception as e:
        print(f"Error during extraction API call: {e}")
        return None

    # Final output dictionary
    final_dict = {
        'title': article_title,
        'link': article_link,
        'short_summary': short_summary,
        'long_summary': long_summary
    }
    return final_dict
