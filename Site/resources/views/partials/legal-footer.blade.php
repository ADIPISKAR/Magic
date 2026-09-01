<footer class="site_legal_footer">
    <div class="site_legal_footer_top">
        <a href="{{ route('home', [], false) }}" aria-label="Магия — главная">
            <img src="{{ asset('images/logo.svg') }}" width="189" height="46" loading="lazy" decoding="async" alt="Магия — ремонт квартир в Ростове-на-Дону" class="site_legal_footer_logo">
        </a>
        <div class="site_legal_footer_requisites">
            <span>Исполнитель</span>
            <strong>{{ config('seo.operator_name') }}</strong>
            <p>{{ config('seo.operator_status') }}</p>
            <p>ИНН {{ config('seo.operator_inn') }}</p>
        </div>
        <div class="site_legal_footer_contacts">
            <span>Контакты и деятельность</span>
            <a href="tel:{{ config('seo.phone') }}">{{ config('seo.phone_display') }}</a>
            @if (config('seo.contact_email'))
                <a href="mailto:{{ config('seo.contact_email') }}">{{ config('seo.contact_email') }}</a>
            @endif
            <p>{{ config('seo.postal_code') }}, {{ config('seo.city') }}, {{ config('seo.street_address') }}</p>
            <p>{{ config('seo.operator_activity') }} · {{ config('seo.operator_region') }}</p>
        </div>
        <nav class="site_legal_footer_links" aria-label="Правовая информация">
            <span>Документы</span>
            <a href="{{ route('privacy', [], false) }}">Политика обработки персональных данных</a>
            <a href="{{ route('personal-data-consent', [], false) }}">Согласие на обработку персональных данных</a>
            <button type="button" data-cookie-settings>Настройки cookie</button>
        </nav>
    </div>
    <div class="site_legal_footer_bottom">
        <p>Информация на сайте носит информационный характер и не является публичной офертой, определяемой положениями статьи 437 ГК РФ.</p>
        <p>© 2026 «Магия»</p>
    </div>
</footer>
