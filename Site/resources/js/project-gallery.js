document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('[data-project-gallery]').forEach((gallery) => {
        const main = gallery.querySelector('[data-gallery-main]');
        const thumbs = [...gallery.querySelectorAll('[data-gallery-thumb]')];
        const current = gallery.querySelector('[data-gallery-current]');
        const previous = gallery.querySelector('[data-gallery-prev]');
        const next = gallery.querySelector('[data-gallery-next]');

        if (!main || !thumbs.length) return;

        let activeIndex = 0;
        let busy = false;

        const openSheet = (index, direction = 1) => {
            if (busy) return;
            activeIndex = (index + thumbs.length) % thumbs.length;
            const thumb = thumbs[activeIndex];
            busy = true;
            main.classList.remove('is-entering-forward', 'is-entering-backward');
            main.classList.add(direction >= 0 ? 'is-leaving-forward' : 'is-leaving-backward');

            window.setTimeout(() => {
                main.src = thumb.dataset.src;
                main.alt = thumb.dataset.alt;
                main.classList.remove('is-leaving-forward', 'is-leaving-backward');
                main.classList.add(direction >= 0 ? 'is-entering-forward' : 'is-entering-backward');
                thumbs.forEach((button, buttonIndex) => {
                    const active = buttonIndex === activeIndex;
                    button.classList.toggle('is-active', active);
                    button.setAttribute('aria-current', String(active));
                });
                if (current) current.textContent = String(activeIndex + 1).padStart(2, '0');
                window.setTimeout(() => {
                    main.classList.remove('is-entering-forward', 'is-entering-backward');
                    busy = false;
                }, 240);
            }, 150);
        };

        thumbs.forEach((thumb, index) => thumb.addEventListener('click', () => openSheet(index, index >= activeIndex ? 1 : -1)));
        previous?.addEventListener('click', () => openSheet(activeIndex - 1, -1));
        next?.addEventListener('click', () => openSheet(activeIndex + 1, 1));

        gallery.addEventListener('keydown', (event) => {
            if (event.key === 'ArrowLeft') openSheet(activeIndex - 1, -1);
            if (event.key === 'ArrowRight') openSheet(activeIndex + 1, 1);
        });
    });
});
