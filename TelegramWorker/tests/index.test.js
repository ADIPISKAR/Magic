import assert from 'node:assert/strict';
import test from 'node:test';

import worker from '../src/index.js';

const request = () => new Request('https://worker.test/api/leads', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'X-Bot-Api-Secret': 'shared-secret',
  },
  body: JSON.stringify({ name: 'Иван', phone: '+7 900 000-00-00' }),
});

test('routes a lead to the configured group topic', async () => {
  const originalFetch = globalThis.fetch;
  let telegramRequest;
  globalThis.fetch = async (url, options) => {
    telegramRequest = { url, options };
    return new Response(JSON.stringify({ ok: true }), {
      status: 200,
      headers: { 'Content-Type': 'application/json' },
    });
  };

  try {
    const response = await worker.fetch(request(), {
      BOT_API_SECRET: 'shared-secret',
      TELEGRAM_BOT_TOKEN: 'bot-token',
      TELEGRAM_GROUP_CHAT_ID: '-1001234567890',
      TELEGRAM_LEADS_THREAD_ID: '42',
    });

    assert.equal(response.status, 202);
    const body = new URLSearchParams(telegramRequest.options.body);
    assert.equal(body.get('chat_id'), '-1001234567890');
    assert.equal(body.get('message_thread_id'), '42');
    assert.match(body.get('text'), /Новая заявка/);
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test('does not fall back to the legacy destination', async () => {
  const response = await worker.fetch(request(), {
    BOT_API_SECRET: 'shared-secret',
    TELEGRAM_BOT_TOKEN: 'bot-token',
    TELEGRAM_CHAT_ID: '-1009999999999',
  });

  assert.equal(response.status, 500);
  assert.deepEqual(await response.json(), { message: 'Bot configuration error.' });
});

test('routes an SEO event only to the configured SEO topic', async () => {
  const originalFetch = globalThis.fetch;
  let telegramRequest;
  globalThis.fetch = async (url, options) => {
    telegramRequest = { url, options };
    return new Response(JSON.stringify({ ok: true }), {
      status: 200,
      headers: { 'Content-Type': 'application/json' },
    });
  };

  try {
    const response = await worker.fetch(new Request('https://worker.test/api/seo-notifications', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Bot-Api-Secret': 'seo-secret',
      },
      body: JSON.stringify({ kind: 'weekly', message: 'Проверка отчёта' }),
    }), {
      SEO_API_SECRET: 'seo-secret',
      TELEGRAM_BOT_TOKEN: 'bot-token',
      TELEGRAM_GROUP_CHAT_ID: '-1001234567890',
      TELEGRAM_SEO_THREAD_ID: '84',
      TELEGRAM_BOT_USERNAME: 'lovestachatbot',
      SEO_DASHBOARD_PUBLIC_URL: 'https://magiarnd.ru/seo-dashboard',
    });

    assert.equal(response.status, 202);
    const body = new URLSearchParams(telegramRequest.options.body);
    assert.equal(body.get('chat_id'), '-1001234567890');
    assert.equal(body.get('message_thread_id'), '84');
    assert.match(body.get('text'), /Еженедельный SEO-отчёт/);
    assert.deepEqual(JSON.parse(body.get('reply_markup')), {
      inline_keyboard: [[
        { text: '🔎 SEO-меню', url: 'https://t.me/lovestachatbot?start=seo' },
        { text: '🌐 Web dashboard', url: 'https://magiarnd.ru/seo-dashboard' },
      ]],
    });
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test('serves the private SEO menu through the protected backend', async () => {
  const originalFetch = globalThis.fetch;
  const calls = [];
  globalThis.fetch = async (url, options) => {
    calls.push({ url: String(url), options });
    if (String(url) === 'https://magiarnd.ru/api/seo/telegram') {
      assert.equal(options.headers['X-SEO-Backend-Secret'], 'backend-secret');
      assert.deepEqual(JSON.parse(options.body), {
        action: 'menu',
        requested_by: 123,
        _backend_secret: 'backend-secret',
      });
      return new Response(JSON.stringify({
        text: 'SEO menu',
        keyboard: [[{ text: '7 дней', callback_data: 'seo:period:7' }]],
      }), { status: 200, headers: { 'Content-Type': 'application/json' } });
    }
    return new Response(JSON.stringify({ ok: true, result: {} }), {
      status: 200,
      headers: { 'Content-Type': 'application/json' },
    });
  };

  try {
    const response = await worker.fetch(new Request('https://worker.test/telegram/webhook', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Telegram-Bot-Api-Secret-Token': 'webhook-secret',
      },
      body: JSON.stringify({
        message: {
          from: { id: 123 },
          chat: { id: 123, type: 'private' },
          text: '/start',
        },
      }),
    }), {
      TELEGRAM_WEBHOOK_SECRET: 'webhook-secret',
      TELEGRAM_BOT_TOKEN: 'bot-token',
      TELEGRAM_ALLOWED_USERS: '123,456',
      SEO_BACKEND_URL: 'https://magiarnd.ru',
      SEO_BACKEND_SECRET: 'backend-secret',
    });

    assert.equal(response.status, 200);
    const telegram = calls.find((call) => call.url.endsWith('/sendMessage'));
    assert.ok(telegram);
    const body = JSON.parse(telegram.options.body);
    assert.equal(body.chat_id, 123);
    assert.equal(body.text, 'SEO menu');
    assert.deepEqual(body.reply_markup.inline_keyboard[0][0], {
      text: '7 дней', callback_data: 'seo:period:7',
    });
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test('rejects Telegram webhook calls without the configured secret', async () => {
  const response = await worker.fetch(new Request('https://worker.test/telegram/webhook', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({}),
  }), {
    TELEGRAM_WEBHOOK_SECRET: 'webhook-secret',
    TELEGRAM_BOT_TOKEN: 'bot-token',
    SEO_BACKEND_URL: 'https://magiarnd.ru',
    SEO_BACKEND_SECRET: 'backend-secret',
  });

  assert.equal(response.status, 401);
});

test('sends a fresh message when a callback comes from a chart photo', async () => {
  const originalFetch = globalThis.fetch;
  const calls = [];
  globalThis.fetch = async (url, options) => {
    calls.push({ url: String(url), options });
    if (String(url) === 'https://magiarnd.ru/api/seo/telegram') {
      return new Response(JSON.stringify({
        text: 'SEO menu',
        keyboard: [[{ text: '📊 Сводка', callback_data: 'seo:section:summary:7' }]],
      }), { status: 200, headers: { 'Content-Type': 'application/json' } });
    }
    return new Response(JSON.stringify({ ok: true, result: {} }), {
      status: 200,
      headers: { 'Content-Type': 'application/json' },
    });
  };

  try {
    const response = await worker.fetch(new Request('https://worker.test/telegram/webhook', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Telegram-Bot-Api-Secret-Token': 'webhook-secret',
      },
      body: JSON.stringify({
        callback_query: {
          id: 'callback-id',
          from: { id: 123 },
          data: 'seo:menu',
          message: {
            message_id: 99,
            chat: { id: 123, type: 'private' },
            photo: [{ file_id: 'photo-id' }],
          },
        },
      }),
    }), {
      TELEGRAM_WEBHOOK_SECRET: 'webhook-secret',
      TELEGRAM_BOT_TOKEN: 'bot-token',
      TELEGRAM_ALLOWED_USERS: '123',
      SEO_BACKEND_URL: 'https://magiarnd.ru',
      SEO_BACKEND_SECRET: 'backend-secret',
    });

    assert.equal(response.status, 200);
    assert.ok(calls.some((call) => call.url.endsWith('/sendMessage')));
    assert.equal(calls.some((call) => call.url.endsWith('/editMessageText')), false);
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test('configures the Telegram webhook without exposing the bot token', async () => {
  const originalFetch = globalThis.fetch;
  let telegramRequest;
  globalThis.fetch = async (url, options) => {
    telegramRequest = { url: String(url), options };
    return new Response(JSON.stringify({ ok: true, result: true }), {
      status: 200,
      headers: { 'Content-Type': 'application/json' },
    });
  };
  try {
    const response = await worker.fetch(new Request('https://worker.test/api/telegram-webhook/setup', {
      method: 'POST',
      headers: { 'X-Bot-Api-Secret': 'seo-secret' },
    }), {
      SEO_API_SECRET: 'seo-secret',
      TELEGRAM_BOT_TOKEN: 'bot-token',
      TELEGRAM_WEBHOOK_SECRET: 'webhook-secret',
    });
    assert.equal(response.status, 200);
    assert.match(telegramRequest.url, /\/setWebhook$/);
    const body = JSON.parse(telegramRequest.options.body);
    assert.equal(body.url, 'https://worker.test/telegram/webhook');
    assert.equal(body.secret_token, 'webhook-secret');
    assert.equal(telegramRequest.url.includes('bot-token'), true);
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test('shows a status placeholder, then sends a single dashboard photo with its keyboard', async () => {
  const originalFetch = globalThis.fetch;
  const calls = [];
  globalThis.fetch = async (url, options) => {
    calls.push({ url: String(url), options });
    if (String(url) === 'https://magiarnd.ru/api/seo/telegram') {
      return new Response(JSON.stringify({
        text: '📊 SEO Dashboard · 7 дней',
        photos: [{ base64: 'aGVsbG8=', filename: 'dashboard-7.png' }],
        keyboard: [[{ text: '📈 Позиции', callback_data: 'seo:chart:positions:7' }]],
      }), { status: 200, headers: { 'Content-Type': 'application/json' } });
    }
    return new Response(JSON.stringify({ ok: true, result: {} }), {
      status: 200,
      headers: { 'Content-Type': 'application/json' },
    });
  };

  try {
    const response = await worker.fetch(new Request('https://worker.test/telegram/webhook', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Telegram-Bot-Api-Secret-Token': 'webhook-secret',
      },
      body: JSON.stringify({
        callback_query: {
          id: 'callback-id',
          from: { id: 123 },
          data: 'seo:dashboard:7',
          message: {
            message_id: 55,
            chat: { id: 123, type: 'private' },
            text: 'previous screen',
          },
        },
      }),
    }), {
      TELEGRAM_WEBHOOK_SECRET: 'webhook-secret',
      TELEGRAM_BOT_TOKEN: 'bot-token',
      TELEGRAM_ALLOWED_USERS: '123',
      SEO_BACKEND_URL: 'https://magiarnd.ru',
      SEO_BACKEND_SECRET: 'backend-secret',
    });

    assert.equal(response.status, 200);

    const placeholderEdit = calls.find((call) => call.url.endsWith('/editMessageText')
      && JSON.parse(call.options.body).text === '⏳ Формирую отчёт...');
    assert.ok(placeholderEdit, 'expected the placeholder status edit before the backend call');

    const photoCall = calls.find((call) => call.url.endsWith('/sendPhoto'));
    assert.ok(photoCall, 'expected a single sendPhoto call');
    assert.equal(photoCall.options.body.get('chat_id'), '123');
    assert.equal(photoCall.options.body.get('caption'), '📊 SEO Dashboard · 7 дней');
    assert.deepEqual(JSON.parse(photoCall.options.body.get('reply_markup')), {
      inline_keyboard: [[{ text: '📈 Позиции', callback_data: 'seo:chart:positions:7' }]],
    });

    const cleanup = calls.find((call) => call.url.endsWith('/deleteMessage'));
    assert.ok(cleanup, 'expected the text placeholder to be deleted once the photo was sent');
    assert.equal(JSON.parse(cleanup.options.body).message_id, 55);

    assert.equal(calls.some((call) => call.url.endsWith('/sendMediaGroup')), false);
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test('sends a 30-day dashboard as a media group plus a follow-up keyboard message', async () => {
  const originalFetch = globalThis.fetch;
  const calls = [];
  globalThis.fetch = async (url, options) => {
    calls.push({ url: String(url), options });
    if (String(url) === 'https://magiarnd.ru/api/seo/telegram') {
      return new Response(JSON.stringify({
        text: '📊 SEO Dashboard · 30 дней',
        photos: [
          { base64: 'aGVsbG8=', filename: 'dashboard-30-1.png' },
          { base64: 'd29ybGQ=', filename: 'dashboard-30-2.png' },
        ],
        keyboard: [[{ text: '🔄 Обновить', callback_data: 'seo:refresh' }]],
      }), { status: 200, headers: { 'Content-Type': 'application/json' } });
    }
    return new Response(JSON.stringify({ ok: true, result: {} }), {
      status: 200,
      headers: { 'Content-Type': 'application/json' },
    });
  };

  try {
    const response = await worker.fetch(new Request('https://worker.test/telegram/webhook', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Telegram-Bot-Api-Secret-Token': 'webhook-secret',
      },
      body: JSON.stringify({
        callback_query: {
          id: 'callback-id',
          from: { id: 123 },
          data: 'seo:dashboard:30',
          message: {
            message_id: 60,
            chat: { id: 123, type: 'private' },
            text: 'previous screen',
          },
        },
      }),
    }), {
      TELEGRAM_WEBHOOK_SECRET: 'webhook-secret',
      TELEGRAM_BOT_TOKEN: 'bot-token',
      TELEGRAM_ALLOWED_USERS: '123',
      SEO_BACKEND_URL: 'https://magiarnd.ru',
      SEO_BACKEND_SECRET: 'backend-secret',
    });

    assert.equal(response.status, 200);

    const mediaGroupCall = calls.find((call) => call.url.endsWith('/sendMediaGroup'));
    assert.ok(mediaGroupCall, 'expected a sendMediaGroup call for two photos');
    const media = JSON.parse(mediaGroupCall.options.body.get('media'));
    assert.equal(media.length, 2);
    assert.equal(media[0].caption, '📊 SEO Dashboard · 30 дней');
    assert.equal(media[1].caption, undefined);
    assert.equal(calls.some((call) => call.url.endsWith('/sendPhoto')), false);

    const followUp = calls.find((call) => call.url.endsWith('/sendMessage')
      && JSON.parse(call.options.body).reply_markup);
    assert.ok(followUp, 'expected a follow-up sendMessage carrying the keyboard');
    assert.deepEqual(JSON.parse(followUp.options.body).reply_markup, {
      inline_keyboard: [[{ text: '🔄 Обновить', callback_data: 'seo:refresh' }]],
    });

    assert.ok(calls.some((call) => call.url.endsWith('/deleteMessage')));
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test('delivers a weekly SEO notification with its dashboard photo to the group topic', async () => {
  const originalFetch = globalThis.fetch;
  const calls = [];
  globalThis.fetch = async (url, options) => {
    calls.push({ url: String(url), options });
    return new Response(JSON.stringify({ ok: true, result: {} }), {
      status: 200,
      headers: { 'Content-Type': 'application/json' },
    });
  };

  try {
    const response = await worker.fetch(new Request('https://worker.test/api/seo-notifications', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Bot-Api-Secret': 'seo-secret',
      },
      body: JSON.stringify({
        kind: 'weekly',
        message: 'Итоги недели',
        photos: [{ base64: 'aGVsbG8=', filename: 'weekly-dashboard.png' }],
      }),
    }), {
      SEO_API_SECRET: 'seo-secret',
      TELEGRAM_BOT_TOKEN: 'bot-token',
      TELEGRAM_GROUP_CHAT_ID: '-1001234567890',
      TELEGRAM_SEO_THREAD_ID: '84',
    });

    assert.equal(response.status, 202);
    const photoCall = calls.find((call) => call.url.endsWith('/sendPhoto'));
    assert.ok(photoCall, 'expected the weekly report photo to be sent');
    assert.equal(photoCall.options.body.get('chat_id'), '-1001234567890');
    assert.equal(photoCall.options.body.get('message_thread_id'), '84');
    assert.match(photoCall.options.body.get('caption'), /Еженедельный SEO-отчёт/);
    assert.equal(calls.some((call) => call.url.endsWith('/sendMessage')), false);
  } finally {
    globalThis.fetch = originalFetch;
  }
});
