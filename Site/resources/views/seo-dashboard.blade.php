<!doctype html>
<html lang="ru">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta name="robots" content="noindex,nofollow,noarchive">
    <meta name="csrf-token" content="{{ csrf_token() }}">
    <title>SEO Analytics · magiarnd.ru</title>
    @vite(['resources/css/seo-dashboard.css', 'resources/js/seo-dashboard.js'])
</head>
<body class="seo-app" data-dashboard-endpoint="{{ route('seo.dashboard.data') }}">
<div class="dashboard-shell">
    <aside class="dashboard-sidebar">
        <div class="dashboard-brand">
            <span class="brand-mark">M</span>
            <span><strong>MAGIA</strong><small>SEO Analytics</small></span>
        </div>
        <nav class="dashboard-nav" aria-label="Разделы dashboard">
            <button class="nav-item is-active" data-view="summary"><span>⌁</span>Сводка</button>
            <button class="nav-item" data-view="positions"><span>⌕</span>Позиции</button>
            <button class="nav-item" data-view="webmaster"><span>W</span>Webmaster</button>
            <button class="nav-item" data-view="metrika"><span>M</span>Metrika</button>
            <button class="nav-item" data-view="technical"><span>✓</span>Technical SEO</button>
        </nav>
        <div class="sidebar-status">
            <span class="live-dot"></span>
            <div><strong>Read-only</strong><small>Автосинхронизация включена</small></div>
        </div>
        <form method="post" action="{{ route('seo.dashboard.logout') }}">
            @csrf
            <button class="logout-button" type="submit">Завершить сессию</button>
        </form>
    </aside>

    <div class="dashboard-workspace">
        <header class="dashboard-header">
            <div>
                <p class="eyebrow">MAGIARND.RU · SEARCH PERFORMANCE</p>
                <h1 id="page-title">Сводка</h1>
                <p id="dashboard-meta" class="dashboard-meta">Загружаем данные…</p>
            </div>
            <div class="header-actions">
                <div class="period-switcher" role="group" aria-label="Период отчёта">
                    <button data-period="1">1D</button>
                    <button data-period="3">3D</button>
                    <button class="is-active" data-period="7">7D</button>
                    <button data-period="30">30D</button>
                </div>
                <button class="refresh-button" id="refresh-dashboard" type="button" title="Перечитать подготовленные данные">↻ <span>Обновить</span></button>
            </div>
        </header>

        <main class="dashboard-content">
            <div id="dashboard-error" class="state-banner state-error" hidden></div>
            <div id="dashboard-loading" class="dashboard-loading"><span></span>Собираем кабинет…</div>

            <section class="dashboard-panel is-active" data-panel="summary">
                <div id="summary-cards" class="summary-grid"></div>
                <div class="chart-grid">
                    <article class="panel-card chart-card chart-card-wide">
                        <div class="panel-heading"><div><p class="eyebrow">TOPVISOR</p><h2>Средняя позиция</h2></div><span class="panel-badge">1 — лучше</span></div>
                        <div class="chart-wrap"><canvas id="average-position-chart"></canvas></div>
                    </article>
                    <article class="panel-card chart-card">
                        <div class="panel-heading"><div><p class="eyebrow">РАСПРЕДЕЛЕНИЕ</p><h2>Охват TOP</h2></div></div>
                        <div class="chart-wrap"><canvas id="distribution-chart"></canvas></div>
                    </article>
                    <article class="panel-card chart-card">
                        <div class="panel-heading"><div><p class="eyebrow">ДИНАМИКА</p><h2>Изменения</h2></div></div>
                        <div class="chart-wrap"><canvas id="movement-chart"></canvas></div>
                    </article>
                </div>
                <div class="source-overview" id="source-overview"></div>
            </section>

            <section class="dashboard-panel" data-panel="positions">
                <article class="panel-card positions-card">
                    <div class="panel-heading panel-heading-wrap">
                        <div><p class="eyebrow">32 ЦЕЛЕВЫХ ЗАПРОСА</p><h2>Контрольные позиции</h2></div>
                        <label class="search-field"><span>⌕</span><input id="position-search" type="search" placeholder="Найти запрос"></label>
                    </div>
                    <div class="filter-bar">
                        <select id="category-filter" aria-label="Категория"><option value="">Все категории</option></select>
                        <select id="status-filter" aria-label="Статус">
                            <option value="">Все статусы</option><option value="found">Найдено</option><option value="not_found">Не найдено</option><option value="error">Ошибка</option>
                        </select>
                        <select id="range-filter" aria-label="Диапазон позиций">
                            <option value="">Любая позиция</option><option value="3">TOP-3</option><option value="10">TOP-10</option><option value="20">TOP-20</option><option value="50">TOP-50</option><option value="100">51–100</option><option value="missing">Не найдено</option>
                        </select>
                        <select id="movement-filter" aria-label="Динамика">
                            <option value="">Любая динамика</option><option value="growth">Рост</option><option value="drop">Падение</option><option value="stable">Без изменений</option><option value="appeared">Появилось</option><option value="disappeared">Пропало</option>
                        </select>
                        <button id="reset-filters" class="ghost-button" type="button">Сбросить</button>
                    </div>
                    <div class="table-scroll">
                        <table class="data-table" id="positions-table">
                            <thead><tr>
                                <th data-sort="keyword">Ключ</th><th data-sort="category">Категория</th><th data-sort="position">Сейчас</th><th data-sort="previous_position">Было</th><th data-sort="change">Δ</th><th data-sort="frequency">Частота</th><th>Landing page</th><th data-sort="status">Статус</th>
                            </tr></thead>
                            <tbody></tbody>
                        </table>
                    </div>
                    <p id="positions-count" class="table-footnote"></p>
                </article>
            </section>

            <section class="dashboard-panel" data-panel="webmaster">
                <div id="webmaster-state"></div>
                <div id="webmaster-cards" class="metric-grid"></div>
                <div class="chart-grid single-row">
                    <article class="panel-card chart-card chart-card-wide">
                        <div class="panel-heading"><div><p class="eyebrow">ФАКТИЧЕСКИЙ СПРОС</p><h2>Показы и клики</h2></div></div>
                        <div class="chart-wrap"><canvas id="webmaster-trend-chart"></canvas></div>
                    </article>
                </div>
                <article class="panel-card">
                    <div class="panel-heading"><div><p class="eyebrow">ПОИСКОВЫЕ ФРАЗЫ</p><h2>Запросы из Webmaster</h2></div><span id="webmaster-query-count" class="panel-badge"></span></div>
                    <div class="table-scroll"><table class="data-table"><thead><tr><th>Запрос</th><th>Показы</th><th>Клики</th><th>CTR</th><th>Позиция показа</th><th>Позиция клика</th><th>Тип</th></tr></thead><tbody id="webmaster-table"></tbody></table></div>
                </article>
            </section>

            <section class="dashboard-panel" data-panel="metrika">
                <div id="metrika-state"></div>
                <div id="metrika-cards" class="metric-grid"></div>
                <div class="chart-grid single-row">
                    <article class="panel-card chart-card chart-card-wide">
                        <div class="panel-heading"><div><p class="eyebrow">ОРГАНИЧЕСКИЙ ТРАФИК</p><h2>Визиты и пользователи</h2></div></div>
                        <div class="chart-wrap"><canvas id="metrika-trend-chart"></canvas></div>
                    </article>
                </div>
                <article class="panel-card">
                    <div class="panel-heading"><div><p class="eyebrow">LANDING PAGE ATTRIBUTION</p><h2>Страницы входа и конверсии</h2></div><span class="panel-badge">Без привязки к запросу</span></div>
                    <div class="table-scroll"><table class="data-table"><thead><tr><th>Landing page</th><th>Визиты</th><th>Пользователи</th><th>Отказы</th><th>Глубина</th><th>Цели</th></tr></thead><tbody id="metrika-table"></tbody></table></div>
                </article>
            </section>

            <section class="dashboard-panel" data-panel="technical">
                <div id="technical-cards" class="metric-grid"></div>
                <article class="panel-card">
                    <div class="panel-heading"><div><p class="eyebrow">STATUS BOARD</p><h2>Проверенные страницы</h2></div><span id="technical-updated" class="panel-badge"></span></div>
                    <div class="table-scroll"><table class="data-table technical-table"><thead><tr><th>Страница</th><th>HTTP</th><th>Title / Description</th><th>H1</th><th>Canonical</th><th>Indexability</th><th>Результат</th></tr></thead><tbody id="technical-table"></tbody></table></div>
                </article>
            </section>
        </main>
    </div>
</div>

<dialog id="keyword-dialog" class="keyword-dialog">
    <button class="dialog-close" type="button" aria-label="Закрыть">×</button>
    <p class="eyebrow">ДИНАМИКА ЗАПРОСА · 30 ДНЕЙ</p>
    <h2 id="keyword-dialog-title"></h2>
    <div id="keyword-dialog-meta" class="keyword-meta"></div>
    <div class="chart-wrap dialog-chart"><canvas id="keyword-chart"></canvas></div>
</dialog>
</body>
</html>
