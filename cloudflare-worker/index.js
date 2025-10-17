// cloudflare-worker/index.js (Final, Self-Contained Version)

// =================================================================
// Default Feeds Configuration (Hardcoded)
// =================================================================
const DEFAULT_FEEDS = [
    {"name":"Lenny's Newsletter","url":"https://www.lennysnewsletter.com/feed"},
    {"name":"Reforge","url":"https://www.reforge.com/blog/rss.xml"},
    {"name":"SaaStr","url":"https://www.saastr.com/feed/"},
    {"name":"First Round Review","url":"http://firstround.com/review/feed.xml"},
    {"name":"Y Combinator","url":"https://www.ycombinator.com/blog/rss"},
    {"name":"a16z","url":"https://a16z.com/feed/"},
    {"name":"AI Breakfast","url":"https://aibreakfast.beehiiv.com/feed"},
    {"name":"Ben's Bites","url":"https://www.bensbites.co/feed"},
    {"name":"DeepLearning.AI","url":"https://www.deeplearning.ai/the-batch/rss.xml"},
    {"name":"FinTech Futures","url":"https://www.fintechfutures.com/feed/"},
    {"name":"Harvard Business Review","url":"https://hbr.org/feed"},
    {"name":"Mind the Product","url":"https://www.mindtheproduct.com/feed/"},
    {"name":"TechCrunch","url":"https://techcrunch.com/feed/"},
    {"name":"CB Insights","url":"https://www.cbinsights.com/blog/rss/"},
    {"name":"Product Hunt","url":"https://www.producthunt.com/feed.rss"}
];


// =================================================================
// Helper Functions
// =================================================================

/** @typedef {{status?: string, selected_topics?: string[], user_feeds?: Array<{name: string, url: string}>}} UserState */

async function getUserState(env, chatId) {
  if (!env.STRATEGIC_RADAR_USERS) {
    console.error("CRITICAL: KV Namespace 'STRATEGIC_RADAR_USERS' is not bound.");
    return {};
  }
  if (!chatId) return {};
  const stateStr = await env.STRATEGIC_RADAR_USERS.get(String(chatId));
  try {
    return stateStr ? JSON.parse(stateStr) : {};
  } catch (e) {
    console.error("Failed to parse user state:", e);
    return {};
  }
}

async function saveUserState(env, chatId, state) {
  if (!env.STRATEGIC_RADAR_USERS) return;
  if (!chatId) return;
  await env.STRATEGIC_RADAR_USERS.put(String(chatId), JSON.stringify(state));
}

async function triggerGitHubActions(env, payload) {
  const GITHUB_API_URL = `https://api.github.com/repos/${env.GITHUB_REPO}/actions/workflows/weekly_podcast.yml/dispatches`;
  const response = await fetch(GITHUB_API_URL, {
    method: 'POST',
    headers: { 'Authorization': `token ${env.GITHUB_TOKEN}`, 'Accept': 'application/vnd.github.v3+json', 'Content-Type': 'application/json', 'User-Agent': 'Cloudflare-Worker' },
    body: JSON.stringify({ ref: 'feature/interactive-worker', inputs: { on_demand_input: JSON.stringify(payload) } })
  });
  if (response.status !== 204) {
    console.error(`Failed to trigger GitHub Actions: ${response.status} ${await response.text()}`);
  }
}

async function sendTelegramMessage(botToken, chatId, text) {
  if (!chatId) return;
  const url = `https://api.telegram.org/bot${botToken}/sendMessage`;
  await fetch(url, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ chat_id: String(chatId), text: text }) });
}

