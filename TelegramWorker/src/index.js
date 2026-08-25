const MAX_BODY_BYTES = 16 * 1024;

export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    if (request.method === 'GET' && url.pathname === '/health') {
      return jsonResponse({ status: 'ok' });
    }

    if (request.method !== 'POST' || url.pathname !== '/api/leads') {
      return jsonResponse({ message: 'Not found' }, 404);
    }

    if (!env.BOT_API_SECRET || !env.TELEGRAM_BOT_TOKEN || !env.TELEGRAM_CHAT_ID) {
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
          chat_id: env.TELEGRAM_CHAT_ID,
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
