@php
    $canonical = config('seo.canonical_url').'/portfolio/'.$slug;
    $cover = 'images/projects/'.$slug.'/'.($project['cover'] ?? 1).'.jpg';
    $business = [
        '@type' => 'HomeAndConstructionBusiness', '@id' => config('seo.canonical_url').'/#business',
        'name' => 'Магия', 'url' => config('seo.canonical_url').'/',
        'telephone' => config('seo.phone'),
        'address' => ['@type' => 'PostalAddress', 'streetAddress' => config('seo.street_address'),
            'addressLocality' => config('seo.city'), 'postalCode' => config('seo.postal_code'), 'addressCountry' => 'RU'],
        'areaServed' => ['@type' => 'City', 'name' => config('seo.city')],
    ];
    $schemaGraph = [
        $business,
        ['@type' => 'CreativeWork', '@id' => $canonical.'#project',
            'name' => $project['heading'], 'description' => $project['description'], 'url' => $canonical,
            'creator' => ['@id' => $business['@id']],
            'image' => config('seo.canonical_url').'/'.$cover,
            'locationCreated' => ['@type' => 'Place', 'name' => $project['complex'],
                'address' => ['@type' => 'PostalAddress', 'addressLocality' => config('seo.city'), 'addressCountry' => 'RU']],
            'dateModified' => $project['updated_at']],
        ['@type' => 'BreadcrumbList', 'itemListElement' => [
            ['@type' => 'ListItem', 'position' => 1, 'name' => 'Главная', 'item' => config('seo.canonical_url').'/'],
            ['@type' => 'ListItem', 'position' => 2, 'name' => 'Портфолио', 'item' => config('seo.canonical_url').'/portfolio'],
            ['@type' => 'ListItem', 'position' => 3, 'name' => $project['name'], 'item' => $canonical],
        ]],
    ];
    if ($project['faq']) {
        $schemaGraph[] = ['@type' => 'FAQPage', '@id' => $canonical.'#faq',
            'mainEntity' => array_map(fn ($faq) => [
                '@type' => 'Question', 'name' => $faq['question'],
                'acceptedAnswer' => ['@type' => 'Answer', 'text' => $faq['answer']],
            ], $project['faq'])];
    }
    $schema = ['@context' => 'https://schema.org', '@graph' => $schemaGraph];
    $specs = [
        'Жилой комплекс' => $project['complex'],
        'Площадь' => $project['area'],
        'Тип' => $project['rooms'],
        'Для кого' => $project['client'],
        'Формат' => $project['kind'],
    ];
@endphp
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{{ $project['title'] }}</title>
    <meta name="description" content="{{ $project['description'] }}">
    <link rel="canonical" href="{{ $canonical }}">
    <meta property="og:type" content="article">
    <meta property="og:locale" content="ru_RU">
    <meta property="og:site_name" content="Магия">
    <meta property="og:title" content="{{ $project['title'] }}">
    <meta property="og:description" content="{{ $project['description'] }}">
    <meta property="og:url" content="{{ $canonical }}">
    <meta property="og:image" content="{{ config('seo.canonical_url') }}/{{ $cover }}">
    <meta property="og:image:alt" content="{{ $project['heading'] }}">
    <script type="application/ld+json">{!! json_encode($schema, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES | JSON_HEX_TAG | JSON_HEX_AMP | JSON_HEX_APOS | JSON_HEX_QUOT) !!}</script>
    <link rel="icon" type="image/svg+xml" href="{{ asset('favicon.svg') }}">
    @vite(['resources/css/app.css', 'resources/js/app.js'])
    @include('partials.metrika')
