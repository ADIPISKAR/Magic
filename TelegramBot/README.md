# TelegramBot

Небольшой PHP HTTP-сервис без базы данных. Он принимает заявки от Laravel и отправляет их в Telegram-канал через Bot API.

## Установка

Требования: PHP 8.2+, расширение cURL и Composer.

```powershell
composer install
Copy-Item .env.example .env
```

Заполните `.env`:

```dotenv
TELEGRAM_BOT_TOKEN=токен_от_BotFather
TELEGRAM_CHAT_ID=-1001234567890
BOT_API_SECRET=длинный_случайный_секрет
BOT_API_HOST=127.0.0.1
BOT_API_PORT=8080
```

`TELEGRAM_CHAT_ID` намеренно не задан: укажите ID своего канала. Добавьте бота в канал администратором с правом публикации сообщений.

## Запуск

Из папки `TelegramBot`:

```powershell
php -S 127.0.0.1:8080 -t public public/index.php
```

## Проверка тестовой заявки

```powershell
$headers = @{ 'Content-Type' = 'application/json'; 'X-Bot-Api-Secret' = 'ваш BOT_API_SECRET' }
$body = '{"name":"Иван","phone":"+7 900 000-00-00"}'
Invoke-RestMethod -Uri http://127.0.0.1:8080/api/leads -Method Post -Headers $headers -Body $body
```

После успешного ответа `Lead accepted.` сообщение появится в канале. Ошибки пишутся в стандартный PHP error log.

## Интеграция с Site

В `.env` Laravel добавьте:

```dotenv
BOT_API_URL=http://127.0.0.1:8080
BOT_API_SECRET=тот_же_секрет_что_в_TelegramBot
```

Laravel отправляет POST `/api/leads` на локальный адрес сайта, а сервер Site пересылает заявку в `TelegramBot` с заголовком `X-Bot-Api-Secret`.
