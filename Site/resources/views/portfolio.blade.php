@php
    $canonical = config('seo.canonical_url').'/portfolio';
    $schema = ['@context' => 'https://schema.org', '@graph' => [
        ['@type' => 'CollectionPage', '@id' => $canonical, 'url' => $canonical,
            'name' => 'Портфолио проектов — Магия',
            'description' => 'Дизайн-проекты квартир в Ростове-на-Дону: планировки, расстановка мебели, электрика и сантехника.'],
        ['@type' => 'BreadcrumbList', 'itemListElement' => [
            ['@type' => 'ListItem', 'position' => 1, 'name' => 'Главная', 'item' => config('seo.canonical_url').'/'],
            ['@type' => 'ListItem', 'position' => 2, 'name' => 'Портфолио', 'item' => $canonical],
        ]],
        ['@type' => 'ItemList', 'itemListElement' => array_values(array_map(
            fn ($slug, $p) => ['@type' => 'ListItem', 'name' => $p['name'],
                'url' => config('seo.canonical_url').'/portfolio/'.$slug],
            array_keys($projects), $projects
        ))],
    ]];
@endphp
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Портфолио дизайн-проектов квартир в Ростове-на-Дону | Магия</title>
    <meta name="description" content="Проекты квартир в Ростове-на-Дону: ЖК «Донской Арбат», «Горизонт», «Пятый Элемент». Планировка, расстановка мебели, электрика и сантехника от 600 ₽/м².">
    <link rel="canonical" href="{{ $canonical }}">
    <meta property="og:type" content="website">
    <meta property="og:locale" content="ru_RU">
    <meta property="og:site_name" content="Магия">
    <meta property="og:title" content="Портфолио дизайн-проектов квартир в Ростове-на-Дону | Магия">
    <meta property="og:url" content="{{ $canonical }}">
    <script type="application/ld+json">{!! json_encode($schema, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES | JSON_HEX_TAG | JSON_HEX_AMP | JSON_HEX_APOS | JSON_HEX_QUOT) !!}</script>
    <link rel="icon" type="image/svg+xml" href="{{ asset('favicon.svg') }}">
    @vite(['resources/css/app.css', 'resources/js/app.js'])
    @include('partials.metrika')
</head>
<body class="service-page">
    <header class="service_header service_header_desktop">
        <a href="{{ route('home', [], false) }}" aria-label="Магия — главная"><img src="{{ asset('images/logo.svg') }}" width="189" height="46" alt="Магия" class="logo"></a>
        <nav aria-label="Основная навигация">
            <a href="{{ route('home', [], false) }}">Главная</a>
            <a href="#contacts">Контакты</a>
        </nav>
        <a href="tel:{{ config('seo.phone') }}">{{ config('seo.phone_display') }}</a>
    </header>
    <main class="service_detail">
        <nav class="service_breadcrumbs" aria-label="Хлебные крошки"><a href="/">Главная</a><span aria-hidden="true">/</span><span aria-current="page">Портфолио</span></nav>
        <section class="service_hero">
            <div>
                <p class="service_eyebrow">Портфолио · {{ config('seo.city') }}</p>
                <h1>Проекты квартир</h1>
                <p class="service_lead">Технический дизайн-проект — основа любого ремонта: планировка, расстановка мебели, электрика и сантехника, расчёт материалов. 600 ₽/м².</p>
                <div class="service_hero_actions">
                    <button type="button" class="button but_black" data-modal-open>Заказать проект</button>
                </div>
            </div>
        </section>
        <section class="service_work_section">
            <h2>Реализованные проекты</h2>
            <div class="project_grid">
                @foreach ($projects as $slug => $project)
                    <a class="project_card" href="{{ route('project', ['project' => $slug], false) }}">
                        <img src="{{ asset('images/projects/'.$slug.'/1.jpg') }}" width="600" height="800" loading="lazy" decoding="async" alt="{{ $project['heading'] }}" class="project_gallery_item">
                        <span class="project_card_title">{{ $project['name'] }}</span>
                        <span class="project_card_text">{{ $project['lead'] }}</span>
                    </a>
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
