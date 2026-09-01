<div class="request_modal" aria-hidden="true">
    <div class="request_modal_overlay" data-modal-close></div>
    <div class="request_modal_dialog" role="dialog" aria-modal="true" aria-labelledby="request-modal-title">
        <button class="request_modal_close" type="button" aria-label="Закрыть окно" data-modal-close>
            <span></span>
            <span></span>
        </button>

        <div class="request_modal_visual">
            <img src="{{ asset('images/WelcomePhoto/Wel_Photo_1.webp') }}" width="370" height="493" loading="lazy" decoding="async" alt="Современный интерьер квартиры" class="request_modal_image">
            <div class="request_modal_visual_content">
                <img src="{{ asset('images/logo.svg') }}" width="189" height="46" alt="Магия" class="request_modal_logo">
                <div>
                    <span class="request_modal_badge">Бесплатная консультация</span>
                    <p>Сначала разберём задачу.<br>Потом посчитаем ремонт.</p>
                </div>
            </div>
        </div>

        <div class="request_modal_content">
            <span class="request_modal_eyebrow">Заявка на расчёт</span>
            <h2 id="request-modal-title">Обсудим ваш ремонт</h2>
            <p data-lead-context>Расскажите о квартире — бесплатно оценим объём работ, сориентируем по стоимости и предложим оптимальный вариант ремонта.</p>

            <form class="request_modal_form" data-lead-form>
                <input type="hidden" name="message" value="" data-lead-message>
                <input type="hidden" name="source" value="Форма сайта" data-lead-source>
                <div class="request_modal_fields">
                    <label>
                        <span>Ваше имя</span>
                        <input type="text" name="name" placeholder="Как к вам обращаться?" autocomplete="name" required>
                    </label>
                    <label>
                        <span>Телефон</span>
                        <input type="tel" name="phone" placeholder="+7 900 000-00-00" autocomplete="tel" inputmode="tel" required>
                    </label>
                </div>
                <button class="request_modal_submit" type="submit">
                    <span>Получить консультацию</span>
                    <span aria-hidden="true">↗</span>
                </button>
                <p class="request_modal_status" role="status" aria-live="polite"></p>
                <label class="request_modal_consent">
                    <input type="checkbox" name="privacy_consent" value="1" required>
                    <span class="request_modal_consent_mark" aria-hidden="true">✓</span>
                    <span>Я даю <a href="{{ route('personal-data-consent', [], false) }}" target="_blank" rel="noopener noreferrer">согласие на обработку персональных данных</a>.</span>
                </label>
                <p class="request_modal_privacy">Как мы используем и защищаем данные, описано в <a href="{{ route('privacy', [], false) }}" target="_blank" rel="noopener noreferrer">политике обработки персональных данных</a>.</p>
            </form>

            <div class="request_modal_messengers">
                <span>Удобнее написать?</span>
                <div>
                    <a href="https://t.me/SergeyWright" target="_blank" rel="noopener noreferrer" aria-label="Написать в Telegram">
                        <img src="{{ asset('images/Icon/Telegram.svg') }}" width="22" height="22" alt="">
                        Telegram
                    </a>
                    <a href="https://max.ru/u/f9LHodD0cOLsSlygVBBUbU_rAlEqsEcBA1bKp0CmWJsn8wMz3aiuwcm9lss" target="_blank" rel="noopener noreferrer" aria-label="Написать в Max">
                        <img src="{{ asset('images/Icon/Max.svg') }}" width="20" height="20" alt="">
                        Max
                    </a>
                </div>
            </div>
        </div>
    </div>
</div>

<div class="exit_offer_modal" aria-hidden="true" data-exit-modal>
    <div class="exit_offer_overlay" data-exit-close></div>
    <div class="exit_offer_dialog" role="dialog" aria-modal="true" aria-labelledby="exit-offer-title" aria-describedby="exit-offer-description">
        <button class="exit_offer_close" type="button" aria-label="Закрыть предложение" data-exit-close>
            <span></span>
            <span></span>
        </button>

        <div class="exit_offer_visual" aria-hidden="true">
            <img src="{{ asset('images/logo.svg') }}" width="189" height="46" alt="" class="exit_offer_logo">
            <div class="exit_offer_discount">
                <strong>−10%</strong>
                <span>на дизайн-проект</span>
            </div>
            <p>Продуманный интерьер<br>до начала ремонта</p>
        </div>

        <div class="exit_offer_content">
            <span class="exit_offer_eyebrow">Предложение для вашего проекта</span>
            <h2 id="exit-offer-title">Скидка 10% на дизайн-проект</h2>
            <p id="exit-offer-description">Оставьте контакты — уточним задачи, состав проекта и зафиксируем скидку перед расчётом.</p>
            <ul>
                <li>Планировка и расстановка мебели</li>
                <li>Схемы электрики и освещения</li>
                <li>Подбор материалов и решений</li>
            </ul>
            <button
                class="exit_offer_submit"
                type="button"
                data-exit-accept
                data-modal-open
                data-lead-context="Зафиксируем скидку 10% на дизайн-проект, уточним задачи и подготовим расчёт."
                data-lead-message="Хочу получить скидку 10% на дизайн-проект."
                data-lead-source="Exit-intent — скидка на дизайн-проект"
            >
                <span>Получить скидку 10%</span>
                <span aria-hidden="true">↗</span>
            </button>
            <button class="exit_offer_decline" type="button" data-exit-close>Продолжить без скидки</button>
        </div>
    </div>
</div>
