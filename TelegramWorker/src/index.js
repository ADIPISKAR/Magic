const MAX_BODY_BYTES = 16 * 1024;
const MAX_NOTIFICATION_BODY_BYTES = 8 * 1024 * 1024; // SEO notifications can carry dashboard PNGs.
const SEO_EVENT_TITLES = {
  daily: 'Ежедневный SEO-отчёт',
  weekly: 'Еженедельный SEO-отчёт',
  position_change: 'Изменение позиций',
  top10_entry: 'Вход в TOP-10',
  top10_exit: 'Выход из TOP-10',
  strong_growth: 'Сильный рост',
  strong_drop: 'Сильное падение',
  metrika: 'Яндекс Метрика',
  wordstat: 'Wordstat',
  service_error: 'Ошибка SEO-сервиса',
  manual_check: 'Ручная SEO-проверка',
  other: 'SEO-уведомление',
  test: 'Проверка SEO-уведомлений',
};

export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    if (request.method === 'GET' && url.pathname === '/health') {
      return jsonResponse({ status: 'ok' });
    }

    if (request.method === 'POST' && url.pathname === '/api/seo-notifications') {
      return handleSeoNotification(request, env);
    }

    if (request.method === 'POST' && url.pathname === '/telegram/webhook') {
      return handleTelegramWebhook(request, env);
    }

    if (request.method === 'POST' && url.pathname === '/api/telegram-webhook/setup') {
      return handleTelegramWebhookSetup(request, env, url.origin);
    }

    if (request.method !== 'POST' || url.pathname !== '/api/leads') {
      return jsonResponse({ message: 'Not found' }, 404);
    }

    const groupChatId = normalizeIdentifier(env.TELEGRAM_GROUP_CHAT_ID);
    const leadsThreadId = normalizeThreadId(env.TELEGRAM_LEADS_THREAD_ID);
    if (!env.BOT_API_SECRET || !env.TELEGRAM_BOT_TOKEN || !groupChatId || !leadsThreadId) {
      return jsonResponse({ message: 'Bot configuration error.' }, 500);
    }

    const providedSecret = request.headers.get('X-Bot-Api-Secret') ?? '';
    if (!(await secretsMatch(env.BOT_API_SECRET, providedSecret))) {
      return jsonResponse({ message: 'Unauthorized' }, 401);
    }

    const contentLength = Number(request.headers.get('Content-Length') ?? '0');
    if (Number.isFinite(contentLength) && contentLength > MAX_BODY_BYTES) {
      return jsonResponse({ message: 'Request body is too large.' }, 413);
    }

    let payload;
    try {
      const body = await request.text();
      if (new TextEncoder().encode(body).byteLength > MAX_BODY_BYTES) {
        return jsonResponse({ message: 'Request body is too large.' }, 413);
      }
      payload = JSON.parse(body);
    } catch {
      return jsonResponse({ message: 'Invalid JSON body.' }, 400);
    }

    const name = normalizeField(payload?.name, 100);
    const phone = normalizeField(payload?.phone, 40);
    if (!name || !phone) {
      return jsonResponse({ message: 'Name and phone are required.' }, 422);
    }

    const lines = [
      '📩 Новая заявка',
      '',
      `👤 Имя: ${escapeHtml(name)}`,
      `📞 Телефон: ${escapeHtml(phone)}`,
    ];

    for (const field of ['message', 'source']) {
      const value = normalizeField(payload?.[field], 1000);
      if (value) {
        lines.push(`${escapeHtml(field)}: ${escapeHtml(value)}`);
      }
    }

    const telegramResponse = await fetch(
      `https://api.telegram.org/bot${env.TELEGRAM_BOT_TOKEN}/sendMessage`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: new URLSearchParams({
          chat_id: groupChatId,
          message_thread_id: leadsThreadId,
          text: lines.join('\n'),
          parse_mode: 'HTML',
        }),
      },
    );

    let telegramResult;
    try {
      telegramResult = await telegramResponse.json();
    } catch {
      telegramResult = null;
    }

    if (!telegramResponse.ok || !telegramResult?.ok) {
      return jsonResponse({ message: 'Unable to deliver lead.' }, 502);
    }

    return jsonResponse({ message: 'Lead accepted.' }, 202);
  },
};

