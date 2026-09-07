@php
    $canonical = config('seo.canonical_url').route('project', $slug, false);
    $imagePath = 'images/projects/'.$slug.'/1.jpg';
    $schemaGraph = [
        [
            '@type' => 'CreativeWork',
            '@id' => $canonical.'#project',
            'name' => $project['heading'],
            'description' => $project['description'],
            'url' => $canonical,
            'image' => config('seo.canonical_url').'/'.$imagePath,
            'creator' => ['@id' => config('seo.canonical_url').'/#business'],
            'about' => ['@type' => 'Apartment', 'name' => $project['rooms'], 'floorSize' => ['@type' => 'QuantitativeValue', 'value' => (int) $project['area'], 'unitText' => 'м²']],
        ],
        [
            '@type' => 'BreadcrumbList',
            'itemListElement' => [
                ['@type' => 'ListItem', 'position' => 1, 'name' => 'Главная', 'item' => config('seo.canonical_url').'/' ],
                ['@type' => 'ListItem', 'position' => 2, 'name' => 'Портфолио', 'item' => config('seo.canonical_url').'/portfolio'],
                ['@type' => 'ListItem', 'position' => 3, 'name' => $project['name'], 'item' => $canonical],
            ],
        ],
        [
            '@type' => 'FAQPage',
            '@id' => $canonical.'#faq',
            'mainEntity' => array_map(fn ($faq) => ['@type' => 'Question', 'name' => $faq['question'], 'acceptedAnswer' => ['@type' => 'Answer', 'text' => $faq['answer']]], $project['faq']),
        ],
    ];
    $schema = ['@context' => 'https://schema.org', '@graph' => $schemaGraph];
    $otherProjects = collect(config('portfolio'))->except($slug)->take(3);
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
    <meta property="og:image" content="{{ config('seo.canonical_url') }}/{{ $imagePath }}">
    <script type="application/ld+json">{!! json_encode($schema, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES | JSON_HEX_TAG | JSON_HEX_AMP | JSON_HEX_APOS | JSON_HEX_QUOT) !!}</script>
    <link rel="icon" type="image/svg+xml" href="{{ asset('favicon.svg') }}">
    @vite(['resources/css/app.css', 'resources/js/app.js'])
    @include('partials.metrika')
