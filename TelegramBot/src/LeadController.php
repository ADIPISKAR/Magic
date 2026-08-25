<?php

declare(strict_types=1);

namespace TelegramBot;

use Throwable;

final class LeadController
{
    public function __construct(private readonly TelegramApiService $telegram)
    {
    }

    /** @return array<string, mixed> */
    public function handle(array $payload): array
    {
        $name = trim((string) ($payload['name'] ?? ''));
        $phone = trim((string) ($payload['phone'] ?? ''));

        if ($name === '' || $phone === '') {
            return ['status' => 422, 'body' => ['message' => 'Name and phone are required.']];
        }

        try {
            $extraFields = [];
            foreach (['message', 'source'] as $field) {
                if (isset($payload[$field])) {
                    $extraFields[$field] = trim((string) $payload[$field]);
                }
            }

            $this->telegram->sendLead($name, $phone, $extraFields);

            return ['status' => 202, 'body' => ['message' => 'Lead accepted.']];
        } catch (Throwable $exception) {
            error_log('[telegram-bot] '.$exception->getMessage());

            return ['status' => 502, 'body' => ['message' => 'Unable to deliver lead.']];
        }
    }
}
