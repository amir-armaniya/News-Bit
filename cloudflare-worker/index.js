// =================================================================
// Helper Functions
// =================================================================

/** @typedef {{status?: string, selected_topics?: string[], custom_feeds?: string[]}} UserState */

/** Fetches a user's state from the KV store. */
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

/** Saves a user's state to the KV store. */
async function saveUserState(env, chatId, state) {
  if (!env.STRATEGIC_RADAR_USERS) return;
  if (!chatId) return;
  await env.STRATEGIC_RADAR_USERS.put(String(chatId), JSON.stringify(state));
}

/** Triggers the GitHub Actions workflow. */
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

/** Sends a simple text message via Telegram API. */
async function sendTelegramMessage(botToken, chatId, text) {
  if (!chatId) return;
  const url = `https://api.telegram.org/bot${botToken}/sendMessage`;
  await fetch(url, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ chat_id: String(chatId), text: text }) });
}

/** Answers a Telegram callback query. */
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
    const url = new URL(request.url);
    
    // Handle feed updates endpoint
    if (url.pathname === '/update-feeds' && request.method === 'POST') {
        try {
            const { chatId, custom_feeds } = await request.json();
            if (chatId && custom_feeds) {
                const userState = await getUserState(env, chatId);
                userState.custom_feeds = custom_feeds;
                await saveUserState(env, chatId, userState);
            }
            return new Response('OK', { status: 200 });
        } catch (e) {
            return new Response('Invalid request', { status: 400 });
        }
    }

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
            payload = { type: 'feed_submission', url: message.text || '' };
            userState.status = 'active';
            await saveUserState(env, chatId, userState);
        } else if (userState.status === 'awaiting_feed_deletion') {
            // Process feed deletion numbers input
            payload = { type: 'feed_deletion_request', numbers: message.text || '' };
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
        
        await answerCallbackQuery(env.TELEGRAM_BOT_TOKEN, callbackQuery.id); // Acknowledge immediately

        if (callbackData.startsWith('topic_')) {
            triggerAction = false; // Handle entirely within the worker
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
            // All other callbacks trigger a GitHub Action
            if (callbackData.startsWith('remove_url:')) {
                const urlToRemove = callbackData.substring('remove_url:'.length);
                if (userState.custom_feeds) userState.custom_feeds = userState.custom_feeds.filter(url => url !== urlToRemove);
                await saveUserState(env, chatId, userState);
                payload = { type: 'callback', data: 'display_feeds', custom_feeds: userState.custom_feeds || [] };
            } else if (callbackData.startsWith('confirm_add:')) {
                const urlToAdd = callbackData.split(':')[1];
                if (!userState.custom_feeds) userState.custom_feeds = [];
                if (!userState.custom_feeds.includes(urlToAdd)) userState.custom_feeds.push(urlToAdd);
                await saveUserState(env, chatId, userState);
                payload = { type: 'callback', data: 'display_feeds', custom_feeds: userState.custom_feeds };
            } else if (callbackData === 'add_feed') {
                userState.status = 'awaiting_feed_url';
                await saveUserState(env, chatId, userState);
                payload = { type: 'callback', data: 'add_feed' };
            } else if (callbackData === 'remove_feed') {
                // Set state to await feed numbers input
                userState.status = 'awaiting_feed_deletion';
                await saveUserState(env, chatId, userState);
                payload = { type: 'callback', data: 'remove_feed_initiated' };
            } else if (['topics_done', 'cancel_add', 'feeds_done'].includes(callbackData)) {
                payload = { type: 'callback', data: callbackData, custom_feeds: userState.custom_feeds || [] };
            } else {
                payload = { type: 'callback', data: callbackData };
            }
        }
    }

    if (!chatId || String(chatId) !== env.TELEGRAM_CHAT_ID) {
        return new Response('Unauthorized', { status: 403 });
    }
    if (payload && triggerAction) {
        await triggerGitHubActions(env, payload);
    }
    
    // **THE CRITICAL FIX**: ALWAYS return a valid Response.
    return new Response('OK', { status: 200 });
}

// =================================================================
// Main Exported Handler
// =================================================================

export default {
  async fetch(request, env) {
    try {
      // **THE CRITICAL FIX**: Ensure the result of handleRequest is returned.
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