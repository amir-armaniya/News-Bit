# News Bit

Telegram bot that fetches and sends news from RSS feeds with AI-powered analysis and translation.

## Features

- **Telegram Bot** — Settings menu, language selection, auto mode toggle
- **Auto Mode** — Sends news every 30 minutes via Cloudflare Cron
- **Multi-Language** — Farsi, Arabic, English (menu + news translation)
- **AI Analysis** — Summarizes articles using OpenRouter API
- **Per-User Settings** — Each user has their own language and preferences

## Architecture

```
Telegram User
    ↓
Cloudflare Worker (webhook + cron)
    ↓
RSS Feeds → AI Analysis → Translation → Telegram
```

- **Webhook**: Handles user commands and settings
- **Cron (*/30 * * * *)**: Auto-sends news to users with auto_mode enabled

## Setup

### 1. Deploy to Cloudflare

```bash
wrangler deploy
```

### 2. Set Secrets

```bash
wrangler secret put TELEGRAM_BOT_TOKEN
wrangler secret put OPENROUTER_API_KEY
```

### 3. Setup Telegram Webhook

Go to @BotFather → /setwebhook → Enter:
```
https://news-bit-worker.amirarmaniya.workers.dev
```

### 4. Create KV Namespaces

```bash
wrangler kv namespace create USERS_KV
wrangler kv namespace create ARTICLES_KV
```

Update `wrangler.toml` with the new IDs.

## Bot Commands

| Command | Description |
|---------|-------------|
| `/start` | Show main menu |
| `/settings` | Open settings (language, auto mode) |
| `/news` | Fetch latest news |

## Branches

| Branch | Description |
|--------|-------------|
| `main` | Active bot (Cloudflare Worker) |
| `auto-news-detective` | Auto mode with per-user settings |
| `weekly-news-sender` | Legacy version (weekly schedule) |

## Tech Stack

- **Cloudflare Worker** — Serverless bot backend
- **Cloudflare KV** — User settings storage
- **Cloudflare Cron** — Scheduled news delivery
- **OpenRouter API** — AI analysis and translation
- **Telegram Bot API** — User interface
