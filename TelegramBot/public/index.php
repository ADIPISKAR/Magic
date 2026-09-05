<?php

declare(strict_types=1);

require dirname(__DIR__).'/vendor/autoload.php';

use Dotenv\Dotenv;
use TelegramBot\LeadController;
use TelegramBot\TelegramApiService;

$root = dirname(__DIR__);
Dotenv::createImmutable($root)->safeLoad();

header('Content-Type: application/json; charset=utf-8');

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(204);
    exit;
}

if ($_SERVER['REQUEST_METHOD'] !== 'POST' || ($_SERVER['REQUEST_URI'] ?? '') !== '/api/leads') {
    http_response_code(404);
    echo json_encode(['message' => 'Not found'], JSON_UNESCAPED_UNICODE);
    exit;
}

$expectedSecret = (string) ($_ENV['BOT_API_SECRET'] ?? '');
$providedSecret = (string) ($_SERVER['HTTP_X_BOT_API_SECRET'] ?? '');
if ($expectedSecret === '' || !hash_equals($expectedSecret, $providedSecret)) {
    http_response_code(401);
    echo json_encode(['message' => 'Unauthorized'], JSON_UNESCAPED_UNICODE);
    exit;
}

$payload = json_decode((string) file_get_contents('php://input'), true);
if (!is_array($payload)) {
    http_response_code(400);
    echo json_encode(['message' => 'Invalid JSON body.'], JSON_UNESCAPED_UNICODE);
    exit;
}

try {
    $controller = new LeadController(new TelegramApiService(
        (string) ($_ENV['TELEGRAM_BOT_TOKEN'] ?? ''),
        (string) ($_ENV['TELEGRAM_GROUP_CHAT_ID'] ?? ''),
        (string) ($_ENV['TELEGRAM_LEADS_THREAD_ID'] ?? ''),
    ));
    $result = $controller->handle($payload);
} catch (Throwable $exception) {
    error_log('[telegram-bot] '.$exception->getMessage());
    $result = ['status' => 500, 'body' => ['message' => 'Bot configuration error.']];
}

http_response_code((int) $result['status']);
echo json_encode($result['body'], JSON_UNESCAPED_UNICODE);