async function answerCallbackQuery(botToken, callbackQueryId, text = null, show_alert = false) {
  const url = `https://api.telegram.org/bot${botToken}/answerCallbackQuery`;
  const payload = { callback_query_id: callbackQueryId };
  if (text) {
    payload.text = text;
    payload.show_alert = show_alert;
  }
  await fetch(url, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
}

// =================================================================
// Main Request Handler Logic
// =================================================================

async function handleRequest(request, env) {
    if (request.method !== 'POST') {
        return new Response('Expected POST request', { status: 405 });
    }

    const body = await request.json();
    let payload = null;
    let chatId;
    let triggerAction = true;

    const message = body.message || body.edited_message;
    const callbackQuery = body.callback_query;

    if (message) {
        chatId = message.chat.id;
        const userState = await getUserState(env, chatId);

        if (userState.status === 'awaiting_feed_url') {
            payload = { type: 'feed_submission', url: message.text || '', user_feeds: userState.user_feeds || [] };
            userState.status = 'active';
            await saveUserState(env, chatId, userState);
        } else {
            payload = { type: 'message', text: message.text || '', first_name: message.from ? message.from.first_name : 'کاربر' };
            if (payload.text && payload.text.toLowerCase() !== '/start') {
                await sendTelegramMessage(env.TELEGRAM_BOT_TOKEN, chatId, "درخواست شما برای تحلیل دریافت شد...");
            }
        }
    } else if (callbackQuery) {
        chatId = callbackQuery.message.chat.id;
        const callbackData = callbackQuery.data;
        const userState = await getUserState(env, chatId);
        
        await answerCallbackQuery(env.TELEGRAM_BOT_TOKEN, callbackQuery.id);

        if (callbackData.startsWith('topic_')) {
            triggerAction = false;
            const topic = callbackData.split('_')[1];
            if (!userState.selected_topics) userState.selected_topics = [];
            if (userState.selected_topics.includes(topic)) {
                userState.selected_topics = userState.selected_topics.filter(t => t !== topic);
            } else if (userState.selected_topics.length < 3) {
                userState.selected_topics.push(topic);
            } else {
                await answerCallbackQuery(env.TELEGRAM_BOT_TOKEN, callbackQuery.id, "خطا: فقط می‌توانید تا ۳ موضوع انتخاب کنید.", true);
            }
            await saveUserState(env, chatId, userState);
        } else {
            if (callbackData.startsWith('remove_execute:')) {
                const urlToRemove = callbackData.substring('remove_execute:'.length);
                if (userState.user_feeds) userState.user_feeds = userState.user_feeds.filter(feed => feed.url !== urlToRemove);
                await saveUserState(env, chatId, userState);
                await sendTelegramMessage(env.TELEGRAM_BOT_TOKEN, chatId, "منبع با موفقیت حذف شد.");
                payload = { type: 'callback', data: 'display_feeds', user_feeds: userState.user_feeds || [] };
            } else if (callbackData.startsWith('confirm_add:')) {
                // Extract the URL directly from the callback_data string.
                const urlToAdd = callbackData.substring('confirm_add:'.length);
                
                if (urlToAdd) {
                    if (!userState.user_feeds) {
                        userState.user_feeds = [];
                    }
                    // Avoid adding duplicates
                    if (!userState.user_feeds.some(feed => feed.url === urlToAdd)) {
                        // Add the new feed. For now, use the URL as a temporary name.
                        userState.user_feeds.push({ name: urlToAdd, url: urlToAdd });
                        console.log(`Added new feed for user ${chatId}: ${urlToAdd}`);
                    }
                }
                
                await saveUserState(env, chatId, userState);
                // Trigger the action to redisplay the updated feed list
                payload = { type: 'callback', data: 'display_feeds', user_feeds: userState.user_feeds || [] };
            } else if (callbackData === 'add_feed') {
                userState.status = 'awaiting_feed_url';
                await saveUserState(env, chatId, userState);
                payload = { type: 'callback', data: 'add_feed', user_feeds: userState.user_feeds || [] };
            } else if (['topics_done', 'cancel_add', 'remove_feed', 'feeds_done', 'display_feeds'].includes(callbackData)) {
                if (callbackData === 'topics_done' && (!userState.user_feeds || userState.user_feeds.length === 0)) {
                    userState.user_feeds = DEFAULT_FEEDS; // Use hardcoded constant
                    console.log(`Initialized user ${chatId} with ${DEFAULT_FEEDS.length} default feeds.`);
                    await saveUserState(env, chatId, userState);
                }
                payload = { type: 'callback', data: callbackData, user_feeds: userState.user_feeds || [] };
            } else {
                payload = { type: 'callback', data: callbackData, user_feeds: userState.user_feeds || [] };
            }
        }
    }

    if (!chatId || String(chatId) !== env.TELEGRAM_CHAT_ID) {
        return new Response('Unauthorized', { status: 403 });
    }
    if (payload && triggerAction) {
        await triggerGitHubActions(env, payload);
    }
    
    return new Response('OK', { status: 200 });
}

export default {
  async fetch(request, env) {
    try {
      return await handleRequest(request, env);
    } catch (e) {
      console.error('Critical error in worker:', e);
      const body = await request.text().catch(() => "");
      try {
        const jsonBody = JSON.parse(body);
        const chatId = jsonBody?.message?.chat?.id || jsonBody?.callback_query?.message?.chat?.id;
        if (chatId) {
          await sendTelegramMessage(env.TELEGRAM_BOT_TOKEN, chatId, "یک خطای بحرانی در سرور رخ داده است.");
        }
      } catch (notifyError) {
        console.error('Failed to parse body or send error notification:', notifyError);
      }
      return new Response('Internal Server Error', { status: 500 });
    }
  }
};