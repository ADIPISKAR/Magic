<div class="request_modal" aria-hidden="true">
            <div class="request_modal_overlay" data-modal-close></div>
            <div class="request_modal_dialog" role="dialog" aria-modal="true" aria-labelledby="request-modal-title">
                <button class="request_modal_close" type="button" aria-label="Закрыть окно" data-modal-close>&times;</button>
                <img src="{{ asset('images/WelcomePhoto/Wel_Photo_1.webp') }}" width="370" height="493" loading="lazy" decoding="async" alt="Современный интерьер квартиры" class="request_modal_image">
                <div class="request_modal_content">
                    <h2 id="request-modal-title">Обсудим ваш проект</h2>
                    <p data-lead-context>Расскажите о квартире — бесплатно оценим объём работ, сориентируем по стоимости и предложим оптимальный вариант ремонта.</p>
                    <form class="request_modal_form" data-lead-form>
                        <input type="hidden" name="message" value="" data-lead-message>
                        <input type="hidden" name="source" value="Форма сайта" data-lead-source>
                        <label>
                            <span class="sr-only">Ваше имя</span>
                            <input type="text" name="name" placeholder="Введите имя" autocomplete="name" required>
                        </label>
                        <label>
                            <span class="sr-only">Номер телефона</span>
                            <input type="tel" name="phone" placeholder="8-932-234-33-29" autocomplete="tel" required>
                        </label>
                        <button class="button but_black" type="submit">Получить консультацию</button>
                        <p class="request_modal_status" role="status" aria-live="polite"></p>
                    </form>
                </div>
            </div>
        </div>
