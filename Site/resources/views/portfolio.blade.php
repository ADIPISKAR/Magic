@php
    $canonical = config('seo.canonical_url').'/portfolio';
    $schema = [
        '@context' => 'https://schema.org',
        '@graph' => [
            [
                '@type' => 'CollectionPage',
                '@id' => $canonical.'#page',
                'name' => 'Портфолио дизайн-проектов квартир в Ростове-на-Дону',
                'description' => 'Технические дизайн-проекты квартир студии, однокомнатной и двухкомнатных квартир в Ростове-на-Дону.',
                'url' => $canonical,
                'isPartOf' => ['@id' => config('seo.canonical_url').'/#website'],
                'mainEntity' => ['@id' => $canonical.'#projects'],
            ],
            [
                '@type' => 'ItemList',
                '@id' => $canonical.'#projects',
                'numberOfItems' => count($projects),
                'itemListElement' => collect($projects)->values()->map(fn ($project, $index) => [
                    '@type' => 'ListItem',
                    'position' => $index + 1,
                    'url' => config('seo.canonical_url').route('project', array_keys($projects)[$index], false),
                    'name' => $project['name'],
                ])->all(),
            ],
            [
                '@type' => 'BreadcrumbList',
                'itemListElement' => [
                    ['@type' => 'ListItem', 'position' => 1, 'name' => 'Главная', 'item' => config('seo.canonical_url').'/' ],
                    ['@type' => 'ListItem', 'position' => 2, 'name' => 'Портфолио', 'item' => $canonical],
                ],
            ],
        ],
    ];
@endphp
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Портфолио дизайн-проектов квартир в Ростове-на-Дону | Магия</title>
    <meta name="description" content="Смотрите технические дизайн-проекты квартир от «Магии»: планировки, расстановка мебели, электрика и сантехника для объектов в Ростове-на-Дону.">
    <link rel="canonical" href="{{ $canonical }}">
    <meta property="og:type" content="website">
    <meta property="og:locale" content="ru_RU">
    <meta property="og:site_name" content="Магия">
    <meta property="og:title" content="Портфолио дизайн-проектов квартир | Магия">
    <meta property="og:description" content="Четыре реальных проекта: от студии 28 м² до двухкомнатной квартиры 65 м².">
    <meta property="og:url" content="{{ $canonical }}">
    <meta property="og:image" content="{{ config('seo.canonical_url') }}/images/projects/donskoy-arbat-65/1.jpg">
    <script type="application/ld+json">{!! json_encode($schema, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES | JSON_HEX_TAG | JSON_HEX_AMP | JSON_HEX_APOS | JSON_HEX_QUOT) !!}</script>
    <link rel="icon" type="image/svg+xml" href="{{ asset('favicon.svg') }}">
    @vite(['resources/css/app.css', 'resources/js/app.js'])
    @include('partials.metrika')
</head>
<body class="service-page portfolio-page">
    @include('partials.portfolio-header')
    <main class="portfolio_main">
        <nav class="service_breadcrumbs" aria-label="Хлебные крошки"><a href="{{ route('home', [], false) }}">Главная</a><span aria-hidden="true">/</span><span aria-current="page">Портфолио</span></nav>

        <section class="portfolio_intro">
            <div class="portfolio_intro_copy">
                <p class="service_eyebrow">Проекты «Магии» · Ростов-на-Дону</p>
                <h1>Ремонт начинается с&nbsp;точного проекта</h1>
                <p>Показываем рабочие материалы квартир разной площади — без постановочных фотографий и общих обещаний. Можно открыть каждый лист и посмотреть, как решения передаются строителям.</p>
                <div class="portfolio_intro_actions">
                    <a class="button but_black" href="#projects">Смотреть проекты</a>
                    <button type="button" data-modal-open>Обсудить свою квартиру ↗</button>
                </div>
            </div>
            <aside class="portfolio_intro_panel" aria-label="Портфолио в цифрах">
                <div><strong>04</strong><span>квартиры в подборке</span></div>
                <div><strong>179</strong><span>м² спроектировано</span></div>
                <p>Студия, однокомнатная и две двухкомнатные квартиры.</p>
            </aside>
        </section>

        <section class="portfolio_projects" id="projects" aria-labelledby="projects-title">
            <div class="portfolio_section_heading">
                <p class="service_eyebrow">Документация вместо обещаний</p>
                <h2 id="projects-title">Выберите квартиру</h2>
                <p>Внутри каждого кейса — исходная задача, принятые решения и все доступные листы проекта.</p>
            </div>
            <div class="portfolio_project_grid">
                @foreach ($projects as $slug => $project)
                    <a class="portfolio_project_item" href="{{ route('project', $slug, false) }}">
                        <span class="portfolio_project_index">{{ str_pad((string) $loop->iteration, 2, '0', STR_PAD_LEFT) }}</span>
                        <span class="portfolio_project_sheet">
                            <img src="{{ asset('images/projects/'.$slug.'/1.jpg') }}" width="{{ $slug === 'donskoy-arbat-65' ? 600 : 566 }}" height="800" loading="{{ $loop->first ? 'eager' : 'lazy' }}" decoding="async" alt="Первый лист проекта: {{ $project['name'] }}">
                            <span class="portfolio_project_sheet_badge">{{ $project['photos'] }} {{ $project['photos'] === 3 ? 'листа' : ($project['photos'] === 4 ? 'листа' : 'листов') }}</span>
                        </span>
                        <span class="portfolio_project_body">
                            <span class="portfolio_project_meta">{{ $project['rooms'] }} · {{ $project['area'] }}</span>
                            <strong>{{ $project['short_name'] }}</strong>
                            <span>{{ $project['lead'] }}</span>
                            <em>Открыть проект <b aria-hidden="true">↗</b></em>
                        </span>
                    </a>
                @endforeach
            </div>
        </section>

        <section class="portfolio_reading" aria-labelledby="portfolio-reading-title">
            <div>
                <p class="service_eyebrow">Что искать на листах</p>
                <h2 id="portfolio-reading-title">Проект отвечает на вопросы до ремонта</h2>
            </div>
            <ol>
                <li><span>01</span><strong>Поместится ли всё нужное</strong><p>Планировка и мебель показывают реальные проходы, зоны хранения и сценарии помещения.</p></li>
                <li><span>02</span><strong>Где пройдут коммуникации</strong><p>Точки электрики и сантехники согласуются с выбранной расстановкой.</p></li>
                <li><span>03</span><strong>Что считать в смете</strong><p>Рабочие решения дают основу для объёмов и предметного разговора с бригадой.</p></li>
            </ol>
        </section>

        <section class="portfolio_cta">
            <div><p class="service_eyebrow">Ваш объект</p><h2>Разберём планировку до начала работ</h2></div>
            <p>Расскажите о квартире и своих задачах. На первой встрече определим, какая документация нужна именно вашему ремонту.</p>
            <button class="button but_white" type="button" data-modal-open data-lead-context="Расскажите о квартире — уточним задачи и предложим подходящий состав дизайн-проекта." data-lead-source="Портфолио — нижний призыв">Обсудить проект ↗</button>
        </section>
        <div id="contacts">@include('partials.contacts')</div>
    </main>
    @include('partials.legal-footer')
    @include('partials.lead-modal')
    @include('partials.cookie-consent')
</body>
</html>
