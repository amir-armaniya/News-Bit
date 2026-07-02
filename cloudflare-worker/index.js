// cloudflare-worker/index.js

// =================================================================
// Default Feeds Configuration (Hardcoded)
// =================================================================
const DEFAULT_FEEDS = [
    {"name":"Lenny's Newsletter","url":"https://www.lennysnewsletter.com/feed", "tags": ["pm", "growth"]},
    {"name":"SaaStr","url":"https://www.saastr.com/feed/", "tags": ["saas", "funding", "growth"]},
    {"name":"Y Combinator","url":"https://www.ycombinator.com/blog/rss", "tags": ["funding", "growth", "team"]},
    {"name":"FinTech Futures","url":"https://www.fintechfutures.com/feed/", "tags": ["fintech"]},
    {"name":"Harvard Business Review","url":"http://feeds.harvardbusiness.org/harvardbusiness/", "tags": ["team", "pm", "growth"]},
    {"name":"TechCrunch","url":"https://techcrunch.com/feed/", "tags": ["funding", "ai", "saas", "fintech", "general"]},
    {"name":"CB Insights","url":"https://www.cbinsights.com/blog/rss/", "tags": ["ai", "fintech", "funding", "general"]},
    {"name":"Product Hunt","url":"https://www.producthunt.com/feed", "tags": ["pm", "growth", "saas"]},
    {"name":"marktechpost","url":"https://www.marktechpost.com/feed/", "tags": ["ai"]},
    {"name":"google research","url":"https://research.google/blog/rss/", "tags": ["ai"]},
    {"name":"mit news","url":"https://news.mit.edu/rss/topic/artificial-intelligence2", "tags": ["ai"]},
    {"name":"oreilly (Ai-ML)","url":"https://www.oreilly.com/radar/topics/ai-ml/feed/", "tags": ["ai"]},
    {"name":"microsoft news","url":"https://news.microsoft.com/source/topics/ai/feed/", "tags": ["ai", "saas"]},
    {"name":"technologyreview (Ai)","url":"https://www.technologyreview.com/topic/artificial-intelligence/feed", "tags": ["ai"]},
    {"name":"kdnuggets","url":"https://www.kdnuggets.com/feed", "tags": ["ai"]},
    {"name":"machinelearningmastery","url":"https://machinelearningmastery.com/blog/feed/", "tags": ["ai"]},
    {"name":"finextra","url":"https://www.finextra.com/rss/channel.aspx?channel=ai", "tags": ["ai", "fintech"]},
    {"name":"OpenAI Blog","url":"https://openai.com/news/rss.xml", "tags": ["ai"]},
    {"name":"Google AI Blog","url":"https://blog.research.google/rss.xml", "tags": ["ai"]},
    {"name":"Microsoft AI Blog","url":"https://blogs.microsoft.com/ai/feed/", "tags": ["ai"]},
    {"name":"CB Insights Research","url":"https://www.cbinsights.com/research/feed/", "tags": ["ai", "fintech", "funding", "general"]},
    {"name":"The Fintech Times","url":"https://thefintechtimes.com/feed/", "tags": ["fintech"]},
    {"name":"Marty Cagan's Blog","url":"https://svpg.com/feed/", "tags": ["pm"]},
    {"name":"Product Plan Blog","url":"https://www.productplan.com/feed/", "tags": ["pm"]},
    {"name":"Harvard Business Review - Leadership","url":"https://hbr.org/topic/subject/leadership/feed", "tags": ["team"]},
    {"name":"GrowthHackers","url":"https://growthhackers.com/feed/", "tags": ["growth"]},
    {"name":"financemagnates (fintech)","url":"https://www.financemagnates.com/fintech/feed/", "tags": ["fintech"]},
    {"name":"fintechnews","url":"https://fintechnews.sg/feed/", "tags": ["fintech"]},
    {"name":"openviewpartners","url":"https://openviewpartners.com/blog/feed", "tags": ["saas", "growth", "funding"]},
    {"name":"techcrunch (fintech)","url":"https://techcrunch.com/tag/fintech/feed/", "tags": ["fintech", "funding"]},
    {"name":"nasdaq (FinTech)","url":"https://www.nasdaq.com/feed/rssoutbound?category=FinTech", "tags": ["fintech"]},
    {"name":"sparktoro","url":"https://sparktoro.com/blog/feed/", "tags": ["growth"]},
    {"name":"buffer","url":"https://buffer.com/resources/rss/", "tags": ["growth"]},
    {"name":"ahrefs","url":"https://ahrefs.com/blog/feed/", "tags": ["growth"]},
    {"name":"moz.com","url":"https://moz.com/feeds/blog.rss", "tags": ["growth"]},
    {"name":"saas-capital","url":"https://www.saas-capital.com/blog-posts/feed/", "tags": ["saas", "funding"]},
    {"name":"saasmag","url":"https://www.saasmag.com/feed/", "tags": ["saas"]},
    {"name":"helpscout","url":"https://www.helpscout.com/feed.xml", "tags": ["saas", "growth", "team"]},
    {"name":"kellblog","url":"https://kellblog.com/feed/", "tags": ["saas", "funding"]},
    {"name":"tomtunguz","url":"https://tomtunguz.com/index.xml", "tags": ["saas", "funding"]},
    {"name":"agile-operator","url":"https://agile-operator.com/feed/", "tags": ["saas", "growth"]},
    {"name":"crazyegg","url":"https://www.crazyegg.com/blog/feed/", "tags": ["growth"]},
    {"name":"saasmetrics","url":"https://saasmetrics.co/feed/", "tags": ["saas", "growth"]},
    {"name":"techcrunch (saas)","url":"https://techcrunch.com/tag/saas/feed/", "tags": ["saas", "funding"]},
    {"name":"chartmogul","url":"https://chartmogul.com/blog/feed/", "tags": ["saas", "growth"]}
];

