// cloudflare-worker/index.js (Final Corrected Version)
// =================================================================
// Default Feeds Configuration (Hardcoded)
// =================================================================
const DEFAULT_FEEDS = [
    {"name":"Lenny's Newsletter","url":"https://www.lennysnewsletter.com/feed", "tags": ["pm", "growth"]},
    {"name":"Reforge","url":"https://www.reforge.com/blog/rss.xml", "tags": ["pm", "growth"]},
    {"name":"SaaStr","url":"https://www.saastr.com/feed/", "tags": ["saas", "funding", "growth"]},
    {"name":"First Round Review","url":"http://firstround.com/review/feed.xml", "tags": ["funding", "team", "pm"]},
    {"name":"Y Combinator","url":"https://www.ycombinator.com/blog/rss", "tags": ["funding", "growth"]},
    {"name":"a16z","url":"https://a16z.com/feed/", "tags": ["funding", "ai", "fintech"]},
    {"name":"AI Breakfast","url":"https://aibreakfast.beehiiv.com/feed", "tags": ["ai"]},
    {"name":"Ben's Bites","url":"https://www.bensbites.co/feed", "tags": ["ai"]},
    {"name":"DeepLearning.AI","url":"https://www.deeplearning.ai/the-batch/rss.xml", "tags": ["ai"]},
    {"name":"FinTech Futures","url":"https://www.fintechfutures.com/feed/", "tags": ["fintech"]},
    {"name":"Harvard Business Review","url":"https://hbr.org/feed", "tags": ["team", "pm"]},
    {"name":"Mind the Product","url":"https://www.mindtheproduct.com/feed/", "tags": ["pm"]},
    {"name":"TechCrunch","url":"https://techcrunch.com/feed/", "tags": ["funding", "ai", "saas"]},
    {"name":"CB Insights","url":"https://www.cbinsights.com/blog/rss/", "tags": ["ai", "fintech"]},
    {"name":"Product Hunt","url":"https://www.producthunt.com/feed.rss", "tags": ["pm", "growth"]}
];

// Helper functions (getUserState, saveUserState, etc.) remain the same...
// Omitting for brevity, they are correct in your version.

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
        // Ensure state properties exist
        userState.user_feeds = userState.user_feeds || [];
        userState.selected_topics = userState.selected_topics || [];

        if (userState.status === 'awaiting_feed_url') {
            payload = { type: 'feed_submission', url: message.text || '', user_feeds: userState.user_feeds, selected_topics: userState.selected_topics };
            userState.status = 'active';
            await saveUserState(env, chatId, userState);
        } else {
            payload = { type: 'message', text: message.text || '', first_name: message.from ? message.from.first_name : 'کاربر', user_feeds: userState.user_feeds, selected_topics: userState.selected_topics };
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
            const topic = callbackData.split('_')[1];
            if (!userState.selected_topics) userState.selected_topics = [];

            if (userState.selected_topics.includes(topic)) {
                userState.selected_topics = userState.selected_topics.filter(t => t !== topic);
            } else if (userState.selected_topics.length < 3) {
                userState.selected_topics.push(topic);
            } else {
                await answerCallbackQuery(env.TELEGRAM_BOT_TOKEN, callbackQuery.id, "خطا: فقط می‌توانید تا ۳ موضوع انتخاب کنید.", true);
                triggerAction = false;
            }
            await saveUserState(env, chatId, userState);

            if (triggerAction) {
                 payload = {
                    type: 'callback',
                    data: 'display_topics', // Command for Python to redraw
                    selected_topics: userState.selected_topics || [],
                    user_feeds: userState.user_feeds || []
                };
            }
        } else {
            // CRITICAL: Ensure user_feeds exists and is an array for all subsequent operations
            if (!userState.user_feeds) userState.user_feeds = [];

            if (callbackData.startsWith('remove_execute:')) {
                const urlToRemove = callbackData.substring('remove_execute:'.length);
                userState.user_feeds = userState.user_feeds.filter(feed => feed.url !== urlToRemove);
                await saveUserState(env, chatId, userState);
                await sendTelegramMessage(env.TELEGRAM_BOT_TOKEN, chatId, "منبع با موفقیت حذف شد.");
                payload = { type: 'callback', data: 'display_feeds', user_feeds: userState.user_feeds, selected_topics: userState.selected_topics || [] };
            } else if (callbackData.startsWith('confirm_add:')) {
                const urlToAdd = callbackData.substring('confirm_add:'.length);
                if (urlToAdd && !userState.user_feeds.some(feed => feed.url === urlToAdd)) {
                    userState.user_feeds.push({ name: urlToAdd, url: urlToAdd, tags: ["custom"] }); // Add custom tag
                }
                await saveUserState(env, chatId, userState);
                payload = { type: 'callback', data: 'display_feeds', user_feeds: userState.user_feeds, selected_topics: userState.selected_topics || [] };
            } else if (callbackData === 'topics_done') {
                if (userState.user_feeds.length === 0) {
                    userState.user_feeds = DEFAULT_FEEDS;
                    await saveUserState(env, chatId, userState);
                }
                payload = { type: 'callback', data: 'topics_done', user_feeds: userState.user_feeds, selected_topics: userState.selected_topics || [] };
            } else {
                // Generic handler for other simple callbacks
                payload = { type: 'callback', data: callbackData, user_feeds: userState.user_feeds, selected_topics: userState.selected_topics || [] };
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
// Default export and other helpers (omitted for brevity)