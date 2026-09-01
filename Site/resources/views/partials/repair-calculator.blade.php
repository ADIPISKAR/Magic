@php($calculator = config('calculator'))
<section
    class="repair_calculator"
    aria-labelledby="repair-calculator-title"
    data-repair-calculator
    data-calculator='@json($calculator)'
>
    <div class="calculator_header">
        <div>
            <h2 id="repair-calculator-title">Рассчитайте стоимость</h2>
            <p>Предварительный расчёт работ за 30 секунд</p>
        </div>
        <span class="calculator_step">3 параметра</span>
    </div>

    <fieldset class="calculator_fieldset">
        <legend><span>01</span> Где планируется ремонт?</legend>
        <div class="calculator_property" data-calculator-property>
            @foreach ($calculator['properties'] as $propertyKey => $property)
                <button type="button" data-property="{{ $propertyKey }}" aria-pressed="{{ $propertyKey === $calculator['default_property'] ? 'true' : 'false' }}">
                    {{ $property['label'] }}
                </button>
            @endforeach
        </div>
    </fieldset>

    <div class="calculator_detail_grid">
        <fieldset class="calculator_fieldset">
            <legend><span>02</span> Какой ремонт нужен?</legend>
            <select class="calculator_plans" data-calculator-plans aria-label="Пакет ремонта"></select>
        </fieldset>

        <div class="calculator_area">
            <label for="calculator-area"><span><b>03</b> Площадь</span><output for="calculator-area" data-calculator-area-output>{{ $calculator['default_area'] }} м²</output></label>
            <input
                id="calculator-area"
                type="range"
                min="{{ $calculator['minimum_area'] }}"
                max="{{ $calculator['maximum_area'] }}"
                value="{{ $calculator['default_area'] }}"
                step="1"
                data-calculator-area
            >
            <div class="calculator_range_labels"><span>{{ $calculator['minimum_area'] }} м²</span><span>{{ $calculator['maximum_area'] }} м²</span></div>
        </div>
    </div>

    <div class="calculator_actions">
        <div class="calculator_result" aria-live="polite">
            <div>
                <span>Предварительная стоимость работ</span>
                <strong data-calculator-total>от 600 000 ₽</strong>
            </div>
            <span class="calculator_rate" data-calculator-rate>12 000 ₽/м²</span>
        </div>
        <button class="calculator_cta" type="button" data-calculator-lead data-modal-open>
            <span>Точная смета</span><span aria-hidden="true">↗</span>
        </button>
    </div>
    <p class="calculator_note">Расчёт ориентировочный: итог зависит от состояния квартиры и состава работ. Материалы и комплектация рассчитываются отдельно.</p>
</section>
