<?php

declare(strict_types=1);

namespace App\Http\Controllers;

use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\URL;

final class SeoTelegramController extends Controller
{
    public function show(Request $request): JsonResponse
    {
        $expected = (string) config('services.seo_backend.secret', '');
        $provided = (string) ($request->header('X-SEO-Backend-Secret')
            ?: $request->input('_backend_secret', ''));
        if ($expected === '' || ! hash_equals($expected, $provided)) {
            return response()->json(['message' => 'Unauthorized'], 401);
        }

        $dashboard = $this->readDashboard((string) config('services.seo_backend.dashboard_path', ''));
        if ($dashboard === null) {
            return response()->json([
                'message' => 'SEO dashboard is not available yet.',
                'text' => 'SEO-данные пока не подготовлены.',
                'keyboard' => $this->mainKeyboard(),
            ], 503);
        }

        $audit = $this->readDashboard((string) config('services.seo_dashboard.audit_path', ''));
        $result = $this->responseFor(
            $dashboard,
            trim((string) $request->input('action', 'menu')),
            $audit,
        );

        return response()->json($result, isset($result['error']) ? 422 : 200);
    }

    /** @return array<string, mixed>|null */
    private function readDashboard(string $path): ?array
    {
        if ($path === '' || ! is_file($path) || ! is_readable($path)) {
            return null;
        }
        $contents = file_get_contents($path);
        $decoded = $contents === false ? null : json_decode($contents, true);

        return is_array($decoded) ? $decoded : null;
    }

    /** @param array<string, mixed> $dashboard
     *  @return array<string, mixed>
     */
    private function responseFor(array $dashboard, string $action, ?array $audit = null): array
    {
        // --- Visual-first routes: images are the primary interface. ---
        if ($action === 'menu') {
            return $this->dashboardResponse($dashboard, 7);
        }
        if (preg_match('/^dashboard:(1|3|7|30)$/', $action, $matches) === 1) {
            return $this->dashboardResponse($dashboard, (int) $matches[1]);
        }
        if (preg_match('/^more:(1|3|7|30)$/', $action, $matches) === 1) {
            return $this->moreChartsMenu((int) $matches[1]);
        }
        if (preg_match('/^chart:(positions|average|traffic|conversions|top10|distribution|growthdrop):(1|3|7|30|90)$/', $action, $matches) === 1) {
            return $this->visualChart($dashboard, $matches[1], (int) $matches[2]);
        }
        if ($action === 'wordstat') {
            return $this->wordstatChart($dashboard);
        }
        if (preg_match('/^keyword:(\d+)$/', $action, $matches) === 1) {
            return $this->keywordDetail($dashboard, (int) $matches[1]);
        }
        if ($action === 'refresh') {
            $response = $this->dashboardResponse($dashboard, 7);
            $response['text'] = $response['text']
                ."\n\n🔄 Экран перечитан из последнего безопасного sync. Платная проверка позиций этой кнопкой не запускается.";

            return $response;
        }

        // --- Legacy text-based routes: kept for old inline keyboards and
        // for anyone who wants the detailed drill-down text views. ---
        if (preg_match('/^section:(summary|positions|webmaster|metrika|technical|charts):(1|3|7|30)$/', $action, $matches) === 1) {
            $section = $matches[1];
            $days = (int) $matches[2];
            $text = match ($section) {
                'summary' => $this->summaryText($dashboard, $days),
                'positions' => $this->positionsText($dashboard, $days),
                'webmaster' => $this->webmasterText($dashboard, $days),
                'metrika' => $this->metrikaText($dashboard, $days),
                'technical' => $this->technicalText($audit),
                'charts' => $this->chartsText($dashboard, $days),
            };

            return ['text' => $text, 'keyboard' => $this->sectionKeyboard($section, $days)];
        }
        if (preg_match('/^period:(1|3|7|30)$/', $action, $matches) === 1) {
            return $this->dashboardResponse($dashboard, (int) $matches[1]);
        }
        if ($action === 'top10' || $action === 'not_found') {
            return ['text' => $this->positionList($dashboard, $action), 'keyboard' => $this->backKeyboard()];
        }
        if ($action === 'growth' || $action === 'drop') {
            return ['text' => $this->movementList($dashboard, $action), 'keyboard' => $this->backKeyboard()];
        }
        if ($action === 'analytics') {
            return ['text' => $this->analyticsText($dashboard), 'keyboard' => $this->backKeyboard()];
        }
        if (preg_match('/^keywords:(\d+)$/', $action, $matches) === 1) {
            return $this->keywordPage($dashboard, (int) $matches[1]);
        }

        return ['error' => 'Unknown action.', 'text' => 'Неизвестная команда.'];
    }

