@php
    $reviews = [
        ['igor', 'Игорь', 'После переезда', '«Получилось именно так, как и хотели»'],
        ['elena', 'Елена', 'Готовая квартира', '«Очень красиво получилось, особенно кухня»'],
        ['dmitriy', 'Дмитрий', 'После сдачи', '«Спасибо, что с вытяжкой так быстро решили»'],
        ['natalya', 'Наталья', 'Обсуждение сметы', '«Отлично, это как раз то, что нужно»'],
        ['elvira', 'Эльвира', 'Ход ремонта', '«Спасибо, так гораздо спокойнее»'],
        ['mihail', 'Михаил', 'Изменение графика', '«Спасибо, что предупредили заранее»'],
    ];
@endphp
<section class="review-gallery" id="reviews" aria-labelledby="reviews-title">
    <div class="review-heading">
        <div><span class="review-eyebrow">НА СВЯЗИ НА КАЖДОМ ЭТАПЕ</span><h2 id="reviews-title">Ремонт заканчивается.<br><span>Общение продолжается.</span></h2></div>
        <p>Смета, ход работ и жизнь после переезда —<br>в сообщениях наших заказчиков.</p>
    </div>
    <div class="review-toolbar">
        <span>● &nbsp; Из переписки в Telegram</span>
        <div class="review-controls"><span>6 историй</span><button type="button" data-review-prev aria-label="Предыдущая переписка">←</button><button type="button" data-review-next aria-label="Следующая переписка">→</button></div>
    </div>
    <div class="review-track" tabindex="0" aria-label="Галерея переписок. Листайте в стороны">
        @foreach ($reviews as [$slug, $name, $stage, $quote])
        <article class="review-card">
            <div class="review-card-top"><span>{{ $stage }}</span><span>{{ sprintf('%02d', $loop->iteration) }}</span></div>
            <a class="review-shot" href="{{ asset('images/reviews/'.$slug.'.jpg') }}" data-review-open data-review-name="{{ $name }}" aria-label="Открыть переписку: {{ $name }}">
                <img src="{{ asset('images/reviews/'.$slug.'.jpg') }}" alt="Переписка — {{ $name }}: {{ $stage }}" width="780" height="1429" loading="lazy" decoding="async">
                <span class="review-expand" aria-hidden="true">↗</span>
            </a>
        </article>
        @endforeach
    </div>
    <dialog class="review-dialog" aria-label="Просмотр переписки">
        <div class="review-dialog-bar"><span data-review-title></span><button type="button" data-review-close aria-label="Закрыть переписку">✕</button></div>
        <img data-review-full alt="">
    </dialog>
</section>
