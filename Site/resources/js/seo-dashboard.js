const root = document.body;

if (root.classList.contains('seo-app')) {
    const state = {
        period: 7,
        view: 'summary',
        data: null,
        sort: { key: 'position', direction: 1 },
    };

    const endpoint = root.dataset.dashboardEndpoint;
    const titles = {
        summary: 'Сводка', positions: 'Позиции', webmaster: 'Yandex Webmaster',
        metrika: 'Yandex Metrika', technical: 'Technical SEO',
    };
    const palette = {
        lime: '#c9f65b', cyan: '#5ddbd2', green: '#56d89c', red: '#ff7a86',
        amber: '#f5c767', blue: '#78a9ff', muted: '#71847a', grid: 'rgba(255,255,255,.08)',
    };

    const escapeHtml = (value) => String(value ?? '')
        .replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;')
        .replaceAll('"', '&quot;').replaceAll("'", '&#039;');

    const number = (value, digits = 0) => value === null || value === undefined
        ? '—'
        : Number(value).toLocaleString('ru-RU', { maximumFractionDigits: digits });
    const percent = (value) => value === null || value === undefined ? '—' : `${number(value, 2)}%`;
    const dateTime = (value) => value ? new Intl.DateTimeFormat('ru-RU', {
        day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit',
    }).format(new Date(value)) : 'время неизвестно';
    const shortDate = (value) => value ? new Intl.DateTimeFormat('ru-RU', {
        day: '2-digit', month: '2-digit',
    }).format(new Date(`${value}T00:00:00`)) : '';
    const duration = (seconds) => {
        if (seconds === null || seconds === undefined) return '—';
        const total = Math.round(Number(seconds));
        return `${Math.floor(total / 60)}:${String(total % 60).padStart(2, '0')}`;
    };

    const setLoading = (loading) => {
        document.querySelector('#dashboard-loading').hidden = !loading;
        document.querySelectorAll('.dashboard-panel').forEach((panel) => {
            if (loading) panel.classList.remove('is-active');
        });
    };

    const showError = (message) => {
        const banner = document.querySelector('#dashboard-error');
        banner.textContent = message;
        banner.hidden = false;
    };

    const sourceCopy = (name, source, hasRows = true) => {
        const labels = { topvisor: 'Topvisor', yandex_webmaster: 'Yandex Webmaster', yandex_metrika: 'Yandex Metrika' };
        if (!source || source.state === 'not_configured') {
            return { tone: 'warning', text: `${labels[name]} ещё не подключён: credentials отсутствуют или sync не выполнялся.` };
        }
        if (source.state === 'error') {
            return { tone: 'error', text: `${labels[name]} подключён, но последняя синхронизация завершилась ошибкой. Нулевые значения не подставлены.` };
        }
        if (!hasRows) {
            return { tone: 'connected', text: `${labels[name]} подключён, sync выполнен. За выбранный период источник не вернул строк — это не подменяется нулями.` };
        }
        return { tone: 'connected', text: `${labels[name]} подключён. Последний успешный sync: ${dateTime(source.finished_at)}.` };
    };

    const renderSourceBanner = (target, name, source, hasRows) => {
        const copy = sourceCopy(name, source, hasRows);
        target.innerHTML = `<div class="state-banner state-${copy.tone}"><strong>${escapeHtml(copy.text.split('.')[0])}.</strong>${escapeHtml(copy.text.slice(copy.text.indexOf('.') + 1))}</div>`;
    };

    const summaryCard = (label, value, note = '', tone = '') => `
        <article class="summary-card ${tone}"><p>${escapeHtml(label)}</p><strong>${escapeHtml(value)}</strong><small>${escapeHtml(note)}</small></article>`;
    const metricCard = (label, value, note = '') => `
        <article class="metric-card"><p>${escapeHtml(label)}</p><strong>${escapeHtml(value)}</strong><small>${escapeHtml(note)}</small></article>`;

    function canvasContext(canvas) {
        const rect = canvas.getBoundingClientRect();
        const ratio = Math.min(window.devicePixelRatio || 1, 2);
        canvas.width = Math.max(1, Math.floor(rect.width * ratio));
        canvas.height = Math.max(1, Math.floor(rect.height * ratio));
        const context = canvas.getContext('2d');
        context.setTransform(ratio, 0, 0, ratio, 0, 0);
        return { context, width: rect.width, height: rect.height };
    }

    function emptyChart(context, width, height, text = 'Недостаточно точек для графика') {
        context.clearRect(0, 0, width, height);
        context.fillStyle = '#71847a';
        context.font = '12px Inter, sans-serif';
        context.textAlign = 'center';
        context.fillText(text, width / 2, height / 2);
    }

    function drawLineChart(canvas, labels, datasets, options = {}) {
        if (!canvas) return;
        const { context, width, height } = canvasContext(canvas);
        const all = datasets.flatMap((set) => set.values.filter((value) => value !== null && value !== undefined && Number.isFinite(Number(value))).map(Number));
        if (!all.length) return emptyChart(context, width, height);
        const padding = { top: 24, right: 18, bottom: 40, left: 45 };
        const plotWidth = width - padding.left - padding.right;
        const plotHeight = height - padding.top - padding.bottom;
        let min = options.min ?? Math.min(...all);
        let max = options.max ?? Math.max(...all);
        if (min === max) { min -= 1; max += 1; }
        if (!options.invert && min > 0) min = 0;
        const x = (index) => padding.left + (labels.length <= 1 ? plotWidth / 2 : index * plotWidth / (labels.length - 1));
        const y = (value) => {
            const progress = (Number(value) - min) / (max - min);
            return padding.top + (options.invert ? progress : 1 - progress) * plotHeight;
        };
        context.clearRect(0, 0, width, height);
        context.lineWidth = 1;
        context.font = '10px Inter, sans-serif';
        context.textAlign = 'right';
        for (let step = 0; step <= 4; step += 1) {
            const value = min + (max - min) * step / 4;
            const yPos = y(value);
            context.strokeStyle = palette.grid;
            context.beginPath(); context.moveTo(padding.left, yPos); context.lineTo(width - padding.right, yPos); context.stroke();
            context.fillStyle = palette.muted;
            context.fillText(number(value, 1), padding.left - 8, yPos + 3);
        }
        const labelIndexes = [...new Set([0, Math.floor((labels.length - 1) / 2), labels.length - 1])];
        context.textAlign = 'center';
        labelIndexes.forEach((index) => {
            context.fillStyle = palette.muted;
            context.fillText(labels[index] ?? '', x(index), height - 12);
        });
        datasets.forEach((dataset) => {
            context.strokeStyle = dataset.color;
            context.lineWidth = dataset.width || 2.2;
            context.lineJoin = 'round'; context.lineCap = 'round';
            context.beginPath();
            let drawing = false;
            dataset.values.forEach((value, index) => {
                if (value === null || value === undefined) { drawing = false; return; }
                if (!drawing) context.moveTo(x(index), y(value)); else context.lineTo(x(index), y(value));
                drawing = true;
            });
            context.stroke();
            dataset.values.forEach((value, index) => {
                if (value === null || value === undefined) return;
                context.fillStyle = dataset.color;
                context.beginPath(); context.arc(x(index), y(value), 2.8, 0, Math.PI * 2); context.fill();
            });
        });
        if (datasets.length > 1) {
            let legendX = padding.left;
            datasets.forEach((dataset) => {
                context.fillStyle = dataset.color; context.fillRect(legendX, 5, 9, 3);
                context.fillStyle = palette.muted; context.textAlign = 'left'; context.font = '9px Inter, sans-serif';
                context.fillText(dataset.label, legendX + 14, 10);
                legendX += context.measureText(dataset.label).width + 34;
            });
        }
    }

    function drawBarChart(canvas, labels, values, colors) {
        if (!canvas) return;
        const { context, width, height } = canvasContext(canvas);
        const known = values.filter((value) => value !== null && value !== undefined).map(Number);
        if (!known.length) return emptyChart(context, width, height);
        const padding = { top: 18, right: 14, bottom: 42, left: 32 };
        const plotWidth = width - padding.left - padding.right;
        const plotHeight = height - padding.top - padding.bottom;
        const max = Math.max(1, ...known);
        const slot = plotWidth / values.length;
        const barWidth = Math.min(52, slot * .58);
        context.clearRect(0, 0, width, height);
        values.forEach((value, index) => {
            const amount = Number(value || 0);
            const barHeight = amount / max * plotHeight;
            const x = padding.left + slot * index + (slot - barWidth) / 2;
            const y = padding.top + plotHeight - barHeight;
            context.fillStyle = colors[index] || palette.lime;
            context.beginPath(); context.roundRect(x, y, barWidth, Math.max(3, barHeight), 7); context.fill();
            context.fillStyle = '#d8e2dc'; context.font = '700 11px Inter, sans-serif'; context.textAlign = 'center';
            context.fillText(number(amount), x + barWidth / 2, Math.max(12, y - 7));
            context.fillStyle = palette.muted; context.font = '9px Inter, sans-serif';
            context.fillText(labels[index], x + barWidth / 2, height - 14);
        });
    }

    function renderSummary() {
        const summary = state.data.summary || {};
        const cards = [
            ['Всего запросов', number(summary.total), 'Контрольная семантика'],
            ['TOP-3', number(summary.top3), 'Первая выдача'],
            ['TOP-10', number(summary.top10), 'Первая страница'],
            ['TOP-20', number(summary.top20), 'Зона роста'],
            ['TOP-50', number(summary.top50), 'Видимые позиции'],
            ['Не найдено', number(summary.not_found), 'За пределами TOP-100', 'warning'],
            ['Средняя позиция', number(summary.average_position, 1), 'Только найденные'],
            ['Выросло', number(summary.improved), `За ${state.period} дн.`, 'positive'],
            ['Упало', number(summary.declined), `За ${state.period} дн.`, 'negative'],
            ['Новых', number(summary.appeared), 'Появились в выдаче', 'positive'],
            ['Пропало', number(summary.disappeared), 'Вышли из TOP-100', 'negative'],
        ];
        document.querySelector('#summary-cards').innerHTML = cards.map((item) => summaryCard(...item)).join('');

        const visual = state.data.visualizations || {};
        const average = visual.average_position || [];
        drawLineChart(
            document.querySelector('#average-position-chart'),
            average.map((row) => shortDate(row.date)),
            [{ label: 'Средняя позиция', values: average.map((row) => row.average_position), color: palette.lime }],
            { invert: true },
        );
        const latestDistribution = [...(visual.distribution || [])].reverse().find((row) => row.top3 !== null);
        drawBarChart(
            document.querySelector('#distribution-chart'),
            ['TOP-3', 'TOP-10', 'TOP-20', 'TOP-50', 'Нет'],
            latestDistribution ? [latestDistribution.top3, latestDistribution.top10, latestDistribution.top20, latestDistribution.top50, latestDistribution.not_found] : [],
            [palette.lime, palette.green, palette.cyan, palette.blue, palette.amber],
        );
        const movement = visual.movement || {};
        drawBarChart(
            document.querySelector('#movement-chart'),
            ['Рост', 'Падение', 'Без изм.', 'Новые', 'Пропало'],
            [movement.improved, movement.declined, movement.unchanged, movement.appeared, movement.disappeared],
            [palette.green, palette.red, palette.muted, palette.cyan, palette.amber],
        );

        document.querySelector('#source-overview').innerHTML = Object.entries({
            topvisor: ['Topvisor', true],
            yandex_webmaster: ['Webmaster', state.data.webmaster?.query_count !== null && state.data.webmaster?.query_count !== undefined],
            yandex_metrika: ['Metrika', state.data.metrika?.visits !== null && state.data.metrika?.visits !== undefined],
        }).map(([name, [label, hasRows]]) => {
            const source = state.data.sources?.[name];
            const copy = sourceCopy(name, source, hasRows);
            return `<article class="source-card"><header><strong>${label}</strong><span class="source-pill ${source?.state || 'not_configured'}"></span></header><p>${escapeHtml(copy.text)}</p></article>`;
        }).join('');
    }

    function positionLabel(row) {
        if (row.status === 'found' && row.position !== null) return number(row.position);
        return '—';
    }

    function filteredPositions() {
        const search = document.querySelector('#position-search').value.trim().toLocaleLowerCase('ru');
        const category = document.querySelector('#category-filter').value;
        const status = document.querySelector('#status-filter').value;
        const range = document.querySelector('#range-filter').value;
        const movement = document.querySelector('#movement-filter').value;
        const result = (state.data.positions || []).filter((row) => {
            if (search && !row.keyword.toLocaleLowerCase('ru').includes(search)) return false;
            if (category && row.category !== category) return false;
            if (status && row.status !== status) return false;
            if (movement && row.movement !== movement) return false;
            if (range === 'missing' && row.status !== 'not_found') return false;
            if (range && range !== 'missing') {
                if (row.status !== 'found' || row.position === null) return false;
                const limit = Number(range);
                if (limit === 100 ? row.position <= 50 : row.position > limit) return false;
            }
            return true;
        });
        const { key, direction } = state.sort;
        return result.sort((a, b) => {
            const av = a[key]; const bv = b[key];
            if (av === null || av === undefined) return 1;
            if (bv === null || bv === undefined) return -1;
            return (typeof av === 'string' ? av.localeCompare(bv, 'ru') : Number(av) - Number(bv)) * direction;
        });
    }

    function renderPositionsTable() {
        const rows = filteredPositions();
        const body = document.querySelector('#positions-table tbody');
        body.innerHTML = rows.length ? rows.map((row) => {
            const change = row.change === null ? '—' : `${row.change > 0 ? '+' : ''}${number(row.change, 1)}`;
            const changeClass = row.change > 0 ? 'change-up' : (row.change < 0 ? 'change-down' : '');
            const statusText = row.status === 'found' ? 'Найдено' : (row.status === 'not_found' ? 'Не найдено' : 'Ошибка');
            const landing = row.landing_page
                ? `<a class="landing-link" href="${escapeHtml(row.landing_page)}" target="_blank" rel="noreferrer">${escapeHtml(new URL(row.landing_page).pathname || '/')}</a>` : '—';
            return `<tr>
                <td class="keyword-cell"><button class="keyword-button" data-keyword-id="${row.keyword_id}">${escapeHtml(row.keyword)}</button></td>
                <td><span class="category-tag">${escapeHtml(row.category)}</span></td>
                <td><span class="position-number">${positionLabel(row)}</span></td><td>${number(row.previous_position)}</td>
                <td class="${changeClass}">${change}</td><td>${number(row.frequency)}</td><td>${landing}</td>
                <td><span class="status-tag ${escapeHtml(row.status)}">${statusText}</span></td>
            </tr>`;
        }).join('') : '<tr><td colspan="8" class="empty-row">По выбранным фильтрам запросов нет.</td></tr>';
        document.querySelector('#positions-count').textContent = `Показано ${rows.length} из ${(state.data.positions || []).length}`;
        body.querySelectorAll('[data-keyword-id]').forEach((button) => button.addEventListener('click', () => openKeyword(Number(button.dataset.keywordId))));
    }

    function renderPositions() {
        const category = document.querySelector('#category-filter');
        const selected = category.value;
        const categories = [...new Set((state.data.positions || []).map((row) => row.category))].sort((a, b) => a.localeCompare(b, 'ru'));
        category.innerHTML = '<option value="">Все категории</option>' + categories.map((item) => `<option value="${escapeHtml(item)}">${escapeHtml(item)}</option>`).join('');
        category.value = categories.includes(selected) ? selected : '';
        renderPositionsTable();
    }

    function renderWebmaster() {
        const data = state.data.webmaster || {};
        const hasRows = data.query_count !== null && data.query_count !== undefined;
        renderSourceBanner(document.querySelector('#webmaster-state'), 'yandex_webmaster', state.data.sources?.yandex_webmaster, hasRows);
        document.querySelector('#webmaster-cards').innerHTML = [
            ['Показы', number(data.shows), 'TOTAL_SHOWS'], ['Клики', number(data.clicks), 'TOTAL_CLICKS'],
            ['CTR', percent(data.ctr), 'Клики / показы'], ['AVG show pos.', number(data.queries?.length ? weighted(data.queries, 'avg_show_position', 'shows') : null, 2), 'Позиция показа'],
            ['AVG click pos.', number(data.queries?.length ? weighted(data.queries, 'avg_click_position', 'clicks') : null, 2), 'Позиция клика'],
            ['Новых запросов', number(data.new_queries?.length ?? null), 'Вне 32 целевых'],
        ].map((item) => metricCard(...item)).join('');
        const trend = data.trend || [];
        drawLineChart(document.querySelector('#webmaster-trend-chart'), trend.map((row) => shortDate(row.date)), [
            { label: 'Показы', values: trend.map((row) => row.shows), color: palette.lime },
            { label: 'Клики', values: trend.map((row) => row.clicks), color: palette.cyan },
        ]);
        const queries = data.queries || [];
        document.querySelector('#webmaster-query-count').textContent = hasRows ? `${queries.length} запросов` : 'нет строк';
        document.querySelector('#webmaster-table').innerHTML = queries.length ? queries.map((row) => `<tr>
            <td class="keyword-cell">${escapeHtml(row.query_text)}</td><td>${number(row.shows)}</td><td>${number(row.clicks)}</td><td>${percent(row.ctr)}</td>
            <td>${number(row.avg_show_position, 2)}</td><td>${number(row.avg_click_position, 2)}</td>
            <td><span class="category-tag">${row.is_target ? 'Целевой' : 'Новый'}</span></td></tr>`).join('')
            : '<tr><td colspan="7" class="empty-row">Запросов за выбранный период нет.</td></tr>';
    }

    function weighted(rows, field, weightField) {
        const values = rows.filter((row) => row[field] !== null && row[field] !== undefined && row[weightField] > 0);
        if (!values.length) return null;
        const weight = values.reduce((sum, row) => sum + Number(row[weightField]), 0);
        return values.reduce((sum, row) => sum + Number(row[field]) * Number(row[weightField]), 0) / weight;
    }

    function renderMetrika() {
        const data = state.data.metrika || {};
        const hasRows = data.visits !== null && data.visits !== undefined;
        renderSourceBanner(document.querySelector('#metrika-state'), 'yandex_metrika', state.data.sources?.yandex_metrika, hasRows);
        document.querySelector('#metrika-cards').innerHTML = [
            ['Органические визиты', number(data.visits), 'Только поисковые системы'], ['Пользователи', number(data.users), 'Уникальные посетители'],
            ['Отказы', percent(data.bounce_rate), 'Взвешено по визитам'], ['Глубина', number(data.page_depth, 2), 'Страниц за визит'],
            ['Вовлечённость', duration(data.avg_visit_duration_seconds), 'Среднее время'], ['Конверсии', number(data.goal_reaches), `Мессенджеры: ${number(data.messenger_reaches)}`],
        ].map((item) => metricCard(...item)).join('');
        const trend = data.trend || [];
        drawLineChart(document.querySelector('#metrika-trend-chart'), trend.map((row) => shortDate(row.date)), [
            { label: 'Визиты', values: trend.map((row) => row.visits), color: palette.lime },
            { label: 'Пользователи', values: trend.map((row) => row.users), color: palette.cyan },
        ]);
        const landings = data.landings || [];
        document.querySelector('#metrika-table').innerHTML = landings.length ? landings.map((row) => {
            const goals = (row.goals || []).reduce((sum, goal) => sum + Number(goal.reaches || 0), 0);
            return `<tr><td><a class="landing-link" href="${escapeHtml(row.landing_page)}" target="_blank" rel="noreferrer">${escapeHtml(row.landing_page)}</a></td>
                <td>${number(row.visits)}</td><td>${number(row.users)}</td><td>${percent(row.bounce_rate)}</td><td>${number(row.page_depth, 2)}</td><td>${number(goals)}</td></tr>`;
        }).join('') : '<tr><td colspan="6" class="empty-row">Органических landing pages за выбранный период нет.</td></tr>';
    }

    function renderTechnical() {
        const data = state.data.technical || {};
        const pages = data.pages || [];
        const ok = pages.filter((page) => !(page.errors || []).length && !(page.warnings || []).length).length;
        document.querySelector('#technical-cards').innerHTML = [
            ['Проверено страниц', number(data.pages_checked), 'Из sitemap.xml'], ['OK', number(ok), 'Без ошибок и предупреждений'],
            ['Ошибки', number(data.error_count), 'Требуют внимания'], ['Предупреждения', number(data.warning_count), 'Нужно проверить'],
            ['HTTP 200', number(pages.filter((page) => page.http_status === 200).length), 'Прямой ответ'], ['Indexable', number(pages.filter((page) => page.indexable === true).length), 'Можно индексировать'],
        ].map((item) => metricCard(...item)).join('');
        document.querySelector('#technical-updated').textContent = data.checked_at ? `Проверено ${dateTime(data.checked_at)}` : 'аудит не выполнен';
        document.querySelector('#technical-table').innerHTML = pages.length ? pages.map((page) => {
            const errors = page.errors || []; const warnings = page.warnings || [];
            const result = errors.length ? `<span class="status-tag error">${errors.length} ошибок</span>`
                : (warnings.length ? `<span class="status-tag not_found">${warnings.length} предупрежд.</span>` : '<span class="status-tag found">OK</span>');
            const checks = [
                ['H1', page.h1_count === 1], ['Canonical', Boolean(page.canonical)], ['Robots', page.robots !== undefined], ['Schema', Number(page.schema_count) > 0], ['Sitemap', page.sitemap_included === true],
            ];
            return `<tr><td><a class="landing-link" href="${escapeHtml(page.url)}" target="_blank" rel="noreferrer">${escapeHtml(new URL(page.url).pathname || '/')}</a></td>
                <td>${page.http_status ?? '—'}</td><td><div class="meta-stack"><strong>${escapeHtml(page.title || 'Title не записан')}</strong><small>${escapeHtml(page.description || 'Description не записан')}</small></div></td>
                <td>${page.h1_count ?? '—'}</td><td>${page.canonical ? '✓' : '—'}</td><td>${page.indexable === true ? '<span class="change-up">Да</span>' : (page.indexable === false ? '<span class="change-down">Нет</span>' : '—')}</td>
                <td><div class="check-list">${checks.map(([label, passed]) => `<span class="check-dot ${passed ? '' : 'unknown'}" title="${label}">${passed ? '✓' : '?'}</span>`).join('')}${result}</div></td></tr>`;
        }).join('') : '<tr><td colspan="7" class="empty-row">Технический аудит ещё не выполнен.</td></tr>';
    }

    function openKeyword(id) {
        const row = state.data.positions.find((item) => item.keyword_id === id);
        if (!row) return;
        const dialog = document.querySelector('#keyword-dialog');
        document.querySelector('#keyword-dialog-title').textContent = row.keyword;
        document.querySelector('#keyword-dialog-meta').innerHTML = [
            `Сейчас: ${positionLabel(row)}`, `Было: ${number(row.previous_position)}`,
            `Частота: ${number(row.frequency)}`, row.category,
        ].map((item) => `<span>${escapeHtml(item)}</span>`).join('');
        dialog.showModal();
        requestAnimationFrame(() => {
            const series = state.data.keyword_series?.[String(id)] || [];
            drawLineChart(document.querySelector('#keyword-chart'), series.map((item) => shortDate(item.date)), [
                { label: row.keyword, values: series.map((item) => item.position), color: palette.lime },
            ], { invert: true });
        });
    }

    function renderAll() {
        renderSummary(); renderPositions(); renderWebmaster(); renderMetrika(); renderTechnical();
        document.querySelector('#dashboard-meta').textContent = `Данные на ${state.data.anchor_date || '—'} · обновлено ${dateTime(state.data.generated_at)} · период ${state.period} дн.`;
        switchView(state.view);
    }

    async function loadData() {
        setLoading(true);
        document.querySelector('#dashboard-error').hidden = true;
        try {
            const response = await fetch(`${endpoint}?period=${state.period}`, {
                headers: { Accept: 'application/json' }, credentials: 'same-origin', cache: 'no-store',
            });
            if (response.status === 401) { window.location.reload(); return; }
            if (!response.ok) throw new Error('Не удалось получить подготовленный SEO-отчёт.');
            state.data = await response.json();
            renderAll();
        } catch (error) {
            showError(error.message || 'Dashboard временно недоступен.');
        } finally {
            setLoading(false);
            switchView(state.view);
        }
    }

    function switchView(view) {
        state.view = view;
        document.querySelector('#page-title').textContent = titles[view];
        document.querySelectorAll('[data-view]').forEach((button) => button.classList.toggle('is-active', button.dataset.view === view));
        document.querySelectorAll('[data-panel]').forEach((panel) => panel.classList.toggle('is-active', panel.dataset.panel === view));
        if (state.data) requestAnimationFrame(() => {
            if (view === 'summary') renderSummary();
            if (view === 'webmaster') renderWebmaster();
            if (view === 'metrika') renderMetrika();
        });
    }

    document.querySelectorAll('[data-view]').forEach((button) => button.addEventListener('click', () => switchView(button.dataset.view)));
    document.querySelectorAll('[data-period]').forEach((button) => button.addEventListener('click', () => {
        state.period = Number(button.dataset.period);
        document.querySelectorAll('[data-period]').forEach((item) => item.classList.toggle('is-active', item === button));
        loadData();
    }));
    document.querySelector('#refresh-dashboard').addEventListener('click', loadData);
    ['position-search', 'category-filter', 'status-filter', 'range-filter', 'movement-filter'].forEach((id) => {
        document.querySelector(`#${id}`).addEventListener(id === 'position-search' ? 'input' : 'change', renderPositionsTable);
    });
    document.querySelector('#reset-filters').addEventListener('click', () => {
        ['position-search', 'category-filter', 'status-filter', 'range-filter', 'movement-filter'].forEach((id) => { document.querySelector(`#${id}`).value = ''; });
        renderPositionsTable();
    });
    document.querySelectorAll('#positions-table th[data-sort]').forEach((header) => header.addEventListener('click', () => {
        state.sort.direction = state.sort.key === header.dataset.sort ? -state.sort.direction : 1;
        state.sort.key = header.dataset.sort;
        renderPositionsTable();
    }));
    document.querySelector('.dialog-close').addEventListener('click', () => document.querySelector('#keyword-dialog').close());
    document.querySelector('#keyword-dialog').addEventListener('click', (event) => {
        if (event.target === event.currentTarget) event.currentTarget.close();
    });
    let resizeTimer;
    window.addEventListener('resize', () => {
        clearTimeout(resizeTimer);
        resizeTimer = setTimeout(() => state.data && renderAll(), 120);
    });

    loadData();
}
