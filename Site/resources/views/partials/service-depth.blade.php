@if ($slug === 'remont-vtorichnogo-zhilya')
    <section class="service_depth service_depth_secondary" id="service-depth" aria-labelledby="secondary-depth-title">
        <div class="service_section_intro">
            <div><p class="service_eyebrow">До начала демонтажа</p><h2 id="secondary-depth-title">Составляем карту состояния квартиры</h2></div>
            <p>Смета вторичного жилья начинается с того, что уже есть на объекте. По каждой зоне фиксируем состояние, решение и влияние на последующие работы.</p>
        </div>
        <div class="service_diagnostic_grid">
            <details><summary><span>01</span><strong>Стены и пол</strong><em>Что проверяем</em></summary><p>Прочность старых оснований, перепады, трещины, пустоты, следы протечек и пригодность поверхностей под новую отделку.</p></details>
            <details><summary><span>02</span><strong>Электрика</strong><em>Что проверяем</em></summary><p>Возраст проводки, расположение щита и точек, предполагаемую нагрузку от техники и доступность скрытых линий.</p></details>
            <details><summary><span>03</span><strong>Сантехника</strong><em>Что проверяем</em></summary><p>Состояние труб, стояков, запорной арматуры и расположение подключений относительно будущего оборудования.</p></details>
            <details><summary><span>04</span><strong>Что сохраняем</strong><em>Что проверяем</em></summary><p>Двери, паркет, мебель и другие элементы отмечаем заранее, чтобы предусмотреть защиту и не включать лишний демонтаж.</p></details>
        </div>
        <div class="service_compare" aria-labelledby="secondary-compare-title">
            <div class="service_compare_heading"><p class="service_eyebrow">Два разных объёма</p><h3 id="secondary-compare-title">Косметический или капитальный</h3></div>
            <div class="service_compare_table">
                <div class="service_compare_row service_compare_head"><span>Решение</span><strong>Косметический</strong><strong>Капитальный</strong></div>
                <div class="service_compare_row"><span>Покрытия</span><p>Локальная подготовка и обновление отделки</p><p>Полное снятие и восстановление оснований по смете</p></div>
                <div class="service_compare_row"><span>Коммуникации</span><p>Сохраняем исправные системы</p><p>Предусматриваем замену согласованных линий</p></div>
                <div class="service_compare_row"><span>Демонтаж</span><p>Только в границах обновления</p><p>По карте состояния и будущей планировке</p></div>
                <div class="service_compare_row"><span>Когда выбирать</span><p>Основания и инженерия исправны</p><p>Нужны глубокие изменения и новая логика квартиры</p></div>
            </div>
        </div>
    </section>
@elseif ($slug === 'remont-vannoy')
    <section class="service_depth service_depth_bathroom" id="service-depth" aria-labelledby="bathroom-depth-title">
        <div class="service_section_intro">
            <div><p class="service_eyebrow">Скрытые работы</p><h2 id="bathroom-depth-title">Что должно быть проверено до плитки</h2></div>
            <p>Готовая облицовка закрывает большую часть инженерных решений. Поэтому контрольные точки выносим в отдельную последовательность и принимаем до перехода к следующему этапу.</p>
        </div>
        <ol class="bathroom_process">
            <li><span>01</span><div><strong>Основание</strong><p>Проверяем плоскости, углы и готовность стен и пола к следующим слоям.</p></div></li>
            <li><span>02</span><div><strong>Разводка</strong><p>Сверяем выводы воды и канализации с размерами выбранного оборудования.</p></div></li>
            <li><span>03</span><div><strong>Гидроизоляция</strong><p>Фиксируем выполнение предусмотренных сметой работ в мокрых зонах до облицовки.</p></div></li>
            <li><span>04</span><div><strong>Раскладка плитки</strong><p>Согласуем направление, подрезки, примыкания и положение сантехнических точек.</p></div></li>
            <li><span>05</span><div><strong>Монтаж и проверка</strong><p>Устанавливаем согласованное оборудование и проверяем подключения перед сдачей.</p></div></li>
        </ol>
        <div class="bathroom_finish">
            <figure><img src="{{ asset('images/Portf/3.webp') }}" width="406" height="565" loading="lazy" decoding="async" alt="Готовая ванная комната после ремонта"><figcaption>Готовый результат из портфолио «Магии»</figcaption></figure>
            <div><p class="service_eyebrow">Пример расчёта</p><h3>Считаем площадь облицовки и выводы, а не площадь пола</h3><p>В планировщике выше можно указать метраж плитки, количество выводов и необходимость демонтажа. Полученный ориентир собирается из опубликованных ставок и скачивается вместе с перечнем проверок.</p><a href="#planner">Рассчитать свою ванную ↑</a></div>
        </div>
    </section>
