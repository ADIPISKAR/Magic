@php
    $canonical = config('seo.canonical_url').'/'.$slug;
    $business = [
        '@type' => 'HomeAndConstructionBusiness', '@id' => config('seo.canonical_url').'/#business',
        'name' => 'Магия', 'url' => config('seo.canonical_url').'/',
        'telephone' => config('seo.phone'),
        'image' => config('seo.canonical_url').'/'.$page['image'],
        'address' => ['@type' => 'PostalAddress', 'streetAddress' => config('seo.street_address'),
            'addressLocality' => config('seo.city'), 'postalCode' => config('seo.postal_code'), 'addressCountry' => 'RU'],
        'areaServed' => ['@type' => 'City', 'name' => config('seo.city')],
    ];
    $schema = ['@context' => 'https://schema.org', '@graph' => [
        $business,
        ['@type' => 'Service', '@id' => $canonical.'#service', 'name' => $page['heading'],
            'description' => $page['description'], 'url' => $canonical,
            'provider' => ['@id' => $business['@id']], 'areaServed' => $business['areaServed']],
        ['@type' => 'BreadcrumbList', 'itemListElement' => [
            ['@type' => 'ListItem', 'position' => 1, 'name' => 'Главная', 'item' => config('seo.canonical_url').'/'],
            ['@type' => 'ListItem', 'position' => 2, 'name' => $page['name'], 'item' => $canonical],
        ]],
    ]];
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
    <noscript><div><img src="https://mc.yandex.ru/watch/111942996" width="1" height="1" style="position:absolute;left:-9999px" alt=""></div></noscript>
    <header class="service_header">
        <a href="{{ route('home', [], false) }}" aria-label="Магия — главная"><img src="{{ asset('images/logo.svg') }}" width="189" height="46" alt="Магия" class="logo"></a>
        <nav aria-label="Основная навигация">
            <a href="/#portfolio">Портфолио</a>
            <a href="#prices">Стоимость</a>
            <a href="#contacts">Контакты</a>
        </nav>
        <a href="tel:{{ config('seo.phone') }}">{{ config('seo.phone_display') }}</a>
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
                    <a href="#works">Что входит в ремонт ↓</a>
                </div>
                <p class="service_small">Бесплатный замер · Подробная смета · Поэтапная оплата</p>
            </div>
            <figure>
                <img src="{{ asset($page['image']) }}" width="638" height="683" alt="{{ $page['image_alt'] }}" fetchpriority="high" decoding="async">
                <figcaption><a href="/#portfolio">Из портфолио «Магии» — посмотреть работы ↗</a></figcaption>
            </figure>
        </section>
        <section class="service_work_section" id="works">
            <div class="service_section_intro"><h2>{{ $page['intro_heading'] }}</h2><p>{{ $page['intro'] }}</p></div>
            <div class="service_work_grid">
                @foreach ($page['works'] as $work)
                    <article><span class="service_number">0{{ $loop->iteration }}</span><h3>{{ $work['title'] }}</h3><p>{{ $work['text'] }}</p></article>
                @endforeach
            </div>
        </section>
        <section class="service_cost" id="prices">
            <div><p class="service_eyebrow">Стоимость</p><h2>Смета под вашу задачу</h2><p>{{ $page['price_note'] }}</p></div>
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
            @foreach ($page['faq'] as $faq)
                <details><summary>{{ $faq['question'] }}</summary><p>{{ $faq['answer'] }}</p></details>
            @endforeach
        </section>
        <section class="service_related"><h2>Другие направления ремонта</h2>@include('partials.service-links')</section>
        <div id="contacts">@include('partials.contacts')</div>
    </main>
    <footer class="service_footer"><a href="/">Магия — ремонт квартир в Ростове-на-Дону</a><span>2026</span></footer>
    @include('partials.lead-modal')
</body>
</html>
