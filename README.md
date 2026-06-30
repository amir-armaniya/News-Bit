# News Bit

An automated news intelligence pipeline that collects, filters, and analyzes articles using AI, delivering personalized strategic insights through an interactive Telegram bot.

Built on **GitHub Actions** (free CI/CD), **Cloudflare Workers** (serverless bridge), and **OpenRouter** (AI APIs).

## Features

- **Interactive Telegram Bot** — Guided onboarding, topic selection, and dynamic feed management via inline buttons
- **Dual-Mode Operation** — Weekly scheduled analysis of RSS feeds + instant on-demand analysis of any URL
- **AI-Powered Filtering** — A fast, low-cost model pre-screens articles for relevance before expensive deep analysis
- **Deep Strategic Analysis** — Multi-part insights including summary, contrarian viewpoint, practical application, and glossary
- **Web Scraping** — Extracts content from any webpage, even without RSS support
- **Persistent Memory** — Tracks processed articles in `processed_articles.jsonl` to prevent duplicates

## Architecture

```
User (Telegram)
    |
    v
Cloudflare Worker (bridge + KV state)
    |
    v
GitHub Actions
    ├── on_demand_analyzer.py  (interactive: onboarding, customization, URL analysis)
    └── main.py                (scheduled: weekly RSS collection + analysis)
    |
    v
Telegram (formatted Markdown output)
```

1. **Cloudflare Worker** receives Telegram webhooks, manages user state (topics, feeds) in KV storage, and triggers the appropriate GitHub Actions workflow
2. **`on_demand_analyzer.py`** handles the full interactive user journey — onboarding flow, topic/feed customization menus, and on-demand link analysis
3. **`main.py`** runs on a weekly schedule to collect articles from RSS feeds, filter by relevance, and generate strategic analyses

## Project Structure

```
News-Bit/
├── main.py                    # Weekly scheduled pipeline
├── on_demand_analyzer.py      # Interactive event handler
├── config.json                # Default RSS feed list
├── context.txt                # User profile & interests (personalization)
├── requirements.txt           # Python dependencies
├── processed_articles.jsonl   # Article deduplication memory
├── modules/
│   ├── ai_processor.py        # OpenRouter AI filtering & analysis
│   ├── content_collector.py   # RSS feed reader
│   ├── memory_manager.py      # Persistence layer
│   ├── telegram_sender.py     # Telegram API integration
│   └── web_scraper.py         # HTML content extraction
└── cloudflare-worker/
    └── index.js               # Cloudflare Worker (webhook handler + KV state)
```

## Setup

### 1. Clone & Install

```bash
git clone <your-repo-url>
cd News-Bit
pip install -r requirements.txt
```

### 2. Environment Variables

Create a `.env` file:

```env
OPENROUTER_API_KEY=your_openrouter_api_key
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_telegram_chat_id
```

### 3. Personalization

- **`context.txt`** — Write your goals, interests, and professional context here. This is the most important file — the AI tailors all analyses based on it.
- **`config.json`** — Edit the default RSS feed list. Users can also add/remove feeds interactively through the bot.

### 4. Cloudflare Worker

Deploy the worker in `cloudflare-worker/` with:

- A **KV Namespace Binding** named `STRATEGIC_RADAR_USERS`
- Environment secrets: `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, `GITHUB_TOKEN`, `GITHUB_REPO`

### 5. GitHub Actions

Set up a workflow that runs `main.py` on a schedule (e.g., weekly) and `on_demand_analyzer.py` when triggered by the Cloudflare Worker.

## Dependencies

| Package | Purpose |
|---------|---------|
| `feedparser` | RSS feed parsing |
| `openai` | OpenRouter AI API client |
| `python-telegram-bot` | Telegram bot API |
| `beautifulsoup4` | HTML content extraction |
| `requests` | HTTP client |
| `python-dotenv` | Environment variable loading |