// =================================================================
// Helper Functions
// =================================================================

async function getUserState(env, chatId) {
  if (!env.NEWSBIT_USERS) {
    console.error("CRITICAL: KV Namespace 'NEWSBIT_USERS' is not bound.");
    return { user_feeds: [], selected_topics: [], status: 'new' };
  }
  if (!chatId) return { user_feeds: [], selected_topics: [], status: 'new' };
  const stateStr = await env.NEWSBIT_USERS.get(String(chatId));
  try {
    const state = stateStr ? JSON.parse(stateStr) : {};
    state.user_feeds = state.user_feeds || [];
    state.selected_topics = state.selected_topics || [];
    return state;
  } catch (e) {
    console.error("Failed to parse user state for chatId:", chatId, e);
    return { user_feeds: [], selected_topics: [], status: 'new' };
  }
}

async function saveUserState(env, chatId, state) {
  if (!env.NEWSBIT_USERS) return;
  if (!chatId) return;
  try {
    await env.NEWSBIT_USERS.put(String(chatId), JSON.stringify(state));
  } catch (e) {
      console.error("Failed to save user state for chatId:", chatId, e);
  }
}

// Get all users for admin stats
async function getAllUsers(env) {
  if (!env.NEWSBIT_USERS) return [];
  const list = await env.NEWSBIT_USERS.list();
  const users = [];
  for (const key of list.keys) {
    const state = await env.NEWSBIT_USERS.get(key.name);
    if (state) {
      try {
        users.push({ chatId: key.name, state: JSON.parse(state) });
      } catch (e) {
        console.error("Failed to parse user state:", key.name, e);
      }
    }
  }
  return users;
}

// Increment usage counter
async function incrementUsage(env, chatId) {
  if (!env.USAGE_STATS) return;
  const key = `usage:${chatId}`;
  const current = await env.USAGE_STATS.get(key);
  const count = current ? parseInt(current) + 1 : 1;
  await env.USAGE_STATS.put(key, count.toString());
  
  // Also track total
  const totalKey = 'total_analyses';
  const total = await env.USAGE_STATS.get(totalKey);
  await env.USAGE_STATS.put(totalKey, ((total ? parseInt(total) : 0) + 1).toString());
}