async function handleTelegramWebhookSetup(request, env, origin) {
  if (!env.SEO_API_SECRET || !env.TELEGRAM_BOT_TOKEN || !env.TELEGRAM_WEBHOOK_SECRET) {
    return jsonResponse({ message: 'Bot configuration error.' }, 500);
  }
  const providedSecret = request.headers.get('X-Bot-Api-Secret') ?? '';
  if (!(await secretsMatch(env.SEO_API_SECRET, providedSecret))) {
    return jsonResponse({ message: 'Unauthorized' }, 401);
  }
  try {
    await telegramMethod(env, 'setWebhook', {
      url: origin + '/telegram/webhook',
      secret_token: env.TELEGRAM_WEBHOOK_SECRET,
      allowed_updates: ['message', 'callback_query'],
      drop_pending_updates: false,
    });
  } catch {
    return jsonResponse({ message: 'Unable to configure Telegram webhook.' }, 502);
  }
  return jsonResponse({ message: 'Telegram webhook configured.' }, 200);
}

async function handleTelegramWebhook(request, env) {
  if (!env.TELEGRAM_WEBHOOK_SECRET
      || !env.TELEGRAM_BOT_TOKEN
      || !env.SEO_BACKEND_URL
      || !env.SEO_BACKEND_SECRET) {
    return jsonResponse({ message: 'Bot configuration error.' }, 500);
  }
  const providedSecret = request.headers.get('X-Telegram-Bot-Api-Secret-Token') ?? '';
  if (!(await secretsMatch(env.TELEGRAM_WEBHOOK_SECRET, providedSecret))) {
    return jsonResponse({ message: 'Unauthorized' }, 401);
  }
  let update;
  try {
    update = await request.json();
  } catch {
    return jsonResponse({ message: 'Invalid JSON body.' }, 400);
  }
  const callback = update?.callback_query;
  const message = callback?.message ?? update?.message;
  const userId = Number(callback?.from?.id ?? message?.from?.id);
  const chatId = Number(message?.chat?.id);
  const allowedUsers = parseAllowedUsers(env.TELEGRAM_ALLOWED_USERS ?? '');
  if (!Number.isInteger(userId) || !allowedUsers.has(userId)
      || !Number.isInteger(chatId) || message?.chat?.type !== 'private') {
    if (callback?.id) {
      await telegramMethod(env, 'answerCallbackQuery', {
        callback_query_id: callback.id,
        text: 'Нет доступа.',
        show_alert: false,
      });
    }
    return jsonResponse({ message: 'Ignored.' }, 200);
  }
  const rawAction = typeof callback?.data === 'string' && callback.data.startsWith('seo:')
    ? callback.data.slice(4)
    : 'menu';
  const text = normalizeField(message?.text, 100);
  const action = callback ? rawAction : (
    /^\/(start|seo)(?:\s+seo)?$/i.test(text) || text === '🔎 Позиции' ? 'menu' : 'menu'
  );

  if (callback?.id) {
    await telegramMethod(env, 'answerCallbackQuery', { callback_query_id: callback.id });
  }

  // The dashboard/chart renders can take a moment (matplotlib + disk cache
  // lookups) -- if we're reacting to a button on an existing text message,
  // flip it to a status line first so the tap feels acknowledged immediately,
  // per the "never leave the user staring at nothing" UX requirement.
  const sourceMessageId = callback?.message?.message_id;
  const sourceHasText = typeof callback?.message?.text === 'string';
  let placeholderShown = false;
  if (sourceMessageId && sourceHasText) {
    try {
      await telegramMethod(env, 'editMessageText', {
        chat_id: chatId,
        message_id: sourceMessageId,
        text: '⏳ Формирую отчёт...',
      });
      placeholderShown = true;
    } catch {
      // Best-effort status update only; proceed regardless.
    }
  }

  let backendResponse;
  try {
    backendResponse = await fetch(env.SEO_BACKEND_URL.replace(/\/$/, '') + '/api/seo/telegram', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-SEO-Backend-Secret': env.SEO_BACKEND_SECRET,
      },
      body: JSON.stringify({
        action,
        requested_by: userId,
        _backend_secret: env.SEO_BACKEND_SECRET,
      }),
    });
  } catch {
    await settleWithText(env, {
      chatId, sourceMessageId, placeholderShown, text: 'SEO-сервис временно недоступен.',
    });
    return jsonResponse({ message: 'SEO backend unavailable.' }, 502);
  }
  let payload;
  try {
    payload = await backendResponse.json();
  } catch {
    payload = null;
  }
  if (!backendResponse.ok || !payload?.text) {
    await settleWithText(env, {
      chatId, sourceMessageId, placeholderShown, text: 'Не удалось получить SEO-отчёт.',
    });
    return jsonResponse({ message: 'SEO backend rejected the request.' }, 502);
  }

  const replyMarkup = Array.isArray(payload.keyboard)
    ? { inline_keyboard: payload.keyboard }
    : undefined;
  const photos = Array.isArray(payload.photos)
    ? payload.photos.filter((photo) => photo && typeof photo.base64 === 'string' && photo.base64)
    : [];

  if (photos.length > 0) {
    await sendPhotosMessage(env, { chatId, photos, caption: payload.text, replyMarkup });
    if (placeholderShown) {
      // The placeholder was a text message; it can't become a photo message,
      // so drop it now that the real (photo) report has been delivered.
      await telegramMethod(env, 'deleteMessage', { chat_id: chatId, message_id: sourceMessageId }).catch(() => {});
    }
  } else if (sourceMessageId && sourceHasText) {
    await telegramMethod(env, 'editMessageText', {
      chat_id: chatId,
      message_id: sourceMessageId,
      text: String(payload.text).slice(0, 3900),
      disable_web_page_preview: true,
      ...(replyMarkup ? { reply_markup: replyMarkup } : {}),
    });
  } else {
    await sendTextMessage(env, { chatId, text: payload.text, replyMarkup });
  }
  return jsonResponse({ message: 'Telegram SEO action accepted.' }, 200);
}

