<!DOCTYPE html>
<html lang="ru">
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">

        <title>Ремонт квартир под ключ в Ростове-на-Дону — от 5 000 ₽/м² | Магия</title>
        <meta name="description" content="Ремонт новостроек и вторичного жилья в Ростове-на-Дону. Бесплатный замер, фиксированная смета и поэтапная оплата. Цены от 5 000 ₽/м², примеры работ.">
        <meta name="google-site-verification" content="{{ config('seo.google_site_verification') }}">
        <link rel="canonical" href="{{ config('seo.canonical_url') }}/">

        <meta property="og:type" content="website">
        <meta property="og:locale" content="ru_RU">
        <meta property="og:site_name" content="Магия">
        <meta property="og:title" content="Ремонт квартир под ключ в Ростове-на-Дону — от 5 000 ₽/м² | Магия">
        <meta property="og:description" content="Ремонт новостроек и вторичного жилья: бесплатный замер, фиксированная смета, поэтапная оплата и цены от 5 000 ₽/м².">
        <meta property="og:url" content="{{ config('seo.canonical_url') }}/">
        <meta property="og:image" content="{{ config('seo.canonical_url') }}/images/WelcomePhoto/Wel_Photo_1.webp">
        <meta property="og:image:alt" content="Ремонт квартиры под ключ в Ростове-на-Дону">

        <script type="application/ld+json">
        {
            "@@context": "https://schema.org",
            "@@type": "HomeAndConstructionBusiness",
            "name": "Магия",
            "telephone": "{{ config('seo.phone') }}",
            "address": {
                "@@type": "PostalAddress",
                "streetAddress": "{{ config('seo.street_address') }}",
                "addressLocality": "{{ config('seo.city') }}",
                "postalCode": "{{ config('seo.postal_code') }}",
                "addressCountry": "RU"
            },
            "url": "{{ config('seo.canonical_url') }}/",
            "logo": "{{ config('seo.canonical_url') }}/images/logo.svg",
            "image": "{{ config('seo.canonical_url') }}/images/WelcomePhoto/Wel_Photo_1.webp",
            "description": "Ремонт квартир под ключ в Ростове-на-Дону: бесплатный замер, фиксированная смета, поэтапная оплата, ремонт новостроек и вторичного жилья.",
            "priceRange": "от 5 000 ₽/м²",
            "areaServed": {
                "@@type": "City",
                "name": "Ростов-на-Дону"
            },
            "sameAs": [
                "https://t.me/SergeyWright",
                "https://max.ru/u/f9LHodD0cOLsSlygVBBUbU_rAlEqsEcBA1bKp0CmWJsn8wMz3aiuwcm9lss"
            ],
            "hasOfferCatalog": {
                "@@type": "OfferCatalog",
                "name": "Услуги по ремонту квартир",
                "itemListElement": [
                    {
                        "@@type": "Offer",
                        "itemOffered": {
                            "@@type": "Service",
                            "name": "Ремонт квартир в новостройках"
                        }
                    },
                    {
                        "@@type": "Offer",
                        "itemOffered": {
                            "@@type": "Service",
                            "name": "Ремонт квартир во вторичном жилье"
                        }
                    },
                    {
                        "@@type": "Offer",
                        "itemOffered": {
                            "@@type": "Service",
                            "name": "Дизайнерский ремонт квартир"
                        }
                    }
                ]
            }
        }
        </script>
        <link rel="icon" type="image/svg+xml" href="{{ asset('favicon.svg') }}">

        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
        <link rel="preconnect" href="https://cdn.jsdelivr.net" crossorigin>

        @vite(['resources/css/app.css', 'resources/js/app.js'])

        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/swiper@11/swiper-bundle.min.css"/>
        <script src="https://cdn.jsdelivr.net/npm/swiper@11/swiper-bundle.min.js" defer></script>

        @include('partials.metrika')
    </head>


    <body id="top">
        <noscript><div><img src="https://mc.yandex.ru/watch/111942996" width="1" height="1" style="position:absolute; left:-9999px;" alt="" /></div></noscript>
        <!-- Хейдер -->
        <header class="header">
            <img src="{{ asset('images/logo.svg') }}" width="189" height="46" alt="Магия — ремонт квартир в Ростове-на-Дону" class="logo">
            
            <div class="navigation">
                <a class="Button_Navigation" href="https://t.me/SergeyWright" target="_blank" rel="noopener noreferrer">
                    <img src="{{ asset('images/Icon/Telegram.svg') }}" width="28" height="28" alt="" class="icon_nav">
                    <p class="navigation_text">Telegram</p>
                </a>

                <div class="Button_Navigation Active_Navigation">
                    <img src="{{ asset('images/Icon/Main.svg') }}" width="19" height="19" alt="" class="icon_nav">
                    <p class="navigation_text">Главная</p>
                </div>

                <a class="Button_Navigation" href="https://max.ru/u/f9LHodD0cOLsSlygVBBUbU_rAlEqsEcBA1bKp0CmWJsn8wMz3aiuwcm9lss" target="_blank" rel="noopener noreferrer">
                    <img src="{{ asset('images/Icon/Max.svg') }}" width="25" height="25" alt="" class="iconnav">
                    <p class="navigation_text">Max</p>
                </a>
            </div>

            <nav class="section_navigation" aria-label="Разделы сайта">
                <a href="#portfolio">Портфолио</a>
                <a href="#services">Услуги и цены</a>
                <a href="#reviews">Отзывы</a>
                <a href="#work-steps">Этапы работ</a>
                <a href="#contacts">Контакты</a>
            </nav>
        </header>

        <!-- Представления -->
        <main class="main">
            <section class="welcome_container">
                <div class="welcome_container_top">
                    <div class="welcome_info">
                        <div class="welcome_text">
                            <h1>Ремонт квартир <br> под ключ</h1>
                            <p>Выполняем ремонт квартир под ключ в Ростове-на-Дону — от бесплатного замера и сметы до чистовой отделки и сдачи готового объекта.</p>
                        </div>

                        <div class="welcome_button_info">
                            <div class="button but_black" data-modal-open>
                                <p>Оставить заявку</p>
                            </div>

                            <a href="#portfolio">смотреть портфолио</a>
                        </div>
                    </div>

                    <div class="hero_calculator_container">
                        @include('partials.repair-calculator')
                    </div>
                </div>
                
                <div class="welcome_container_down">
                    <div class="welcome_info_down">  
                        <div class="icon_info_down">
                            <img src="{{ asset('images/Icon/ruletka.svg') }}" width="442" height="442" alt="" class="icon_info">
                            <h2>Замер — бесплатно</h2>          
                        </div>
                        <p>Бесплатно выезжаем на объект в Ростове-на-Дону, выполняем замер и обсуждаем задачи ремонта до начала работ.</p>
                    </div>

                    <div class="welcome_info_down active_welcome_info_down">
                        <div class="icon_info_down">
                            <img src="{{ asset('images/Icon/smeta.svg') }}" width="474" height="512" alt="" class="icon_info">
                            <h2>Прозрачная смета</h2>                         
                        </div>
                        <p>Составляем подробную смету по работам и материалам, чтобы стоимость ремонта квартиры была понятна до подписания договора.</p>
                    </div>

                    <div class="welcome_info_down">
                        <div class="icon_info_down">
                            <img src="{{ asset('images/Icon/squad.svg') }}" width="512" height="512" alt="" class="icon_info">
                            <h2>Своя команда</h2>
                        </div>
                        <p>Собственная команда специалистов ведет объект от черновых работ до чистовой отделки и контролирует качество на каждом этапе.</p>
                    </div>
            </section>
        </main>

        <!-- Портфолио -->
        <div class="portfolio" id="portfolio">
            <section class="portfolio_container">
                <div class="Main_text_center">
                    <h2 class="seo-section-heading">Портфолио</h2>
                    <p>Показываем примеры ремонта квартир в Ростове-на-Дону: кухни, санузлы, спальни и комплексная отделка под ключ.</p>
                </div>

                @php
                    $portfolioImages = collect(range(1, 9))
                        ->map(fn ($image) => asset("images/Portf/{$image}." . ($image === 6 ? 'svg' : 'webp')))
                        ->values()
                        ->all();
                    $portfolioImageDimensions = [
                        1 => [456, 555],
                        2 => [456, 555],
                        3 => [406, 565],
                        4 => [475, 565],
                        5 => [638, 683],
                        6 => [960, 1280],
                        7 => [486, 564],
                        8 => [486, 555],
                        9 => [486, 555],
                    ];
                    $portfolioColumns = [1 => 1, 2 => 1, 3 => 2, 4 => 3, 5 => 4, 6 => 4, 7 => 1, 8 => 3, 9 => 4];
                    $portfolioProjects = [
                        1 => [
                            'title' => 'Ремонт двухкомнатной квартиры',
                            'description' => 'Комплексный ремонт квартиры в Ростове-на-Дону: выровняли стены, выполнили чистовую отделку и подготовили интерьер к заселению.',
                        ],
                        2 => [
                            'title' => 'Ремонт кухни-гостиной',
                            'description' => 'Объединили кухню и гостиную в удобное пространство, продумали хранение, освещение и отделку износостойкими материалами.',
                        ],
                        3 => [
                            'title' => 'Ремонт ванной комнаты',
                            'description' => 'Выполнили ремонт ванной комнаты под ключ: гидроизоляция, укладка плитки, разводка сантехники и установка оборудования.',
                        ],
                        4 => [
                            'title' => 'Ремонт квартиры в новостройке',
                            'description' => 'Провели отделку квартиры в новостройке Ростова-на-Дону с нуля: инженерные сети, стяжка пола, штукатурка и финишная отделка.',
                        ],
                        5 => [
                            'title' => 'Дизайнерский ремонт спальни',
                            'description' => 'Создали спокойный интерьер спальни с точной геометрией, продуманным освещением и качественной декоративной отделкой стен.',
                        ],
                        6 => [
                            'title' => 'Ремонт гостиной в современном стиле',
                            'description' => 'Обновили гостиную: выполнили малярные работы, монтаж напольного покрытия и многоуровневое освещение для комфортного интерьера.',
                        ],
                        7 => [
                            'title' => 'Капитальный ремонт квартиры',
                            'description' => 'Выполнили капитальный ремонт квартиры с заменой электрики, сантехнических коммуникаций и полной отделкой помещений под ключ.',
                        ],
                        8 => [
                            'title' => 'Ремонт прихожей и коридора',
                            'description' => 'Организовали функциональную прихожую с практичной отделкой, встроенным хранением и износостойкими материалами для ежедневного использования.',
                        ],
                        9 => [
                            'title' => 'Ремонт квартиры в Ростове-на-Дону',
                            'description' => 'Реализовали ремонт квартиры под ключ в Ростове-на-Дону: согласовали смету, выполнили работы и передали готовый интерьер заказчику.',
                        ],
                    ];
                @endphp

                <div class="wrapper" aria-label="Проекты портфолио">
                    @for ($cardIndex = 1; $cardIndex <= 9; $cardIndex++)
                        @php
                            $imageIndex = ($cardIndex - 1) % count($portfolioImages);
                            $cardImages = [
                                $portfolioImages[$imageIndex],
                                $portfolioImages[($imageIndex + 1) % count($portfolioImages)],
                                $portfolioImages[($imageIndex + 2) % count($portfolioImages)],
                            ];
                        @endphp
                        <article
                            class="portfolio_card portfolio_card--{{ $cardIndex }}"
                            style="--portfolio-column: {{ $portfolioColumns[$cardIndex] }};"
                            data-images="{{ json_encode($cardImages) }}"
                        >
                            <img src="{{ $cardImages[0] }}" width="{{ $portfolioImageDimensions[$cardIndex][0] }}" height="{{ $portfolioImageDimensions[$cardIndex][1] }}" loading="lazy" decoding="async" alt="Фото проекта: {{ $portfolioProjects[$cardIndex]['title'] }}" class="portfolio_card_image">
                            <div class="portfolio_card_info">
                                <span class="portfolio_card_number">{{ str_pad($cardIndex, 2, '0', STR_PAD_LEFT) }}</span>
                                <h3>{{ $portfolioProjects[$cardIndex]['title'] }}</h3>
                                <p>{{ $portfolioProjects[$cardIndex]['description'] }}</p>
                            </div>
                        </article>
                    @endfor
                </div>
            </section>
        </div>

        <!-- Наши услуги -->
        <div class="service" id="services">
            <section class="service_container">
                <div class="Main_text_left">
                    <h2 class="seo-section-heading">Наши услуги<span class="sr-only">: ремонт квартир под ключ в Ростове-на-Дону</span></h2>
                    <p>Подбираем формат ремонта под задачу: отделка квартиры в новостройке с нуля, ремонт вторичного жилья или комплексное обновление интерьера.</p>
                </div>

                <div class="service_main">
                    @include('partials.service-links')
                    <div class="service_switch">
                        <div class="switch_btn enable_switch is-selected" data-service-mode="new" role="button" tabindex="0">
                            <img src="{{ asset('images/Icon/Hammer.svg') }}" width="24" height="22" alt="" class="">
                            <p>Новостройка</p>
                        </div>

                        <div class="switch_btn" data-service-mode="secondary" role="button" tabindex="0">
                            <img src="{{ asset('images/Icon/Hammer.svg') }}" width="24" height="22" alt="" class="">
                            <p>Вторичка</p>
                        </div>
                    </div>

                    <div class="service_price">
                        <div class="container">
                            <div class="row">

                                <div class="col-xl-3 col-xxl-3 col-lg-4 col-md-6 col-sm-6 col-xs-12 col-12">
                                    <div class="Service_Price" data-secondary-title="Косметический" data-secondary-description="Косметический ремонт вторичной квартиры без перепланировки: обновили поверхности, освещение и напольное покрытие." data-secondary-tags="Штукатурные работы|Отопительные работы|Малярные работы" data-secondary-price="₽10,000">
                                        <div class="d-flex flex-column gap-3">
                                            <h3>Черновой</h3>

                                            <div class="service_card_tags d-flex flex-column gap-2">
                                                <p>Базовая отделка квартиры в новостройке с подготовкой стен, пола и инженерных систем к чистовым работам.</p>
                                                <div class="bord_block">Штукатурные работы</div>
                                                <div class="bord_block">Малярные работы</div>
                                            </div>
                                        </div>

                                        <div class="d-flex flex-column gap-2">
                                            <div class="price"><p>₽5,000</p><span>/ метр</span></div>

                                            <div class="button but_white" data-modal-open>
                                                <p>Оставить заявку</p>
                                            </div>
                                        </div>
                                    </div>       
                                </div>

                                <div class="col-xl-3 col-xxl-3 col-lg-4 col-md-6 col-sm-6 col-xs-12 col-12">
                                    <div class="Service_Price" data-secondary-title="Капитальный" data-secondary-description="Капитально обновляем вторичное жильё: меняем коммуникации, выравниваем стены и выполняем чистовую отделку." data-secondary-tags="Штукатурные работы|Отопительные работы|Малярные работы" data-secondary-price="₽14,000">
                                        <div class="d-flex flex-column gap-3">
                                            <h3>Эконом</h3>

                                            <div class="service_card_tags d-flex flex-column gap-2">
                                                <p>Рациональный ремонт квартиры с подготовкой поверхностей и практичной чистовой отделкой без лишних расходов.</p>
                                                <div class="bord_block">Штукатурные работы</div>
                                                <div class="bord_block">Малярные работы</div>
                                            </div>
                                        </div>

                                        <div class="d-flex flex-column gap-2">
                                            <div class="price"><p>₽12,000</p><span>/ метр</span></div>

                                            <div class="button but_white" data-modal-open>
                                                <p>Оставить заявку</p>
                                            </div>
                                        </div>
                                    </div>       
                                </div>

                                <div class="col-xl-3 col-xxl-3 col-lg-4 col-md-6 col-sm-6 col-xs-12 col-12">
                                    <div class="Service_Price" data-secondary-title="Евроремонт" data-secondary-description="Ремонт вторичной квартиры под ключ с обновлением электрики, подготовкой стен и качественной чистовой отделкой." data-secondary-tags="Штукатурные работы|Отопительные работы|Малярные работы" data-secondary-price="₽18,000">
                                        <div class="d-flex flex-column gap-3">
                                            <h3>Евроремонт</h3>

                                            <div class="service_card_tags d-flex flex-column gap-2">
                                                <p>Комплексный ремонт квартиры под ключ с обновлением инженерных систем и качественной отделкой помещений.</p>
                                                <div class="bord_block">Штукатурные работы</div>
                                                <div class="bord_block">Малярные работы</div>
                                            </div>
                                        </div>

                                        <div class="d-flex flex-column gap-2">
                                            <div class="price"><p>₽16,000</p><span>/ метр</span></div>

                                            <div class="button but_white" data-modal-open>
                                                <p>Оставить заявку</p>
                                            </div>
                                        </div>
                                    </div>       
                                </div>

                                <div class="col-xl-3 col-xxl-3 col-lg-4 col-md-6 col-sm-6 col-xs-12 col-12">
                                    <div class="Service_Price" data-secondary-title="Дизайнерский" data-secondary-description="Создаем индивидуальный интерьер вторичной квартиры с дизайн-проектом, продуманным светом и выразительной отделкой." data-secondary-tags="Штукатурные работы|Отопительные работы|Малярные работы" data-secondary-price="₽22,000">
                                        <div class="d-flex flex-column gap-3">
                                            <h3>Дизайнерский</h3>

                                            <div class="service_card_tags d-flex flex-column gap-2">
                                                <p>Индивидуальный ремонт с учетом планировки, дизайн-проекта, выбранных материалов и требований к интерьеру.</p>
                                                <div class="bord_block">Штукатурные работы</div>
                                                <div class="bord_block">Малярные работы</div>
                                            </div>
                                        </div>

                                        <div class="d-flex flex-column gap-2">
                                            <div class="price"><p>₽20,000</p><span>/ метр</span></div>

                                            <div class="button but_white" data-modal-open>
                                                <p>Оставить заявку</p>
                                            </div>
                                        </div>
                                    </div>       
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </section>
        </div>

        <!-- Обратная связь -->
        <div class="feedback" id="reviews">
            <section class="feedback_container">
                <div class="Main_text_center">
                    <h2 class="seo-section-heading">Наши отзывы</h2>
                    <p>Стоимость ремонта квартиры зависит от площади, состояния помещений, объема инженерных работ и выбранных материалов. Показываем состав работ в подробной смете.</p>
                </div>

                <div class="swiper my-slider">
                    <div class="swiper-wrapper">

                        <div class="swiper-slide">
                            <div class="Main_Swiper_Text">
                                <img src="{{ asset('images/feedback/1w.webp') }}" width="100" height="100" loading="lazy" decoding="async" alt="Ольга, клиентка компании" class="feedback_icon">
                                <p>Ольга</p>
                            </div>

                            <p>Заказала комплексный ремонт квартиры в Ростове-на-Дону. Получила понятную смету, аккуратную работу и готовый интерьер точно в согласованные сроки.</p>
                        </div>

                        <div class="swiper-slide">
                            <div class="Main_Swiper_Text">
                                <img src="{{ asset('images/feedback/1m.webp') }}" width="96" height="100" loading="lazy" decoding="async" alt="Максим, клиент компании" class="feedback_icon">
                                <p>Максим</p>
                            </div>

                            <p>Заказал ремонт кухни-гостиной под ключ: команда помогла с выбором материалов, организовала работы и оставила после себя чистый объект.</p>
                        </div>
                        
                        <div class="swiper-slide">
                            <div class="Main_Swiper_Text">
                                <img src="{{ asset('images/feedback/2w.webp') }}" width="100" height="100" loading="lazy" decoding="async" alt="Екатерина, клиентка компании" class="feedback_icon">
                                <p>Екатерина</p>
                            </div>

                            <p>Обратилась за ремонтом ванной комнаты. Специалисты качественно выполнили гидроизоляцию, плиточные и сантехнические работы, я осталась довольна результатом.</p>
                        </div>

                        <div class="swiper-slide">
                            <div class="Main_Swiper_Text">
                                <img src="{{ asset('images/feedback/2m.webp') }}" width="96" height="100" loading="lazy" decoding="async" alt="Андрей, клиент компании" class="feedback_icon">
                                <p>Андрей</p>
                            </div>

                            <p>Заказал ремонт квартиры в новостройке. Все прошло организованно: от черновой отделки и электрики до финишных покрытий и установки дверей.</p>
                        </div>

                        <div class="swiper-slide">
                            <div class="Main_Swiper_Text">
                                <img src="{{ asset('images/feedback/3w.webp') }}" width="96" height="100" loading="lazy" decoding="async" alt="Марина, клиентка компании" class="feedback_icon">
                                <p>Марина</p>
                            </div>

                            <p>Мне понравился подход к дизайнерскому ремонту спальни: учли мои пожелания, продумали освещение и помогли подобрать отделочные материалы.</p>
                        </div>

                        <div class="swiper-slide">
                            <div class="Main_Swiper_Text">
                                <img src="{{ asset('images/feedback/3m.webp') }}" width="96" height="100" loading="lazy" decoding="async" alt="Дмитрий, клиент компании" class="feedback_icon">
                                <p>Дмитрий</p>
                            </div>

                            <p>Заказал капитальный ремонт вторичной квартиры. Все этапы и стоимость заранее обсудили, специалисты поддерживали порядок на объекте.</p>
                        </div>

                        <div class="swiper-slide">
                            <div class="Main_Swiper_Text">
                                <img src="{{ asset('images/feedback/4m.webp') }}" width="96" height="100" loading="lazy" decoding="async" alt="Сергей, клиент компании" class="feedback_icon">
                                <p>Сергей</p>
                            </div>

                            <p>Бесплатный замер и подробная смета помогли быстро принять решение о ремонте. Работы выполнили последовательно, без неожиданных платежей.</p>
                        </div>

                        <div class="swiper-slide">
                            <div class="Main_Swiper_Text">
                                <img src="{{ asset('images/feedback/5m.webp') }}" width="96" height="100" loading="lazy" decoding="async" alt="Алексей, клиент компании" class="feedback_icon">
                                <p>Алексей</p>
                            </div>

                            <p>Заказал ремонт квартиры под ключ в Ростове-на-Дону. Получил профессиональную команду, прозрачные условия и аккуратную чистовую отделку.</p>
                        </div>
                    </div>
                
                    <!-- Пагинация (точки) -->
                    <div class="swiper-pagination"></div>
                </div>
                
            </section>
        </div>
        
        <!-- Смета -->
        <div class="estimate">
            <section class="estimate_container">
                <div class="container_main_text">
                    <div class="Main_text_left">
                        <h2 class="seo-section-heading">Фиксированная смета в договоре</h2>
                        <p>В смете собраны основные работы для ремонта квартиры: демонтаж, стены, электрика, сантехника, отопление, полы, плитка и чистовая отделка.</p>
                    </div>

                    <div class="estimate_second_text">
                        <a class="button but_black" href="{{ asset('СМЕТА ШАБЛОН.pdf') }}" download="Смета-на-ремонт.pdf">
                            <img src="{{ asset('images/Icon/download.svg') }}" width="16" height="16" alt="" class="">
                            <p>Скачать полную смету PDF</p>
                        </a>

                        <p>PDF содержит полный перечень работ и пример оформления нашей сметы.</p>
                    </div>
                </div>

                <div class="estimate_catalog" aria-label="Категории работ"></div>

                <div class="table_wrapper">
                    <table class="estimate_table">
                        <thead>
                            <tr>
                                <th>Наименование работ</th>
                                <th>Ед.</th>
                                <th>Цена</th>
                            </tr>
                        </thead>

                        <tbody></tbody>
                    </table>
                </div>

                <div class="estimate_after">
                    <div>
                        <p>Как используется смета</p>
                        <p>Итоговая цена ремонта формируется по площади объекта, состоянию квартиры, перечню работ и выбранным материалам. Все позиции фиксируем в смете.</p>
                    </div>

                    <a class="button but_black" href="{{ asset('СМЕТА ШАБЛОН.pdf') }}" download="Смета-на-ремонт.pdf">
                        <p>Скачать PDF-смету</p>
                    </a>
                </div>
            </section>
        </div>   

        @include('partials.lead-modal')

        <!-- Этапы работ -->
         <div class="step_work" id="work-steps">
            <section class="container_step_work">
                <div class="Main_text_left">
                    <h2 class="seo-section-heading">Этапы работ</h2>
                    <p>Организуем ремонт квартиры под ключ по понятному плану: от замера и подготовки сметы до контроля работ и передачи готового объекта.</p>
                </div>

                <div class="step_work_main">
                    <div class="wrapper_2">
                        <div class="box1_2">
                            <div class="box_main_text">
                                <p>Без полной предоплаты</p>
                                <div class="numeric">01</div>
                            </div>
                            
                            <p>
                                Выполняем ремонт квартиры под ключ в Ростове-на-Дону без полной предоплаты. Сначала согласовываем состав работ, материалы, сроки и подробную смету, а затем ведем объект поэтапно — от демонтажа и черновой отделки до чистовой отделки и сдачи готовой квартиры. Вы оплачиваете только фактически выполненные и принятые работы, поэтому бюджет ремонта остается прозрачным на каждом этапе.
                            </p>
                        </div>

                        <div class="box2_2">
                            <div class="box_main_text">
                                <p>Бесплатный замер</p>
                                <div class="numeric">02</div>
                            </div>
                            
                            <p>
                                Выезжаем на объект и выполняем замер бесплатно. Подробно консультируем по всем техническим особенностям помещений.
                            </p>
                        </div>

                        <div class="box3_2">
                            <div class="box_main_text">
                                <p>Дизайн-проект</p>
                                <div class="numeric">03</div>
                            </div>
                            
                            <p>
                                Разрабатываем дизайн-проект дешевле среднерыночной стоимости, бережно сохраняя качество и высокую проработку каждой детали.
                            </p>
                        </div>

                        <div class="box4_2">
                            <div class="box_main_text">
                                <p>Прозрачная смета</p>
                                <div class="numeric">04</div>
                            </div>
                            
                            <p>
                                Клиент заранее видит полный перечень планируемых работ и их стоимость. Исключаем появление любых непонятных скрытых платежей.
                            </p> 
                        </div>

                        <div class="box5_2">
                            <div class="box_main_text">
                                <p>Договор и сроки</p>
                                <div class="numeric">05</div>
                            </div>
                            
                            <p>
                                Фиксируем все основные условия сотрудничества, точные сроки, итоговую стоимость и взаимные обязательства сторон в официальном договоре.
                            </p>
                        </div>

                        <div class="box6_2">
                            <div class="box_main_text">
                                <p>Контроль качества</p>
                                <div class="numeric">06</div>
                            </div>
                            
                            <p>
                                Следим за технологией выполнения работ на каждом этапе и строго контролируем соответствие результата всем техническим регламентам.
                            </p>
                        </div>
                    </div>
                </div>
            </section>
         </div>

        <!-- Карта / Футер -->
        <div class="map" id="contacts">
            @include('partials.contacts')
            <section class="map_container">
                <iframe
                    class="map_frame"
                    src="https://yandex.ru/map-widget/v1/?z=12&ol=biz&oid=29377814826"
                    width="560"
                    height="400"
                    loading="lazy"
                    frameborder="0"
                    allowfullscreen="true"
                    title="Мы на карте"
                ></iframe>

                <div class="footer">
                    <img src="{{ asset('images/logo.svg') }}" width="189" height="46" loading="lazy" decoding="async" alt="Магия — ремонт квартир в Ростове-на-Дону" class="logo">

                    <div>
                        <p>Информация на сайте носит информационный характер и не является публичной офертой, определяемой положениями статьи 437 ГК РФ.</p>
                        <p>2026</p>
                    </div>
                </div>
            </section>
        </div>

        <script>
            window.addEventListener('DOMContentLoaded', () => {
                new Swiper('.my-slider', {
                    slidesPerView: 5,
                    spaceBetween: 16,

                    breakpoints: {
                        0: {
                            slidesPerView: 1,
                            spaceBetween: 10,
                        },
                        576: {
                            slidesPerView: 2,
                            spaceBetween: 16,
                        },
                        1200: {
                            slidesPerView: 5,
                            spaceBetween: 16,
                        },
                    },

                    pagination: {
                        el: '.my-slider .swiper-pagination',
                        clickable: true,
                    },
                });
            });
        </script>
    </body>
</html>