    // === Visual-first: dashboard image, sub-charts, keyword cards ===

    /** @param array<string, mixed> $dashboard
     *  @return array<string, mixed>
     */
    private function dashboardResponse(array $dashboard, int $days): array
    {
        $chartsRoot = is_array($dashboard['charts'] ?? null) ? $dashboard['charts'] : [];
        $dashboardCharts = is_array($chartsRoot['dashboard'] ?? null) ? $chartsRoot['dashboard'] : [];
        $paths = $days === 30
            ? [$dashboardCharts['30_1'] ?? null, $dashboardCharts['30_2'] ?? null]
            : [$dashboardCharts[(string) $days] ?? null];
        $photos = $this->photosFor($paths);

        if ($photos === []) {
            return [
                'text' => $this->summaryText($dashboard, $days)
                    ."\n\n⚠️ Графики временно недоступны (недостаточно данных или не установлен matplotlib).",
                'keyboard' => $this->dashboardKeyboard($days),
            ];
        }

        return [
            'text' => $this->dashboardCaption($dashboard, $days),
            'photos' => $photos,
            'keyboard' => $this->dashboardKeyboard($days),
        ];
    }

    /** @param array<string, mixed> $dashboard */
    private function dashboardCaption(array $dashboard, int $days): string
    {
        $positions = $dashboard['periods'][(string) $days]['positions'] ?? [];
        $metrika = $dashboard['periods'][(string) $days]['metrika'] ?? [];
        $positions = is_array($positions) ? $positions : [];
        $metrika = is_array($metrika) ? $metrika : [];
        $metric = static fn (array $row, string $key): string => array_key_exists($key, $row)
            && $row[$key] !== null ? (string) $row[$key] : '—';
        $avgDelta = ($positions['average_change'] ?? null) !== null
            ? sprintf(' (%+.1f)', (float) $positions['average_change']) : '';

        return implode("\n", array_filter([
            '📊 SEO Dashboard · '.$this->periodLabel($days),
            'Средняя позиция: '.$metric($positions, 'average_position').$avgDelta.
                '   ·   TOP-10: '.$metric($positions, 'top10'),
            ($metrika['visits'] ?? null) !== null
                ? 'Трафик: '.$metric($metrika, 'visits').'   ·   Заявки: '.$metric($metrika, 'goal_reaches')
                : null,
        ], static fn (mixed $line): bool => $line !== null));
    }

    /** @return array<int, array<int, array<string, string>>> */
    private function dashboardKeyboard(int $days): array
    {
        $period = static fn (int $value, string $label): string => $value === $days ? '• '.$label : $label;

        return [
            [
                ['text' => '📈 Позиции', 'callback_data' => "seo:chart:positions:{$days}"],
                ['text' => '🌐 Трафик', 'callback_data' => "seo:chart:traffic:{$days}"],
            ],
            [
                ['text' => '🎯 Конверсии', 'callback_data' => "seo:chart:conversions:{$days}"],
                ['text' => '🔑 Wordstat', 'callback_data' => 'seo:wordstat'],
            ],
            [['text' => '📊 Ещё графики', 'callback_data' => "seo:more:{$days}"]],
            [
                ['text' => $period(1, 'Сегодня'), 'callback_data' => 'seo:dashboard:1'],
                ['text' => $period(3, '3 дня'), 'callback_data' => 'seo:dashboard:3'],
                ['text' => $period(7, '7 дней'), 'callback_data' => 'seo:dashboard:7'],
                ['text' => $period(30, '30 дней'), 'callback_data' => 'seo:dashboard:30'],
            ],
            [['text' => '📄 Текстовая сводка', 'callback_data' => "seo:section:summary:{$days}"]],
            [['text' => '🔄 Обновить', 'callback_data' => 'seo:refresh']],
        ];
    }

