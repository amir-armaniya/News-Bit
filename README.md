
# English:

# News Bit Assistant

This project is an intelligent and automated pipeline for collecting, filtering, analyzing, and presenting news and articles. The system is designed to act as a personal strategic assistant for a startup founder or product manager, providing tailored analysis via a fully interactive Telegram bot.

This project runs for free on **GitHub Actions**, with **Cloudflare Workers** as the interactive bridge and **OpenRouter** for AI APIs.

## 🚀 Key Features

This intelligent assistant provides a set of powerful features to optimize the process of receiving and analyzing information:

  * **Interactive & Personalized Experience:**

      * **Guided Onboarding:** The bot actively guides new users through a setup process, demonstrating its value and capabilities from the first interaction.
      * **Topic Selection:** Users can choose their specific areas of interest (e.g., AI, FinTech, Product Management) to receive more relevant analyses.
      * **Dynamic Feed Management:** Users can add their own custom RSS feeds or remove default ones directly through the bot's interactive interface.

  * **Dual-Mode Operation:**

      * **Scheduled Analysis:** Automatically and weekly, it collects and analyzes new articles from the user's customized list of RSS sources.
      * **On-Demand Analysis:** Provides instant analysis of any link sent to the Telegram bot.

  * **AI Core:**

      * **Smart Filter:** Before any in-depth analysis, it uses a fast, low-cost AI model to select articles based on their relevance to the user's goals (defined in `context.txt`).
      * **Deep Strategic Analysis:** Using a powerful AI model, it provides multi-part analyses that include **Summary**, **Contrarian Viewpoint**, **Practical Application for the User**, and a **Glossary of Key Terms**.

  * **Multi-purpose Data Collection:**

      * **RSS Reader:** Collects new articles from the list of default and user-added RSS sources.
      * **Web Scraper:** Can extract text content from any website link (even those without an RSS feed).

  * **Long-Term Memory (Persistence):**

      * The system uses a persistent memory (`processed_articles.jsonl`) that stores the link of every analyzed article. This ensures that no duplicate news is ever sent.

## ⚙️ Architecture and How It Works

The system uses a modular and stateful architecture to provide an interactive experience:

1.  **User Input:** The user interacts with the bot by sending a command (`/start`), clicking a button, or sending a link.
2.  **Cloudflare Worker (The Bridge & Memory):** An always-on serverless function acts as the main gateway. It receives messages, manages user state and preferences (like selected topics and custom feeds) using a KV store, and intelligently triggers the correct GitHub Actions workflow.
3.  **GitHub Actions (The Brain):**
      * **Interactive Execution (`on_demand_analyzer.py`):** This script handles the entire interactive user journey, including the onboarding flow, customization menus, and on-demand analysis of links.
      * **Scheduled Execution (`main.py`):** Weekly, the workflow executes this script, which is responsible for collecting, filtering, and analyzing news from the user's personalized sources.
4.  **Output:** All analyses are sent to the user as professionally formatted Markdown messages in Telegram.

## 🛠️ Setup and Configuration

