@php
    $canonical = config('seo.canonical_url').'/'.$slug;
    $experience = config("service_content.{$slug}");
    $faqItems = array_merge($page['faq'], $experience['faq'] ?? []);
    $business = [
        '@type' => 'HomeAndConstructionBusiness', '@id' => config('seo.canonical_url').'/#business',
        'name' => 'Магия', 'url' => config('seo.canonical_url').'/',
        'telephone' => config('seo.phone'),
        'image' => config('seo.canonical_url').'/'.$page['image'],
        'address' => ['@type' => 'PostalAddress', 'streetAddress' => config('seo.street_address'),
            'addressLocality' => config('seo.city'), 'postalCode' => config('seo.postal_code'), 'addressCountry' => 'RU'],
        'areaServed' => ['@type' => 'City', 'name' => config('seo.city')],
    ];
    $schemaGraph = [
        $business,
        ['@type' => 'Service', '@id' => $canonical.'#service', 'name' => $page['heading'],
            'description' => $page['description'], 'url' => $canonical,
            'provider' => ['@id' => $business['@id']], 'areaServed' => $business['areaServed']],
        ['@type' => 'BreadcrumbList', 'itemListElement' => [
            ['@type' => 'ListItem', 'position' => 1, 'name' => 'Главная', 'item' => config('seo.canonical_url').'/'],
            ['@type' => 'ListItem', 'position' => 2, 'name' => $page['name'], 'item' => $canonical],
        ]],
    ];
    if ($faqItems) {
        $schemaGraph[] = [
            '@type' => 'FAQPage',
            '@id' => $canonical.'#faq',
            'mainEntity' => array_map(fn ($faq) => [
                '@type' => 'Question',
                'name' => $faq['question'],
                'acceptedAnswer' => ['@type' => 'Answer', 'text' => $faq['answer']],
            ], $faqItems),
        ];
    }
    $schema = ['@context' => 'https://schema.org', '@graph' => $schemaGraph];
@endphp
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{{ $page['title'] }}</title>
    <meta name="description" content="{{ $page['description'] }}">
    <link rel="canonical" href="{{ $canonical }}">
    <meta property="og:type" content="website">
    <meta property="og:locale" content="ru_RU">
    <meta property="og:site_name" content="Магия">
    <meta property="og:title" content="{{ $page['title'] }}">
    <meta property="og:description" content="{{ $page['description'] }}">
    <meta property="og:url" content="{{ $canonical }}">
    <meta property="og:image" content="{{ config('seo.canonical_url') }}/{{ $page['image'] }}">
    <meta property="og:image:alt" content="{{ $page['image_alt'] }}">
    <script type="application/ld+json">{!! json_encode($schema, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES | JSON_HEX_TAG | JSON_HEX_AMP | JSON_HEX_APOS | JSON_HEX_QUOT) !!}</script>
    <link rel="icon" type="image/svg+xml" href="{{ asset('favicon.svg') }}">
    @vite(['resources/css/app.css', 'resources/js/app.js'])
    @include('partials.metrika')