    /** @return array<string, mixed> */
    private function moreChartsMenu(int $days): array
    {
        return [
            'text' => '📊 Ещё графики · '.$this->periodLabel($days),
            'keyboard' => [
                [['text' => '🏆 TOP-10 динамика', 'callback_data' => "seo:chart:top10:{$days}"]],
                [['text' => '📊 Распределение TOP', 'callback_data' => "seo:chart:distribution:{$days}"]],
                [['text' => '🚀 Рост / падение', 'callback_data' => "seo:chart:growthdrop:{$days}"]],
                [['text' => '⬅️ Назад к дашборду', 'callback_data' => "seo:dashboard:{$days}"]],
            ],
        ];
    }

    /** @param array<string, mixed> $dashboard
     *  @return array<string, mixed>
     */
    private function visualChart(array $dashboard, string $kind, int $days): array
    {
        $chartsRoot = is_array($dashboard['charts'] ?? null) ? $dashboard['charts'] : [];
        [$bucket, $label] = match ($kind) {
            'positions', 'average' => ['average_position', '📈 Динамика средней позиции'],
            'top10' => ['top10_dynamics', '🏆 Динамика TOP-10'],
            'distribution' => ['distribution', '📊 Распределение по TOP'],
            'growthdrop' => ['growth_drop', '🚀 Рост и падение позиций'],
            'traffic' => ['traffic', '🌐 Органический трафик'],
            'conversions' => ['conversions', '🎯 Конверсии'],
        };
        $bucketData = is_array($chartsRoot[$bucket] ?? null) ? $chartsRoot[$bucket] : [];
        $path = $bucketData[(string) $days] ?? null;
        $photos = is_string($path) ? $this->photosFor([$path]) : [];
        $backKeyboard = [[['text' => '⬅️ Назад к дашборду', 'callback_data' => "seo:dashboard:{$days}"]]];

        if ($photos === []) {
            return [
                'text' => "{$label}\n\nГрафик пока недоступен: недостаточно данных за этот период.",
                'keyboard' => $backKeyboard,
            ];
        }

        return [
            'text' => $label.' · '.$this->periodLabel($days),
            'photos' => $photos,
            'keyboard' => $backKeyboard,
        ];
    }

    /** @param array<string, mixed> $dashboard
     *  @return array<string, mixed>
     */
    private function wordstatChart(array $dashboard): array
    {
        $path = $dashboard['charts']['wordstat'] ?? null;
        $photos = is_string($path) ? $this->photosFor([$path]) : [];
        if ($photos === []) {
            return [
                'text' => "🔑 Wordstat\n\nЧастотность ещё не собрана.",
                'keyboard' => $this->backKeyboard(),
            ];
        }

        return [
            'text' => '🔑 Частотность ядра (Wordstat)',
            'photos' => $photos,
            'keyboard' => $this->backKeyboard(),
        ];
    }

    private function periodLabel(int $days): string
    {
        return match ($days) {
            1 => 'сегодня',
            3 => '3 дня',
            7 => '7 дней',
            default => '30 дней',
        };
    }

    /** @param array<int, string|null> $paths
     *  @return array<int, array{base64: string, filename: string}>
     */
    private function photosFor(array $paths): array
    {
        $photos = [];
        foreach ($paths as $path) {
            if (! is_string($path) || $path === '' || ! is_file($path) || ! is_readable($path)) {
                continue;
            }
            $contents = file_get_contents($path);
            if ($contents === false) {
                continue;
            }
            $photos[] = ['base64' => base64_encode($contents), 'filename' => basename($path)];
        }

        return $photos;
    }

