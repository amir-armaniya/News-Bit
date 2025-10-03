#English:

# Strategic Analysis Assistant

This project is an intelligent and automated pipeline for collecting, filtering, analyzing, and presenting news and articles from various web sources. The system is designed to act as a personal assistant for a startup founder or product manager, providing strategic and personalized analysis via a Telegram bot.

This project is completely free and runs on **GitHub Actions** and free AI APIs (via **OpenRouter**).

## 🚀 Key Features

This intelligent assistant provides a set of powerful features to optimize the process of receiving and analyzing information:

* **Dual-Mode Operation:**

* **Scheduled Analysis:** Automatically and weekly collects and analyzes new news from defined RSS sources.
* **On-Demand Analysis:** Instant analysis of any link or article sent to the Telegram bot.

* **AI Core:**

* **Smart Filter:** Before any in-depth analysis, it uses a fast and low-cost AI model to select articles based on their relevance to the user's goals (defined in `context.txt`) to avoid clutter and irrelevant information.
* **Deep Strategic Analysis:** Using a powerful AI model and the "Chain of Thought" technique, it provides multi-part analyses that include **Summary**, **Opposite Viewpoint**, **Practical Application for the User**, and **Glossary of Key Terms**.

* **Multi-purpose Data Collection:**

* **RSS Reader:** Collects new articles from the list of RSS sources defined in `config.json`.
* **Web Scraper:** It has the ability to extract text content from any website link (even websites without RSS).

* **Long-term memory (Persistence):**

* The system is equipped with a persistent memory (`processed_articles.jsonl`) that stores the link of all analyzed articles. This feature ensures that you will never be sent a duplicate news item, and the memory is automatically updated in the GitHub repository after each successful execution.

## ⚙️ Architecture and how it works

The system uses a modular and interactive architecture:

1. **User input (for request analysis):** The user sends a link to the Telegram bot.
2. **Cloudflare Worker:** An always-on serverless function receives the message, verifies the user's identity, and instructs GitHub Actions to start an "on-demand" operation.
3. **GitHub Actions:**
* **On-demand execution:** The GitHub workflow executes the `on_demand_analyzer.py` script upon receiving the command. This script scrapes the link, analyzes its content, and sends the result to Telegram.
* **Scheduled execution:** Weekly, the workflow executes the `main.py` script, which is responsible for collecting, filtering, and analyzing news from RSS sources.
4. **Output:** All analysis is sent to the user as a text message with professional Markdown formatting in Telegram.

## 🛠️ Setup and Configuration

To setup this assistant, follow these steps:

1. **Clone the repository:**

```bash
git clone https://github.com/AmirArmaniya/podcast-generator.git
cd podcast-generator
```

2. **Install dependencies:**

```bash
pip install -r requirements.txt
```

3. **Configure environment variables:**

* Create a `.env` file in the root of the project and put the following variables in it:
* `OPENROUTER_API_KEY`: Your API key from the OpenRouter service.
* `TELEGRAM_BOT_TOKEN`: Your Telegram bot token.
* `TELEGRAM_CHAT_ID`: Your Telegram chat numeric ID (for receiving messages).

4. **Customization:**

* **`config.json`:** Edit the list of your desired RSS sources in this file.
* **`context.txt`:** This is the most important file for personalization. Write your goals, interests, and work context in this file to fully optimize your AI analytics for you.

5. **GitHub and Cloudflare Settings:**

* For full activation (including interactivity), follow the steps to create a **Cloudflare Worker** and set up **Secrets** in your GitHub repository (including `GITHUB_TOKEN`).

#Persian:

# دستیار تحلیلگر استراتژیک اخبار (Strategic Analysis Assistant)

این پروژه یک پایپ‌لاین (pipeline) هوشمند و خودکار برای جمع‌آوری، فیلتر، تحلیل و ارائه اخبار و مقالات از منابع مختلف وب است. سیستم به گونه‌ای طراحی شده که به عنوان یک دستیار شخصی برای یک بنیان‌گذار استارتاپ یا مدیر محصول عمل کند و تحلیل‌های استراتژیک و شخصی‌سازی شده را از طریق یک ربات تلگرام ارائه دهد.

این پروژه کاملاً رایگان است و بر بستر **GitHub Actions** و APIهای رایگان هوش مصنوعی (از طریق **OpenRouter**) اجرا می‌شود.

## 🚀 قابلیت‌های کلیدی