</head>
<body class="service-page">
    <header class="service_header service_header_desktop">
        <a href="{{ route('home', [], false) }}" aria-label="Магия — главная"><img src="{{ asset('images/logo.svg') }}" width="189" height="46" alt="Магия" class="logo"></a>
        <nav aria-label="Основная навигация">
            <a href="#planner">Ваш сценарий</a>
            <a href="#works">Состав работ</a>
            <a href="#prices">Стоимость</a>
            <a href="#contacts">Контакты</a>
        </nav>
        <a href="tel:{{ config('seo.phone') }}">{{ config('seo.phone_display') }}</a>
    </header>
    <header class="mobile_header service_mobile_header" data-mobile-header>
        <div class="mobile_header_bar">
            <a href="{{ route('home', [], false) }}" aria-label="Магия — главная">
                <img src="{{ asset('images/logo.svg') }}" width="189" height="46" alt="Магия — ремонт квартир в Ростове-на-Дону" class="mobile_header_logo">
            </a>
            <div class="mobile_header_quick" aria-label="Быстрые контакты">
                <a class="mobile_header_social" href="https://t.me/SergeyWright" target="_blank" rel="noopener noreferrer" aria-label="Написать в Telegram">
                    <img src="{{ asset('images/Icon/Telegram.svg') }}" width="24" height="24" alt="">
                </a>
                <a class="mobile_header_social" href="https://max.ru/u/f9LHodD0cOLsSlygVBBUbU_rAlEqsEcBA1bKp0CmWJsn8wMz3aiuwcm9lss" target="_blank" rel="noopener noreferrer" aria-label="Написать в Max">
                    <img src="{{ asset('images/Icon/Max.svg') }}" width="22" height="22" alt="">
                </a>
                <button class="mobile_header_toggle" type="button" aria-expanded="false" aria-controls="mobile-service-menu" aria-label="Открыть меню" data-mobile-menu-toggle>
                    <span></span>
                    <span></span>
                </button>
            </div>
        </div>
        <div class="mobile_header_panel" id="mobile-service-menu" aria-hidden="true" data-mobile-menu>
            <div class="mobile_header_panel_inner">
                <nav aria-label="Мобильная навигация">
                    <a href="#planner">Ваш сценарий</a>
                    <a href="#works">Состав работ</a>
                    <a href="#prices">Стоимость</a>
                    <a href="#contacts">Контакты</a>
                </nav>
                <div class="mobile_header_contact">
                    <span>Обсудить ремонт</span>
                    <a href="tel:{{ config('seo.phone') }}">{{ config('seo.phone_display') }}</a>
                </div>
            </div>
        </div>
    </header>
    <main class="service_detail">
        <nav class="service_breadcrumbs" aria-label="Хлебные крошки"><a href="/">Главная</a><span aria-hidden="true">/</span><span aria-current="page">{{ $page['name'] }}</span></nav>
        <section class="service_hero">
            <div>
                <p class="service_eyebrow">Магия · Ростов-на-Дону</p>
                <h1>{{ $page['heading'] }}</h1>
                <p class="service_lead">{{ $page['lead'] }}</p>
                <div class="service_hero_actions">
                    <button type="button" class="button but_black" data-modal-open>Получить смету</button>
                    <a href="#planner">Подобрать сценарий ↓</a>
                </div>
                <p class="service_small">Бесплатный замер · Подробная смета · Поэтапная оплата</p>
            </div>
            <div class="hero_image_container service_hero_slider" data-hero-stack aria-label="Проекты по услуге «{{ $page['name'] }}»">
                <span class="service_hero_slider_count" aria-hidden="true">{{ count($experience['hero_slides']) }} проекта</span>
                @foreach ($experience['hero_slides'] as $slide)
                    <button type="button" class="hero_card" aria-label="{{ $slide['title'] }} — показать описание" aria-pressed="false">
                        <span class="hero_card_inner">
                            <span class="hero_card_front">
                                <img
                                    src="{{ asset($slide['image']) }}"
                                    width="475"
                                    height="565"
                                    @if ($loop->first) fetchpriority="high" @else loading="lazy" @endif
                                    decoding="async"
                                    alt="{{ $slide['alt'] }}"
                                    class="hero_image"
                                >
                            </span>
                            <span class="hero_card_back">
                                <span class="hero_card_back_top">
                                    <span class="hero_card_badge">Проект {{ str_pad((string) $loop->iteration, 2, '0', STR_PAD_LEFT) }} / {{ str_pad((string) $loop->count, 2, '0', STR_PAD_LEFT) }}</span>
                                    <span class="hero_card_brand">Магия</span>
                                </span>
                                <span class="hero_card_back_body">
                                    <span class="hero_card_back_rule" aria-hidden="true"></span>
                                    <strong>{{ $slide['title'] }}</strong>
                                    <span class="hero_card_text">{{ $slide['text'] }}</span>
                                </span>
                                <span class="hero_card_back_action">
                                    <span>Нажмите ещё раз</span>
                                    <span aria-hidden="true">↗</span>
                                </span>
                            </span>
                        </span>
                    </button>
                @endforeach
                <p class="service_hero_slider_hint">Наведите на проект или нажмите, чтобы узнать детали</p>
            </div>
        </section>
        <section class="service_planner" id="planner" aria-labelledby="planner-title" data-service-planner>
            <div class="service_section_intro">
                <div>
                    <p class="service_eyebrow">Интерактивный помощник</p>
                    <h2 id="planner-title">{{ $experience['planner_heading'] }}</h2>
                </div>
                <p>{{ $experience['planner_intro'] }}</p>
            </div>
            <div class="service_planner_shell">
                <div class="service_scenario_tabs" role="tablist" aria-label="{{ $experience['planner_label'] }}">
                    @foreach ($experience['scenarios'] as $scenario)
                        <button
                            type="button"
                            role="tab"
                            id="scenario-tab-{{ $loop->index }}"
                            aria-controls="scenario-panel-{{ $loop->index }}"
                            aria-selected="{{ $loop->first ? 'true' : 'false' }}"
                            tabindex="{{ $loop->first ? '0' : '-1' }}"
                            data-service-scenario
                        >
                            <span>0{{ $loop->iteration }}</span>
                            {{ $scenario['label'] }}
                        </button>
                    @endforeach
                </div>
                <div class="service_scenario_panels">
                    @foreach ($experience['scenarios'] as $scenario)
                        <article
                            id="scenario-panel-{{ $loop->index }}"
                            role="tabpanel"
                            aria-labelledby="scenario-tab-{{ $loop->index }}"
                            data-service-scenario-panel
                            @if (! $loop->first) hidden @endif
                        >
                            <div class="service_scenario_copy">
                                <p class="service_eyebrow">Ваш маршрут</p>
                                <h3>{{ $scenario['title'] }}</h3>
                                <p>{{ $scenario['summary'] }}</p>
                                <button
                                    type="button"
                                    class="button but_black"
                                    data-modal-open
                                    data-lead-context="{{ $scenario['lead_context'] }}"
                                    data-lead-message="{{ $scenario['lead_message'] }}"
                                    data-lead-source="{{ $page['name'] }} — сценарий «{{ $scenario['label'] }}»"
                                >Обсудить этот сценарий</button>
                            </div>
                            <div class="service_scenario_points">
                                <h4>На замере проверим</h4>
                                <ul>
                                    @foreach ($scenario['points'] as $point)
                                        <li><span aria-hidden="true">✓</span>{{ $point }}</li>
                                    @endforeach
                                </ul>
                                <p class="service_scenario_callout"><strong>Обратите внимание.</strong> {{ $scenario['callout'] }}</p>
                            </div>
                        </article>
                    @endforeach
                </div>
            </div>
        </section>
        <section class="service_work_section" id="works">
            <div class="service_section_intro"><h2>{{ $page['intro_heading'] }}</h2><p>{{ $page['intro'] }}</p></div>
            <div class="service_work_grid">
                @foreach ($page['works'] as $work)
                    <article><span class="service_number">0{{ $loop->iteration }}</span><h3>{{ $work['title'] }}</h3><p>{{ $work['text'] }}</p></article>
                @endforeach
            </div>
        </section>
        <section class="service_stages" id="stages" aria-labelledby="stages-title">
            <div class="service_section_intro">
                <h2 id="stages-title">{{ $experience['stages_heading'] }}</h2>
                <p>{{ $experience['stages_intro'] }}</p>
            </div>
            <ol class="service_stage_list">
                @foreach ($experience['stages'] as $stage)
                    <li>
                        <span class="service_stage_number">0{{ $loop->iteration }}</span>
                        <h3>{{ $stage['title'] }}</h3>
                        <p>{{ $stage['text'] }}</p>
                    </li>
                @endforeach
            </ol>
        </section>
        <section class="service_checklist" aria-labelledby="checklist-title" data-service-checklist>
            <div class="service_checklist_copy">
                <p class="service_eyebrow">Подготовка без спешки</p>
                <h2 id="checklist-title">{{ $experience['checklist_heading'] }}</h2>
                <p>{{ $experience['checklist_intro'] }}</p>
                <button type="button" class="service_checklist_reset" data-service-checklist-reset>Сбросить отметки</button>
            </div>
            <div class="service_checklist_card">
                <div class="service_checklist_progress">
                    <span>Готовность к замеру</span>
                    <strong data-service-checklist-status>0 из {{ count($experience['checklist']) }}</strong>
                </div>
                <div class="service_checklist_bar" aria-hidden="true"><span data-service-checklist-bar></span></div>
                <fieldset>
                    <legend class="sr-only">Отметьте подготовленные материалы</legend>
                    @foreach ($experience['checklist'] as $item)
                        <label>
                            <input type="checkbox" data-service-check-item>
                            <span aria-hidden="true"></span>
                            <em>{{ $item }}</em>
                        </label>
                    @endforeach
                </fieldset>
                <p class="service_checklist_hint" aria-live="polite" data-service-checklist-hint>Начните с любого пункта — всё остальное обсудим на замере.</p>
            </div>
        </section>
        <section class="service_cost" id="prices">
            <div>
                <p class="service_eyebrow">Стоимость</p>
                <h2>Смета под вашу задачу</h2>
                <p>{{ $page['price_note'] }}</p>
                <div class="service_unit_prices">
                    <h3>{{ $page['unit_prices_heading'] }}</h3>
                    <dl>
                        @foreach ($page['unit_prices'] as [$label, $price])
                            <div><dt>{{ $label }}</dt><dd>{{ $price }}</dd></div>
                        @endforeach
                    </dl>
                    <p>Цены относятся к отдельным работам и служат ориентиром. Объём и итоговую стоимость фиксируем в смете после замера.</p>
                </div>
            </div>
            <div>
                @if ($page['prices'])
                    <dl class="service_price_list">
                        @foreach ($page['prices'] as [$label, $price])
                            <div><dt>{{ $label }}</dt><dd>{{ $price }}</dd></div>
                        @endforeach
                    </dl>
                @else
                    <p class="service_individual_price">По индивидуальной смете</p>
                @endif
                <a class="button but_white" href="{{ asset('СМЕТА ШАБЛОН.pdf') }}" download="Смета-на-ремонт.pdf">Скачать пример сметы ↓</a>
            </div>
        </section>
        <section class="service_faq" aria-labelledby="faq-title">
            <h2 id="faq-title">До начала ремонта</h2>
            @foreach ($faqItems as $faq)
                <details><summary>{{ $faq['question'] }}</summary><p>{{ $faq['answer'] }}</p></details>
            @endforeach
        </section>
        <section class="service_related"><h2>Другие направления ремонта</h2>@include('partials.service-links')</section>
        <div id="contacts">@include('partials.contacts')</div>
    </main>
    @include('partials.legal-footer')
    @include('partials.lead-modal')
    @include('partials.cookie-consent')
</body>
</html>