    // === Legacy text views (kept for backward compatibility & drill-down) ===

    /** @param array<string, mixed> $dashboard */
    private function menuText(array $dashboard): string
    {
        $labels = $dashboard['source_labels'] ?? [];
        $value = static fn (string $name): string => is_array($labels)
            ? (string) ($labels[$name] ?? 'нет данных') : 'нет данных';

        return implode("\n", [
            '🔎 SEO-мониторинг', '',
            'Контрольные позиции: Topvisor — '.$value('topvisor'),
            'Поисковая аналитика: Webmaster — '.$value('yandex_webmaster'),
            'Органика и конверсии: Metrika — '.$value('yandex_metrika'), '',
            'Дата позиции: '.(string) ($dashboard['anchor_date'] ?? 'нет данных'),
        ]);
    }

    /** @param array<string, mixed> $dashboard */
    private function summaryText(array $dashboard, int $days): string
    {
        $summary = $dashboard['periods'][(string) $days]['positions'] ?? null;
        if (! is_array($summary)) {
            return "📊 Сводка · {$days}D\n\nДанные за период ещё не подготовлены.";
        }
        $metric = static fn (string $key): string => array_key_exists($key, $summary)
            && $summary[$key] !== null ? (string) $summary[$key] : '—';

        return implode("\n", [
            "📊 SEO-сводка · {$days}D", '',
            'Всего запросов: '.$metric('total'),
            'TOP-3 / 10 / 20 / 50: '.$metric('top3').' / '.$metric('top10').' / '.$metric('top20').' / '.$metric('top50'),
            'Не найдено: '.$metric('not_found'),
            'Средняя позиция: '.$metric('average_position'), '',
            '📈 Выросло: '.$metric('improved').'  ·  📉 Упало: '.$metric('declined'),
            '🆕 Новых: '.$metric('appeared').'  ·  ❌ Пропало: '.$metric('disappeared'), '',
            'Источник позиций: Topvisor',
            'Обновлено: '.(string) ($dashboard['generated_at'] ?? 'время неизвестно'),
        ]);
    }

    /** @param array<string, mixed> $dashboard */
    private function positionsText(array $dashboard, int $days): string
    {
        $rows = is_array($dashboard['keywords'] ?? null) ? $dashboard['keywords'] : [];
        $histories = is_array($dashboard['keyword_histories'] ?? null)
            ? $dashboard['keyword_histories'] : [];
        usort($rows, static fn (array $a, array $b): int =>
            ($a['position'] ?? 999) <=> ($b['position'] ?? 999));
        $lines = ["🔎 Позиции · {$days}D", '', 'Первые 14 из '.count($rows).' запросов:'];
        foreach (array_slice($rows, 0, 14) as $row) {
            $history = $histories[(string) ($row['keyword_id'] ?? 0)] ?? [];
            $baseline = is_array($history) ? ($history['periods'][(string) $days] ?? null) : null;
            $current = ($row['status'] ?? null) === 'found' ? (string) $row['position'] : '—';
            $previous = is_array($baseline) && ($baseline['status'] ?? null) === 'found'
                ? (string) $baseline['position'] : '—';
            $change = is_array($baseline) && ($baseline['change'] ?? null) !== null
                ? sprintf('%+g', (float) $baseline['change']) : '—';
            $lines[] = '• '.(string) $row['keyword'];
            $lines[] = "  {$previous} → {$current} ({$change}) · частота ".
                ($row['frequency'] ?? '—');
        }
        $lines[] = '';
        $lines[] = 'Полная таблица, фильтры и история каждого ключа — в Web dashboard.';

        return implode("\n", $lines);
    }