این دستیار هوشمند مجموعه‌ای از قابلیت‌های قدرتمند را برای بهینه‌سازی فرآیند دریافت و تحلیل اطلاعات فراهم می‌کند:

  * **اجرای دوگانه (Dual-Mode Operation):**

      * **تحلیل زمان‌بندی شده:** به صورت خودکار و هفتگی، اخبار جدید را از منابع RSS تعریف شده جمع‌آوری و تحلیل می‌کند.
      * **تحلیل درخواستی (On-Demand):** قابلیت تحلیل فوری هر لینک یا مقاله‌ای که برای ربات تلگرام ارسال می‌شود.

  * **مغز متفکر هوشمند (AI Core):**

      * **فیلتر هوشمند:** قبل از هر تحلیل عمیق، با استفاده از یک مدل هوش مصنوعی سریع و کم‌هزینه، مقالات را بر اساس ارتباط با اهداف کاربر (تعریف شده در `context.txt`) گزینش می‌کند تا از شلوغی و ارسال اطلاعات نامرتبط جلوگیری شود.
      * **تحلیل استراتژیک عمیق:** با استفاده از یک مدل هوش مصنوعی قدرتمند و تکنیک "زنجیره افکار" (Chain of Thought)، تحلیل‌های چندبخشی ارائه می‌دهد که شامل **خلاصه جامع**، **دیدگاه مخالف**، **کاربرد عملی برای کاربر** و **واژه‌نامه اصطلاحات کلیدی** است.

  * **جمع‌آوری چندمنظوره اطلاعات:**

      * **خواننده RSS:** مقالات جدید را از لیست منابع RSS تعریف شده در `config.json` جمع‌آوری می‌کند.
      * **خزنده وب (Web Scraper):** قابلیت استخراج محتوای متنی از هر لینک وب‌سایت (حتی وب‌سایت‌های بدون RSS) را دارد.

  * **حافظه بلندمدت (Persistence):**

      * سیستم مجهز به یک حافظه پایدار (`processed_articles.jsonl`) است که لینک تمام مقالات تحلیل شده را در خود ذخیره می‌کند. این قابلیت تضمین می‌کند که هرگز یک خبر تکراری برای شما ارسال نشود و حافظه پس از هر اجرای موفق به صورت خودکار در ریپازیتوری گیت‌هاب به‌روزرسانی می‌شود.

## ⚙️ معماری و نحوه کار

این سیستم از یک معماری ماژولار و تعاملی بهره می‌برد:

1.  **ورودی کاربر (برای تحلیل درخواستی):** کاربر لینکی را به ربات تلگرام ارسال می‌کند.
2.  **پل ارتباطی (Cloudflare Worker):** یک تابع سرورلس همیشه فعال، پیام را دریافت کرده، هویت کاربر را تایید می‌کند و به GitHub Actions فرمان شروع یک عملیات "درخواستی" را می‌دهد.
3.  **مغز متفکر (GitHub Actions):**
      * **اجرای درخواستی:** گردش کار گیت‌هاب با دریافت فرمان، اسکریپت `on_demand_analyzer.py` را اجرا می‌کند. این اسکریپت لینک را خراشیده، محتوای آن را تحلیل کرده و نتیجه را در تلگرام ارسال می‌کند.
      * **اجرای زمان‌بندی شده:** به صورت هفتگی، گردش کار اسکریپت `main.py` را اجرا می‌کند که وظیفه جمع‌آوری، فیلتر و تحلیل اخبار از منابع RSS را بر عهده دارد.
4.  **خروجی:** تمام تحلیل‌ها به صورت یک پیام متنی با فرمت‌بندی حرفه‌ای Markdown در تلگرام برای کاربر ارسال می‌شود.

## 🛠️ راه‌اندازی و پیکربندی

برای راه‌اندازی این دستیار، مراحل زیر را دنبال کنید:

1.  **کلون کردن ریپازیتوری:**

    ```bash
    git clone https://github.com/AmirArmaniya/podcast-generator.git
    cd podcast-generator
    ```

2.  **نصب وابستگی‌ها:**

    ```bash
    pip install -r requirements.txt
    ```

3.  **پیکربندی متغیرهای محیطی:**

      * یک فایل `.env` در ریشه پروژه بسازید و متغیرهای زیر را در آن قرار دهید:
          * `OPENROUTER_API_KEY`: کلید API شما از سرویس OpenRouter.
          * `TELEGRAM_BOT_TOKEN`: توکن ربات تلگرام شما.
          * `TELEGRAM_CHAT_ID`: شناسه عددی چت تلگرام شما (برای دریافت پیام‌ها).

4.  **شخصی‌سازی:**

      * **`config.json`:** لیست منابع RSS مورد نظر خود را در این فایل ویرایش کنید.
      * **`context.txt`:** این مهم‌ترین فایل برای شخصی‌سازی است. اهداف، علایق و زمینه کاری خود را در این فایل بنویسید تا تحلیل‌های هوش مصنوعی کاملاً برای شما بهینه شوند.

5.  **تنظیمات GitHub و Cloudflare:**

      * برای فعال‌سازی کامل (شامل قابلیت تعاملی)، مراحل مربوط به ساخت **Cloudflare Worker** و تنظیم **Secrets** در ریپازیتوری گیت‌هاب (شامل `GITHUB_TOKEN`) را دنبال کنید.