// Get usage stats for admin
async function getUsageStats(env) {
  if (!env.USAGE_STATS) {
    return { total: 0, users: {} };
  }
  const total = await env.USAGE_STATS.get('total_analyses') || '0';
  const list = await env.USAGE_STATS.list();
  const userStats = {};
  
  for (const key of list.keys) {
    if (key.name.startsWith('usage:')) {
      const chatId = key.name.replace('usage:', '');
      const count = await env.USAGE_STATS.get(key.name) || '0';
      userStats[chatId] = parseInt(count);
    }
  }
  
  return { total: parseInt(total), users: userStats };
}

async function triggerGitHubActions(env, payload) {
  const workflowFile = env.GITHUB_WORKFLOW || 'news-bit.yml';
  const gitBranch = env.GITHUB_BRANCH || 'main';
  const GITHUB_API_URL = `https://api.github.com/repos/${env.GITHUB_REPO}/actions/workflows/${workflowFile}/dispatches`;
  try {
      const response = await fetch(GITHUB_API_URL, {
        method: 'POST',
        headers: { 'Authorization': `token ${env.GITHUB_TOKEN}`, 'Accept': 'application/vnd.github.v3+json', 'Content-Type': 'application/json', 'User-Agent': 'Cloudflare-Worker' },
        body: JSON.stringify({ ref: gitBranch, inputs: { on_demand_input: JSON.stringify(payload) } })
      });
      if (response.status !== 204) {
        console.error(`Failed to trigger GitHub Actions: ${response.status} ${await response.text()}`);
      } else {
        console.log("Successfully triggered GitHub Actions with payload:", JSON.stringify(payload));
      }
  } catch (e) {
      console.error("Error triggering GitHub Actions:", e);
  }
}

async function sendTelegramMessage(botToken, chatId, text) {
  if (!chatId) return;
  const url = `https://api.telegram.org/bot${botToken}/sendMessage`;
  try {
    const response = await fetch(url, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ chat_id: String(chatId), text: text }) });
    if (!response.ok) {
        console.error(`Telegram API error (sendMessage): ${response.status} ${await response.text()}`);
    }
  } catch (e) {
      console.error("Error sending Telegram message:", e);
  }
}

