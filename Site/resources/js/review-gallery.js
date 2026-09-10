import '../css/review-gallery.css';

const gallery = document.querySelector('.review-gallery');
if (gallery) {
    const track = gallery.querySelector('.review-track');
    const dialog = gallery.querySelector('dialog');
    const image = dialog.querySelector('[data-review-full]');
    let opener;
    let drag = null;
    let suppressClick = false;
    track.addEventListener('dragstart', (event) => event.preventDefault());
    track.addEventListener('pointerdown', (event) => {
        if (event.pointerType !== 'mouse' || event.button !== 0) return;
        suppressClick = false;
        drag = { id: event.pointerId, x: event.clientX, left: track.scrollLeft, moved: false };
    });
    track.addEventListener('pointermove', (event) => {
        if (!drag || event.pointerId !== drag.id) return;
        const delta = event.clientX - drag.x;
        if (!drag.moved && Math.abs(delta) < 5) return;
        if (!drag.moved) {
            drag.moved = true;
            track.setPointerCapture(event.pointerId);
            track.classList.add('is-dragging');
        }
        event.preventDefault();
        track.scrollLeft = drag.left - delta;
    });
    const finishDrag = () => {
        if (!drag) return;
        const { id, moved } = drag;
        drag = null;
        suppressClick = moved;
        if (track.hasPointerCapture(id)) track.releasePointerCapture(id);
        track.classList.remove('is-dragging');
    };
    window.addEventListener('pointerup', finishDrag);
    window.addEventListener('pointercancel', finishDrag);
    track.addEventListener('lostpointercapture', finishDrag);
    window.addEventListener('blur', finishDrag);
    track.addEventListener('click', (event) => {
        if (!suppressClick) return;
        event.preventDefault();
        event.stopImmediatePropagation();
        suppressClick = false;
    }, true);
    const update = () => {
        gallery.querySelector('[data-review-prev]').disabled = track.scrollLeft < 2;
        gallery.querySelector('[data-review-next]').disabled = track.scrollLeft >= track.scrollWidth - track.clientWidth - 2;
    };
    const move = (direction) => track.scrollBy({ left: direction * (gallery.querySelector('.review-card').getBoundingClientRect().width + 24), behavior: window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'instant' : 'smooth' });
    gallery.querySelector('[data-review-prev]').addEventListener('click', () => move(-1));
    gallery.querySelector('[data-review-next]').addEventListener('click', () => move(1));
    track.addEventListener('scroll', update, { passive: true });
    window.addEventListener('resize', update);
    track.addEventListener('keydown', (event) => {
        if (event.key === 'ArrowRight' || event.key === 'ArrowLeft') {
            event.preventDefault();
            move(event.key === 'ArrowRight' ? 1 : -1);
        }
    });
    gallery.querySelectorAll('[data-review-open]').forEach((link) => link.addEventListener('click', (event) => {
        event.preventDefault();
        opener = link;
        image.src = link.href;
        image.alt = link.querySelector('img').alt;
        dialog.querySelector('[data-review-title]').textContent = link.dataset.reviewName + ' · Переписка';
        dialog.showModal();
        dialog.scrollTop = 0;
        document.body.classList.add('review-is-open');
    }));
    dialog.querySelector('[data-review-close]').addEventListener('click', () => dialog.close());
    dialog.addEventListener('click', (event) => { if (event.target === dialog) dialog.close(); });
    dialog.addEventListener('close', () => { document.body.classList.remove('review-is-open'); opener?.focus({ preventScroll: true }); });
    update();
}