</head>
<body class="service-page project-page">
    @include('partials.portfolio-header')
    <main class="project_main">
        <nav class="service_breadcrumbs" aria-label="Хлебные крошки"><a href="{{ route('home', [], false) }}">Главная</a><span aria-hidden="true">/</span><a href="{{ route('portfolio', [], false) }}">Портфолио</a><span aria-hidden="true">/</span><span aria-current="page">{{ $project['short_name'] }}</span></nav>

        <section class="project_hero">
            <div class="project_hero_copy">
                <p class="service_eyebrow">{{ $project['kind'] }} · Ростов-на-Дону</p>
                <h1>{{ $project['heading'] }}</h1>
                <p class="project_lead">{{ $project['lead'] }}</p>
                <dl class="project_facts">
                    <div><dt>Площадь</dt><dd>{{ $project['area'] }}</dd></div>
                    <div><dt>Тип</dt><dd>{{ $project['rooms'] }}</dd></div>
                    <div><dt>Задача</dt><dd>{{ $project['client'] }}</dd></div>
                </dl>
                <div class="project_hero_actions"><a class="button but_black" href="#project-sheets">Смотреть листы ↓</a><button type="button" data-modal-open data-lead-context="Расскажите о квартире — обсудим планировку и состав технического проекта." data-lead-source="Кейс: {{ $project['name'] }}">Обсудить свой проект ↗</button></div>
            </div>
            <div class="project_hero_visual" aria-hidden="true">
                @foreach (range(1, min(3, $project['photos'])) as $number)
                    <span class="project_hero_paper project_hero_paper_{{ $loop->iteration }}"><img src="{{ asset('images/projects/'.$slug.'/'.$number.'.jpg') }}" width="{{ $slug === 'donskoy-arbat-65' ? 600 : 566 }}" height="800" @if(!$loop->first) loading="lazy" @endif decoding="async" alt=""></span>
                @endforeach
                <span class="project_hero_counter">{{ str_pad((string) $project['photos'], 2, '0', STR_PAD_LEFT) }} листов</span>
            </div>
        </section>

        <section class="project_brief" aria-labelledby="project-brief-title">
            <div><p class="service_eyebrow">Логика проекта</p><h2 id="project-brief-title">Сначала сценарий квартиры.<br>Затем чертежи.</h2></div>
            <div><p>{{ $project['intro'] }}</p><ul>@foreach ($project['focus'] as $item)<li><span aria-hidden="true">✓</span>{{ $item }}</li>@endforeach</ul></div>
        </section>

        <section class="project_gallery" id="project-sheets" aria-labelledby="project-sheets-title" data-project-gallery>
            <div class="project_gallery_heading">
                <div><p class="service_eyebrow">Материалы проекта</p><h2 id="project-sheets-title">Рабочие листы</h2></div>
                <div class="project_gallery_status" aria-live="polite"><span data-gallery-current>01</span><i>/</i><span>{{ str_pad((string) $project['photos'], 2, '0', STR_PAD_LEFT) }}</span></div>
            </div>
            <div class="project_gallery_viewer">
                <div class="project_gallery_stage">
                    <img data-gallery-main src="{{ asset($imagePath) }}" width="{{ $slug === 'donskoy-arbat-65' ? 600 : 566 }}" height="800" alt="Лист 1 проекта {{ $project['name'] }}">
                    <button type="button" class="project_gallery_nav project_gallery_prev" data-gallery-prev aria-label="Предыдущий лист">←</button>
                    <button type="button" class="project_gallery_nav project_gallery_next" data-gallery-next aria-label="Следующий лист">→</button>
                </div>
                <div class="project_gallery_side">
                    <p>Выберите лист или листайте стрелками. Изображение показано целиком, чтобы сохранить масштаб и подписи документа.</p>
                    <div class="project_gallery_thumbs" role="list" aria-label="Листы проекта">
                        @foreach (range(1, $project['photos']) as $number)
                            <button type="button" role="listitem" class="{{ $loop->first ? 'is-active' : '' }}" data-gallery-thumb data-src="{{ asset('images/projects/'.$slug.'/'.$number.'.jpg') }}" data-alt="Лист {{ $number }} проекта {{ $project['name'] }}" aria-label="Открыть лист {{ $number }}" aria-current="{{ $loop->first ? 'true' : 'false' }}">
                                <span>{{ str_pad((string) $number, 2, '0', STR_PAD_LEFT) }}</span>
                                <img src="{{ asset('images/projects/'.$slug.'/'.$number.'.jpg') }}" width="{{ $slug === 'donskoy-arbat-65' ? 600 : 566 }}" height="800" loading="lazy" decoding="async" alt="">
                            </button>
                        @endforeach
                    </div>
                </div>
            </div>
        </section>

        <section class="project_documents" aria-labelledby="project-documents-title">
            <div><p class="service_eyebrow">Результат</p><h2 id="project-documents-title">Документ, по которому можно строить</h2></div>
            <div class="project_documents_grid">
                <article><span>01</span><h3>Планировка</h3><p>Зоны и расстановка мебели согласованы до начала ремонта.</p></article>
                <article><span>02</span><h3>Коммуникации</h3><p>Рабочие точки связаны с логикой будущего интерьера.</p></article>
                <article><span>03</span><h3>Расчёт</h3><p>Зафиксированные решения помогают считать объёмы и обсуждать смету.</p></article>
            </div>
        </section>

        <section class="project_faq" aria-labelledby="project-faq-title"><h2 id="project-faq-title">Вопросы о проекте</h2>@foreach ($project['faq'] as $faq)<details><summary>{{ $faq['question'] }}</summary><p>{{ $faq['answer'] }}</p></details>@endforeach</section>

        <section class="project_more" aria-labelledby="project-more-title">
            <div class="portfolio_section_heading"><p class="service_eyebrow">Следующие проекты</p><h2 id="project-more-title">Посмотреть другую площадь</h2></div>
            <div class="project_more_grid">@foreach ($otherProjects as $otherSlug => $other)<a href="{{ route('project', $otherSlug, false) }}"><span>{{ $other['rooms'] }}</span><strong>{{ $other['short_name'] }}</strong><em>{{ $other['area'] }} ↗</em></a>@endforeach</div>
        </section>

        <section class="portfolio_cta"><div><p class="service_eyebrow">Технический дизайн-проект</p><h2>Стоимость — от 600 ₽/м²</h2></div><p>Итоговая цена зависит от площади и состава документации. После обсуждения зафиксируем, какие листы нужны для вашего объекта.</p><button class="button but_white" type="button" data-modal-open data-lead-context="Расскажите о квартире — рассчитаем стоимость технического дизайн-проекта." data-lead-source="Кейс: {{ $project['name'] }} — расчёт проекта">Рассчитать проект ↗</button></section>
        <div id="contacts">@include('partials.contacts')</div>
    </main>
    @include('partials.legal-footer')
    @include('partials.lead-modal')
    @include('partials.cookie-consent')
</body>
</html>
