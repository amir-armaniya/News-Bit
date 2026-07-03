// News Bit Bot - Simple & Working Version

const DEFAULT_FEEDS = [
  { name: "TechCrunch", url: "https://techcrunch.com/feed/" },
  { name: "OpenAI Blog", url: "https://openai.com/news/rss.xml" },
  { name: "Y Combinator", url: "https://www.ycombinator.com/blog/rss" }
];

// Telegram API helpers
async function tg(token, method, data = {}) {
  const res = await fetch(`https://api.telegram.org/bot${token}/${method}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data)
  });
  return res.json();
}

async function sendMsg(token, chatId, text, replyMarkup = null) {
  const data = { chat_id: chatId, text, parse_mode: "HTML" };
  if (replyMarkup) data.reply_markup = replyMarkup;
  return tg(token, "sendMessage", data);
}

async function answerCb(token, id, text = "") {
  return tg(token, "answerCallbackQuery", { callback_query_id: id, text });
}

// KV helpers
async function getUser(env, chatId) {
  const key = String(chatId);
  const data = await env.USERS_KV.get(key);
  return data ? JSON.parse(data) : { lang: "en", auto: false };
}

async function saveUser(env, chatId, user) {
  await env.USERS_KV.put(String(chatId), JSON.stringify(user));
}

// RSS parser
function parseRSS(xml) {
  const items = [];
  const regex = /<item>([\s\S]*?)<\/item>/gi;
  let match;
  while ((match = regex.exec(xml)) !== null) {
    const item = match[1];
    const get = (tag) => {
      const m = item.match(new RegExp(`<${tag}[^>]*>(?:<!\\[CDATA\\[)?(.*?)(?:\\]\\]>)?<\\/${tag}>`, "is"));
      return m ? m[1].trim() : "";
    };
    const pubDate = get("pubDate");
    items.push({ title: get("title"), link: get("link"), desc: get("description"), pubDate });
  }
  return items;
}

// Get recent articles from feeds (per-user per-language to avoid duplicates)
async function fetchArticles(env, chatId, lang) {
  const userKey = `seen_${String(chatId)}_${lang}`;
  const seen = JSON.parse(await env.ARTICLES_KV.get(userKey) || "[]");
  const articles = [];
  const cutoff = Date.now() - 30 * 60 * 1000; // 30 minutes

  for (const feed of DEFAULT_FEEDS) {
    try {
      const res = await fetch(feed.url, { headers: { "User-Agent": "NewsBit/1.0" } });
      const xml = await res.text();
      for (const item of parseRSS(xml)) {
        // Skip if already seen
        if (seen.includes(item.link)) continue;

        // Skip if article is older than 30 minutes
        if (item.pubDate) {
          const pubTime = new Date(item.pubDate).getTime();
          if (pubTime < cutoff) continue;
        }

        articles.push({ ...item, source: feed.name });
        seen.push(item.link);
      }
    } catch (e) {
      console.error(`Feed error: ${feed.name}`, e);
    }
  }

  // Keep ALL seen articles (no truncation) to prevent duplicates
  await env.ARTICLES_KV.put(userKey, JSON.stringify(seen));
  return articles.slice(0, 5);
}

// AI analysis
async function analyzeArticle(env, article) {
  if (!env.OPENROUTER_API_KEY) return null;

  try {
    const res = await fetch("https://openrouter.ai/api/v1/chat/completions", {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${env.OPENROUTER_API_KEY}`,
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        model: "google/gemma-4-26b-a4b-it:free",
        messages: [{
          role: "user",
          content: `You are a professional tech news analyst. Analyze this article and respond in EXACTLY this format (in Persian/Farsi):

HEADLINE: [emoji] [headline in Persian, max 10 words]

KEY_POINTS:
• [bullet point 1]
• [bullet point 2]

WHY_MATTERS:
[2-3 sentences explaining why this matters for startup founders, in Persian]

---
Article Title: ${article.title}
Article Summary: ${article.desc}`
        }],
        max_tokens: 500
      })
    });
    const data = await res.json();
    return data.choices?.[0]?.message?.content || null;
  } catch (e) {
    console.error("AI error:", e);
    return null;
  }
}

// Format message for Telegram
function formatNews(analysis, article, lang) {
  if (!analysis) {
    let text = `📰 <b>${article.title}</b>\nSource: ${article.source}\n\n${article.desc}`;
    if (lang === "fa") text = `📰 <b>${article.title}</b>\nمنبع: ${article.source}\n\n${article.desc}`;
    return text.substring(0, 4000);
  }

  // Parse the AI analysis
  let headline = "", keyPoints = "", whyMatters = "";
  const lines = analysis.split("\n");
  for (const line of lines) {
    if (line.startsWith("HEADLINE:")) headline = line.replace("HEADLINE:", "").trim();
    else if (line.startsWith("•")) keyPoints += line + "\n";
    else if (line.startsWith("WHY_MATTERS:")) whyMatters = line.replace("WHY_MATTERS:", "").trim();
    else if (whyMatters && !line.startsWith("---")) whyMatters += " " + line.trim();
  }

  if (!headline) headline = article.title;
  if (!keyPoints) keyPoints = `• ${article.desc.substring(0, 100)}...`;

  const sourceText = lang === "fa" ? "منبع" : lang === "ar" ? "المصدر" : "Source";

  return `${headline}\n\n${keyPoints}\n\n💡 ${lang === "fa" ? "چرا این مهم است؟" : lang === "ar" ? "لماذا هذا مهم؟" : "Why this matters?"}\n${whyMatters}\n\n🔗 ${sourceText}: ${article.source}`;
}

