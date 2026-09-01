<?php

return [
    // Change only after a substantive update; never use today's date at request time.
    'home_lastmod' => '2026-09-01',
    'canonical_url' => rtrim(
        env('SEO_CANONICAL_URL', 'https://magiarnd.ru'),
        '/',
    ),
    // Verified against the linked Yandex Business listing on 2026-09-01.
    'phone' => '+79894345744',
    'phone_display' => '+7 (989) 434-57-44',
    'street_address' => 'проспект Соколова, 34/1',
    'postal_code' => '344006',
    'city' => 'Ростов-на-Дону',
    'maps_url' => 'https://yandex.ru/maps/org/magiya/29377814826/',
    'google_site_verification' => '9QjxoE4Ov-scAYEmS3oMIzR8NGySSXQze6AUJpLCVhI',
];
