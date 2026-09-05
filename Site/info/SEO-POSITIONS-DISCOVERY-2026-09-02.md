# SEO Positions — Discovery и Stage B

> Обновление Stage C–E: 02.09.2026 контрольным источником позиций выбран
> Topvisor; Yandex Search API отключён и оставлен резервом. Фактические запросы
> и поисковые метрики поступают из Yandex Webmaster, органический трафик и цели
> — из Yandex Metrika. Актуальная runtime-архитектура описана в
> `info/scripts/README.md`.

Дата проверки: 2 сентября 2026 года. Production-домен: `https://magiarnd.ru`.

## Найденное семантическое ядро

Актуальный источник — Topvisor, проект **Magic #32438229**. В интерфейсе проекта
проверены 32 запроса, Яндекс, регион **Ростов-на-Дону [39]**, глубина 100.
28 геозапросов ранее были зафиксированы в `SEO-AUDIT-YANDEX-2026-09-02.md`;
ещё четыре исходных запроса подтверждены непосредственно в текущей таблице
Topvisor. Полная проверенная копия сохранена в `info/scripts/seo-keywords.json`.

| Категория | Запросов |
|---|---:|
| Главная | 8 |
| Новостройки | 6 |
| Вторичное жильё | 6 |
| Ванная | 6 |
| Дизайнерский ремонт | 6 |
| **Всего** | **32** |

Все запросы Topvisor находятся в одной технической группе «Новая группа».
Категории восстановлены не предположением, а по карте страниц и разделам
зафиксированного SEO-аудита; четыре общих запроса отнесены к соответствующим
страницам услуг.

## Исторические позиции

Topvisor показывает два доступных замера: 1 и 2 сентября 2026 года. Последняя
проверка в момент Discovery — 02.09.2026 14:53, средняя позиция 93, один запрос
в диапазоне 11–30 и пять в диапазоне 51–100. В репозитории, Git history и на
VPS отсутствуют Topvisor CSV/XLSX/JSON или иная историческая БД. Локальный
`database/database.sqlite` имеет размер 0 байт.

Автоматический импорт не выполнен: визуальный отчёт не даёт надёжного файла с
однозначным соответствием `keyword + date + position`. После явного экспорта
Topvisor эти две даты можно импортировать отдельной проверяемой командой.

## Production-инфраструктура

На VPS установлен Python 3.14.4. Текущие SEO-скрипты — плоский набор Python CLI
в `/var/www/magia/Site/info/scripts`; `seo_daily.py` запускает read-only
`seo_audit.py` и опционально GSC. Daily/weekly systemd units вызывают этот CLI и
пишут только в приватный каталог SEO-отчётов.

PostgreSQL и `psql` отсутствуют. Laravel настроен на SQLite, но новый движок не
использует production Laravel DB. На VPS также нет Yandex Search API credentials.

## Выбранная архитектура Stage B

```text
seo-keywords.json (32 production queries)
             |
             v
seo_positions.py -> Yandex Search API v2 -> ordered XML SERP TOP-100
             |                    |
             |                    +-> explicit API/rate/CAPTCHA/request errors
             v
private SQLite: keywords + append-only checks + events + settings
             |
             +-> current / previous / 3 / 7 / 30 day comparisons
             +-> TOP buckets, averages, categories, important SEO events
             +-> Telegram-ready text (transport is connected in a later stage)
```

Источник выдачи — официальный Yandex Search API v2:
`POST https://searchapi.api.cloud.yandex.net/v2/web/search`. Используются русский
тип поиска, регион 39 из конфигурации, релевантностная плоская выдача, XML в
base64-конверте и API-key authorization. Официальный лимит результатов выше
требуемого TOP-100; рабочие квоты существенно выше одного суточного прогона 32
запросов.

Stage B реализован в `seo_positions.py`; настройки расширены в
`seo-settings.json`, окружение — в `seo-telegram.env.example`, документация — в
`info/scripts/README.md`. `seo_daily.py`, systemd, Cloudflare Worker и Telegram
routing не изменялись.

## Объективный блокер реального замера

Для сетевого запроса нужны `YANDEX_FOLDER_ID` и `YANDEX_SEARCH_API_KEY` сервисного
аккаунта Yandex Cloud с доступом `yc.search-api.execute` и активным биллингом.
Их нет ни локально, ни на VPS. До их появления команда `check` завершается до
записи данных, поэтому отсутствие credentials не может превратиться в 32 ложных
`not_found` или Telegram-уведомления.