    /** @param array<string, mixed> $dashboard */
    private function webmasterText(array $dashboard, int $days): string
    {
        $source = $dashboard['sources']['yandex_webmaster'] ?? null;
        $data = $dashboard['periods'][(string) $days]['webmaster'] ?? null;
        if (! is_array($source) || ($source['status'] ?? null) === 'not_configured') {
            return "🔍 Yandex Webmaster · {$days}D\n\nИсточник ещё не подключён: нет credentials или sync не выполнялся.";
        }
        if (($source['status'] ?? null) === 'error') {
            return "🔍 Yandex Webmaster · {$days}D\n\nПоследняя синхронизация завершилась ошибкой. Значения не заменены нулями.";
        }
        if (! is_array($data) || ($data['query_count'] ?? null) === null) {
            return "🔍 Yandex Webmaster · {$days}D\n\nИсточник подключён, sync выполнен. За выбранный период строк нет — это не нули.";
        }
        $metric = static fn (string $key): string => array_key_exists($key, $data)
            && $data[$key] !== null ? (string) $data[$key] : '—';
        $lines = ["🔍 Yandex Webmaster · {$days}D", '',
            'Запросов: '.$metric('query_count'), 'Показы: '.$metric('shows'),
            'Клики: '.$metric('clicks'), 'CTR: '.$metric('ctr').'%',
            'Новых запросов: '.count(is_array($data['new_queries'] ?? null) ? $data['new_queries'] : []),
        ];
        foreach (array_slice($data['new_queries'] ?? [], 0, 6) as $row) {
            if (is_array($row)) {
                $lines[] = '• '.$row['query_text'].' · показы '.($row['shows'] ?? '—');
            }
        }

        return implode("\n", $lines);
    }

    /** @param array<string, mixed> $dashboard */
    private function metrikaText(array $dashboard, int $days): string
    {
        $source = $dashboard['sources']['yandex_metrika'] ?? null;
        $data = $dashboard['periods'][(string) $days]['metrika'] ?? null;
        if (! is_array($source) || ($source['status'] ?? null) === 'not_configured') {
            return "📈 Yandex Metrika · {$days}D\n\nИсточник ещё не подключён: нет credentials или sync не выполнялся.";
        }
        if (($source['status'] ?? null) === 'error') {
            return "📈 Yandex Metrika · {$days}D\n\nПоследняя синхронизация завершилась ошибкой. Значения не заменены нулями.";
        }
        if (! is_array($data) || ($data['visits'] ?? null) === null) {
            return "📈 Yandex Metrika · {$days}D\n\nИсточник подключён, sync выполнен. Органических строк за период нет — это не нули.";
        }
        $metric = static fn (string $key): string => array_key_exists($key, $data)
            && $data[$key] !== null ? (string) $data[$key] : '—';

        return implode("\n", [
            "📈 Yandex Metrika · {$days}D", '',
            'Органические визиты: '.$metric('visits'),
            'Пользователи: '.$metric('users'),
            'Отказы: '.$metric('bounce_rate').'%',
            'Глубина: '.$metric('page_depth'),
            'Достижения целей: '.$metric('goal_reaches'),
            'Мессенджеры: '.$metric('messenger_reaches'), '',
            'Конверсии связаны только с landing page, не с конкретным запросом.',
        ]);
    }

    /** @param array<string, mixed>|null $audit */
    private function technicalText(?array $audit): string
    {
        if ($audit === null) {
            return "🛠 Technical SEO\n\nАудит ещё не выполнен или файл отчёта недоступен.";
        }
        $pages = is_array($audit['pages'] ?? null) ? $audit['pages'] : [];
        $errors = $warnings = $ok = 0;
        foreach ($pages as $page) {
            if (! is_array($page)) {
                continue;
            }
            $pageErrors = is_array($page['errors'] ?? null) ? $page['errors'] : [];
            $pageWarnings = is_array($page['warnings'] ?? null) ? $page['warnings'] : [];
            $errors += count($pageErrors);
            $warnings += count($pageWarnings);
            $ok += $pageErrors === [] && $pageWarnings === [] ? 1 : 0;
        }

        return implode("\n", [
            '🛠 Technical SEO', '',
            'Проверено страниц: '.count($pages),
            '✅ OK: '.$ok,
            '❌ Ошибки: '.$errors,
            '⚠️ Предупреждения: '.$warnings, '',
            'Проверяются HTTP, title, description, H1, canonical, robots, sitemap, indexability и JSON-LD.',
            'Подробный status board доступен в Web dashboard.',
        ]);
    }

