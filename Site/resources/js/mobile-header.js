document.addEventListener('DOMContentLoaded', () => {
	const header = document.querySelector('[data-mobile-header]');
	const toggle = header?.querySelector('[data-mobile-menu-toggle]');
	const menu = header?.querySelector('[data-mobile-menu]');

	if (!header || !toggle || !menu) return;

	const setOpen = (open) => {
		header.classList.toggle('is-open', open);
		toggle.setAttribute('aria-expanded', String(open));
		toggle.setAttribute('aria-label', open ? 'Закрыть меню' : 'Открыть меню');
		menu.setAttribute('aria-hidden', String(!open));
	};

	toggle.addEventListener('click', () => {
		setOpen(toggle.getAttribute('aria-expanded') !== 'true');
	});

	menu.querySelectorAll('a').forEach((link) => {
		link.addEventListener('click', () => setOpen(false));
	});

	document.addEventListener('keydown', (event) => {
		if (event.key === 'Escape' && toggle.getAttribute('aria-expanded') === 'true') {
			setOpen(false);
			toggle.focus();
		}
	});

	document.addEventListener('click', (event) => {
		if (toggle.getAttribute('aria-expanded') === 'true' && !header.contains(event.target)) {
			setOpen(false);
		}
	});
});
