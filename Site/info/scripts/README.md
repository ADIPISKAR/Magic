# SEO-инструменты Magic

Адаптированы для Laravel и `https://magiarnd.ru`. Источник URL — действующий
`/sitemap.xml`, а не файлы `public_html`. Все команды ниже запускаются из `Site`.

## Проверка без доступов к Google

Достаточно Python 3.10+ и curl (в Windows он уже есть). Если curl отсутствует,
используется стандартная библиотека Python; проверка TLS остаётся включённой.

```powershell
python -X utf8 info/scripts/seo_audit.py
python -X utf8 info/scripts/seo_audit.py --fetch-base http://127.0.0.1:8000
python -X utf8 info/scripts/seo_daily.py
python -X utf8 -m unittest discover -s info/scripts/tests -v
```

Аудит проверяет HTTP 200 без редиректа, title, description, один H1, canonical,
og:url, noindex, JSON-LD и дубли метаданных между страницами sitemap.
Пустой sitemap, HTTP-сбой или чужой домен завершают проверку ошибкой.
Чтение sitemapindex поддерживается. Это технический аудит, он не определяет
позиции, частотность запросов, фактическую индексацию и Core Web Vitals.

Отчёты сохраняются в `storage/app/private/seo-reports/`, исключённую из Git.
Проверяйте `checked_at` и код завершения: оставшийся старый файл не означает,
что последний запуск завершился успешно.

## Search Console

1. Подтвердите `magiarnd.ru` в нужном Google-аккаунте. На 01.09.2026 в доступном
   браузерном аккаунте ресурс Magic отсутствовал; статистика другого сайта не использовалась.
2. В Google Cloud включите **Search Console API**. Indexing API не нужен.
3. Установите зависимости: `python -m pip install -r info/scripts/requirements.txt`.
4. Создайте Desktop OAuth client, сохраните его JSON как
   `info/scripts/credentials.json`, затем запустите `python info/scripts/gsc_auth.py`.
   Авторизация запрашивает только `webmasters.readonly`.
5. Альтернатива для сервера — `info/scripts/service_account.json` с уже выданным
   этому аккаунту доступом к нужному ресурсу GSC. Права владельца ради отчётов не требуются.
6. Ресурс и домен задаются в `seo-settings.json`. Локальные переопределения — в
   `seo-settings.local.json`; также доступны переменные `SEO_SITE_URL`, `GSC_PROPERTY`.
   Для URL-prefix используйте `"gsc_property": "https://magiarnd.ru/"`.
   Скрытого переключения ресурса или аккаунта нет.

```powershell
python -X utf8 info/scripts/gsc_stats.py 28
python -X utf8 info/scripts/gsc_coverage.py
python -X utf8 info/scripts/seo_daily.py --with-gsc
```

Отчёт GSC содержит период, ресурс, общие показатели, предыдущий равный период,
дневные значения, до 1000 запросов/страниц и запросы на позициях 4–15.
По умолчанию исключены последние 3 дня; API запрашивается с `dataState=final`.
Общий итог GSC и суммы строк по запросам/страницам нельзя безусловно приравнивать.
Пустой успешный ответ обозначается `null` (нет данных); API-ошибка — ненулевой
код завершения, а не отчёт с нулями.

Проверка индексации по умолчанию ограничена 200 URL за запуск. Ошибки проверки
не добавляются в `needs_review`. При частичной ошибке сохраняется отдельный
отчёт `coverage-failed-*`; последний успешный `coverage.json` остаётся прежним.
`needs_review` — список для анализа в GSC, а не очередь автоматической отправки.

JSON с токенами/ключами исключены из Git. Не помещайте их в `public/`, не
отправляйте в сообщения и не добавляйте в репозиторий вручную.

## IndexNow после публикации

Обычный запуск только показывает список. Для отправки нужны свой ключ и доступный
публичный `https://magiarnd.ru/<ключ>.txt` с этим ключом. Задайте `INDEXNOW_KEY`
в окружении процесса. Скрипт проверит файл и домен до обращения к API.