/** Replace the "⏳ Формирую отчёт..." placeholder (or send fresh) with a plain status line. */
async function settleWithText(env, { chatId, sourceMessageId, placeholderShown, text }) {
  if (placeholderShown && sourceMessageId) {
    await telegramMethod(env, 'editMessageText', { chat_id: chatId, message_id: sourceMessageId, text })
      .catch(() => sendTextMessage(env, { chatId, text }));
    return;
  }
  await sendTextMessage(env, { chatId, text });
}

function parseAllowedUsers(value) {
  const users = new Set();
  for (const item of String(value).split(/[\s,]+/).filter(Boolean)) {
    if (/^\d+$/.test(item) && Number(item) > 0) users.add(Number(item));
  }
  return users;
}

async function telegramMethod(env, method, payload) {
  const response = await fetch(`https://api.telegram.org/bot${env.TELEGRAM_BOT_TOKEN}/${method}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  let result;
  try {
    result = await response.json();
  } catch {
    result = null;
  }
  const description = String(result?.description || '');
  if ((!response.ok || !result?.ok)
      && method.startsWith('editMessage')
      && description.toLowerCase().includes('message is not modified')) {
    return result?.result ?? true;
  }
  if (!response.ok || !result?.ok) {
    throw new Error(`Telegram ${method} failed`);
  }
  return result.result;
}

function blobFromBase64(base64) {
  const binary = Uint8Array.from(atob(base64), (character) => character.charCodeAt(0));
  return new Blob([binary], { type: 'image/png' });
}

function firstLine(text) {
  const value = String(text || '').trim();
  const newlineIndex = value.indexOf('\n');
  return newlineIndex === -1 ? value : value.slice(0, newlineIndex);
}

/** @param {{chatId:number, threadId?:string|null, text:string, replyMarkup?:object, parseMode?:string}} options */
async function sendTextMessage(env, { chatId, threadId, text, replyMarkup, parseMode }) {
  return telegramMethod(env, 'sendMessage', {
    chat_id: chatId,
    ...(threadId ? { message_thread_id: threadId } : {}),
    text: String(text).slice(0, 3900),
    disable_web_page_preview: true,
    ...(parseMode ? { parse_mode: parseMode } : {}),
    ...(replyMarkup ? { reply_markup: replyMarkup } : {}),
  });
}

/** A single Telegram photo message. Kept separate from the media-group path
 * below because sendPhoto (unlike sendMediaGroup) can carry an inline
 * keyboard directly, so the single-image case doesn't need a follow-up. */
async function sendPhotoMessage(env, { chatId, threadId, photo, caption, replyMarkup, parseMode }) {
  const form = new FormData();
  form.append('chat_id', String(chatId));
  if (threadId) form.append('message_thread_id', String(threadId));
  if (caption) form.append('caption', String(caption).slice(0, 900));
  if (parseMode) form.append('parse_mode', parseMode);
  form.append('photo', blobFromBase64(photo.base64), photo.filename || 'seo-chart.png');
  if (replyMarkup) form.append('reply_markup', JSON.stringify(replyMarkup));
  const response = await fetch(`https://api.telegram.org/bot${env.TELEGRAM_BOT_TOKEN}/sendPhoto`, {
    method: 'POST',
    body: form,
  });
  const result = await response.json().catch(() => null);
  if (!response.ok || !result?.ok) throw new Error('Telegram sendPhoto failed');
  return result.result;
}

