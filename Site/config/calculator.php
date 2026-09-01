<?php

// The calculator uses the same published labour rates as the service pages.
return [
    'minimum_area' => 20,
    'maximum_area' => 200,
    'default_area' => 50,
    'default_property' => 'new',
    'default_plan' => 1,
    'properties' => [
        'new' => [
            'label' => 'Новостройка',
            'plans' => [
                ['name' => 'Черновой', 'rate' => 5000],
                ['name' => 'Эконом', 'rate' => 12000],
                ['name' => 'Евроремонт', 'rate' => 16000],
                ['name' => 'Дизайнерский', 'rate' => 20000],
            ],
        ],
        'secondary' => [
            'label' => 'Вторичное жильё',
            'plans' => [
                ['name' => 'Косметический', 'rate' => 10000],
                ['name' => 'Капитальный', 'rate' => 14000],
                ['name' => 'Евроремонт', 'rate' => 18000],
                ['name' => 'Дизайнерский', 'rate' => 22000],
            ],
        ],
    ],
];
