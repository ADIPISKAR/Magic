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
npx wrangler secret put TELEGRAM_CHAT_ID
npx wrangler secret put BOT_API_SECRET
npm run deploy
```

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
- Requests require `X-Bot-Api-Secret` and are limited to a 16 KiB JSON body.
- The Worker does not persist lead data and does not log request bodies.
- Only `POST /api/leads` sends a Telegram message; `GET /health` is read-only.