async function sendMediaGroupMessage(env, { chatId, threadId, photos, caption, parseMode }) {
  const form = new FormData();
  form.append('chat_id', String(chatId));
  if (threadId) form.append('message_thread_id', String(threadId));
  const media = photos.slice(0, 10).map((photo, index) => {
    const attachName = `photo${index}`;
    form.append(attachName, blobFromBase64(photo.base64), photo.filename || `seo-chart-${index}.png`);
    return {
      type: 'photo',
      media: `attach://${attachName}`,
      ...(index === 0 && caption ? { caption: String(caption).slice(0, 900), ...(parseMode ? { parse_mode: parseMode } : {}) } : {}),
    };
  });
  form.append('media', JSON.stringify(media));
  const response = await fetch(`https://api.telegram.org/bot${env.TELEGRAM_BOT_TOKEN}/sendMediaGroup`, {
    method: 'POST',
    body: form,
  });
  const result = await response.json().catch(() => null);
  if (!response.ok || !result?.ok) throw new Error('Telegram sendMediaGroup failed');
  return result.result;
}

/** One photo -> sendPhoto (keyboard attaches directly). Several photos ->
 * sendMediaGroup (caption on the first image only), followed by a short
 * separate message carrying the keyboard, since Telegram does not support
 * reply_markup on a media group itself. */
async function sendPhotosMessage(env, { chatId, threadId, photos, caption, replyMarkup, parseMode }) {
  const list = Array.isArray(photos) ? photos.filter((photo) => photo && photo.base64) : [];
  if (list.length === 0) {
    return null;
  }
  if (list.length === 1) {
    return sendPhotoMessage(env, { chatId, threadId, photo: list[0], caption, replyMarkup, parseMode });
  }
  const result = await sendMediaGroupMessage(env, { chatId, threadId, photos: list, caption, parseMode });
  if (replyMarkup) {
    await sendTextMessage(env, { chatId, threadId, text: firstLine(caption) || '📌 Меню', replyMarkup });
  }
  return result;
}

