<header class="service_header service_header_desktop portfolio_header">
    <a href="{{ route('home', [], false) }}" aria-label="Магия — главная"><img src="{{ asset('images/logo-mark.png') }}" width="222" height="104" alt="Магия" class="logo"></a>
    <nav aria-label="Основная навигация">
        <a href="{{ route('portfolio', [], false) }}">Портфолио</a>
        <a href="{{ route('home', [], false) }}#services">Услуги и цены</a>
        <a href="{{ route('home', [], false) }}#work-steps">Этапы работ</a>
        <a href="#contacts">Контакты</a>
    </nav>
    <div class="portfolio_header_contacts">
        <a href="https://t.me/SergeyWright" target="_blank" rel="noopener noreferrer" aria-label="Написать в Telegram"><img src="{{ asset('images/Icon/Telegram.svg') }}" width="22" height="22" alt=""></a>
        <a href="https://max.ru/u/f9LHodD0cOLsSlygVBBUbU_rAlEqsEcBA1bKp0CmWJsn8wMz3aiuwcm9lss" target="_blank" rel="noopener noreferrer" aria-label="Написать в Max"><img src="{{ asset('images/Icon/Max.svg') }}" width="20" height="20" alt=""></a>
        <a class="portfolio_header_phone" href="tel:{{ config('seo.phone') }}">{{ config('seo.phone_display') }}</a>
    </div>
</header>
<header class="mobile_header service_mobile_header" data-mobile-header>
    <div class="mobile_header_bar">
        <a href="{{ route('home', [], false) }}" aria-label="Магия — главная"><img src="{{ asset('images/logo-mark.png') }}" width="222" height="104" alt="Магия" class="mobile_header_logo"></a>
        <div class="mobile_header_quick" aria-label="Быстрые контакты">
            <a class="mobile_header_social" href="https://t.me/SergeyWright" target="_blank" rel="noopener noreferrer" aria-label="Написать в Telegram"><img src="{{ asset('images/Icon/Telegram.svg') }}" width="24" height="24" alt=""></a>
            <a class="mobile_header_social" href="https://max.ru/u/f9LHodD0cOLsSlygVBBUbU_rAlEqsEcBA1bKp0CmWJsn8wMz3aiuwcm9lss" target="_blank" rel="noopener noreferrer" aria-label="Написать в Max"><img src="{{ asset('images/Icon/Max.svg') }}" width="22" height="22" alt=""></a>
            <button class="mobile_header_toggle" type="button" aria-expanded="false" aria-controls="mobile-portfolio-menu" aria-label="Открыть меню" data-mobile-menu-toggle><span></span><span></span></button>
        </div>
    </div>
    <div class="mobile_header_panel" id="mobile-portfolio-menu" aria-hidden="true" data-mobile-menu>
        <div class="mobile_header_panel_inner">
            <nav aria-label="Мобильная навигация">
                <a href="{{ route('portfolio', [], false) }}">Портфолио</a>
                <a href="{{ route('home', [], false) }}#services">Услуги и цены</a>
                <a href="{{ route('home', [], false) }}#work-steps">Этапы работ</a>
                <a href="#contacts">Контакты</a>
            </nav>
            <div class="mobile_header_contact"><span>Обсудить ремонт</span><a href="tel:{{ config('seo.phone') }}">{{ config('seo.phone_display') }}</a></div>
        </div>
    </div>
</header>