To set up this assistant, follow these steps:

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/AmirArmaniya/Strategic-Radar.git
    cd Strategic-Radar
    ```
2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
3.  **Configure environment variables:**
      * Create a `.env` file and add your `OPENROUTER_API_KEY`, `TELEGRAM_BOT_TOKEN`, and `TELEGRAM_CHAT_ID`.
4.  **Customization:**
      * **`config.json`:** Edit the initial list of default RSS sources.
      * **`context.txt`:** This is the most important file for personalization. Write your goals, interests, and professional context here to tailor the AI analysis.
5.  **GitHub and Cloudflare Settings:**
      * For full activation, create a **Cloudflare Worker** with a **KV Namespace Binding**, and set up the required **Secrets** in your GitHub repository.

-----

# Persian:

# دستیار News Bit

این پروژه یک پایپ‌لاین (pipeline) هوشمند و خودکار برای جمع‌آوری، فیلتر، تحلیل و ارائه اخبار و مقالات است. سیستم به گونه‌ای طراحی شده که به عنوان یک دستیار استراتژیک شخصی برای یک بنیان‌گذار استارتاپ یا مدیر محصول عمل کند و تحلیل‌های سفارشی‌شده را از طریق یک ربات تلگرام کاملاً تعاملی ارائه دهد.

این پروژه به صورت رایگان بر بستر **GitHub Actions**، با استفاده از **Cloudflare Workers** به عنوان پل ارتباطی تعاملی و **OpenRouter** برای APIهای هوش مصنوعی اجرا می‌شود.

## 🚀 قابلیت‌های کلیدی

این دستیار هوشمند مجموعه‌ای از قابلیت‌های قدرتمند را برای بهینه‌سازی فرآیند دریافت و تحلیل اطلاعات فراهم می‌کند:

  * **تجربه تعاملی و شخصی‌سازی شده (جدید):**

      * **آنبوردینگ هوشمند:** ربات به صورت فعال کاربران جدید را در یک فرآیند راه‌اندازی راهنمایی می‌کند و ارزش و قابلیت‌های خود را از همان ابتدا به نمایش می‌گذارد.
      * **انتخاب موضوعات:** کاربران می‌توانند حوزه‌های مورد علاقه خود (مانند هوش مصنوعی، فین‌تک، مدیریت محصول) را انتخاب کنند تا تحلیل‌های مرتبط‌تری دریافت نمایند.
      * **مدیریت پویای منابع:** کاربران می‌توانند منابع خبری RSS دلخواه خود را اضافه کرده یا منابع پیش‌فرض را مستقیماً از طریق رابط کاربری تعاملی ربات مدیریت کنند.

  * **اجرای دوگانه (Dual-Mode Operation):**

      * **تحلیل زمان‌بندی شده:** به صورت خودکار و هفتگی، اخبار جدید را از لیست سفارشی‌شده منابع RSS کاربر جمع‌آوری و تحلیل می‌کند.
      * **تحلیل درخواستی (On-Demand):** قابلیت تحلیل فوری هر لینکی که برای ربات تلگرام ارسال می‌شود.

  * **مغز متفکر هوشمند (AI Core):**

      * **فیلتر هوشمند:** قبل از هر تحلیل عمیق، با استفاده از یک مدل هوش مصنوعی سریع و کم‌هزینه، مقالات را بر اساس ارتباط با اهداف کاربر (تعریف شده در `context.txt`) گزینش می‌کند.
      * **تحلیل استراتژیک عمیق:** با استفاده از یک مدل هوش مصنوعی قدرتمند، تحلیل‌های چندبخشی ارائه می‌دهد که شامل **خلاصه جامع**، **دیدگاه مخالف**، **کاربرد عملی برای کاربر** و **واژه‌نامه اصطلاحات کلیدی** است.

  * **جمع‌آوری چندمنظوره اطلاعات:**

      * **خواننده RSS:** مقالات جدید را از لیست منابع پیش‌فرض و منابع اضافه‌شده توسط کاربر جمع‌آوری می‌کند.
      * **خزنده وب (Web Scraper):** قابلیت استخراج محتوای متنی از هر لینک وب‌سایت (حتی وب‌سایت‌های بدون RSS) را دارد.

  * **حافظه بلندمدت (Persistence):**

      * سیستم از یک حافظه پایدار (`processed_articles.jsonl`) استفاده می‌کند که لینک تمام مقالات تحلیل شده را ذخیره می‌کند. این قابلیت تضمین می‌کند که هرگز یک خبر تکراری ارسال نشود.

## ⚙️ معماری و نحوه کار

این سیستم از یک معماری ماژولار و حالت‌مند (Stateful) برای ارائه یک تجربه تعاملی بهره می‌برد:

1.  **ورودی کاربر:** کاربر از طریق ارسال دستور (`/start`)، کلیک روی دکمه‌ها، یا ارسال لینک با ربات تعامل می‌کند.
2.  **پل ارتباطی و حافظه (Cloudflare Worker):** یک تابع سرورلس همیشه فعال که به عنوان دروازه اصلی عمل می‌کند. این سرویس پیام‌ها را دریافت کرده، **وضعیت و تنظیمات کاربر** (مانند موضوعات انتخابی و فیدهای شخصی) را با استفاده از **حافظه KV** مدیریت می‌کند و گردش کار مناسب را در GitHub Actions به صورت هوشمند فراخوانی می‌کند.
3.  **مغز متفکر (GitHub Actions):**
      * **اجرای تعاملی (`on_demand_analyzer.py`):** این اسکریپت اکنون **کل سفر تعاملی کاربر**، شامل فرآیند آنبوردینگ، منوهای شخصی‌سازی، و تحلیل درخواستی لینک‌ها را مدیریت می‌کند.
      * **اجرای زمان‌بندی شده (`main.py`):** به صورت هفتگی، گردش کار این اسکریپت را اجرا می‌کند که وظیفه جمع‌آوری، فیلتر و تحلیل اخبار از منابع شخصی‌سازی‌شده کاربر را بر عهده دارد.
4.  **خروجی:** تمام تحلیل‌ها به صورت یک پیام متنی با فرمت‌بندی حرفه‌ای Markdown در تلگرام برای کاربر ارسال می‌شود.

## 🛠️ راه‌اندازی و پیکربندی

برای راه‌اندازی این دستیار، مراحل زیر را دنبال کنید:

1.  **کلون کردن ریپازیتوری:**
    ```bash
    git clone https://github.com/AmirArmaniya/Strategic-Radar.git
    cd Strategic-Radar
    ```
2.  **نصب وابستگی‌ها:**
    ```bash
    pip install -r requirements.txt
    ```
3.  **پیکربندی متغیرهای محیطی:**
      * یک فایل `.env` بسازید و متغیرهای `OPENROUTER_API_KEY`، `TELEGRAM_BOT_TOKEN` و `TELEGRAM_CHAT_ID` را در آن قرار دهید.
4.  **شخصی‌سازی:**
      * **`config.json`:** لیست اولیه منابع RSS پیش‌فرض را در این فایل ویرایش کنید.
      * **`context.txt`:** این مهم‌ترین فایل برای شخصی‌سازی است. اهداف، علایق و زمینه کاری خود را در این فایل بنویسید تا تحلیل‌های هوش مصنوعی کاملاً برای شما بهینه شوند.
5.  **تنظیمات GitHub و Cloudflare:**
      * برای فعال‌سازی کامل، یک **Cloudflare Worker** به همراه یک **KV Namespace Binding** بسازید و **Secrets** مورد نیاز را در ریپازیتوری گیت‌هاب خود تنظیم کنید.
