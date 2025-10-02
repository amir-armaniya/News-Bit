import os
import asyncio
from modules import ai_processor, telegram_sender, web_scraper

async def main():
    user_input = os.getenv('ON_DEMAND_INPUT', '').strip()

    if not user_input:
        print("No on-demand input provided. Exiting.")
        return

    print(f"Received on-demand input: {user_input}")

    # --- Simple Command Handling ---
    if user_input.lower().startswith('/add_source'):
        # Placeholder for adding a new source
        await telegram_sender.send_text_to_telegram("Functionality to add sources is not yet implemented.")
        return

    # --- URL Analysis ---
    if user_input.startswith(('http://', 'https://')):
        print(f"Input is a URL. Starting web scraping for: {user_input}")

        # Scrape the content from the URL
        scraped_content = web_scraper.scrape_url(user_input)

        if not scraped_content:
            await telegram_sender.send_text_to_telegram(f"Sorry, I could not extract content from the URL: {user_input}")
            return

        print("Scraping successful. Analyzing content...")
        # Send the scraped content for analysis
        analysis_dict = ai_processor.process_article_in_persian(
            scraped_content['title'],
            scraped_content['text'],
            user_input # Use the original URL as the link
        )

        if analysis_dict:
            await telegram_sender.send_article_analysis(analysis_dict)
            print("Analysis sent successfully.")
        else:
            await telegram_sender.send_text_to_telegram("Sorry, I failed to analyze the content of the URL.")
    else:
        # Handle other text commands if needed
        await telegram_sender.send_text_to_telegram("I received your message, but I can only process URLs or specific commands for now.")
        print("Non-URL input handled.")

if __name__ == "__main__":
    asyncio.run(main())