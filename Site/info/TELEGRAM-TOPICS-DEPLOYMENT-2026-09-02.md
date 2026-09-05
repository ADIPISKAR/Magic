# Telegram topics deployment — 2 September 2026

Production notifications now use the forum group «Магия - SEO»:

- Laravel leads: Cloudflare Worker → topic «Заявки»;
- Python SEO reports: systemd → authenticated Cloudflare Worker gateway → topic «SEO».

The existing Telegram bot is reused. Its token remains an encrypted Cloudflare
secret; the Python host stores only a separate gateway secret. No destination
identifier is accepted from an HTTP request body, and the legacy
`TELEGRAM_CHAT_ID` is not a fallback.

## Production state

- Cloudflare Worker: `magia-telegram-leads`, deployed version
  `1b1e46b9-c57a-4d5d-80ae-b0e260dfe957`.
- Worker secrets: `BOT_API_SECRET`, `SEO_API_SECRET`, `TELEGRAM_BOT_TOKEN`,
  `TELEGRAM_GROUP_CHAT_ID`, `TELEGRAM_LEADS_THREAD_ID`,
  `TELEGRAM_SEO_THREAD_ID`.
- Server environment: `/etc/magia/seo-telegram.env`, mode `600`, directory mode
  `700`; the file contains the gateway URL/secret, allowed user IDs and enable
  flag, but no Telegram bot token.
- Daily timer: `magia-seo-daily.timer`, 08:00 Europe/Moscow.
- Weekly timer: `magia-seo-weekly.timer`, Monday 09:00 Europe/Moscow.
- Both timers are enabled, active and persistent across missed boots.
- Private reports: `/var/www/magia/Site/storage/app/private/seo-reports`, owned
  by `www-data`, mode `700`.

The server currently has no GSC, Metrika or Wordstat credentials. Scheduled
reports therefore contain the live five-page technical audit. The notification
transport already supports weekly reports, position changes, TOP-10 entry/exit,
strong growth/drop, Metrika, Wordstat, service errors and manual checks when
their collectors are configured.

## Verification

- production Laravel lead request returned HTTP 202 and appeared once in topic
  «Заявки»;
- no lead appeared in topic «SEO» or the old group;
- Python daily and weekly systemd services completed with status 0 and their
  reports appeared in topic «SEO»;
- Worker tests: 3 passed;
- Python tests: 17 passed;
- Laravel tests: 14 passed, 270 assertions;
- PHP syntax checks passed;
- Worker health returned `ok`; temporary diagnostic endpoints and secrets were
  removed.

## Backup and rollback

The closed server backup is `/root/magic-telegram-topics-20260902` (mode `700`).
It contains the previous TelegramBot/Worker files, the prior TelegramBot `.env`,
deployment payloads and staging copies. A rollback must also disable/remove the
four `magia-seo-*` systemd units, remove `/etc/magia/seo-telegram.env`, restore
the backed-up repository files and bot environment, and roll the Cloudflare
Worker back to the selected pre-gateway version. Do not delete the old Telegram
group or its history.