async function handleSeoNotification(request, env) {
  const groupChatId = normalizeIdentifier(env.TELEGRAM_GROUP_CHAT_ID);
  const seoThreadId = normalizeThreadId(env.TELEGRAM_SEO_THREAD_ID);
  if (!env.SEO_API_SECRET || !env.TELEGRAM_BOT_TOKEN || !groupChatId || !seoThreadId) {
    return jsonResponse({ message: 'Bot configuration error.' }, 500);
  }

  const providedSecret = request.headers.get('X-Bot-Api-Secret') ?? '';
  if (!(await secretsMatch(env.SEO_API_SECRET, providedSecret))) {
    return jsonResponse({ message: 'Unauthorized' }, 401);
  }

  const contentLength = Number(request.headers.get('Content-Length') ?? '0');
  if (Number.isFinite(contentLength) && contentLength > MAX_NOTIFICATION_BODY_BYTES) {
    return jsonResponse({ message: 'Request body is too large.' }, 413);
  }

  let payload;
  try {
    const body = await request.text();
    if (new TextEncoder().encode(body).byteLength > MAX_NOTIFICATION_BODY_BYTES) {
      return jsonResponse({ message: 'Request body is too large.' }, 413);
    }
    payload = JSON.parse(body);
  } catch {
    return jsonResponse({ message: 'Invalid JSON body.' }, 400);
  }

  const kind = normalizeField(payload?.kind, 40);
  const message = normalizeField(payload?.message, 3200);
  const title = SEO_EVENT_TITLES[kind];
  if (!title || !message) {
    return jsonResponse({ message: 'A valid kind and message are required.' }, 422);
  }

  // Weekly/daily reports attach the dashboard PNG(s) so the group chat gets
  // the same visual-first report as the private bot, not a text wall.
  const photos = (Array.isArray(payload?.photos) ? payload.photos : [])
    .filter((item) => item && typeof item.base64 === 'string' && item.base64)
    .slice(0, 10)
    .map((item, index) => ({
      base64: item.base64,
      filename: normalizeField(item.filename, 120) || `seo-report-${index}.png`,
    }));

  const notificationKeyboard = buildNotificationKeyboard(env);
  const caption = `<b>${escapeHtml(title)}</b>\n\n${escapeHtml(message)}`;

  if (photos.length > 0) {
    try {
      await sendPhotosMessage(env, {
        chatId: groupChatId,
        threadId: seoThreadId,
        photos,
        caption,
        replyMarkup: notificationKeyboard ?? undefined,
        parseMode: 'HTML',
      });
    } catch {
      return jsonResponse({ message: 'Unable to deliver SEO notification.' }, 502);
    }

    return jsonResponse({ message: 'SEO notification accepted.' }, 202);
  }

  // Plain-text notifications keep the original direct sendMessage call
  // (form-encoded body) rather than routing through telegramMethod's JSON
  // transport -- purely a wire-format choice, kept stable on purpose.
  const telegramResponse = await fetch(
    `https://api.telegram.org/bot${env.TELEGRAM_BOT_TOKEN}/sendMessage`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: new URLSearchParams({
        chat_id: groupChatId,
        message_thread_id: seoThreadId,
        text: caption,
        parse_mode: 'HTML',
        disable_web_page_preview: 'true',
        ...(notificationKeyboard ? { reply_markup: JSON.stringify(notificationKeyboard) } : {}),
      }),
    },
  );
  let telegramResult;
  try {
    telegramResult = await telegramResponse.json();
  } catch {
    telegramResult = null;
  }
  return telegramResponse.ok && telegramResult?.ok
    ? jsonResponse({ message: 'SEO notification accepted.' }, 202)
    : jsonResponse({ message: 'Unable to deliver SEO notification.' }, 502);
}

function buildNotificationKeyboard(env) {
  const row = [];
  const username = String(env.TELEGRAM_BOT_USERNAME || '').trim().replace(/^@/, '');
  if (/^[A-Za-z0-9_]{5,}$/.test(username)) {
    row.push({ text: '🔎 SEO-меню', url: `https://t.me/${username}?start=seo` });
  }
  const dashboardUrl = String(env.SEO_DASHBOARD_PUBLIC_URL || '').trim();
  try {
    const parsed = new URL(dashboardUrl);
    if (parsed.protocol === 'https:') {
      row.push({ text: '🌐 Web dashboard', url: parsed.toString() });
    }
  } catch {
    // Optional dashboard shortcut is omitted when the URL is not configured.
  }
  return row.length ? { inline_keyboard: [row] } : null;
}

function normalizeIdentifier(value) {
  return typeof value === 'string' && /^-?\d+$/.test(value.trim()) ? value.trim() : '';
}

function normalizeThreadId(value) {
  const identifier = normalizeIdentifier(value);
  return identifier && Number(identifier) > 0 ? identifier : '';
}

function normalizeField(value, maxLength) {
  return typeof value === 'string' ? value.trim().slice(0, maxLength) : '';
}

function escapeHtml(value) {
  return value
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#039;');
}

async function secretsMatch(expected, provided) {
  if (!expected || !provided) {
    return false;
  }

  const encoder = new TextEncoder();
  const [expectedHash, providedHash] = await Promise.all([
    crypto.subtle.digest('SHA-256', encoder.encode(expected)),
    crypto.subtle.digest('SHA-256', encoder.encode(provided)),
  ]);

  const expectedBytes = new Uint8Array(expectedHash);
  const providedBytes = new Uint8Array(providedHash);
  let difference = 0;
  for (let index = 0; index < expectedBytes.length; index += 1) {
    difference |= expectedBytes[index] ^ providedBytes[index];
  }

  return difference === 0;
}

function jsonResponse(payload, status = 200) {
  return new Response(JSON.stringify(payload), {
    status,
    headers: {
      'Content-Type': 'application/json; charset=utf-8',
      'Cache-Control': 'no-store',
      'X-Content-Type-Options': 'nosniff',
    },
  });
}