    /** @param array<string, mixed> $dashboard */
    private function chartsText(array $dashboard, int $days): string
    {
        $visual = $dashboard['visualizations'][(string) $days] ?? null;
        $points = is_array($visual) && is_array($visual['average_position'] ?? null)
            ? count(array_filter($visual['average_position'], static fn (mixed $row): bool =>
                is_array($row) && ($row['average_position'] ?? null) !== null)) : 0;

        return implode("\n", [
            "📉 Графики · {$days}D", '',
            'Точек средней позиции: '.$points,
            'Доступны: средняя позиция, распределение TOP-3/10/20/50, динамика роста/падения и история каждого ключа.', '',
            'PNG-графики можно открыть кнопками ниже. Полная интерактивная визуализация — в Web dashboard.',
        ]);
    }

    /** @return array<int, array<int, array<string, string>>> */
    private function mainKeyboard(): array
    {
        return $this->dashboardKeyboard(7);
    }

    /** @return array<int, array<int, array<string, string>>> */
    private function sectionKeyboard(string $section, int $days): array
    {
        $period = static fn (int $value): string => $value === $days ? '• '.$value.'D' : $value.'D';
        $dashboardUrl = $this->dashboardUrl();
        $keyboard = [
            [
                ['text' => '📊 Сводка', 'callback_data' => "seo:section:summary:{$days}"],
                ['text' => '🔎 Позиции', 'callback_data' => "seo:section:positions:{$days}"],
            ],
            [
                ['text' => '🔍 Webmaster', 'callback_data' => "seo:section:webmaster:{$days}"],
                ['text' => '📈 Metrika', 'callback_data' => "seo:section:metrika:{$days}"],
            ],
            [
                ['text' => '🛠 Technical SEO', 'callback_data' => "seo:section:technical:{$days}"],
                ['text' => '📉 Графики', 'callback_data' => "seo:section:charts:{$days}"],
            ],
            [
                ['text' => $period(1), 'callback_data' => "seo:section:{$section}:1"],
                ['text' => $period(3), 'callback_data' => "seo:section:{$section}:3"],
                ['text' => $period(7), 'callback_data' => "seo:section:{$section}:7"],
                ['text' => $period(30), 'callback_data' => "seo:section:{$section}:30"],
            ],
            [['text' => '🖼 Дашборд', 'callback_data' => "seo:dashboard:{$days}"]],
        ];
        if ($section === 'charts') {
            $chartDays = $days >= 30 ? 30 : 7;
            $keyboard[] = [
                ['text' => '📈 Средняя позиция', 'callback_data' => "seo:chart:positions:{$chartDays}"],
                ['text' => '🏆 TOP-10', 'callback_data' => 'seo:chart:top10:30'],
            ];
        }
        if ($dashboardUrl !== null) {
            $keyboard[] = [['text' => '🌐 Web dashboard', 'url' => $dashboardUrl]];
        }
        $keyboard[] = [['text' => '🔄 Обновить', 'callback_data' => 'seo:refresh']];

        return $keyboard;
    }

    private function dashboardUrl(): ?string
    {
        if (! app('router')->has('seo.dashboard.access')) {
            return null;
        }
        $minutes = max(5, (int) config('services.seo_dashboard.signed_link_minutes', 60));

        return URL::temporarySignedRoute(
            'seo.dashboard.access',
            now()->addMinutes($minutes),
        );
    }

