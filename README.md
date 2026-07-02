# News Bit - Auto News Detective

An automated news intelligence pipeline that collects, filters, and analyzes articles using AI, delivering personalized strategic insights through an interactive Telegram bot.

Built on **GitHub Actions** (free CI/CD), **Cloudflare Workers** (serverless bridge), and **OpenRouter** (AI APIs).

## Features

- **Interactive Telegram Bot** — Guided onboarding, topic selection, and dynamic feed management via inline buttons
- **Auto Mode** — Automatically detects and sends important news every 30 minutes
- **Multi-Language Support** — Translate news to Farsi, Arabic, or English with synchronized menu
- **AI-Powered Filtering** — A fast, low-cost model pre-screens articles for relevance before expensive deep analysis
- **Deep Strategic Analysis** — Multi-part insights including summary, contrarian viewpoint, practical application, and glossary
- **Web Scraping** — Extracts content from any webpage, even without RSS support
- **Persistent Memory** — Tracks processed articles in `processed_articles.jsonl` to prevent duplicates

## Architecture

```
User (Telegram)
    |
    v
Cloudflare Worker
    ├── fetch (webhook) ──→ GitHub Actions (manual/on-demand)
    └── scheduled (cron) ──→ Direct processing (auto mode)
    |
    v
Telegram (formatted Markdown output)
```

1. **Cloudflare Worker** handles two modes:
   - **Webhook**: Receives Telegram updates, triggers GitHub Actions for manual analysis
   - **Cron (every 30 min)**: Automatically fetches, filters, and sends news to users with auto_mode enabled
2. **`main.py`** runs manually for on-demand analysis (triggered by GitHub Actions)
3. **KV Storage**: Stores user settings, processed articles, and usage stats

## Auto Mode & Language Settings

### Auto Mode (Cloudflare Cron)
- Runs every 30 minutes automatically
- Only processes for users with `auto_mode: true` in their settings
- No cold start delay (unlike GitHub Actions)
- Free tier: 10,000 requests/day

### Multi-Language Support
- **Farsi (فارسی)** — Full translation of news and menu
- **Arabic (العربية)** — Full translation of news and menu
- **English** — Default language

Language settings are per-user (based on Telegram chat_id) and synchronized across:
- News content translation
- Telegram bot menu labels
- Section headers in messages

## Project Structure

```
News-Bit/
├── main.py                    # Auto mode (30 min) + manual run
├── on_demand_analyzer.py      # Interactive event handler
├── config.json                # Default RSS feed list
├── context.txt                # User profile & interests (personalization)
├── requirements.txt           # Python dependencies
├── processed_articles.jsonl   # Article deduplication memory
├── user_prefs.json            # User settings (language, auto mode)
├── modules/
│   ├── ai_processor.py        # OpenRouter AI filtering, analysis & translation
│   ├── content_collector.py   # RSS feed reader (30-min window)
│   ├── memory_manager.py      # Persistence layer
│   ├── settings_manager.py    # Language & auto mode settings
│   ├── telegram_sender.py     # Telegram API integration (multi-language)
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