@elseif ($slug === 'dizaynerskiy-remont')
    <section class="service_depth service_depth_designer" id="service-depth" aria-labelledby="designer-depth-title">
        <div class="service_section_intro">
            <div><p class="service_eyebrow">От идеи к реализации</p><h2 id="designer-depth-title">Проект переводит интерьер на язык работ</h2></div>
            <p>Документация отвечает на вопросы строителей до чистовой отделки. Готовые интерьеры показывают уровень деталей, к которому ведёт последовательная реализация решений.</p>
        </div>
        <div class="designer_bridge">
            <a href="{{ route('project', 'donskoy-arbat-65', false) }}" class="designer_bridge_project">
                <span>Пример технического проекта</span>
                <img src="{{ asset('images/projects/donskoy-arbat-65/1.jpg') }}" width="600" height="800" loading="lazy" decoding="async" alt="Лист технического дизайн-проекта квартиры 65 м²">
                <strong>Открыть все листы ↗</strong>
            </a>
            <div class="designer_bridge_arrow" aria-hidden="true">→</div>
            <div class="designer_bridge_result">
                <span>Примеры готовых интерьеров</span>
                <div><img src="{{ asset('images/Portf/1.webp') }}" width="456" height="555" loading="lazy" decoding="async" alt="Готовая кухня-гостиная из портфолио"><img src="{{ asset('images/Portf/8.webp') }}" width="486" height="555" loading="lazy" decoding="async" alt="Готовая спальня из портфолио"></div>
                <p>Проектные листы и фотографии показаны как разные примеры работ компании.</p>
            </div>
        </div>
        <div class="designer_documents">
            <article><span>01</span><h3>Планировка</h3><p>Расстановка мебели, проходы и функциональные зоны.</p></article>
            <article><span>02</span><h3>Рабочие чертежи</h3><p>Привязки электрики, сантехники и решений отделки.</p></article>
            <article><span>03</span><h3>Спецификации</h3><p>Перечень согласованных материалов и оборудования в составе выбранной услуги.</p></article>
            <article><span>04</span><h3>Смета реализации</h3><p>Работы считаются по утверждённым решениям и состоянию объекта.</p></article>
        </div>
    </section>
@elseif ($slug === 'remont-novostroek')
    <section class="service_depth service_depth_newbuild" id="service-depth" aria-labelledby="newbuild-depth-title">
        <div class="service_section_intro">
            <div><p class="service_eyebrow">Три контрольные точки</p><h2 id="newbuild-depth-title">Что решаем до чистовой отделки</h2></div>
            <p>В новостройке проще предусмотреть правильную последовательность, пока поверхности и коммуникации остаются открытыми. Проект и замер помогают не возвращаться к закрытым этапам.</p>
        </div>
        <div class="newbuild_case_line">
            <article><img src="{{ asset('images/projects/pyatyy-element-48/1.jpg') }}" width="566" height="800" loading="lazy" decoding="async" alt="Лист проекта квартиры 48 м²"><span>01 · На плане</span><h3>Мебель и маршруты</h3><p>Сначала проверяем, как квартира будет использоваться каждый день.</p></article>
            <article><img src="{{ asset('images/Portf/4.webp') }}" width="475" height="565" loading="lazy" decoding="async" alt="Готовая гостиная после ремонта"><span>02 · До отделки</span><h3>Свет и коммуникации</h3><p>Привязываем инженерные точки к будущей расстановке.</p></article>
            <article><img src="{{ asset('images/Portf/1.webp') }}" width="456" height="555" loading="lazy" decoding="async" alt="Готовая кухня-гостиная после ремонта"><span>03 · На финише</span><h3>Материалы и примыкания</h3><p>Согласованные покрытия определяют требования к подготовке оснований.</p></article>
        </div>
    </section>
@endif