    /** @return array<int, array<int, array<string, string>>> */
    private function legacyMainKeyboard(): array
    {
        return [
            [['text' => '📅 Сегодня', 'callback_data' => 'seo:period:1']],
            [
                ['text' => '📅 3 дня', 'callback_data' => 'seo:period:3'],
                ['text' => '📅 7 дней', 'callback_data' => 'seo:period:7'],
                ['text' => '📅 30 дней', 'callback_data' => 'seo:period:30'],
            ],
            [
                ['text' => '🏆 TOP-10', 'callback_data' => 'seo:top10'],
                ['text' => '📈 Рост', 'callback_data' => 'seo:growth'],
                ['text' => '📉 Падение', 'callback_data' => 'seo:drop'],
            ],
            [
                ['text' => '❌ Не найдено', 'callback_data' => 'seo:not_found'],
                ['text' => '🔑 Запросы', 'callback_data' => 'seo:keywords:0'],
            ],
            [['text' => '📊 Webmaster + Metrika', 'callback_data' => 'seo:analytics']],
            [
                ['text' => '📈 Позиции 30 дней', 'callback_data' => 'seo:chart:positions:30'],
                ['text' => '🏆 TOP-10 30 дней', 'callback_data' => 'seo:chart:top10:30'],
            ],
            [['text' => '🔄 Обновление', 'callback_data' => 'seo:refresh']],
        ];
    }

    /** @return array<int, array<int, array{text: string, callback_data: string}>> */
    private function backKeyboard(): array
    {
        return [[['text' => '⬅️ Назад', 'callback_data' => 'seo:menu']]];
    }

    /** @param array<string, mixed> $dashboard */
    private function positionList(array $dashboard, string $type): string
    {
        $rows = is_array($dashboard['keywords'] ?? null) ? $dashboard['keywords'] : [];
        $selected = array_values(array_filter($rows, static function (mixed $row) use ($type): bool {
            if (! is_array($row)) {
                return false;
            }

            return $type === 'top10'
                ? ($row['status'] ?? null) === 'found' && (int) ($row['position'] ?? 999) <= 10
                : ($row['status'] ?? null) === 'not_found';
        }));
        $title = $type === 'top10' ? '🏆 Запросы в TOP-10' : '❌ Не найдено в TOP-100';
        if ($selected === []) {
            return $title."\n\nНет запросов.";
        }
        $lines = [$title, ''];
        foreach (array_slice($selected, 0, 30) as $row) {
            $position = $row['position'] ?? '—';
            $frequency = array_key_exists('frequency', $row) && $row['frequency'] !== null
                ? ' · частота '.$row['frequency'] : '';
            $lines[] = $row['keyword'].' — '.$position.$frequency;
        }

        return implode("\n", $lines);
    }

    /** @param array<string, mixed> $dashboard */
    private function movementList(array $dashboard, string $type): string
    {
        $summary = $dashboard['periods']['7']['positions'] ?? [];
        $rows = $summary[$type === 'growth' ? 'best_growth' : 'worst_drop'] ?? [];
        $title = $type === 'growth' ? '📈 Рост за 7 дней' : '📉 Падение за 7 дней';
        if (! is_array($rows) || $rows === []) {
            return $title."\n\nНет сопоставимых изменений.";
        }
        $lines = [$title, ''];
        foreach (array_slice($rows, 0, 20) as $row) {
            $lines[] = sprintf(
                "%s\n%s → %s (%+.1f)",
                $row['keyword'], $row['before'], $row['current'], (float) ($row['change'] ?? 0),
            );
        }

        return implode("\n", $lines);
    }

    /** @param array<string, mixed> $dashboard */
    private function analyticsText(array $dashboard): string
    {
        $period = $dashboard['periods']['7'] ?? [];
        $webmaster = is_array($period['webmaster'] ?? null) ? $period['webmaster'] : [];
        $metrika = is_array($period['metrika'] ?? null) ? $period['metrika'] : [];
        $metric = static fn (array $row, string $key): string => array_key_exists($key, $row)
            && $row[$key] !== null ? (string) $row[$key] : 'нет данных';

        return implode("\n", [
            '📊 Фактическая аналитика за 7 дней', '', 'Webmaster:',
            'Показы: '.$metric($webmaster, 'shows'),
            'Клики: '.$metric($webmaster, 'clicks'),
            'CTR: '.$metric($webmaster, 'ctr'),
            'Новых запросов: '.(is_array($webmaster['new_queries'] ?? null)
                ? count($webmaster['new_queries']) : 'нет данных'), '',
            'Metrika — органика:',
            'Визиты: '.$metric($metrika, 'visits'),
            'Пользователи: '.$metric($metrika, 'users'),
            'Достижения целей: '.$metric($metrika, 'goal_reaches'),
            'Мессенджеры: '.$metric($metrika, 'messenger_reaches'), '',
            'Конверсии связываются только с landing page, не с конкретным запросом.',
        ]);
    }

