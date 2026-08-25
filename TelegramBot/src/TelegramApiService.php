<?php

declare(strict_types=1);

namespace TelegramBot;

use RuntimeException;

final class TelegramApiService
{
    public function __construct(
        private readonly string $token,
        private readonly string $chatId,
    ) {
        if ($this->token === '' || $this->chatId === '') {
            throw new RuntimeException('TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID must be configured.');
        }
    }

    /** @param array<string, string> $fields */
    public function sendLead(string $name, string $phone, array $fields = []): void
    {
        $lines = [
            '📩 Новая заявка',
            '',
            '👤 Имя: '. $this->escape($name),
            '📞 Телефон: '. $this->escape($phone),
        ];

        foreach ($fields as $label => $value) {
            if ($value !== '') {
                $lines[] = $this->escape((string) $label).': '.$this->escape($value);
            }
        }

        $this->request('sendMessage', [
            'chat_id' => $this->chatId,
            'text' => implode("\n", $lines),
            'parse_mode' => 'HTML',
        ]);
    }

    /** @param array<string, string> $payload */
    private function request(string $method, array $payload): void
    {
        $handle = curl_init('https://api.telegram.org/bot'.$this->token.'/'.$method);
        curl_setopt_array($handle, [
            CURLOPT_POST => true,
            CURLOPT_POSTFIELDS => http_build_query($payload),
            CURLOPT_RETURNTRANSFER => true,
            CURLOPT_CONNECTTIMEOUT => 5,
            CURLOPT_TIMEOUT => 15,
            CURLOPT_HTTPHEADER => ['Content-Type: application/x-www-form-urlencoded'],
        ]);

        $response = curl_exec($handle);
        $error = curl_error($handle);
        $status = (int) curl_getinfo($handle, CURLINFO_RESPONSE_CODE);
        curl_close($handle);

        if ($response === false || $error !== '') {
            throw new RuntimeException('Telegram connection failed: '.$error);
        }

        $decoded = json_decode($response, true);
        if ($status >= 400 || !is_array($decoded) || !($decoded['ok'] ?? false)) {
            $description = is_array($decoded) ? ($decoded['description'] ?? 'Unknown Telegram API error') : 'Invalid Telegram API response';
            throw new RuntimeException('Telegram API error ('.$status.'): '.$description);
        }
    }

    private function escape(string $value): string
    {
        return htmlspecialchars($value, ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8');
    }
}
