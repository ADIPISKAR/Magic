<!DOCTYPE html>
<html lang="{{ str_replace('_', '-', app()->getLocale()) }}">
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">

        <title>{{ config('app.name', 'Laravel') }}</title>

        @vite(['resources/css/app.css', 'resources/js/app.js'])

        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/swiper@11/swiper-bundle.min.css"/>
        <script src="https://cdn.jsdelivr.net/npm/swiper@11/swiper-bundle.min.js"></script>
    </head>


    <body>
        <!-- Хейдер -->
        <header class="header">
            <img src="{{ asset('images/logo.svg') }}" alt="Logo" class="logo">
            
            <div class="navigation">
                <div class="Button_Navigation">
                    <img src="{{ asset('images/Icon/Telegram.svg') }}" alt="" class="icon_nav">
                    <p class="navigation_text">Telegram</p>
                </div>

                <div class="Button_Navigation Active_Navigation">
                    <img src="{{ asset('images/Icon/Main.svg') }}" alt="" class="icon_nav">
                    <p class="navigation_text">Главная</p>
                </div>

                <div class="Button_Navigation">
                    <img src="{{ asset('images/Icon/Max.svg') }}" alt="" class="iconnav">
                    <p class="navigation_text">Max</p>
                </div>
            </div>
        </header>

        <!-- Представления -->
        <div class="main">
            <section class="welcome_container">
                <div class="welcome_container_top">
                    <div class="welcome_info">
                        <div class="welcome_text">
                            <h1>Ремонт квартир <br> в Ростове-на-Дону</h1>
                            <p>Ясность нашей позиции очевидна: укрепление и развитие внутренней структуры создаёт предпосылки для направлений прогрессивного развития.</p>
                        </div>

                        <div class="welcome_button_info">
                            <div class="button but_black">
                                <p>Заказать ремонт</p>
                            </div>

                            <p>смотреть портфолио</p>
                        </div>
                    </div>

                    <div class="hero_image_container">
                        <div class="hero_card">
                            <div class="hero_card_inner">
                                <div class="hero_card_front">
                                    <img src="{{ asset('images/WelcomePhoto/Wel_Photo_1.svg') }}" alt="Интерьер кухни" class="hero_image">
                                </div>
                                <div class="hero_card_back">
                                    <strong>Кухня-гостиная</strong>
                                    <p>Продумали хранение, освещение и удобную рабочую зону.</p>
                                </div>
                            </div>
                        </div>

                        <div class="hero_card">
                            <div class="hero_card_inner">
                                <div class="hero_card_front">
                                    <img src="{{ asset('images/WelcomePhoto/Wel_Photo_2.svg') }}" alt="Интерьер ванной комнаты" class="hero_image">
                                </div>
                                <div class="hero_card_back">
                                    <strong>Ванная комната</strong>
                                    <p>Собрали спокойный интерьер с практичными материалами.</p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="welcome_container_down">
                    <div class="welcome_info_down">  
                        <div class="icon_info_down">
                            <img src="{{ asset('images/Icon/Gal.svg') }}" alt="Icon" class="icon_info">
                            <h2>Бесплатный выезд и замер</h2>          
                        </div>
                        <p>Актуальные позиции отделочных, сантехнических, электромонтажных и других видов работ с ориентировочными расценками.</p>
                    </div>

                    <div class="welcome_info_down active_welcome_info_down">
                        <div class="icon_info_down">
                            <img src="{{ asset('images/Icon/Garant.svg') }}" alt="Icon" class="icon_info">
                            <h2>Бесплатный выезд и замер</h2>                         
                        </div>

                        <p>Актуальные позиции отделочных, сантехнических, электромонтажных и других видов работ с ориентировочными расценками.</p>
                    </div>

                    <div class="welcome_info_down">
                        <div class="icon_info_down">
                            <img src="{{ asset('images/Icon/Main.svg') }}" alt="Icon" class="icon_info">
                            <h2>Бесплатный выезд и замер</h2>
                        </div>
                        <p>Актуальные позиции отделочных, сантехнических, электромонтажных и других видов работ с ориентировочными расценками.</p>
                    </div>
            </section>
        </div>

        <!-- Портфолио -->
        <div class="portfolio">
            <section class="portfolio_container">
                <div class="Main_text_center">
                    <h1>Портфолио</h1>
                    <p>Актуальные позиции отделочных, сантехнических, электромонтажных и других видов работ с ориентировочными расценками.</p>
                </div>

                @php
                    $portfolioImages = collect(range(1, 9))
                        ->map(fn ($image) => asset("images/Portf/{$image}.svg"))
                        ->values()
                        ->all();
                    $portfolioColumns = [1 => 1, 2 => 1, 3 => 2, 4 => 3, 5 => 4, 6 => 4, 7 => 1, 8 => 3, 9 => 4];
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
                            <img src="{{ $cardImages[0] }}" alt="Проект {{ $cardIndex }}" class="portfolio_card_image">
                            <div class="portfolio_card_info">
                                <span class="portfolio_card_number">{{ str_pad($cardIndex, 2, '0', STR_PAD_LEFT) }}</span>
                                <h2>Проект {{ $cardIndex }}</h2>
                                <p>Дизайн и ремонт интерьера с вниманием к каждой детали.</p>
                            </div>
                        </article>
                    @endfor
                </div>
            </section>
        </div>

        <!-- Наши услуги -->
        <div class="service">
            <section class="service_container">
                <div class="Main_text_left">
                    <h1>Наши услуги</h1>
                    <p>Актуальные позиции отделочных, сантехнических, электромонтажных и других видов работ с ориентировочными расценками.</p>
                </div>

                <div class="service_main">
                    <div class="service_switch">
                        <div class="switch_btn enable_switch">
                            <img src="{{ asset('images/Icon/Hammer.svg') }}" alt="Hero Image" class="">
                            <p>Новостройка</p>
                        </div>

                        <div class="switch_btn">
                            <img src="{{ asset('images/Icon/Hammer.svg') }}" alt="Hero Image" class="">
                            <p>Новостройка</p>
                        </div>
                    </div>

                    <div class="service_price">
                        <div class="container">
                            <div class="row">

                                <div class="col-xl-3 col-xxl-3 col-lg-4 col-md-6 col-sm-6 col-xs-12 col-12">
                                    <div class="Service_Price">
                                        <div class="d-flex flex-column gap-3">
                                            <h2>Черновой</h2>

                                            <div class="d-flex flex-column gap-2">
                                                <p>Актуальные позиции отделочных, сантехнических, электромонтажных и других видов работ с ориентировочными расценками.</p>
                                                <div class="bord_block">Штукатурные работы</div>
                                                <div class="bord_block">Малярные работы</div>
                                            </div>
                                        </div>

                                        <div class="d-flex flex-column gap-2">
                                            <div class="price"><p>₽5,000</p><span>/ метр</span></div>

                                            <div class="button but_white">
                                                <p>Заказать ремонт</p>
                                            </div>
                                        </div>
                                    </div>       
                                </div>

                                <div class="col-xl-3 col-xxl-3 col-lg-4 col-md-6 col-sm-6 col-xs-12 col-12">
                                    <div class="Service_Price">
                                        <div class="d-flex flex-column gap-3">
                                            <h2>Черновой</h2>

                                            <div class="d-flex flex-column gap-2">
                                                <p>Актуальные позиции отделочных, сантехнических, электромонтажных и других видов работ с ориентировочными расценками.</p>
                                                <div class="bord_block">Штукатурные работы</div>
                                                <div class="bord_block">Малярные работы</div>
                                            </div>
                                        </div>

                                        <div class="d-flex flex-column gap-2">
                                            <div class="price"><p>₽5,000</p><span>/ метр</span></div>

                                            <div class="button but_white">
                                                <p>Заказать ремонт</p>
                                            </div>
                                        </div>
                                    </div>       
                                </div>

                                <div class="col-xl-3 col-xxl-3 col-lg-4 col-md-6 col-sm-6 col-xs-12 col-12">
                                    <div class="Service_Price">
                                        <div class="d-flex flex-column gap-3">
                                            <h2>Черновой</h2>

                                            <div class="d-flex flex-column gap-2">
                                                <p>Актуальные позиции отделочных, сантехнических, электромонтажных и других видов работ с ориентировочными расценками.</p>
                                                <div class="bord_block">Штукатурные работы</div>
                                                <div class="bord_block">Малярные работы</div>
                                            </div>
                                        </div>

                                        <div class="d-flex flex-column gap-2">
                                            <div class="price"><p>₽5,000</p><span>/ метр</span></div>

                                            <div class="button but_white">
                                                <p>Заказать ремонт</p>
                                            </div>
                                        </div>
                                    </div>       
                                </div>

                                <div class="col-xl-3 col-xxl-3 col-lg-4 col-md-6 col-sm-6 col-xs-12 col-12">
                                    <div class="Service_Price">
                                        <div class="d-flex flex-column gap-3">
                                            <h2>Черновой</h2>

                                            <div class="d-flex flex-column gap-2">
                                                <p>Актуальные позиции отделочных, сантехнических, электромонтажных и других видов работ с ориентировочными расценками.</p>
                                                <div class="bord_block">Штукатурные работы</div>
                                                <div class="bord_block">Малярные работы</div>
                                            </div>
                                        </div>

                                        <div class="d-flex flex-column gap-2">
                                            <div class="price"><p>₽5,000</p><span>/ метр</span></div>

                                            <div class="button but_white">
                                                <p>Заказать ремонт</p>
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
        <div class="feedback">
            <section class="feedback_container">
                <div class="Main_text_center">
                    <h1>Наши отзывы</h1>
                    <p>Актуальные позиции отделочных, сантехнических, электромонтажных и других видов работ с ориентировочными расценками.</p>
                </div>

                <div class="swiper my-slider">
                    <div class="swiper-wrapper">

                        <div class="swiper-slide">
                            <div class="Main_Swiper_Text">
                                <img src="{{ asset('images/feedback/1.svg') }}" alt="Hero Image" class="feedback_icon">
                                <p>Игорь Матвиенко</p>
                            </div>

                            <p>Долго искали компанию, которой можно доверить ремонт всей квартиры. Здесь сделали всё идеально: работа аккуратная, материалы качественные, сроки соблюдены. Рекомендуем!</p>
                        </div>

                        <div class="swiper-slide">
                            <div class="Main_Swiper_Text">
                                <img src="{{ asset('images/feedback/2.svg') }}" alt="Hero Image" class="feedback_icon">
                                <p>Игорь Матвиенко</p>
                            </div>

                            <p>Долго искали компанию, которой можно доверить ремонт всей квартиры. Здесь сделали всё идеально: работа аккуратная, материалы качественные, сроки соблюдены. Рекомендуем!</p>
                        </div>
                        
                        <div class="swiper-slide">
                            <div class="Main_Swiper_Text">
                                <img src="{{ asset('images/feedback/3.svg') }}" alt="Hero Image" class="feedback_icon">
                                <p>Игорь Матвиенко</p>
                            </div>

                            <p>Долго искали компанию, которой можно доверить ремонт всей квартиры. Здесь сделали всё идеально: работа аккуратная, материалы качественные, сроки соблюдены. Рекомендуем!</p>
                        </div>

                        <div class="swiper-slide">
                            <div class="Main_Swiper_Text">
                                <img src="{{ asset('images/feedback/4.svg') }}" alt="Hero Image" class="feedback_icon">
                                <p>Игорь Матвиенко</p>
                            </div>

                            <p>Долго искали компанию, которой можно доверить ремонт всей квартиры. Здесь сделали всё идеально: работа аккуратная, материалы качественные, сроки соблюдены. Рекомендуем!</p>
                        </div>

                        <div class="swiper-slide">
                            <div class="Main_Swiper_Text">
                                <img src="{{ asset('images/feedback/5.svg') }}" alt="Hero Image" class="feedback_icon">
                                <p>Игорь Матвиенко</p>
                            </div>

                            <p>Долго искали компанию, которой можно доверить ремонт всей квартиры. Здесь сделали всё идеально: работа аккуратная, материалы качественные, сроки соблюдены. Рекомендуем!</p>
                        </div>

                        <div class="swiper-slide">
                            <div class="Main_Swiper_Text">
                                <img src="{{ asset('images/feedback/1.svg') }}" alt="Hero Image" class="feedback_icon">
                                <p>Игорь Матвиенко</p>
                            </div>

                            <p>Долго искали компанию, которой можно доверить ремонт всей квартиры. Здесь сделали всё идеально: работа аккуратная, материалы качественные, сроки соблюдены. Рекомендуем!</p>
                        </div>

                        <div class="swiper-slide">
                            <div class="Main_Swiper_Text">
                                <img src="{{ asset('images/feedback/2.svg') }}" alt="Hero Image" class="feedback_icon">
                                <p>Игорь Матвиенко</p>
                            </div>

                            <p>Долго искали компанию, которой можно доверить ремонт всей квартиры. Здесь сделали всё идеально: работа аккуратная, материалы качественные, сроки соблюдены. Рекомендуем!</p>
                        </div>

                        <div class="swiper-slide">
                            <div class="Main_Swiper_Text">
                                <img src="{{ asset('images/feedback/3.svg') }}" alt="Hero Image" class="feedback_icon">
                                <p>Игорь Матвиенко</p>
                            </div>

                            <p>Долго искали компанию, которой можно доверить ремонт всей квартиры. Здесь сделали всё идеально: работа аккуратная, материалы качественные, сроки соблюдены. Рекомендуем!</p>
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
                        <h1>Фиксированная смета в договоре</h1>
                        <p>Актуальные позиции отделочных, сантехнических, электромонтажных и других видов работ с ориентировочными расценками.</p>
                    </div>

                    <div class="estimate_second_text">
                        <div class="button but_black">
                            <img src="{{ asset('images/Icon/download.svg') }}" alt="Hero Image" class="">
                            <p>Скачать полную смету PDF</p>
                        </div>

                        <p>PDF содержит полный перечень работ и пример оформления нашей сметы.</p>
                    </div>
                </div>

                <div class="estimate_catalog">
                    <div class="bord_block bord_block_active">Отделочные работы</div>
                    <div class="bord_block">Штукатурные работы</div>
                    <div class="bord_block">Малярные работы</div>
                    <div class="bord_block">Отопительные работы</div>
                    <div class="bord_block">Стяжка пола</div>
                    <div class="bord_block">Плиточные работы</div>
                    <div class="bord_block">Напольные покрытия</div>
                    <div class="bord_block">Сантехнические работы</div>
                    <div class="bord_block">Электромонтажные работы</div>
                    <div class="bord_block">Демонтаж</div>
                    <div class="bord_block">Отделочные работы</div>
                    <div class="bord_block">Штукатурные работы</div>
                    <div class="bord_block">Малярные работы</div>
                    <div class="bord_block">Отопительные работы</div>
                    <div class="bord_block">Стяжка пола</div>
                    <div class="bord_block">Плиточные работы</div>
                    <div class="bord_block">Напольные покрытия</div>
                    <div class="bord_block">Сантехнические работы</div>
                    <div class="bord_block">Электромонтажные работы</div>
                    <div class="bord_block">Демонтаж</div>
                </div>

                <div class="table_wrapper">
                    <table class="estimate_table">
                        <thead>
                            <tr>
                                <th>Наименование работ</th>
                                <th>Ед.</th>
                                <th>Цена</th>
                            </tr>
                        </thead>

                        <tbody>
                            <tr>
                                <td>Демонтаж старого покрытия</td>
                                <td>м²</td>
                                <td>350 ₽</td>
                            </tr>

                            <tr>
                                <td>Штукатурка стен</td>
                                <td>м²</td>
                                <td>650 ₽</td>
                            </tr>

                            <tr class="active_column">
                                <td>Укладка плитки</td>
                                <td>м²</td>
                                <td>1 200 ₽</td>
                            </tr>

                            <tr>
                                <td>Укладка плитки</td>
                                <td>м²</td>
                                <td>1 200 ₽</td>
                            </tr>

                            <tr>
                                <td>Укладка плитки</td>
                                <td>м²</td>
                                <td>1 200 ₽</td>
                            </tr>

                            <tr>
                                <td>Укладка плитки</td>
                                <td>м²</td>
                                <td>1 200 ₽</td>
                            </tr>

                            <tr>
                                <td>Укладка плитки</td>
                                <td>м²</td>
                                <td>1 200 ₽</td>
                            </tr>

                            <tr>
                                <td>Укладка плитки</td>
                                <td>м²</td>
                                <td>1 200 ₽</td>
                            </tr>

                            <tr>
                                <td>Укладка плитки</td>
                                <td>м²</td>
                                <td>1 200 ₽</td>
                            </tr>

                            <tr>
                                <td>Укладка плитки</td>
                                <td>м²</td>
                                <td>1 200 ₽</td>
                            </tr>

                            <tr>
                                <td>Укладка плитки</td>
                                <td>м²</td>
                                <td>1 200 ₽</td>
                            </tr>

                            <tr>
                                <td>Укладка плитки</td>
                                <td>м²</td>
                                <td>1 200 ₽</td>
                            </tr>

                            <tr>
                                <td>Укладка плитки</td>
                                <td>м²</td>
                                <td>1 200 ₽</td>
                            </tr>
                        </tbody>
                    </table>
                </div>

                <div class="estimate_after">
                    <div>
                        <p>Как используется смета</p>
                        <p>Это пример структуры нашей рабочей сметы. Точная стоимость зависит от площади объекта, состояния помещения и выбранных материалов.</p>
                    </div>

                    <div class="button but_black">
                        <p>Скачать PDF-смету</p>
                    </div>
                </div>
            </section>
        </div>   

        <!-- Этапы работ -->
         <div class="step_work">
            <section class="container_step_work">
                <div class="Main_text_left">
                    <h1>Этапы работ</h1>
                    <p>Актуальные позиции отделочных, сантехнических, электромонтажных и других видов работ с ориентировочными расценками.</p>
                </div>

                <div class="step_work_main">
                    <div class="wrapper_2">
                        <div class="box1_2">
                            <div class="box_main_text">
                                <p>Без предоплаты</p>
                                <div class="numeric">01</div>
                            </div>
                            
                            <p>
                                Не требуем полной предоплаты за ремонт. Условия оплаты прозрачны и заранее согласовываются с клиентом — вы платите поэтапно только за фактически выполненные и принятые работы.Не требуем полной предоплаты за ремонт. Условия оплаты прозрачны и заранее согласовываются с клиентом — вы платите поэтапно только за фактически выполненные и принятые работы.Не требуем полной предоплаты за ремонт. Условия оплаты прозрачны и заранее согласовываются с клиентом — вы платите поэтапно только за фактически выполненные и принятые работы.
                            </p>
                        </div>

                        <div class="box2_2">
                            <div class="box_main_text">
                                <p>Без предоплаты</p>
                                <div class="numeric">02</div>
                            </div>
                            
                            <p>
                                Выезжаем на объект и выполняем замер бесплатно. Подробно консультируем по всем техническим особенностям помещений.
                            </p>
                        </div>

                        <div class="box3_2">
                            <div class="box_main_text">
                                <p>Без предоплаты</p>
                                <div class="numeric">03</div>
                            </div>
                            
                            <p>
                                Разрабатываем дизайн-проект дешевле среднерыночной стоимости, бережно сохраняя качество и высокую проработку каждой детали.
                            </p>
                        </div>

                        <div class="box4_2">
                            <div class="box_main_text">
                                <p>Без предоплаты</p>
                                <div class="numeric">04</div>
                            </div>
                            
                            <p>
                                Клиент заранее видит полный перечень планируемых работ и их стоимость. Исключаем появление любых непонятных скрытых платежей.
                            </p> 
                        </div>

                        <div class="box5_2">
                            <div class="box_main_text">
                                <p>Без предоплаты</p>
                                <div class="numeric">05</div>
                            </div>
                            
                            <p>
                                Фиксируем все основные условия сотрудничества, точные сроки, итоговую стоимость и взаимные обязательства сторон в официальном договоре.
                            </p>
                        </div>

                        <div class="box6_2">
                            <div class="box_main_text">
                                <p>Без предоплаты</p>
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
        <div class="map">
            <section class="map_container">
                <div class="map_image"></div>

                <div class="footer">
                    <img src="http://127.0.0.1:8000/images/logo.svg" alt="Logo" class="logo">

                    <div>
                        <p>Информация на сайте носит информационный характер и не является публичной офертой, определяемой положениями статьи 437 ГК РФ.</p>
                        <p>2026</p>
                    </div>
                </div>
            </section>
        </div>

        <script>
            const swiper = new Swiper('.my-slider', {
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
        </script>
    </body>
</html>
