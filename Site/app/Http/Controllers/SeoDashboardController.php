<?php

declare(strict_types=1);

namespace App\Http\Controllers;

use Illuminate\Http\JsonResponse;
use Illuminate\Http\RedirectResponse;
use Illuminate\Http\Request;
use Illuminate\View\View;

final class SeoDashboardController extends Controller
{
    private const SESSION_KEY = 'seo_dashboard_authorized';

    public function index(Request $request): View
    {
        if (! $request->session()->get(self::SESSION_KEY, false)) {
            return view('seo-dashboard-login');
        }

        return view('seo-dashboard');
    }

    public function access(Request $request): RedirectResponse
    {
        $request->session()->regenerate();
        $request->session()->put(self::SESSION_KEY, true);

        return redirect()->route('seo.dashboard');
    }

    public function logout(Request $request): RedirectResponse
    {
        $request->session()->forget(self::SESSION_KEY);
        $request->session()->regenerateToken();

        return redirect()->route('seo.dashboard');
    }

    public function data(Request $request): JsonResponse
    {
        abort_unless($request->session()->get(self::SESSION_KEY, false), 401);

        $days = (int) $request->integer('period', 7);
        abort_unless(in_array($days, [1, 3, 7, 30], true), 422);

        $dashboard = $this->readJson((string) config('services.seo_backend.dashboard_path', ''));
        abort_if($dashboard === null, 503, 'SEO dashboard is not available yet.');

        $period = $dashboard['periods'][(string) $days] ?? null;
        abort_unless(is_array($period), 503, 'Selected SEO period is not available.');

        $response = response()->json([
            'generated_at' => $dashboard['generated_at'] ?? null,
            'anchor_date' => $dashboard['anchor_date'] ?? null,
            'period_days' => $days,
            'position_source' => $dashboard['position_source'] ?? 'topvisor',
            'search_api_reserve_enabled' => (bool) ($dashboard['search_api_reserve_enabled'] ?? false),
            'sources' => $this->safeSources($dashboard['sources'] ?? []),
            'summary' => $period['positions'] ?? [],
            'positions' => $this->positionRows($dashboard, $days),
            'visualizations' => $dashboard['visualizations'][(string) $days] ?? [],
            'keyword_series' => $dashboard['keyword_series'] ?? [],
            'webmaster' => $period['webmaster'] ?? [],
            'metrika' => $period['metrika'] ?? [],
            'technical' => $this->technicalReport(),
        ]);

        return $response->header('Cache-Control', 'no-store, private');
    }

    /** @return array<string, mixed>|null */
    private function readJson(string $path): ?array
    {
        if ($path === '' || ! is_file($path) || ! is_readable($path)) {
            return null;
        }

        $contents = file_get_contents($path);
        $decoded = $contents === false ? null : json_decode($contents, true);

        return is_array($decoded) ? $decoded : null;
    }

    /** @param mixed $sources
     *  @return array<string, array<string, mixed>>
     */
    private function safeSources(mixed $sources): array
    {
        $sources = is_array($sources) ? $sources : [];
        $result = [];
        foreach (['topvisor', 'yandex_webmaster', 'yandex_metrika'] as $name) {
            $source = is_array($sources[$name] ?? null) ? $sources[$name] : [];
            $status = (string) ($source['status'] ?? 'not_configured');
            $result[$name] = [
                'status' => $status,
                'state' => match ($status) {
                    'ok' => 'connected',
                    'error' => 'error',
                    default => 'not_configured',
                },
                'finished_at' => $source['finished_at'] ?? null,
                'period_start' => $source['period_start'] ?? null,
                'period_end' => $source['period_end'] ?? null,
                'row_count' => $source['row_count'] ?? null,
            ];
        }

        return $result;
    }

    /** @param array<string, mixed> $dashboard
     *  @return array<int, array<string, mixed>>
     */
    private function positionRows(array $dashboard, int $days): array
    {
        $keywords = is_array($dashboard['keywords'] ?? null) ? $dashboard['keywords'] : [];
        $histories = is_array($dashboard['keyword_histories'] ?? null)
            ? $dashboard['keyword_histories'] : [];
        $rows = [];

        foreach ($keywords as $keyword) {
            if (! is_array($keyword)) {
                continue;
            }
            $id = (int) ($keyword['keyword_id'] ?? 0);
            $history = is_array($histories[(string) $id] ?? null)
                ? $histories[(string) $id] : [];
            $periods = is_array($history['periods'] ?? null) ? $history['periods'] : [];
            $baseline = is_array($periods[(string) $days] ?? null)
                ? $periods[(string) $days] : null;
            $status = (string) ($keyword['status'] ?? 'unchecked');
            $position = $keyword['position'] ?? null;
            $previousStatus = $baseline['status'] ?? null;
            $previousPosition = $baseline['position'] ?? null;
            $change = null;
            $movement = 'unknown';

            if ($status === 'found' && $previousStatus === 'found'
                && is_numeric($position) && is_numeric($previousPosition)) {
                $change = (float) $previousPosition - (float) $position;
                $movement = $change > 0 ? 'growth' : ($change < 0 ? 'drop' : 'stable');
            } elseif ($status === 'found' && $previousStatus === 'not_found') {
                $movement = 'appeared';
            } elseif ($status === 'not_found' && $previousStatus === 'found') {
                $movement = 'disappeared';
            }

            $rows[] = [
                'keyword_id' => $id,
                'keyword' => (string) ($keyword['keyword'] ?? ''),
                'category' => (string) ($keyword['category'] ?? 'Без категории'),
                'position' => $position,
                'previous_position' => $previousPosition,
                'change' => $change,
                'frequency' => $keyword['frequency'] ?? null,
                'landing_page' => $keyword['found_url'] ?? null,
                'status' => $status,
                'movement' => $movement,
                'checked_at' => $keyword['checked_at'] ?? null,
            ];
        }

        return $rows;
    }

    /** @return array<string, mixed> */
    private function technicalReport(): array
    {
        $report = $this->readJson((string) config('services.seo_dashboard.audit_path', ''));
        if ($report === null) {
            return [
                'status' => 'not_available',
                'message' => 'Технический аудит ещё не выполнен.',
                'pages_checked' => null,
                'pages' => [],
            ];
        }

        $pages = is_array($report['pages'] ?? null) ? $report['pages'] : [];
        $errors = 0;
        $warnings = 0;
        foreach ($pages as $page) {
            if (! is_array($page)) {
                continue;
            }
            $errors += count(is_array($page['errors'] ?? null) ? $page['errors'] : []);
            $warnings += count(is_array($page['warnings'] ?? null) ? $page['warnings'] : []);
        }

        return [
            'status' => 'ready',
            'site' => $report['site'] ?? null,
            'checked_at' => $report['checked_at'] ?? null,
            'pages_checked' => $report['pages_checked'] ?? count($pages),
            'error_count' => $errors,
            'warning_count' => $warnings,
            'pages' => $pages,
        ];
    }
}
