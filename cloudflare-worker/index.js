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
    items.push({ title: get("title"), link: get("link"), desc: get("description") });
  }
  return items;
}

// Get recent articles from feeds (per-user to avoid duplicates)
async function fetchArticles(env, chatId) {
  const userKey = `seen_${String(chatId)}`;
  const seen = JSON.parse(await env.ARTICLES_KV.get(userKey) || "[]");
  const articles = [];

  for (const feed of DEFAULT_FEEDS) {
    try {
      const res = await fetch(feed.url, { headers: { "User-Agent": "NewsBit/1.0" } });
      const xml = await res.text();
      for (const item of parseRSS(xml)) {
        if (!seen.includes(item.link)) {
          articles.push({ ...item, source: feed.name });
          seen.push(item.link);
        }
      }
    } catch (e) {
      console.error(`Feed error: ${feed.name}`, e);
    }
  }

  // Save and return only NEW articles
  await env.ARTICLES_KV.put(userKey, JSON.stringify(seen.slice(-200)));
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
        model: "openai/gpt-oss-20b:free",
        messages: [{
          role: "user",
          content: `Analyze this news briefly:\nTitle: ${article.title}\nSummary: ${article.desc}\n\nProvide:\n1. Summary (2-3 sentences)\n2. Why it matters\n3. Key takeaway`
        }],
        max_tokens: 300
      })
    });
    const data = await res.json();
    return data.choices?.[0]?.message?.content || null;
  } catch (e) {
    console.error("AI error:", e);
    return null;
  }
}

// Translation
async function translate(env, text, lang) {
  if (lang === "en" || !env.OPENROUTER_API_KEY) return text;
  
  const langNames = { fa: "Persian", ar: "Arabic" };
  try {
    const res = await fetch("https://openrouter.ai/api/v1/chat/completions", {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${env.OPENROUTER_API_KEY}`,
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        model: "openai/gpt-oss-20b:free",
        messages: [{ role: "user", content: `Translate to ${langNames[lang]}:\n${text}` }],
        max_tokens: 500
      })
    });
    const data = await res.json();
    return data.choices?.[0]?.message?.content || text;
  } catch (e) {
    return text;
  }
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
        const articles = await fetchArticles(env, chatId);
        if (articles.length === 0) {
          await sendMsg(token, chatId, "No new articles found.");
        } else {
          for (const art of articles) {
            let text = `<b>${art.title}</b>\nSource: ${art.source}\n\n${art.desc}`;
            if (user.lang !== "en") text = await translate(env, text, user.lang);
            await sendMsg(token, chatId, text.substring(0, 4000));
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
      const articles = await fetchArticles(env, chatId);
      if (articles.length === 0) {
        await sendMsg(token, chatId, "No new articles found.");
      } else {
        for (const art of articles) {
          let text = `<b>${art.title}</b>\nSource: ${art.source}\n\n${art.desc}`;
          if (user.lang !== "en") text = await translate(env, text, user.lang);
          await sendMsg(token, chatId, text.substring(0, 4000));
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

          const articles = await fetchArticles(env, key.name);
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