```powershell
python -X utf8 info/scripts/bing_indexnow.py sitemap
python -X utf8 info/scripts/bing_indexnow.py urls https://magiarnd.ru/remont-vannoy --submit
```

Отправляйте опубликованные новые/изменённые URL. Команда не входит в ежедневный
прогон. Ответ 200 означает получение уведомления, 202 — ожидание проверки ключа;
это не гарантия включения в поиск. Пакеты ограничены 10 000 URL без потери хвоста.

## Sitemap и устаревшие команды

Sitemap формируется в `resources/views/sitemap.blade.php` по `config/seo_pages.php`.
После содержательного изменения страницы обновляйте её `updated_at`; для главной —
`home_lastmod` в `config/seo.php`. Дата не меняется при каждом запросе или запуске.

- `gsc_index.py` отключён с явной ошибкой: Google Indexing API не предназначен для страниц ремонта.
- `refresh_sitemap_lastmod.py` объясняет обновление дат в Laravel, ничего не переписывает.
- `fix_hreflang_clusters.py` ничего не изменяет: переводов на сайте сейчас нет.
- `seo_daily.py` готов для ручного запуска или планировщика; системное расписание не устанавливает.

## Telegram: группа «Магия SEO», тема «SEO»

Все Python-уведомления проходят через `seo_telegram.py`. Транспорт требует три
явные переменные и всегда передаёт одновременно `chat_id` и `message_thread_id`:

```dotenv
TELEGRAM_BOT_TOKEN=
TELEGRAM_GROUP_CHAT_ID=
TELEGRAM_SEO_THREAD_ID=
TELEGRAM_ALLOWED_USERS=
SEO_TELEGRAM_ENABLED=false
```

Шаблон находится в `seo-telegram.env.example`. Старый `TELEGRAM_CHAT_ID` не
поддерживается как fallback, поэтому при неполной настройке сообщение не сможет
случайно уйти в прежнюю группу. `TELEGRAM_ALLOWED_USERS` — список числовых ID
через запятую; он проверяется для уведомлений, инициированных ручной командой.

Ежедневный и еженедельный прогоны:

```powershell
python -X utf8 info/scripts/seo_daily.py --with-gsc --telegram
python -X utf8 info/scripts/seo_daily.py --with-gsc --telegram --notification-kind weekly
```

Для планировщика можно вместо `--telegram` задать `SEO_TELEGRAM_ENABLED=true`.
Ошибка аудита или SEO-сервиса отправляется как `service_error`. Другие источники
(изменение позиций, вход/выход из TOP-10, Метрика и Wordstat) вызывают единый CLI:

```powershell
python -X utf8 info/scripts/seo_telegram.py position_change "Запрос: позиция 12 → 7"
python -X utf8 info/scripts/seo_telegram.py metrika "Сводка Метрики"
python -X utf8 info/scripts/seo_telegram.py manual_check "Проверка завершена" --requested-by 123456789
```

Безопасная проверка конфигурации без сообщения:

```powershell
python -X utf8 info/scripts/seo_telegram.py test --dry-run
```

Если production-хостинг не может обращаться к `api.telegram.org`, используйте
уже развёрнутый Cloudflare Worker как шлюз вместо копирования токена на сервер:

```dotenv
TELEGRAM_GATEWAY_URL=https://magia-telegram-leads.example.workers.dev
TELEGRAM_GATEWAY_SECRET=
TELEGRAM_ALLOWED_USERS=
SEO_TELEGRAM_ENABLED=true
```

Шлюз принимает только известные типы SEO-событий и сам подставляет сохранённые
`TELEGRAM_GROUP_CHAT_ID`/`TELEGRAM_SEO_THREAD_ID`; клиент не может переопределить
destination. Для endpoint используется отдельный `SEO_API_SECRET`.

Production unit-файлы находятся в `info/systemd/`: ежедневный timer запускается
в 08:00, еженедельный — по понедельникам в 09:00; в обоих случаях календарная
зона явно задана как `Europe/Moscow`. Секреты читаются из закрытого файла
`/etc/magia/seo-telegram.env`, а отчёты записываются в существующий приватный
каталог Laravel. Timer-файлы используют `Persistent=true`, поэтому пропущенный
запуск выполняется после перезагрузки сервера.

