# Telegram Worker

Cloudflare Worker accepts leads from the Laravel site and sends them to the
Telegram Bot API outside the Russian hosting network. It replaces the local
`TelegramBot` PHP service without changing the site's `/api/leads` contract.

## Deploy

Requirements: a free Cloudflare account and Node.js.

```powershell
cd TelegramWorker
npm install
npx wrangler login
npx wrangler secret put TELEGRAM_BOT_TOKEN
npx wrangler secret put TELEGRAM_GROUP_CHAT_ID
npx wrangler secret put TELEGRAM_LEADS_THREAD_ID
npx wrangler secret put TELEGRAM_SEO_THREAD_ID
npx wrangler secret put BOT_API_SECRET
npx wrangler secret put SEO_API_SECRET
npx wrangler secret put TELEGRAM_WEBHOOK_SECRET
npx wrangler secret put TELEGRAM_ALLOWED_USERS
npx wrangler secret put SEO_BACKEND_URL
npx wrangler secret put SEO_BACKEND_SECRET
npm run deploy
```

Non-secret Worker variables used for navigation buttons:

- `TELEGRAM_BOT_USERNAME` — bot username without `@`;
- `SEO_DASHBOARD_PUBLIC_URL=https://magiarnd.ru/seo-dashboard`.

Use the same `BOT_API_SECRET` value that is already configured in `Site/.env`.
Do not add tokens or secrets to `wrangler.jsonc` or Git.

Wrangler prints a URL similar to:

```text
https://magia-telegram-leads.<account-subdomain>.workers.dev
```

Verify the public health endpoint:

```powershell
Invoke-RestMethod https://magia-telegram-leads.<account-subdomain>.workers.dev/health
```

Then update the production Laravel environment:

```dotenv
BOT_API_URL=https://magia-telegram-leads.<account-subdomain>.workers.dev
```

Run `php artisan config:clear` from `Site` after changing the environment.

## Security

- Telegram credentials and the shared API secret are stored as encrypted
  Cloudflare Worker secrets.
- `TELEGRAM_GROUP_CHAT_ID` identifies the forum group «Магия SEO», while
  `TELEGRAM_LEADS_THREAD_ID` identifies its «Заявки» topic. Both are required;
  the legacy `TELEGRAM_CHAT_ID` is deliberately not used as a fallback.
- `POST /api/seo-notifications` uses a separate `SEO_API_SECRET` and always
  sends to `TELEGRAM_SEO_THREAD_ID`; it never accepts a destination from the
  request body. This lets the production Python process reuse the existing bot
  when direct Telegram API access is blocked by the hosting network.
- `POST /telegram/webhook` is authenticated with Telegram's webhook secret,
  accepts only private chats from `TELEGRAM_ALLOWED_USERS`, and requests a
  prepared read-only dashboard from Laravel using `SEO_BACKEND_SECRET`.
- The Worker never receives Topvisor, Webmaster or Metrika credentials. The
  Laravel endpoint cannot start a paid Topvisor check and does not use the
  production Laravel database.
- Requests require `X-Bot-Api-Secret` and are limited to a 16 KiB JSON body.
- The Worker does not persist lead data and does not log request bodies.
- Only `POST /api/leads` and authenticated `POST /api/seo-notifications` send
  Telegram messages; `GET /health` is read-only.
