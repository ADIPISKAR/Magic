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

Результаты проверок не публикуют изменения сайта. Для обновления действующего
Laravel-сайта требуется обычный процесс развёртывания проекта.