    /** @param array<string, mixed> $dashboard
     *  @return array<string, mixed>
     */
    private function keywordPage(array $dashboard, int $offset): array
    {
        $keywords = array_values(is_array($dashboard['keywords'] ?? null) ? $dashboard['keywords'] : []);
        $offset = max(0, min($offset, max(count($keywords) - 1, 0)));
        $page = array_slice($keywords, $offset, 8);
        $keyboard = [];
        foreach ($page as $row) {
            if (! is_array($row)) {
                continue;
            }
            $position = ($row['status'] ?? null) === 'found' ? (string) $row['position'] : '—';
            $keyboard[] = [[
                'text' => $position.' · '.mb_strimwidth((string) $row['keyword'], 0, 42, '…'),
                'callback_data' => 'seo:keyword:'.(int) $row['keyword_id'],
            ]];
        }
        $navigation = [];
        if ($offset > 0) {
            $navigation[] = ['text' => '◀️', 'callback_data' => 'seo:keywords:'.max(0, $offset - 8)];
        }
        if ($offset + 8 < count($keywords)) {
            $navigation[] = ['text' => '▶️', 'callback_data' => 'seo:keywords:'.($offset + 8)];
        }
        if ($navigation !== []) {
            $keyboard[] = $navigation;
        }
        $keyboard[] = [['text' => '⬅️ Назад', 'callback_data' => 'seo:menu']];

        return [
            'text' => '🔑 Целевые запросы '.($offset + 1).'–'.min($offset + 8, count($keywords)).
                ' из '.count($keywords),
            'keyboard' => $keyboard,
        ];
    }

    /** @param array<string, mixed> $dashboard
     *  @return array<string, mixed>
     */
    private function keywordDetail(array $dashboard, int $keywordId): array
    {
        $history = $dashboard['keyword_histories'][(string) $keywordId] ?? null;
        if (! is_array($history)) {
            return ['error' => 'Unknown keyword.', 'text' => 'Запрос не найден.'];
        }
        $current = is_array($history['current'] ?? null) ? $history['current'] : [];
        $keyboard = [
            [['text' => '⬅️ К списку', 'callback_data' => 'seo:keywords:0']],
            [['text' => '⬅️ В меню', 'callback_data' => 'seo:menu']],
        ];

        $chartsRoot = is_array($dashboard['charts'] ?? null) ? $dashboard['charts'] : [];
        $keywordCharts = is_array($chartsRoot['keyword'] ?? null) ? $chartsRoot['keyword'] : [];
        $path = $keywordCharts[(string) $keywordId] ?? null;
        $photos = is_string($path) ? $this->photosFor([$path]) : [];

        if ($photos !== []) {
            return [
                'text' => '🔑 '.(string) ($history['keyword'] ?? ''),
                'photos' => $photos,
                'keyboard' => $keyboard,
            ];
        }

        // Graceful text fallback: chart image missing (matplotlib unavailable,
        // or the keyword has no history yet), same information as text.
        $lines = ['🔑 '.(string) ($history['keyword'] ?? ''), '',
            'Сейчас: '.($current['position'] ?? 'не найдено')];
        foreach ([3, 7, 30] as $days) {
            $row = $history['periods'][(string) $days] ?? $history['periods'][$days] ?? null;
            $lines[] = $days.' дней: '.(is_array($row)
                ? (($row['position'] ?? 'не найдено').' · изменение '.($row['change'] ?? '—'))
                : 'нет измерения');
        }
        if (! empty($current['found_url'])) {
            $lines[] = '';
            $lines[] = 'URL: '.$current['found_url'];
        }

        return ['text' => implode("\n", $lines), 'keyboard' => $keyboard];
    }
}
