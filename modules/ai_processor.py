# modules/ai_processor.py
import os
from openai import OpenAI

# Fast and low-cost model for initial filtering
FAST_MODEL = "google/gemma-3-12b-it:free" 
# Powerful model for deep strategic analysis
POWERFUL_MODEL = "google/gemma-3-27b-it:free"

def is_article_relevant(article_title: str, article_summary: str, selected_topics: list | None = None) -> bool:
    api_key = os.getenv('OPENROUTER_API_KEY')
    if not api_key:
        print("OPENROUTER_API_KEY not found.")
        return False
    client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=api_key)
    user_context = ""
    try:
        with open('context.txt', 'r', encoding='utf-8') as f:
            user_context = f.read().strip()
    except FileNotFoundError:
        pass
    
    # NEW DYNAMIC PROMPT LOGIC
    if selected_topics:
        # If specific topics are provided, focus the AI on them.
        topic_str = ", ".join(selected_topics)
        relevance_question = f"Is this article specifically relevant to one of these high-priority topics for the founder: {topic_str}?"
    else:
        # Fallback to the general context if no topics are selected.
        relevance_question = "Is this article relevant to the founder's work in SaaS, FinTech, AI, product management, funding, or team building?"

    prompt = f"""
    You are an expert assistant for a tech startup founder in Iran.
    The founder's general interests are: "{user_context}"

    Analyze the following article and determine if it's relevant based on this specific question:
    Article Title: "{article_title}"
    Article Summary: "{article_summary}"

    Question: {relevance_question}
    Consider articles about market trends, new technologies, startup strategies, or case studies within the specified topics.

    Answer with only 'YES' or 'NO'.
    """
    try:
        response = client.chat.completions.create(
            model=FAST_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=10,  # Increase max_tokens
            temperature=0.1
        )
        answer = response.choices[0].message.content.strip().upper()
        print(f"   API Response: {answer}")  # Add log for debug
        
        # If response is empty, consider the article as relevant
        if not answer:
            print("   -> Empty API response, treating as RELEVANT")
            return True
            
        return "YES" in answer
    except Exception as e:
        print(f"Relevance check failed: {e}")
        # On error, consider the article as relevant
        return True

def process_article_in_english(article_title: str, article_summary: str, article_link: str) -> dict | None:
    api_key = os.getenv('OPENROUTER_API_KEY')
    if not api_key:
        print("OPENROUTER_API_KEY not found.")
        return None
    client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=api_key)
    
    user_context = ""
    try:
        with open('context.txt', 'r', encoding='utf-8') as f:
            user_context = f.read().strip()
    except FileNotFoundError:
        pass

    # Process in English directly
    combined_text = f"Title: {article_title}\n\nSummary: {article_summary}"

    # --- CRITICAL UPGRADE: Chain of Thought Prompt ---
    system_prompt_analysis = """You are a world-class strategic analyst, acting as a personal advisor to a tech founder. Your task is to perform a multi-step analysis of the provided [NEWS ARTICLE] based on the [USER CONTEXT].

Your thought process must be as follows:
1.  **Summarize:** First, identify the core message and key data points of the article.
2.  **Critique:** Second, think about the hidden risks, challenges, or contrarian viewpoints.
3.  **Apply:** Third, connect the article's insights directly to the user's goals (SaaS, FinTech, product management, funding).
4.  **Define:** Fourth, identify any important technical or business jargon that needs explanation.
5.  **Synthesize:** Finally, combine all of your thoughts into a structured, well-written report using the specified delimiters.

Your entire final output MUST be structured using these exact delimiters:
[Comprehensive Summary]
(A detailed paragraph based on your summary.)
[Contrarian View]
(A short paragraph based on your critique.)
[Practical Application for User]
(2-3 actionable ideas based on your application step.)
[Glossary]
(Explain up to 5 key terms based on your definition step, in the format: '- Term: Explanation')"""
    
    user_message = f"[USER CONTEXT]\n{user_context}\n\n[NEWS ARTICLE]\n{combined_text}"
    
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
        comprehensive_summary = analysis_text.split('[Comprehensive Summary]')[1].split('[Contrarian View]')[0].strip()
        contrarian_view = analysis_text.split('[Contrarian View]')[1].split('[Practical Application for User]')[0].strip()
        practical_application = analysis_text.split('[Practical Application for User]')[1].split('[Glossary]')[0].strip()
        glossary = analysis_text.split('[Glossary]')[1].strip()
    except IndexError:
        print(f"Error parsing analysis response. The model did not follow the format. Response was:\n{analysis_text}")
        return None

    return {
        'title': article_title, 'link': article_link,
        'comprehensive_summary': comprehensive_summary, 'contrarian_view': contrarian_view,
        'practical_application': practical_application, 'glossary': glossary
    }