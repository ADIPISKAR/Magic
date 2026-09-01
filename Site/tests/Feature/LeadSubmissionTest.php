<?php

namespace Tests\Feature;

use Illuminate\Http\Client\Request;
use Illuminate\Support\Facades\Http;
use Tests\TestCase;

class LeadSubmissionTest extends TestCase
{
    public function test_calculator_context_is_forwarded_with_the_lead(): void
    {
        config()->set('services.telegram_bot.url', 'https://bot.test');
        config()->set('services.telegram_bot.secret', 'test-secret');
        Http::fake(['https://bot.test/api/leads' => Http::response(['message' => 'accepted'], 202)]);

        $payload = [
            'name' => 'Иван',
            'phone' => '+7 900 000-00-00',
            'message' => 'Новостройка, 80 м², дизайнерский, ориентир от 1 600 000 ₽',
            'source' => 'Калькулятор стоимости',
        ];

        $this->postJson('/api/leads', $payload)->assertStatus(202);

        Http::assertSent(fn (Request $request) => $request->url() === 'https://bot.test/api/leads'
            && $request->hasHeader('X-Bot-Api-Secret', 'test-secret')
            && $request->data() === $payload);
    }
}
