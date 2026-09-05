<?php

declare(strict_types=1);

namespace Tests\Feature;

use Illuminate\Support\Facades\Config;
use Illuminate\Support\Facades\URL;
use Tests\TestCase;

final class SeoDashboardTest extends TestCase
{
    private string $dashboard;
    private string $audit;

    protected function setUp(): void
    {
        parent::setUp();
        $this->dashboard = tempnam(sys_get_temp_dir(), 'seo-web-dashboard-');
        $this->audit = tempnam(sys_get_temp_dir(), 'seo-audit-');

        file_put_contents($this->dashboard, json_encode([
            'generated_at' => '2026-09-03T10:00:00+03:00',
            'anchor_date' => '2026-09-03',
            'position_source' => 'topvisor',
            'search_api_reserve_enabled' => false,
            'sources' => [
                'topvisor' => ['status' => 'ok', 'row_count' => 32, 'error_message' => 'secret detail'],
                'yandex_webmaster' => ['status' => 'ok', 'row_count' => 3],
                'yandex_metrika' => ['status' => 'not_configured'],
            ],
            'keywords' => [[
                'keyword_id' => 1,
                'keyword' => 'ремонт квартир ростов-на-дону',
                'category' => 'Ремонт',
                'status' => 'found',
                'position' => 8,
                'frequency' => 53,
                'found_url' => 'https://magiarnd.ru/remont-kvartir',
                'checked_at' => '2026-09-03T09:00:00+03:00',
            ]],
            'keyword_histories' => ['1' => [
                'periods' => ['7' => ['status' => 'found', 'position' => 11]],
            ]],
            'keyword_series' => ['1' => [['date' => '2026-09-03', 'position' => 8]]],
            'periods' => ['7' => [
                'positions' => ['total' => 1, 'top3' => 0, 'top10' => 1, 'average_position' => 8],
                'webmaster' => ['shows' => 100, 'clicks' => 5, 'ctr' => 5.0, 'trend' => []],
                'metrika' => ['visits' => null, 'trend' => []],
            ]],
            'visualizations' => ['7' => [
                'average_position' => [['date' => '2026-09-03', 'average_position' => 8]],
                'distribution' => [],
                'movement' => [],
            ]],
            'charts' => ['average_30' => 'C:\\private\\secret.png'],
        ], JSON_UNESCAPED_UNICODE));

        file_put_contents($this->audit, json_encode([
            'site' => 'https://magiarnd.ru',
            'checked_at' => '2026-09-03T08:00:00+03:00',
            'pages_checked' => 1,
            'pages' => [[
                'url' => 'https://magiarnd.ru/',
                'http_status' => 200,
                'title' => 'Magia',
                'description' => 'Описание',
                'h1_count' => 1,
                'canonical' => 'https://magiarnd.ru/',
                'indexable' => true,
                'errors' => [],
                'warnings' => [],
            ]],
        ], JSON_UNESCAPED_UNICODE));

        Config::set('services.seo_backend.dashboard_path', $this->dashboard);
        Config::set('services.seo_dashboard.audit_path', $this->audit);
    }

    protected function tearDown(): void
    {
        @unlink($this->dashboard);
        @unlink($this->audit);
        parent::tearDown();
    }

    public function test_dashboard_is_protected_until_a_signed_link_is_used(): void
    {
        $this->get('/seo-dashboard')
            ->assertOk()
            ->assertSee('Защищённый SEO-dashboard')
            ->assertDontSee('Ремонт', false);

        $this->getJson('/seo-dashboard/data?period=7')->assertUnauthorized();
    }

    public function test_signed_access_establishes_a_private_read_only_session(): void
    {
        $url = URL::temporarySignedRoute('seo.dashboard.access', now()->addMinute());

        $this->get($url)
            ->assertRedirect(route('seo.dashboard'))
            ->assertSessionHas('seo_dashboard_authorized', true);

        $this->get('/seo-dashboard')
            ->assertOk()
            ->assertSee('SEO Control Center')
            ->assertSee('data-period="30"', false);
    }

    public function test_data_endpoint_returns_sanitized_real_period_data(): void
    {
        $response = $this->withSession(['seo_dashboard_authorized' => true])
            ->getJson('/seo-dashboard/data?period=7')
            ->assertOk()
            ->assertHeader('Cache-Control', 'no-store, private')
            ->assertJsonPath('period_days', 7)
            ->assertJsonPath('position_source', 'topvisor')
            ->assertJsonPath('search_api_reserve_enabled', false)
            ->assertJsonPath('positions.0.previous_position', 11)
            ->assertJsonPath('positions.0.change', 3)
            ->assertJsonPath('positions.0.movement', 'growth')
            ->assertJsonPath('technical.status', 'ready')
            ->assertJsonPath('technical.pages_checked', 1);

        $payload = $response->json();
        $this->assertArrayNotHasKey('error_message', $payload['sources']['topvisor']);
        $this->assertArrayNotHasKey('charts', $payload);
        $this->assertStringNotContainsString('private', $response->getContent());
    }

    public function test_unknown_period_is_rejected_instead_of_returning_fake_data(): void
    {
        $this->withSession(['seo_dashboard_authorized' => true])
            ->getJson('/seo-dashboard/data?period=2')
            ->assertUnprocessable();
    }
}