// Menu texts
const MENU = {
  en: { start: "Welcome! Choose an option:", settings: "Settings", lang: "Language", auto: "Auto Mode", on: "ON", off: "OFF", fa: "Persian", ar: "Arabic", en: "English", send: "Send News", back: "Back" },
  fa: { start: "خوش آمدید! یک گزینه انتخاب کنید:", settings: "تنظیمات", lang: "زبان", auto: "حالت خودکار", on: "فعال", off: "غیرفعال", fa: "فارسی", ar: "عربی", en: "انگلیسی", send: "ارسال اخبار", back: "بازگشت" },
  ar: { start: "مرحباً! اختر خياراً:", settings: "الإعدادات", lang: "اللغة", auto: "الوضع التلقائي", on: "مفعّل", off: "معطّل", fa: "الفارسية", ar: "العربية", en: "الإنجليزية", send: "إرسال الأخبار", back: "رجوع" }
};

// Main handler
export default {
  async fetch(request, env) {
    if (request.method !== "POST") return new Response("OK");

    const body = await request.json();
    const msg = body.message || body.callback_query?.message;
    const cb = body.callback_query;
    const chatId = msg?.chat?.id || cb?.message?.chat?.id;
    if (!chatId) return new Response("OK");

    const token = env.TELEGRAM_BOT_TOKEN;
    const user = await getUser(env, chatId);
    const m = MENU[user.lang] || MENU.en;

    // Handle callback buttons
    if (cb) {
      const data = cb.data;
      await answerCb(token, cb.id);

      if (data === "settings") {
        const autoStatus = user.auto ? m.on : m.off;
        await sendMsg(token, chatId, `${m.settings}\n\n${m.lang}: ${m[user.lang]}\n${m.auto}: ${autoStatus}`, {
          inline_keyboard: [
            [{ text: m.lang, callback_data: "changelang" }],
            [{ text: `${m.auto}: ${autoStatus}`, callback_data: "toggleauto" }],
            [{ text: m.send, callback_data: "sendnews" }]
          ]
        });
      } else if (data === "changelang") {
        await sendMsg(token, chatId, "Select language:", {
          inline_keyboard: [
            [{ text: "فارسی", callback_data: "setlang_fa" }, { text: "العربية", callback_data: "setlang_ar" }, { text: "English", callback_data: "setlang_en" }]
          ]
        });
      } else if (data.startsWith("setlang_")) {
        user.lang = data.split("_")[1];
        await saveUser(env, chatId, user);
        const newM = MENU[user.lang];
        await sendMsg(token, chatId, `${newM.settings} - ${newM[user.lang]} ✓`);
      } else if (data === "toggleauto") {
        user.auto = !user.auto;
        await saveUser(env, chatId, user);
        const autoStatus = user.auto ? m.on : m.off;
        await sendMsg(token, chatId, `${m.auto}: ${autoStatus}`);
      } else if (data === "sendnews") {
        const articles = await fetchArticles(env, chatId, user.lang);
        if (articles.length === 0) {
          await sendMsg(token, chatId, "No new articles found.");
        } else {
          for (const art of articles) {
            const analysis = await analyzeArticle(env, art);
            const text = formatNews(analysis, art, user.lang);
            await sendMsg(token, chatId, text);
            await new Promise(r => setTimeout(r, 1000));
          }
        }
      }
      return new Response("OK");
    }

    // Handle text messages
    const text = (msg?.text || "").toLowerCase();
    
    if (text === "/start" || text === "start") {
      await sendMsg(token, chatId, m.start, {
        inline_keyboard: [[{ text: m.settings, callback_data: "settings" }]]
      });
    } else if (text === "/settings" || text === "settings") {
      const autoStatus = user.auto ? m.on : m.off;
      await sendMsg(token, chatId, `${m.settings}\n\n${m.lang}: ${m[user.lang]}\n${m.auto}: ${autoStatus}`, {
        inline_keyboard: [
          [{ text: m.lang, callback_data: "changelang" }],
          [{ text: `${m.auto}: ${autoStatus}`, callback_data: "toggleauto" }],
          [{ text: m.send, callback_data: "sendnews" }]
        ]
      });
    } else if (text === "/news" || text === "news") {
      const articles = await fetchArticles(env, chatId, user.lang);
      if (articles.length === 0) {
        await sendMsg(token, chatId, "No new articles found.");
      } else {
        for (const art of articles) {
          const analysis = await analyzeArticle(env, art);
          const text = formatNews(analysis, art, user.lang);
          await sendMsg(token, chatId, text);
          await new Promise(r => setTimeout(r, 1000));
        }
      }
    } else {
      await sendMsg(token, chatId, m.start, {
        inline_keyboard: [[{ text: m.settings, callback_data: "settings" }]]
      });
    }

    return new Response("OK");
  },

  // Cron handler - every 30 minutes
  async scheduled(event, env, ctx) {
    ctx.waitUntil((async () => {
      const list = await env.USERS_KV.list();
      for (const key of list.keys) {
        try {
          const user = JSON.parse(await env.USERS_KV.get(key.name));
          if (!user.auto) continue;

          const articles = await fetchArticles(env, key.name, user.lang);
          if (articles.length === 0) continue;

          const token = env.TELEGRAM_BOT_TOKEN;

          for (const art of articles) {
            let text = `<b>${art.title}</b>\nSource: ${art.source}\n\n${art.desc}`;
            if (user.lang !== "en") text = await translate(env, text, user.lang);
            await sendMsg(token, key.name, text.substring(0, 4000));
            await new Promise(r => setTimeout(r, 1000));
          }
        } catch (e) {
          console.error(`Error for user ${key.name}:`, e);
        }
      }
    })());
  }
};