async function answerCallbackQuery(botToken, callbackQueryId, text = null, show_alert = false) {
  const url = `https://api.telegram.org/bot${botToken}/answerCallbackQuery`;
  const payload = { callback_query_id: callbackQueryId };
  if (text) {
    payload.text = text;
    payload.show_alert = show_alert;
  }
  try {
      const response = await fetch(url, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
      if (!response.ok) {
        console.error(`Telegram API error (answerCallbackQuery): ${response.status} ${await response.text()}`);
      }
  } catch (e) {
      console.error("Error answering Telegram callback query:", e);
  }
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

    try {
        if (message) {
            chatId = message.chat.id;
            const userState = await getUserState(env, chatId);
            const userText = message.text || '';

            // Handle /admin command - check if user is admin
            if (userText.toLowerCase() === '/admin') {
                const adminId = env.ADMIN_CHAT_ID;
                if (adminId && String(chatId) !== adminId) {
                    await sendTelegramMessage(env.TELEGRAM_BOT_TOKEN, chatId, "You don't have permission to use this command.");
                    return new Response('OK', { status: 200 });
                }
                
                // Get stats
                const stats = await getUsageStats(env);
                let statsText = "📊 *Usage Statistics*\n\n";
                statsText += `Total Analyses: *${stats.total}*\n`;
                statsText += `Active Users: *${Object.keys(stats.users).length}*\n\n`;
                
                if (Object.keys(stats.users).length > 0) {
                    statsText += "📈 Per User:\n";
                    const sortedUsers = Object.entries(stats.users).sort((a, b) => b[1] - a[1]);
                    for (const [userId, count] of sortedUsers.slice(0, 10)) {
                        statsText += `• User ${userId.slice(-4)}...: ${count} analyses\n`;
                    }
                }
                
                await sendTelegramMessage(env.TELEGRAM_BOT_TOKEN, chatId, statsText);
                return new Response('OK', { status: 200 });
            }

            if (userState.status === 'awaiting_feed_url') {
                payload = { type: 'feed_submission', url: message.text || '', user_feeds: userState.user_feeds, selected_topics: userState.selected_topics, chatId: chatId };
                userState.status = 'active';
                await saveUserState(env, chatId, userState);
            } else {
                payload = { type: 'message', text: message.text || '', first_name: message.from ? message.from.first_name : 'User', user_feeds: userState.user_feeds, selected_topics: userState.selected_topics, chatId: chatId };
                if (payload.text && payload.text.toLowerCase() !== '/start' && payload.text.toLowerCase() !== '/admin') {
                    // Track usage for every analysis request
                    await incrementUsage(env, chatId);
                    await sendTelegramMessage(env.TELEGRAM_BOT_TOKEN, chatId, "Your request for analysis has been received...");
                }
            }
        } else if (callbackQuery) {
            chatId = callbackQuery.message.chat.id;
            const callbackData = callbackQuery.data;
            const userState = await getUserState(env, chatId);

            await answerCallbackQuery(env.TELEGRAM_BOT_TOKEN, callbackQuery.id);

            // Track usage for callback actions
            if (callbackData === 'activate_quick' || callbackData === 'activate_custom' || callbackData.startsWith('confirm_add:')) {
                await incrementUsage(env, chatId);
            }

            if (callbackData.startsWith('topic_')) {
                const topic = callbackData.split('_')[1];
                if (!Array.isArray(userState.selected_topics)) userState.selected_topics = [];

                if (userState.selected_topics.includes(topic)) {
                    userState.selected_topics = userState.selected_topics.filter(t => t !== topic);
                } else if (userState.selected_topics.length < 3) {
                    userState.selected_topics.push(topic);
                } else {
                    await answerCallbackQuery(env.TELEGRAM_BOT_TOKEN, callbackQuery.id, "Error: You can only select up to 3 topics.", true);
                    triggerAction = false;
                }

                await saveUserState(env, chatId, userState);

                if (triggerAction) {
                     payload = {
                        type: 'callback',
                        data: 'display_topics',
                        selected_topics: userState.selected_topics || [],
                        user_feeds: userState.user_feeds || [],
                        chatId: chatId
                    };
                }
            } else {
                if (!Array.isArray(userState.user_feeds)) userState.user_feeds = [];

                if (callbackData.startsWith('remove_execute:')) {
                    const urlToRemove = callbackData.substring('remove_execute:'.length);
                    userState.user_feeds = userState.user_feeds.filter(feed => feed.url !== urlToRemove);
                    await saveUserState(env, chatId, userState);
                    await sendTelegramMessage(env.TELEGRAM_BOT_TOKEN, chatId, "Source removed successfully.");
                    payload = { type: 'callback', data: 'display_feeds', user_feeds: userState.user_feeds, selected_topics: userState.selected_topics || [], chatId: chatId };
                } else if (callbackData.startsWith('confirm_add:')) {
                    const urlToAdd = callbackData.substring('confirm_add:'.length);
                    if (urlToAdd && !userState.user_feeds.some(feed => feed.url === urlToAdd)) {
                        userState.user_feeds.push({ name: urlToAdd, url: urlToAdd, tags: ["custom"] });
                    }
                    await saveUserState(env, chatId, userState);
                    payload = { type: 'callback', data: 'display_feeds', user_feeds: userState.user_feeds, selected_topics: userState.selected_topics || [], chatId: chatId };
                } else if (callbackData === 'add_feed') {
                    userState.status = 'awaiting_feed_url';
                    await saveUserState(env, chatId, userState);
                    payload = { type: 'callback', data: 'add_feed', user_feeds: userState.user_feeds, selected_topics: userState.selected_topics || [], chatId: chatId };
                } else if (callbackData === 'topics_done') {
                    if (userState.user_feeds.length === 0) {
                        userState.user_feeds = DEFAULT_FEEDS.map(feed => ({...feed}));
                        await saveUserState(env, chatId, userState);
                    }
                    payload = { type: 'callback', data: 'topics_done', user_feeds: userState.user_feeds, selected_topics: userState.selected_topics || [], chatId: chatId };
                } else {
                    payload = { type: 'callback', data: callbackData, user_feeds: userState.user_feeds, selected_topics: userState.selected_topics || [], chatId: chatId };
                }
            }
        } else {
             console.error("Received invalid request body structure:", JSON.stringify(body));
             return new Response('Invalid request', { status: 400 });
        }

        if (payload && triggerAction) {
            await triggerGitHubActions(env, payload);
        } else if (payload) {
             console.log("Action trigger skipped for payload:", JSON.stringify(payload));
        }

        return new Response('OK', { status: 200 });

    } catch (e) {
      console.error('Critical error in worker handleRequest:', e);
      const potentialChatId = message?.chat?.id || callbackQuery?.message?.chat?.id;
      if (potentialChatId) {
           try {
                await sendTelegramMessage(env.TELEGRAM_BOT_TOKEN, potentialChatId, "A critical error occurred while processing your request.");
           } catch (notifyError) {
                console.error('Failed to send error notification:', notifyError);
           }
      }
      return new Response('Internal Server Error', { status: 500 });
    }
}

// =================================================================
// Cron Handler: Auto News Detection (every 30 minutes)
// =================================================================

async function handleScheduled(env) {
  console.log("=== CRON TRIGGER: Auto News Detection ===");

  // Get all users who have auto_mode enabled
  const list = await env.NEWSBIT_USERS.list();
  const autoUsers = [];

  for (const key of list.keys) {
    try {
      const state = JSON.parse(await env.NEWSBIT_USERS.get(key.name));
      if (state && state.auto_mode === true) {
        autoUsers.push({ chatId: key.name, state });
      }
    } catch (e) {
      console.error("Failed to parse user state:", key.name, e);
    }
  }
  
  if (autoUsers.length === 0) {
    console.log("No users with auto_mode enabled. Skipping.");
    return;
  }
  
  console.log(`Found ${autoUsers.length} users with auto_mode enabled.`);
  
  // Fetch articles from all feeds
  const allArticles = await fetchAllArticles(env);
  
  if (allArticles.length === 0) {
    console.log("No new articles found.");
    return;
  }
  
  console.log(`Fetched ${allArticles.length} total articles.`);
  
  // Process for each user with auto_mode
  for (const user of autoUsers) {
    try {
      await processForUser(env, user.chatId, user.state, allArticles);
    } catch (e) {
      console.error(`Error processing for user ${user.chatId}:`, e);
    }
  }
  
  console.log("=== Cron job completed ===");
}

async function fetchAllArticles(env) {
  const processedKey = "processed_links";
  const processedLinksStr = await env.PROCESSED_ARTICLES.get(processedKey);
  const processedLinks = processedLinksStr ? JSON.parse(processedLinksStr) : [];
  
  const articles = [];
  const cutoff = Date.now() - 30 * 60 * 1000; // 30 minutes ago
  
  for (const feed of DEFAULT_FEEDS) {
    try {
      const response = await fetch(feed.url, {
        headers: { 'User-Agent': 'NewsBit-Bot/1.0' }
      });
      const text = await response.text();
      
      // Simple RSS parsing (extract items)
      const items = parseRSSItems(text);
      
      for (const item of items) {
        if (processedLinks.includes(item.link)) continue;
        
        // Check if article is recent (within 30 minutes)
        if (item.pubDate && new Date(item.pubDate).getTime() >= cutoff) {
          articles.push({
            title: item.title,
            link: item.link,
            summary: item.summary || '',
            source: feed.name
          });
          processedLinks.push(item.link);
        }
      }
    } catch (e) {
      console.error(`Error fetching feed ${feed.name}:`, e);
    }
  }
  
  // Save processed links (keep last 1000)
  const trimmed = processedLinks.slice(-1000);
  await env.PROCESSED_ARTICLES.put(processedKey, JSON.stringify(trimmed));
  
  return articles;
}

function parseRSSItems(xml) {
  const items = [];
  const itemRegex = /<item>([\s\S]*?)<\/item>/gi;
  let match;
  
  while ((match = itemRegex.exec(xml)) !== null) {
    const itemXml = match[1];
    const title = extractTag(itemXml, 'title');
    const link = extractTag(itemXml, 'link');
    const summary = extractTag(itemXml, 'description');
    const pubDate = extractTag(itemXml, 'pubDate');
    
    if (title && link) {
      items.push({ title, link, summary, pubDate });
    }
  }
  
  return items;
}

function extractTag(xml, tag) {
  const regex = new RegExp(`<${tag}[^>]*>(?:<!\\[CDATA\\[)?(.*?)(?:\\]\\]>)?<\\/${tag}>`, 'is');
  const match = xml.match(regex);
  return match ? match[1].trim() : null;
}

async function processForUser(env, chatId, userState, allArticles) {
  const language = userState.language || 'en';
  const selectedTopics = userState.selected_topics || [];
  
  // Filter articles by relevance using AI
  const relevantArticles = [];
  
  for (const article of allArticles.slice(0, 10)) { // Limit to 10 articles
    const isRelevant = await checkRelevance(env, article, selectedTopics);
    if (isRelevant) {
      relevantArticles.push(article);
    }
  }
  
  if (relevantArticles.length === 0) {
    console.log(`No relevant articles for user ${chatId}`);
    return;
  }
  
  // Process each relevant article
  for (const article of relevantArticles.slice(0, 3)) { // Limit to 3 articles per user
    const analysis = await analyzeArticle(env, article);
    
    if (analysis) {
      // Translate if needed
      let translatedAnalysis = analysis;
      if (language !== 'en') {
        translatedAnalysis = await translateAnalysis(env, analysis, language);
      }
      
      // Send to user
      await sendAnalysisToUser(env, chatId, translatedAnalysis, language);
    }
  }
}

async function checkRelevance(env, article, selectedTopics) {
  const apiKey = env.OPENROUTER_API_KEY;
  if (!apiKey) return true; // Default to relevant if no API key
  
  const topicStr = selectedTopics.length > 0 
    ? `Focus on these topics: ${selectedTopics.join(', ')}`
    : "Focus on SaaS, FinTech, AI, product management, funding, team building";
  
  const prompt = `Is this article relevant? ${topicStr}
Title: "${article.title}"
Summary: "${article.summary}"
Answer with only 'YES' or 'NO'.`;
  
  try {
    const response = await fetch("https://openrouter.ai/api/v1/chat/completions", {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${apiKey}`,
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        model: "openai/gpt-oss-20b:free",
        messages: [{ role: "user", content: prompt }],
        max_tokens: 10,
        temperature: 0.1
      })
    });
    
    const data = await response.json();
    const answer = data.choices?.[0]?.message?.content?.trim()?.toUpperCase() || '';
    return answer.includes('YES');
  } catch (e) {
    console.error("Relevance check failed:", e);
    return true;
  }
}

async function analyzeArticle(env, article) {
  const apiKey = env.OPENROUTER_API_KEY;
  if (!apiKey) return null;
  
  const prompt = `Analyze this news article and provide:
1. Comprehensive Summary
2. Contrarian View  
3. Practical Application
4. Glossary (key terms)

Title: "${article.title}"
Summary: "${article.summary}"

Format your response with these sections exactly:
[Comprehensive Summary]
[Contrarian View]
[Practical Application]
[Glossary]`;
  
  try {
    const response = await fetch("https://openrouter.ai/api/v1/chat/completions", {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${apiKey}`,
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        model: "openai/gpt-oss-20b:free",
        messages: [{ role: "user", content: prompt }],
        max_tokens: 1000
      })
    });
    
    const data = await response.json();
    const content = data.choices?.[0]?.message?.content || '';
    
    // Parse the response
    const sections = content.split(/\[(.*?)\]/g).filter(Boolean);
    const analysis = {};
    
    for (let i = 0; i < sections.length; i += 2) {
      const key = sections[i].toLowerCase().replace(/\s+/g, '_');
      const value = sections[i + 1]?.trim() || '';
      analysis[key] = value;
    }
    
    return {
      title: article.title,
      link: article.link,
      summary: analysis['comprehensive_summary'] || article.summary,
      contrarian: analysis['contrarian_view'] || '',
      practical: analysis['practical_application'] || '',
      glossary: analysis['glossary'] || ''
    };
  } catch (e) {
    console.error("Analysis failed:", e);
    return null;
  }
}

