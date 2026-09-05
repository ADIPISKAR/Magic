<?php

declare(strict_types=1);

namespace Tests\Feature;

use Illuminate\Support\Facades\Config;
use Illuminate\Testing\Fluent\AssertableJson;
use Tests\TestCase;

final class SeoTelegramTest extends TestCase
{
    private string $dashboard;

    protected function setUp(): void
    {
        parent::setUp();
        $this->dashboard = tempnam(sys_get_temp_dir(), 'seo-dashboard-');
        file_put_contents($this->dashboard, json_encode([
            'anchor_date' => '2026-09-02',
            'source_labels' => [
                'topvisor' => 'готово',
                'yandex_webmaster' => 'не настроено',
                'yandex_metrika' => 'не настроено',
            ],
            'generated_at' => '2026-09-02T12:00:00+03:00',
            'sources' => [
                'topvisor' => ['status' => 'ok'],
                'yandex_webmaster' => ['status' => 'not_configured'],
                'yandex_metrika' => ['status' => 'not_configured'],
            ],
            'keywords' => [[
                'keyword_id' => 1,
                'keyword' => 'ремонт квартир ростов-на-дону',
                'status' => 'not_found',
                'position' => null,
                'frequency' => 53,
            ]],
            'keyword_histories' => ['1' => [
                'keyword' => 'ремонт квартир ростов-на-дону',
                'current' => ['position' => null, 'found_url' => null],
                'periods' => ['3' => null, '7' => null, '30' => null],
            ]],
            'periods' => [
                '1' => ['positions' => ['total' => 1]],
                '3' => ['telegram_text' => 'Отчёт 3 дня', 'positions' => ['total' => 1]],
                '7' => [
                    'telegram_text' => 'Отчёт 7 дней',
                    'positions' => [
                        'total' => 1,
                        'top3' => 0,
                        'top10' => 0,
                        'top20' => 0,
                        'top50' => 0,
                        'not_found' => 1,
                        'average_position' => null,
                        'improved' => 0,
                        'declined' => 0,
                        'appeared' => 0,
                        'disappeared' => 0,
                        'best_growth' => [],
                        'worst_drop' => [],
                    ],
                    'webmaster' => ['shows' => null, 'clicks' => null, 'ctr' => null, 'new_queries' => []],
                    'metrika' => ['visits' => null, 'users' => null, 'goal_reaches' => null, 'messenger_reaches' => null],
                ],
                '30' => ['telegram_text' => 'Отчёт 30 дней', 'positions' => ['total' => 1]],
            ],
            'visualizations' => ['7' => ['average_position' => []]],
            'charts' => [],
        ], JSON_UNESCAPED_UNICODE));
        Config::set('services.seo_backend.secret', 'test-secret');
        Config::set('services.seo_backend.dashboard_path', $this->dashboard);
    }

    protected function tearDown(): void
    {
        @unlink($this->dashboard);
        parent::tearDown();
    }

    public function test_backend_requires_its_secret(): void
    {
        $this->postJson('/api/seo/telegram', ['action' => 'menu'])->assertUnauthorized();
    }

    public function test_menu_shows_the_visual_dashboard_keyboard_and_falls_back_to_text_without_charts(): void
    {
        // The fixture's dashboard has no rendered charts ('charts' => []), so
        // the visual-first menu gracefully falls back to a text summary --
        // but it must still offer the new image-first navigation, not the
        // old text-only section menu.
        $this->withHeader('X-SEO-Backend-Secret', 'test-secret')
            ->postJson('/api/seo/telegram', ['action' => 'menu'])
            ->assertOk()
            ->assertJson(fn (AssertableJson $json) => $json
                ->where('keyboard.0.0.text', '📈 Позиции')
                ->where('keyboard.0.0.callback_data', 'seo:chart:positions:7')
                ->where('keyboard.0.1.text', '🌐 Трафик')
                ->where('keyboard.1.0.text', '🎯 Конверсии')
                ->where('keyboard.1.1.text', '🔑 Wordstat')
                ->where('keyboard.2.0.text', '📊 Ещё графики')
                ->where('keyboard.2.0.callback_data', 'seo:more:7')
                ->where('keyboard.3.0.text', 'Сегодня')
                ->where('keyboard.3.1.text', '3 дня')
                ->where('keyboard.3.2.text', '• 7 дней')
                ->where('keyboard.3.2.callback_data', 'seo:dashboard:7')
                ->where('keyboard.3.3.text', '30 дней')
                ->where('keyboard.4.0.text', '📄 Текстовая сводка')
                ->where('keyboard.4.0.callback_data', 'seo:section:summary:7')
                ->where('keyboard.5.0.text', '🔄 Обновить')
                ->missing('photos')
                ->etc());
    }

    public function test_period_returns_the_dashboard_for_the_requested_period(): void
    {
        $this->withHeader('X-SEO-Backend-Secret', 'test-secret')
            ->postJson('/api/seo/telegram', ['action' => 'period:7'])
            ->assertOk()
            ->assertJsonPath('keyboard.3.2.text', '• 7 дней')
            ->assertJsonPath('keyboard.3.2.callback_data', 'seo:dashboard:7')
            ->assertJsonPath('keyboard.4.0.callback_data', 'seo:section:summary:7');
    }

    public function test_section_keeps_the_selected_period_across_the_private_menu(): void
    {
        $this->withHeader('X-SEO-Backend-Secret', 'test-secret')
            ->postJson('/api/seo/telegram', ['action' => 'section:webmaster:30'])
            ->assertOk()
            ->assertJsonPath('keyboard.0.0.callback_data', 'seo:section:summary:30')
            ->assertJsonPath('keyboard.1.0.callback_data', 'seo:section:webmaster:30')
            ->assertJsonPath('keyboard.3.3.text', '• 30D')
            ->assertJsonPath('keyboard.3.0.callback_data', 'seo:section:webmaster:1')
            ->assertJsonPath('text', "🔍 Yandex Webmaster · 30D\n\nИсточник ещё не подключён: нет credentials или sync не выполнялся.");
    }

    public function test_body_secret_supports_fastcgi_that_does_not_forward_custom_headers(): void
    {
        $this->postJson('/api/seo/telegram', [
            'action' => 'period:3',
            '_backend_secret' => 'test-secret',
        ])->assertOk()->assertJsonPath('keyboard.3.1.text', '• 3 дня');
    }
}