Результаты проверок не публикуют изменения сайта. Для обновления действующего
Laravel-сайта требуется обычный процесс развёртывания проекта.

## SEO Analytics: Topvisor + Webmaster + Metrika

Канонический набор находится в `info/scripts/seo-keywords.json`: 32 запроса
production-проекта Magic, проверенные в Topvisor 02.09.2026. В файле сохранены
пять кластеров и регион Ростов-на-Дону. Это не демонстрационная семантика.

Контрольные позиции, история и доступная частотность поступают из Topvisor,
проект `Magic #32438229`. Внутренний индекс региона Topvisor — `76`, георегион
Яндекса — `39`, глубина — TOP-100. Подтверждённый экспорт 01–02.09.2026 и
частотность сохранены в `topvisor-bootstrap-2026-09-02.json`.

`seo_sources.py` разделяет источники:

- Topvisor — только 32 целевых запроса, позиции, URL и частотность;
- Yandex Webmaster — фактические запросы, показы, клики, CTR,
  `AVG_SHOW_POSITION`, `AVG_CLICK_POSITION` и новые запросы;
- Yandex Metrika — органические визиты, пользователи, landing pages и цели.

Связка выполняется по нормализованному тексту запроса там, где Webmaster вернул
целевой запрос, и по landing page через релевантный URL Topvisor. Достижения
целей не приписываются конкретному запросу: в объединённом dashboard они всегда
помечены уровнем атрибуции `landing_page`.

История хранится отдельно от Laravel DB в приватном SQLite-файле
`storage/app/private/seo-analytics/positions.sqlite3`:

- `seo_keywords` — активное каноническое ядро и категории;
- `seo_position_checks` — append-only измерения; UPDATE/DELETE запрещены триггерами;
- `seo_events` — вход/выход из TOP и большие изменения;
- `seo_settings` — зарезервировано для runtime-настроек следующих этапов.
- `seo_source_runs` — статус каждой загрузки источника;
- `seo_webmaster_queries` — append-only фактическая поисковая аналитика;
- `seo_metrika_landings` и `seo_metrika_goals` — append-only органика и цели.

`not_found` означает значение `--` в контрольном замере Topvisor. Отсутствующие
показатели Webmaster/Metrika сохраняются как `NULL`, а не как ноль. Ошибки
источников записываются в `seo_source_runs` и не создают аналитические строки.

Read-only credentials задаются только в закрытом окружении:

```dotenv
SEO_ANALYTICS_ENABLED=1
TOPVISOR_USER_ID=
TOPVISOR_API_KEY=
YANDEX_WEBMASTER_TOKEN=
YANDEX_METRIKA_TOKEN=
YANDEX_METRIKA_GOAL_IDS=
```

Команды из каталога `Site`:

```powershell
python -X utf8 info/scripts/seo_sources.py init
python -X utf8 info/scripts/seo_sources.py bootstrap-topvisor
python -X utf8 info/scripts/seo_sources.py sync-all
python -X utf8 info/scripts/seo_dashboard.py build
python -X utf8 info/scripts/seo_dashboard.py report --days 7
python -X utf8 info/scripts/seo_positions.py keyword "ремонт квартир ростов-на-дону"
```

`init` безопасно создаёт отдельную БД и синхронизирует 32 запроса. Bootstrap
идемпотентен. Каждый новый замер добавляет строку; существующая история не
изменяется. Dashboard и PNG-графики находятся в
`storage/app/private/seo-analytics/`.
Периоды 3/7/30 дней используют ближайшее предыдущее достоверное измерение в
настраиваемом окне 2/3/5 дней. Знак изменения SEO: `18 → 9 = +9`.

Yandex Search API сохранён в `seo_positions.py` как резерв. Он выключен через
`positions.yandex_search_api.enabled=false` и не вызывается `sync-all`, daily,
weekly или Telegram.

При `SEO_ANALYTICS_ENABLED=1` существующий `seo_daily.py` сначала обновляет три
источника, атомарно собирает dashboard и только затем добавляет краткий
technical audit. Сами daily/weekly timers и Telegram routing не меняются.