async function translateAnalysis(env, analysis, targetLang) {
  const apiKey = env.OPENROUTER_API_KEY;
  if (!apiKey) return analysis;
  
  const langNames = { 'fa': 'Persian/Farsi', 'ar': 'Arabic' };
  const targetName = langNames[targetLang] || 'English';
  
  const textToTranslate = `Title: ${analysis.title}
Summary: ${analysis.summary}
Contrarian: ${analysis.contrarian}
Practical: ${analysis.practical}
Glossary: ${analysis.glossary}`;
  
  try {
    const response = await fetch("https://openrouter.ai/api/v1/chat/completions", {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${apiKey}`,
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        model: "openai/gpt-oss-20b:free",
        messages: [{
          role: "user",
          content: `Translate to ${targetName}. Keep format:\n${textToTranslate}`
        }],
        max_tokens: 2000,
        temperature: 0.3
      })
    });
    
    const data = await response.json();
    const translated = data.choices?.[0]?.message?.content || textToTranslate;
    
    // Parse translated content back
    const lines = translated.split('\n');
    return {
      title: lines.find(l => l.startsWith('Title:'))?.replace('Title:', '')?.trim() || analysis.title,
      link: analysis.link,
      summary: lines.find(l => l.startsWith('Summary:'))?.replace('Summary:', '')?.trim() || analysis.summary,
      contrarian: lines.find(l => l.startsWith('Contrarian:'))?.replace('Contrarian:', '')?.trim() || analysis.contrarian,
      practical: lines.find(l => l.startsWith('Practical:'))?.replace('Practical:', '')?.trim() || analysis.practical,
      glossary: lines.find(l => l.startsWith('Glossary:'))?.replace('Glossary:', '')?.trim() || analysis.glossary
    };
  } catch (e) {
    console.error("Translation failed:", e);
    return analysis;
  }
}

async function sendAnalysisToUser(env, chatId, analysis, language) {
  const langConfig = {
    'fa': { summary: 'خلاصه جامع', contrarian: 'دیدگاه متفاوت', practical: 'کاربرد عملی', glossary: 'واژه‌نامه' },
    'ar': { summary: 'ملخص شامل', contrarian: 'وجهة نظر معارضة', practical: 'التطبيق العملي', glossary: 'المسرد' },
    'en': { summary: 'Comprehensive Summary', contrarian: 'Contrarian View', practical: 'Practical Application', glossary: 'Glossary' }
  };
  
  const headers = langConfig[language] || langConfig['en'];
  
  const text = `*__${analysis.title}__*

*${headers.summary}:*
${analysis.summary}

*${headers.contrarian}:*
${analysis.contrarian}

*${headers.practical}:*
${analysis.practical}

*${headers.glossary}:*
${analysis.glossary}

[Source Link](${analysis.link})`;
  
  await sendTelegramMessage(env.TELEGRAM_BOT_TOKEN, chatId, text);
}

// =================================================================
// Main Exported Handler
// =================================================================

export default {
  async fetch(request, env) {
      return await handleRequest(request, env);
  },
  
  async scheduled(event, env, ctx) {
      ctx.waitUntil(handleScheduled(env));
  }
};