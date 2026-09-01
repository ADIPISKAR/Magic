<?php

declare(strict_types=1);

namespace App\Http\Controllers;

use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Http;
use Illuminate\Support\Facades\Log;

final class LeadController extends Controller
{
    public function store(Request $request): JsonResponse
    {
        $validated = $request->validate([
            'name' => ['required', 'string', 'max:100'],
            'phone' => ['required', 'string', 'max:40'],
            'message' => ['nullable', 'string', 'max:1000'],
            'source' => ['nullable', 'string', 'max:100'],
        ]);

        $botUrl = rtrim((string) config('services.telegram_bot.url'), '/');
        $secret = (string) config('services.telegram_bot.secret');

        if ($botUrl === '' || $secret === '') {
            Log::error('Telegram bot integration is not configured.');

            return response()->json(['message' => 'Сервис заявок временно недоступен.'], 503);
        }

        try {
            $response = Http::asJson()
                ->withHeaders(['X-Bot-Api-Secret' => $secret])
                ->timeout(15)
                ->post($botUrl.'/api/leads', $validated);

            if ($response->failed()) {
                Log::error('Telegram bot rejected lead.', [
                    'status' => $response->status(),
                    'response' => $response->json(),
                ]);

                return response()->json(['message' => 'Не удалось отправить заявку.'], 502);
            }

            return response()->json(['message' => 'Заявка отправлена.'], 202);
        } catch (\Throwable $exception) {
            Log::error('Telegram bot request failed.', ['exception' => $exception]);

            return response()->json(['message' => 'Не удалось отправить заявку.'], 502);
        }
    }
}