</head>
<body class="service-page project-page">
    <header class="service_header service_header_desktop">
        <a href="{{ route('home', [], false) }}" aria-label="Магия — главная"><img src="{{ asset('images/logo.svg') }}" width="189" height="46" alt="Магия" class="logo"></a>
        <nav aria-label="Основная навигация">
            <a href="#gallery">Проект</a>
            <a href="#included">Что входит</a>
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
                <button class="mobile_header_toggle" type="button" aria-expanded="false" aria-controls="mobile-project-menu" aria-label="Открыть меню" data-mobile-menu-toggle>
                    <span></span>
                    <span></span>
                </button>
            </div>
        </div>
        <div class="mobile_header_panel" id="mobile-project-menu" aria-hidden="true" data-mobile-menu>
            <div class="mobile_header_panel_inner">
                <nav aria-label="Мобильная навигация">
                    <a href="#gallery">Проект</a>
                    <a href="#included">Что входит</a>
                    <a href="#prices">Стоимость</a>
                    <a href="#contacts">Контакты</a>
                </nav>
                <div class="mobile_header_contact">
                    <span>Обсудить проект</span>
                    <a href="tel:{{ config('seo.phone') }}">{{ config('seo.phone_display') }}</a>
                </div>
            </div>
        </div>
    </header>
    <main class="service_detail">
        <nav class="service_breadcrumbs" aria-label="Хлебные крошки"><a href="/">Главная</a><span aria-hidden="true">/</span><a href="/portfolio">Портфолио</a><span aria-hidden="true">/</span><span aria-current="page">{{ $project['name'] }}</span></nav>

        <section class="service_hero">
            <div>
                <p class="service_eyebrow">Портфолио · {{ config('seo.city') }}</p>
                <h1>{{ $project['heading'] }}</h1>
                <p class="service_lead">{{ $project['lead'] }}</p>
                <div class="service_hero_actions">
                    <button type="button" class="button but_black" data-modal-open>Заказать проект</button>
                    <a href="#included">Что входит в проект ↓</a>
                </div>
                <p class="service_small">600 ₽/м² · Технический проект — основа ремонта</p>
            </div>
            <figure>
                <img src="{{ asset($cover) }}" width="600" height="800" fetchpriority="high" decoding="async" alt="{{ $project['heading'] }} — {{ $project['complex'] }}">
            </figure>
        </section>

        <section class="service_work_section" id="specs">
            <h2>Об объекте</h2>
            <dl class="project_specs">
                @foreach ($specs as $label => $value)
                    <div><dt>{{ $label }}</dt><dd>{{ $value }}</dd></div>
                @endforeach
            </dl>
            <p>{{ $project['intro'] }}</p>
        </section>

        <section class="service_work_section" id="gallery" aria-labelledby="gallery-title">
            <h2 id="gallery-title">Материалы проекта</h2>
            <p>Комплект из {{ $project['photos'] }} листов: планировка, развёртки, расстановка мебели и оборудования.</p>
            <div class="project_gallery">
                @for ($i = 1; $i <= $project['photos']; $i++)
                    <figure>
                        <div class="project_sheet">
                            <img
                                src="{{ asset('images/projects/'.$slug.'/'.$i.'.jpg') }}"
                                width="600" height="800" loading="lazy" decoding="async"
                                alt="{{ $project['heading'] }} — лист {{ $i }}"
                            >
                        </div>
                        <figcaption>Лист {{ $i }} из {{ $project['photos'] }}</figcaption>
                    </figure>
                @endfor
            </div>
        </section>

        <section class="service_work_section" id="included">
            <h2>Что входит в технический проект</h2>
            <div class="service_work_grid">
                <article><h3>Планировка</h3><p>Перепланировка и зонирование под то, как вы живёте: проходы, хранение, расстановка мебели.</p></article>
                <article><h3>Инженерия</h3><p>Расположение электрики и сантехники под будущую мебель и оборудование — до начала отделки, а не по ходу.</p></article>
                <article><h3>Расчёт материалов</h3><p>Объёмы по каждому помещению, чтобы смета опиралась на цифры, а не на прикидку.</p></article>
            </div>
        </section>

        <section class="service_cost" id="prices">
            <div>
                <p class="service_eyebrow">Стоимость</p>
                <h2>600 ₽ за квадратный метр</h2>
                <p>Цена технического проекта считается от площади квартиры. Для объекта {{ $project['area'] }} это ориентир, который подтверждаем после уточнения задач. Проект можно заказать отдельно от ремонта — документация останется у вас.</p>
            </div>
            <div>
                <dl class="service_price_list">
                    <div><dt>Технический проект</dt><dd>600 ₽/м²</dd></div>
                    <div><dt>Срок</dt><dd>от 7 дней</dd></div>
                </dl>
                <a class="button but_white" href="{{ route('service', ['service' => 'dizaynerskiy-remont'], false) }}">Дизайнерский ремонт под ключ →</a>
            </div>
        </section>

        @if ($project['faq'])
            <section class="service_faq" aria-labelledby="faq-title">
                <h2 id="faq-title">Вопросы по проекту</h2>
                @foreach ($project['faq'] as $faq)
                    <details><summary>{{ $faq['question'] }}</summary><p>{{ $faq['answer'] }}</p></details>
                @endforeach
            </section>
        @endif

        <section class="service_related">
            <h2>Другие проекты</h2>
            <div class="service_links">
                @foreach (config('portfolio') as $otherSlug => $other)
                    @continue($otherSlug === $slug)
                    <a href="{{ route('project', ['project' => $otherSlug], false) }}">{{ $other['name'] }}</a>
                @endforeach
            </div>
        </section>

        <section class="service_related"><h2>Услуги</h2>@include('partials.service-links')</section>
        <div id="contacts">@include('partials.contacts')</div>
    </main>
    @include('partials.legal-footer')
    @include('partials.lead-modal')
    @include('partials.cookie-consent')
</body>
</html>
