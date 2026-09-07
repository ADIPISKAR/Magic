/* Эксперимент: фокус следует за центром экрана. Блок, накрывающий середину
   вьюпорта, остаётся резким, остальные размываются тем сильнее, чем дальше
   они от неё. */

const BLOCKS = '.welcome_container, .portfolio, .service, .feedback, .estimate, .step_work, .map';
const REACH = 0.58;      // доля высоты экрана, на которой блок уходит в полный расфокус
const STORAGE_KEY = 'focus-scroll';

const reduced = matchMedia('(prefers-reduced-motion: reduce)').matches;
const blocks = [...document.querySelectorAll(BLOCKS)];

if (blocks.length && !reduced) {
    blocks.forEach((el) => el.setAttribute('data-focus-block', ''));

    let queued = false;
    function apply() {
        queued = false;
        const middle = innerHeight / 2;
        const reach = innerHeight * REACH;
        blocks.forEach((el) => {
            const rect = el.getBoundingClientRect();
            /* Блок, накрывающий середину экрана, резкий; для остальных берём
               расстояние до ближайшего края, иначе длинная секция уходила бы
               в расфокус, даже занимая весь экран. */
            const distance = rect.top > middle ? rect.top - middle
                : (rect.bottom < middle ? middle - rect.bottom : 0);
            const k = Math.min(1, Math.max(0, distance / reach));
            el.style.setProperty('--focus', k.toFixed(3));
        });
    }
    const schedule = () => {
        if (queued) return;
        queued = true;
        requestAnimationFrame(apply);
    };

    const toggle = document.createElement('button');
    toggle.type = 'button';
    toggle.className = 'focus-toggle';
    toggle.textContent = 'Расфокус';

    function setEnabled(on) {
        document.documentElement.classList.toggle('focus-scroll-on', on);
        toggle.setAttribute('aria-pressed', String(on));
        try { localStorage.setItem(STORAGE_KEY, on ? '1' : '0'); } catch { /* приватный режим */ }
        if (on) apply();
        else blocks.forEach((el) => el.style.setProperty('--focus', '0'));
    }

    toggle.addEventListener('click', () =>
        setEnabled(toggle.getAttribute('aria-pressed') !== 'true'));
    document.body.appendChild(toggle);

    addEventListener('scroll', () => {
        if (document.documentElement.classList.contains('focus-scroll-on')) schedule();
    }, { passive: true });
    addEventListener('resize', schedule, { passive: true });

    let saved = '1';
    try { saved = localStorage.getItem(STORAGE_KEY) ?? '1'; } catch { /* приватный режим */ }
    setEnabled(saved === '1');

    /* Модуль выполняется до того, как картинки получат размеры, поэтому первый
       расчёт идёт по ещё не разложенной странице. Пересчитываем, когда высоты
       установятся, и следим за дальнейшими сдвигами вёрстки. */
    addEventListener('load', schedule);
    if ('ResizeObserver' in window) new ResizeObserver(schedule).observe(document.body);
}
